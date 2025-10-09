"""
FastAPI routers for DOTbot following CLAUDE.md standards.
"""

from .scraping import router as scraping_router
from .evaluation import router as evaluation_router
from .workflow import router as workflow_router

__all__ = [
    "scraping_router", 
    "evaluation_router",
    "workflow_router"
]