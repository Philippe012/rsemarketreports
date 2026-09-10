from typing import List

_CHART_RATIO_RANGE = (0.6, 1.8)
_CHART_CAPTION_HINTS = ('chart', 'graph', 'plot', 'figure')


def _classify_figure(figure: dict) -> str:
    width, height = figure.get('width'), figure.get('height')
    source = (figure.get('source') or '').lower()
    if any(hint in source for hint in _CHART_CAPTION_HINTS):
        return 'chart_or_diagram'
    if width and height:
        ratio = width / height
        if _CHART_RATIO_RANGE[0] <= ratio <= _CHART_RATIO_RANGE[1]:
            return 'chart_or_diagram'
    return 'image'


def document_vision_summary(extracted_data: dict, datasets: List[dict]) -> dict:
    charts = extracted_data.get('charts') or []
    figures = extracted_data.get('figures') or []

    figure_kinds = {'chart_or_diagram': 0, 'image': 0}
    for figure in figures:
        figure_kinds[_classify_figure(figure)] += 1

    return {
        'tables_detected': len(datasets),
        'charts_suggested': len(charts),
        'figures_total': len(figures),
        'figures_chart_like': figure_kinds['chart_or_diagram'],
        'figures_photo_or_diagram': figure_kinds['image'],
        'forms_detected': 0,
    }
