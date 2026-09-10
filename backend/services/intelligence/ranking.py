from typing import List

MAX_FINDINGS = 8
_SEVERITY_SCORE = {'high': 3, 'medium': 2, 'low': 1}
_CATEGORY_SCORE = {'data_quality': 2, 'anomaly': 2, 'discovery': 1}


def _score(finding: dict) -> tuple:
    return (
        _SEVERITY_SCORE.get(finding['severity'], 0),
        _CATEGORY_SCORE.get(finding['category'], 0),
    )


def what_matters_most(discoveries: List[str], anomalies: List[dict], forensics: dict) -> List[dict]:
    findings: List[dict] = []

    for issue in forensics.get('issues', []):
        findings.append({
            'category': 'data_quality',
            'severity': issue.get('severity', 'medium'),
            'text': issue.get('message'),
            'dataset': issue.get('dataset'),
            'column': issue.get('column'),
        })

    for anomaly in anomalies:
        findings.append({
            'category': 'anomaly',
            'severity': anomaly.get('severity', 'medium'),
            'text': anomaly.get('message'),
            'dataset': anomaly.get('dataset'),
            'column': anomaly.get('column'),
        })

    for text in discoveries:
        findings.append({
            'category': 'discovery', 'severity': 'medium', 'text': text,
            'dataset': None, 'column': None,
        })

    findings.sort(key=_score, reverse=True)
    return findings[:MAX_FINDINGS]
