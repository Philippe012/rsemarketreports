from .base import AnswerEngine
from .generic_engine import GenericAnswerEngine
from .rse_engine import RseAnswerEngine


def get_answer_engine(extracted_data: dict) -> AnswerEngine:
    kind = (extracted_data or {}).get('kind')
    if kind == 'rse_market_report':
        return RseAnswerEngine(extracted_data)
    return GenericAnswerEngine(extracted_data)
