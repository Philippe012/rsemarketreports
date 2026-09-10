import re
from typing import List

from services.normalization.clean_data import parse_number

MAX_POINTS = 60

KNOWN_LOCATIONS = {
    'rwanda': (-1.9403, 29.8739), 'kigali': (-1.9441, 30.0619),
    'kenya': (-0.0236, 37.9062), 'nairobi': (-1.2921, 36.8219),
    'uganda': (1.3733, 32.2903), 'kampala': (0.3476, 32.5825),
    'tanzania': (-6.3690, 34.8888), 'dar es salaam': (-6.7924, 39.2083),
    'burundi': (-3.3731, 29.9189), 'bujumbura': (-3.3822, 29.3644),
    'drc': (-4.0383, 21.7587), 'congo': (-4.0383, 21.7587), 'kinshasa': (-4.4419, 15.2663),
    'usa': (37.0902, -95.7129), 'united states': (37.0902, -95.7129),
    'uk': (55.3781, -3.4360), 'united kingdom': (55.3781, -3.4360),
    'china': (35.8617, 104.1954), 'india': (20.5937, 78.9629),
    'south africa': (-30.5595, 22.9375), 'nigeria': (9.0820, 8.6753),
    'ethiopia': (9.1450, 40.4897), 'egypt': (26.8206, 30.8025),
    'ghana': (7.9465, -1.0232), 'france': (46.2276, 2.2137),
    'germany': (51.1657, 10.4515), 'zambia': (-13.1339, 27.8493),
}

_LAT_NAME_RE = re.compile(r'\b(lat|latitude)\b', re.IGNORECASE)
_LON_NAME_RE = re.compile(r'\b(lon|lng|longitude)\b', re.IGNORECASE)
_LOCATION_NAME_RE = re.compile(r'\b(country|city|region|location|market|nation|branch)\b', re.IGNORECASE)


def _find_column(columns: List[dict], pattern: re.Pattern) -> dict | None:
    return next((c for c in columns if pattern.search(c.get('display_name', ''))), None)


def geographic_intelligence(datasets: List[dict]) -> dict:
    points: List[dict] = []

    for dataset in datasets:
        columns = dataset.get('columns', [])
        rows = dataset.get('rows', [])
        measures = [c for c in columns if c.get('semantic_type') in ('currency', 'number', 'quantity')]
        measure = measures[0] if measures else None

        lat_column, lon_column = _find_column(columns, _LAT_NAME_RE), _find_column(columns, _LON_NAME_RE)
        if lat_column and lon_column:
            for row in rows:
                lat = parse_number(row.get(lat_column['name']))
                lon = parse_number(row.get(lon_column['name']))
                if lat is None or lon is None:
                    continue
                points.append({
                    'label': dataset['name'], 'lat': lat, 'lon': lon, 'dataset': dataset['name'],
                    'value': parse_number(row.get(measure['name'])) if measure else None,
                })
            continue

        location_column = _find_column(columns, _LOCATION_NAME_RE) or next(
            (c for c in columns if c.get('semantic_type') == 'category'), None,
        )
        if not location_column:
            continue

        totals: dict = {}
        for row in rows:
            raw = row.get(location_column['name'])
            if not raw:
                continue
            key = str(raw).strip().lower()
            coords = KNOWN_LOCATIONS.get(key)
            if not coords:
                continue
            entry = totals.setdefault(key, {
                'label': str(raw), 'lat': coords[0], 'lon': coords[1],
                'dataset': dataset['name'], 'value': 0.0, 'count': 0,
            })
            if measure:
                value = parse_number(row.get(measure['name']))
                entry['value'] += value or 0
            entry['count'] += 1
        points.extend(totals.values())

    points = points[:MAX_POINTS]
    return {'has_geo': bool(points), 'points': points}
