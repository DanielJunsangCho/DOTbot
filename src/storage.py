from sqlalchemy import create_engine, Column, Integer, String, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from .schemas import ScrapeResult, EvaluationMetrics

Base = declarative_base()

class SketchyBehaviorRecord(Base):
    __tablename__ = "sketchy_behaviors"
    
    id = Column(Integer, primary_key=True)
    url = Column(String)
    source = Column(String)
    excerpt = Column(String)
    categories = Column(JSON)
    severity = Column(Integer)
    stance = Column(String)
    tone = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    evaluation_metrics = Column(JSON)

class StorageManager:
    def __init__(self, db_url: str = "sqlite:///sketchy_behaviors.db"):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
    
    async def store_result(
        self, 
        result: ScrapeResult,
        metrics: Optional[EvaluationMetrics] = None
    ):
        with Session(self.engine) as session:
            for report in result.structured_data:
                record = SketchyBehaviorRecord(
                    url=report.url,
                    source=report.source,
                    excerpt=report.excerpt,
                    categories=report.categories,
                    severity=report.severity,
                    stance=report.stance,
                    tone=report.tone,
                    evaluation_metrics=metrics.dict() if metrics else None
                )
                session.add(record)
            session.commit()
    
    async def get_records(
        self,
        source: Optional[str] = None,
        min_severity: Optional[int] = None
    ) -> List[SketchyBehaviorRecord]:
        with Session(self.engine) as session:
            query = session.query(SketchyBehaviorRecord)
            
            if source:
                query = query.filter(SketchyBehaviorRecord.source == source)
            
            if min_severity:
                query = query.filter(SketchyBehaviorRecord.severity >= min_severity)
            
            return query.all()
    
    async def get_statistics(self) -> dict:
        with Session(self.engine) as session:
            total = session.query(SketchyBehaviorRecord).count()
            by_source = session.query(
                SketchyBehaviorRecord.source,
                func.count(SketchyBehaviorRecord.id)
            ).group_by(SketchyBehaviorRecord.source).all()
            
            avg_severity = session.query(
                func.avg(SketchyBehaviorRecord.severity)
            ).scalar()
            
            return {
                "total_records": total,
                "records_by_source": dict(by_source),
                "average_severity": float(avg_severity) if avg_severity else 0
            }