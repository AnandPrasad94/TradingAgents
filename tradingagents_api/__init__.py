"""TradingAgentsAPI: Production REST API and Azure Functions backend for TradingAgents.

This package exposes the multi-agent trading framework as an API service,
fully compatible with Azure Functions (Python v2 model) and standalone ASGI/WSGI servers.
"""

__version__ = "0.6.0"

from .models import (
    AnalyzeRequest,
    AnalyzeResponse,
    ChatRequest,
    ChatResponse,
    HealthResponse,
    WatchlistRequest,
    WatchlistResponse,
)
from .service import TradingAgentsService

__all__ = [
    "__version__",
    "AnalyzeRequest",
    "AnalyzeResponse",
    "ChatRequest",
    "ChatResponse",
    "HealthResponse",
    "WatchlistRequest",
    "WatchlistResponse",
    "TradingAgentsService",
]
