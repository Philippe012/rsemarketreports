from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

SemanticType = Literal[
    'identifier', 'category', 'date', 'datetime', 'number',
    'currency', 'percentage', 'quantity', 'text', 'boolean',
]
Confidence = Literal['high', 'medium', 'low']
ChartType = Literal['line', 'bar', 'pie']
MetricKind = Literal['sum', 'average', 'count']


class ColumnStats(BaseModel):
    model_config = {'extra': 'forbid'}

    min: Optional[float] = None
    max: Optional[float] = None
    mean: Optional[float] = None
    std: Optional[float] = None
    unique_count: Optional[int] = None
    missing_count: int = 0


class ColumnModel(BaseModel):
    model_config = {'extra': 'forbid'}

    name: str
    display_name: str
    semantic_type: SemanticType
    data_type: str
    nullable: bool
    non_null_count: int = Field(ge=0)
    total_count: int = Field(ge=0)
    confidence: Confidence
    sample_values: List[Any] = Field(default_factory=list, max_length=5)
    stats: Optional[ColumnStats] = None

    @field_validator('non_null_count')
    @classmethod
    def _non_null_within_total(cls, v, info):
        total = info.data.get('total_count')
        if total is not None and v > total:
            raise ValueError('non_null_count cannot exceed total_count')
        return v


class DatasetModel(BaseModel):
    model_config = {'extra': 'forbid'}

    name: str
    source: str
    columns: List[ColumnModel]
    rows: List[dict]
    row_count: int = Field(ge=0)
    duplicate_row_count: int = Field(default=0, ge=0)


class MetricModel(BaseModel):
    model_config = {'extra': 'forbid'}

    label: str
    value: Any
    dataset: str
    column: str
    kind: MetricKind
    format_hint: Literal['number', 'currency', 'percentage', 'quantity']


class ChartModel(BaseModel):
    model_config = {'extra': 'forbid'}

    dataset: str
    chart_type: ChartType
    x: str
    y: str
    title: str


class SectionModel(BaseModel):
    model_config = {'extra': 'forbid'}

    title: Optional[str] = None
    content: str


class FigureModel(BaseModel):
    model_config = {'extra': 'forbid'}

    source: str
    width: Optional[int] = None
    height: Optional[int] = None
    format: str
    thumbnail: Optional[str] = None


class EntitiesModel(BaseModel):
    model_config = {'extra': 'forbid'}

    numbers: List[str] = Field(default_factory=list)
    dates: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)


class DocumentModel(BaseModel):
    model_config = {'extra': 'forbid'}

    kind: Literal['generic_document'] = 'generic_document'
    filename: str
    source_type: Literal['pdf', 'excel', 'csv', 'docx', 'txt']
    document_type: str
    document_type_confidence: Confidence
    sections: List[SectionModel]
    datasets: List[DatasetModel]
    metrics: List[MetricModel]
    charts: List[ChartModel]
    figures: List[FigureModel] = Field(default_factory=list)
    insights: List[str] = Field(default_factory=list)
    entities: EntitiesModel = Field(default_factory=lambda: EntitiesModel())


def validate_document_shape(document: dict) -> dict:
    return DocumentModel(**document).model_dump()
