from typing import List, Optional

from .adapter import to_analysis_datasets
from .alerts import evaluate_alerts
from .anomalies import detect_anomalies
from .discoveries import compute_discoveries
from .forensics import compute_forensics
from .geography import geographic_intelligence
from .ranking import what_matters_most
from .relationships import entity_relationship_graph
from .trading import trading_analytics
from .vision import document_vision_summary


def _investigate_summary(datasets: list, forensics: dict, anomalies: list, discoveries: list) -> str:
    total_rows = sum(d.get('row_count', 0) for d in datasets)
    parts = [f'{len(datasets)} dataset(s) covering {total_rows} record(s) analyzed.']

    if forensics['quality_score'] < 100:
        parts.append(f"Data quality score: {forensics['quality_score']}/100.")

    high_anomalies = [a for a in anomalies if a['severity'] == 'high']
    if high_anomalies:
        plural = 'anomaly' if len(high_anomalies) == 1 else 'anomalies'
        parts.append(f'{len(high_anomalies)} high-severity {plural} detected.')

    if discoveries:
        parts.append(f'{len(discoveries)} notable pattern(s) found — see Discoveries.')

    if not high_anomalies and forensics['quality_score'] >= 90 and not discoveries:
        parts.append('No major issues or notable patterns detected.')

    return ' '.join(parts)


def build_analysis(extracted_data: dict, alert_rules: Optional[List[dict]] = None) -> dict:
    datasets = to_analysis_datasets(extracted_data)
    forensics = compute_forensics(datasets)
    anomalies = detect_anomalies(datasets)
    discoveries = compute_discoveries(extracted_data)
    ranked = what_matters_most(discoveries, anomalies, forensics)
    is_rse = extracted_data.get('kind') == 'rse_market_report'

    return {
        'investigate': {
            'summary': _investigate_summary(datasets, forensics, anomalies, discoveries),
            'key_metrics': extracted_data.get('metrics') or [],
        },
        'forensics': forensics,
        'anomalies': anomalies,
        'discoveries': discoveries,
        'what_matters_most': ranked,
        'relationships': entity_relationship_graph(datasets),
        'geography': geographic_intelligence(datasets),
        'vision': document_vision_summary(extracted_data, datasets),
        'alerts': evaluate_alerts(alert_rules or [], extracted_data),
        'trading': trading_analytics(extracted_data) if is_rse else None,
    }
