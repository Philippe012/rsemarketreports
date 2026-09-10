from typing import Iterable, List

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

SORT_FIELDS = {
    'created_at': lambda r: r.created_at,
    'report_date': lambda r: r.report_date or r.created_at.date(),
    'filename': lambda r: (r.original_filename or '').lower(),
    'value': lambda r: r.headline_metric_value if r.headline_metric_value is not None else float('-inf'),
}


def document_type_of(report) -> str:
    data = report.extracted_data or {}
    if not data:
        return ''
    
    if data.get('kind') == 'rse_market_report' or 'market_overview' in data:
        return 'RSE market report'
    return data.get('document_type') or ''


def year_of(report) -> int:
    if report.report_date:
        return report.report_date.year
    return report.created_at.year


def apply_filters(reports: Iterable, params) -> List:
    search = (params.get('search') or '').strip().lower()
    source_type = (params.get('source_type') or '').strip()
    status_filter = (params.get('status') or '').strip()
    year = (params.get('year') or '').strip()
    document_type = (params.get('document_type') or '').strip().lower()

    filtered = []
    for r in reports:
        if search and search not in r.original_filename.lower():
            continue
        if source_type and r.source_type != source_type:
            continue
        if status_filter and r.status != status_filter:
            continue
        if year and str(year_of(r)) != year:
            continue
        if document_type and document_type not in document_type_of(r).lower():
            continue
        filtered.append(r)
    return filtered


def apply_sort(reports: List, sort_param) -> List:
    sort_param = (sort_param or '-created_at').strip()
    reverse = sort_param.startswith('-')
    key = sort_param[1:] if reverse else sort_param
    key_fn = SORT_FIELDS.get(key, SORT_FIELDS['created_at'])
    return sorted(reports, key=key_fn, reverse=reverse)


def paginate(reports: List, params) -> tuple:
    try:
        page = max(int(params.get('page', 1)), 1)
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = min(max(int(params.get('page_size', DEFAULT_PAGE_SIZE)), 1), MAX_PAGE_SIZE)
    except (TypeError, ValueError):
        page_size = DEFAULT_PAGE_SIZE

    count = len(reports)
    total_pages = max(-(-count // page_size), 1) 
    page = min(page, total_pages)
    start = (page - 1) * page_size
    page_items = reports[start:start + page_size]
    meta = {'count': count, 'page': page, 'page_size': page_size, 'total_pages': total_pages}
    return page_items, meta


def available_facets(reports: Iterable) -> dict:
    reports = list(reports)
    years = sorted({year_of(r) for r in reports}, reverse=True)
    source_types = sorted({r.source_type for r in reports})
    document_types = sorted({dt for r in reports if (dt := document_type_of(r))})
    return {'years': years, 'source_types': source_types, 'document_types': document_types}
