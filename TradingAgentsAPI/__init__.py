"""TradingAgentsAPI namespace forwarding to tradingagents_api."""

from tradingagents_api import (
    AnalyzeRequest,
    AnalyzeResponse,
    ChatRequest,
    ChatResponse,
    HealthResponse,
    TradingAgentsService,
    WatchlistRequest,
    WatchlistResponse,
    __version__,
)

__all__ = [
    "__version__",
    "AnalyzeRequest",
    "AnalyzeResponse",
    "ChatRequest",
    "ChatResponse",
    "HealthResponse",
    "TradingAgentsService",
    "WatchlistRequest",
    "WatchlistResponse",
]
