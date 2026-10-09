"""Data models for TradingAgentsAPI requests and responses."""

from datetime import datetime
from typing import Any, Dict, List, Optional
try:
    from pydantic import BaseModel, Field
except ImportError:
    # Graceful fallback if pydantic is not yet installed in local environment
    class BaseModel:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
        def model_dump(self) -> dict:
            return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
        def dict(self) -> dict:
            return self.model_dump()
    def Field(default=None, **kwargs):
        return default


class DecisionMetrics(BaseModel):
    """Quantitative risk, target, and confidence metrics."""
    target_price: Optional[float] = Field(default=None, description="Projected target price")
    stop_loss: Optional[float] = Field(default=None, description="Stop-loss price level")
    confidence_score: Optional[float] = Field(default=None, description="Confidence rating 0-100%")
    risk_level: Optional[str] = Field(default="Moderate", description="Risk classification: Low, Moderate, High")
    recommended_allocation: Optional[str] = Field(default="5%", description="Recommended portfolio allocation percentage")
    grok_sentiment_score: Optional[float] = Field(default=None, description="Sentiment score -100 to +100")


class ThesesBreakdown(BaseModel):
    """Bull vs Bear debate theses."""
    bull_thesis: str = Field(default="", description="Bullish growth arguments")
    bear_thesis: str = Field(default="", description="Bearish downside arguments")


class AnalyzeRequest(BaseModel):
    """Request payload to initiate or query stock analysis."""
    ticker: str = Field(..., description="Stock or asset ticker symbol, e.g. NVDA, AAPL, BTC-USD")
    trade_date: Optional[str] = Field(default=None, description="Analysis date YYYY-MM-DD (defaults to current date)")
    asset_type: str = Field(default="stock", description="Asset type: 'stock' or 'crypto'")
    risk_profile: str = Field(default="Neutral", description="Risk profile: Aggressive, Neutral, Conservative")
    selected_analysts: Optional[List[str]] = Field(
        default=["market", "social", "news", "fundamentals"],
        description="Analyst modules to run"
    )
    max_debate_rounds: int = Field(default=1, description="Debate rounds between Bull and Bear agents")
    max_risk_rounds: int = Field(default=1, description="Risk discussion rounds")
    mock: bool = Field(default=False, description="Set True to return simulated institutional analysis without invoking paid LLM APIs")
    force_refresh: bool = Field(default=False, description="Bypass cache and force rerun")


class AnalyzeResponse(BaseModel):
    """Structured response containing multi-agent decision and insights."""
    task_id: str
    ticker: str
    trade_date: str
    asset_type: str
    decision: str  # BUY, OVERWEIGHT, HOLD, UNDERWEIGHT, SELL
    confidence: float
    summary: str
    metrics: DecisionMetrics
    theses: ThesesBreakdown
    agent_reports: Dict[str, Any]
    status: str
    timestamp: str
    is_mock: bool = False


class ReportResponse(BaseModel):
    """Report retrieval payload."""
    report_id: str
    ticker: str
    date: str
    decision: str
    markdown_content: Optional[str] = None
    html_url: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None


class WatchlistRequest(BaseModel):
    """Watchlist modification payload."""
    ticker: str


class WatchlistResponse(BaseModel):
    """Watchlist items."""
    tickers: List[str]
    count: int
    updated_at: str


class ChatRequest(BaseModel):
    """Interactive question to Grok/TradingAgents assistant."""
    ticker: str
    message: str
    context_report_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response from AI financial analyst assistant."""
    ticker: str
    reply: str
    source: str
    timestamp: str


class HealthResponse(BaseModel):
    """Health check response for monitoring and Azure probes."""
    status: str = "healthy"
    version: str
    service: str = "TradingAgentsAPI"
    runtime: str = "Azure Functions Python v2"
    llm_provider: str
    deep_think_llm: str
    quick_think_llm: str
    endpoints: List[str]
    timestamp: str
