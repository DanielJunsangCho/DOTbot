from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

class AISketchyReport(BaseModel):
    url: str
    excerpt: str
    categories: List[str]
    severity: int
    source: str
    date: Optional[str]
    stance: Optional[str]
    tone: Optional[str]

class ScrapeResult(BaseModel):
    structured_data: List[AISketchyReport]
    metadata: Dict[str, any]

class RawScrapeData(BaseModel):
    url: str
    text: str
    source: str
    timestamp: datetime

class BehaviorClassification(BaseModel):
    excerpt: str
    categories: List[str]
    severity: int
    stance: str
    tone: str

class EvaluationMetrics(BaseModel):
    recall: float
    precision_llm: float
    semantic_fidelity: float
    faithfulness: float
    coverage: float
    novelty_score: float
    llm_agreement: float