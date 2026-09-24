from typing import List, Optional

from .base import AnswerEngine, AnswerResult, Source, not_found
from .fact_index import FactIndex
from .formatting import num, percent
from .text_match import best_matching_text, tokenize

_COMPARE_TRIGGERS = ('compare', ' vs ', ' vs. ', ' versus ')

_AGGREGATE_WORDS = {
    'sum': ['total', 'sum'],
    'average': ['average', 'mean'],
}

MAX_LIST_ITEMS = 12
EXCERPT_LENGTH = 320


def _words(*parts) -> set:
    words = set()
    for part in parts:
        if part:
            words.update(tokenize(str(part)))
    return words


def _format_metric_value(metric: dict) -> str:
    value = metric.get('value')
    if value is None:
        return 'not available in this document'
    hint = metric.get('format_hint')
    if hint == 'percentage':
        return percent(value, signed=False)
    if isinstance(value, (int, float)):
        return num(value, 2 if hint in ('currency',) else 0)
    return str(value)


class GenericAnswerEngine(AnswerEngine):
    def __init__(self, data: dict):
        self._data = data
        self._index = FactIndex()
        self._sections: List[dict] = data.get('sections') or []
        self._comparables: dict = {}
        self._build()

    # -- index construction ---------------------------------------------------

    def _build(self) -> None:
        self._build_overview()
        self._build_datasets()
        self._build_metrics()
        self._build_insights()
        self._build_entities()
        self._build_intelligence()

    def _build_intelligence(self) -> None:
        """Extends the AI Analyst with the Advanced Intelligence layer:
        "what matters most", "what looks unusual", and data-quality
        questions, all backed by services.intelligence rather than a
        second copy of that logic."""
        from services.intelligence.adapter import to_analysis_datasets
        from services.intelligence.anomalies import detect_anomalies
        from services.intelligence.forensics import compute_forensics
        from services.intelligence.ranking import what_matters_most

        datasets = to_analysis_datasets(self._data)
        forensics = compute_forensics(datasets)
        anomalies = detect_anomalies(datasets)
        ranked = what_matters_most(self._data.get('insights') or [], anomalies, forensics)

        if ranked:
            summary = ' '.join(f'({i + 1}) {f["text"]}' for i, f in enumerate(ranked[:5]))
            self._index.add(
                ['matters', 'most', 'important', 'priority'],
                f'What matters most in this document: {summary}',
                Source('What matters most'),
            )

        if anomalies:
            summary = ' '.join(a['message'] for a in anomalies[:5])
            self._index.add(
                ['unusual', 'anomaly', 'anomalies', 'outlier', 'outliers', 'strange', 'odd', 'suspicious'],
                f'Unusual values detected: {summary}',
                Source('Anomaly radar'),
            )
        else:
            self._index.add(
                ['unusual', 'anomaly', 'anomalies', 'outlier', 'outliers', 'strange', 'odd', 'suspicious'],
                "No statistical anomalies were detected in this document's numeric data.",
                Source('Anomaly radar'),
            )

        self._index.add(
            ['quality', 'clean', 'reliable', 'trustworthy'],
            (
                f"Data quality score: {forensics['quality_score']}/100, based on "
                f"{forensics['missing_cells']} missing value(s) and {forensics['duplicate_rows']} "
                f"duplicate row(s) out of {forensics['total_rows']} record(s)."
            ),
            Source('Data forensics'),
        )

    def _try_compare(self, question: str) -> Optional[AnswerResult]:
        """Handles "compare X and Y" style questions by looking up each
        named entity's already-indexed identifier summary directly, rather
        than relying on FactIndex.best_match, which only ever returns one
        single best fact."""
        lowered = question.lower()
        if not any(trigger in lowered for trigger in _COMPARE_TRIGGERS):
            return None
        matches = [summary for key, summary in self._comparables.items() if key in lowered]
        if len(matches) < 2:
            return None
        return AnswerResult(answer=' '.join(matches[:4]), sources=[Source('Comparison')], confidence='medium')

    def _build_overview(self) -> None:
        doc_type = self._data.get('document_type') or 'General document'
        datasets = self._data.get('datasets') or []
        total_rows = sum(d.get('row_count', 0) for d in datasets)
        src = Source('Document overview')
        self._index.add(
            ['document', 'type', 'kind'],
            f"This document was classified as \"{doc_type}\", with {len(datasets)} dataset(s) "
            f"totalling {total_rows} record(s) and {len(self._sections)} section(s) of text.",
            src,
        )

    def _build_datasets(self) -> None:
        for dataset in self._data.get('datasets') or []:
            name = dataset.get('name') or ''
            name_words = _words(name)
            src = Source(f'Dataset: {name}')
            self._index.add(
                name_words | {'many', 'records', 'rows', 'count'},
                f"The \"{name}\" dataset has {dataset.get('row_count', 0)} record(s) "
                f"({dataset.get('duplicate_row_count', 0)} flagged as duplicates).",
                src,
            )

            columns = dataset.get('columns') or []
            self._index.add(
                name_words | {'columns', 'fields'},
                f"The \"{name}\" dataset has these columns: {', '.join(c.get('display_name', c.get('name', '')) for c in columns)}.",
                src,
            )

            for column in columns:
                stats = column.get('stats')
                if not stats:
                    continue
                col_words = _words(column.get('display_name'), column.get('name'))
                col_src = Source(f'Dataset: {name}', column.get('display_name'))
                if stats.get('max') is not None:
                    self._index.add(
                        name_words | col_words | {'highest', 'maximum', 'max', 'largest'},
                        f"The highest {column.get('display_name')} in \"{name}\" is {num(stats['max'], 2)}.",
                        col_src,
                    )
                if stats.get('min') is not None:
                    self._index.add(
                        name_words | col_words | {'lowest', 'minimum', 'min', 'smallest'},
                        f"The lowest {column.get('display_name')} in \"{name}\" is {num(stats['min'], 2)}.",
                        col_src,
                    )

            self._build_identifier_lookups(dataset, name_words)

    def _build_identifier_lookups(self, dataset: dict, dataset_name_words: set) -> None:
        columns = dataset.get('columns') or []
        identifier_columns = [c for c in columns if c.get('semantic_type') == 'identifier']
        if not identifier_columns:
            return
        display_columns = [c for c in columns if c.get('semantic_type') != 'identifier'][:5]
        for row in dataset.get('rows') or []:
            for id_col in identifier_columns:
                id_value = row.get(id_col['name'])
                if id_value in (None, ''):
                    continue
                id_words = tokenize(str(id_value))
                if not id_words:
                    continue
                parts = [
                    f"{c.get('display_name')} {row.get(c['name'])}"
                    for c in display_columns if row.get(c['name']) not in (None, '')
                ]
                if not parts:
                    continue
                summary = f"{id_value} ({dataset.get('name')}) — {', '.join(parts)}."
                self._index.add(
                    set(id_words) | dataset_name_words,
                    f"For {id_col.get('display_name')} \"{id_value}\" in \"{dataset.get('name')}\": {', '.join(parts)}.",
                    Source(f"Dataset: {dataset.get('name')}", f"{id_col.get('display_name')} {id_value}"),
                )
                key = str(id_value).strip().lower()
                if key:
                    self._comparables[key] = summary

    def _build_metrics(self) -> None:
        for metric in self._data.get('metrics') or []:
            kind = metric.get('kind')
            words = _AGGREGATE_WORDS.get(kind)
            if not words:
                continue 
            column_words = _words(metric.get('column'))
            dataset_words = _words(metric.get('dataset'))
            self._index.add(
                dataset_words | column_words | set(words),
                f"{metric.get('label')} is {_format_metric_value(metric)}.",
                Source(f"Dataset: {metric.get('dataset')}", metric.get('column') or ''),
            )

    def _build_insights(self) -> None:
        insights = self._data.get('insights') or []
        if not insights:
            return
        self._index.add(
            ['insights', 'insight', 'highlights', 'key', 'findings'],
            ' '.join(insights[:MAX_LIST_ITEMS]),
            Source('Insights'),
        )

    def _build_entities(self) -> None:
        entities = self._data.get('entities') or {}
        dates = entities.get('dates') or []
        numbers = entities.get('numbers') or []
        keywords = entities.get('keywords') or []

        self._index.add(
            ['dates', 'date', 'when'],
            (f"Dates mentioned in this document: {', '.join(dates[:MAX_LIST_ITEMS])}." if dates
             else 'No dates were found in this document.'),
            Source('Extracted entities', 'Dates'),
        )
        self._index.add(
            ['numbers', 'percentages', 'percent', 'figures', 'amounts'],
            (f"Numbers and percentages mentioned in this document: {', '.join(numbers[:MAX_LIST_ITEMS])}." if numbers
             else 'No standalone numbers or percentages were found in this document\'s text.'),
            Source('Extracted entities', 'Numbers'),
        )
        self._index.add(
            ['keywords', 'topics', 'themes', 'terms'],
            (f"Frequently mentioned terms in this document: {', '.join(keywords[:MAX_LIST_ITEMS])}." if keywords
             else 'No frequently repeated terms were identified in this document.'),
            Source('Extracted entities', 'Keywords'),
        )


    def _search_sections(self, question: str) -> Optional[AnswerResult]:
        if not self._sections:
            return None
        texts = [f"{s.get('title') or ''} {s.get('content') or ''}" for s in self._sections]
        index = best_matching_text(question, texts)
        if index == -1:
            return None
        section = self._sections[index]
        content = section.get('content') or ''
        excerpt = content if len(content) <= EXCERPT_LENGTH else content[:EXCERPT_LENGTH].rsplit(' ', 1)[0] + '…'
        title = section.get('title') or 'Untitled section'
        return AnswerResult(
            answer=f"From \"{title}\": {excerpt}",
            sources=[Source('Section', title)],
            confidence='medium',
        )

 
    def answer(self, question: str) -> AnswerResult:
        comparison = self._try_compare(question)
        if comparison is not None:
            return comparison

        fact = self._index.best_match(question)
        if fact is not None:
            return AnswerResult(answer=fact.answer_text, sources=[fact.source], confidence=fact.confidence)

        narrative = self._search_sections(question)
        if narrative is not None:
            return narrative

        return not_found()

    def suggested_questions(self) -> List[str]:
        questions: List[str] = ['What is this document about?']
        datasets = self._data.get('datasets') or []
        metrics = self._data.get('metrics') or []
        sections = self._sections
        insights = self._data.get('insights') or []
        entities = self._data.get('entities') or {}

        if datasets:
            questions.append(f"How many records are in the \"{datasets[0].get('name')}\" dataset?")
        for metric in metrics:
            if metric.get('kind') == 'sum':
                questions.append(f"What is the {metric.get('label', '').lower()}?")
                break
        if sections and sections[0].get('title'):
            questions.append(f"What does the \"{sections[0]['title']}\" section say?")
        if insights:
            questions.append('What are the key insights from this document?')
        if entities.get('dates'):
            questions.append('What dates are mentioned in this document?')
        questions.append('What matters most in this document?')
        questions.append('What looks unusual?')

        return questions[:6]
