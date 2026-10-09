"""Tests for TradingAgentsAPI and Azure Functions HTTP handlers."""

import json
import pytest

from tradingagents_api.models import (
    AnalyzeRequest,
    AnalyzeResponse,
    ChatRequest,
    ChatResponse,
    HealthResponse,
    WatchlistRequest,
    WatchlistResponse,
)
from tradingagents_api.service import TradingAgentsService, trading_service
from tradingagents_api.handlers import (
    handle_health,
    handle_analyze,
    handle_get_report,
    handle_list_reports,
    handle_watchlist_get,
    handle_watchlist_post,
    handle_watchlist_delete,
    handle_chat,
    handle_docs,
)


class MockHttpRequest:
    """Mock Azure Functions HttpRequest."""

    def __init__(self, method="GET", url="http://localhost:7071/api", headers=None, params=None, body=None, route_params=None):
        self.method = method
        self.url = url
        self.headers = headers or {}
        self.params = params or {}
        self.route_params = route_params or {}
        if body is None:
            self._body = b""
        elif isinstance(body, bytes):
            self._body = body
        elif isinstance(body, str):
            self._body = body.encode("utf-8")
        else:
            self._body = json.dumps(body).encode("utf-8")

    def get_json(self):
        if not self._body:
            return {}
        return json.loads(self._body.decode("utf-8"))

    def get_body(self):
        return self._body


@pytest.mark.unit
def test_models_instantiation():
    """Verify that Pydantic request and response models instantiate and serialize correctly."""
    req = AnalyzeRequest(ticker="NVDA", risk_profile="Aggressive", mock=True)
    assert req.ticker == "NVDA"
    assert req.risk_profile == "Aggressive"
    assert req.mock is True

    health = HealthResponse(
        version="0.6.0",
        llm_provider="openai",
        deep_think_llm="o3-mini",
        quick_think_llm="gpt-4o-mini",
        endpoints=["/api/health", "/api/analyze"],
        timestamp="2026-10-09T00:00:00",
    )
    assert health.status == "healthy"


@pytest.mark.unit
def test_service_mock_analysis():
    """Verify that TradingAgentsService returns complete structured reports in mock mode."""
    svc = TradingAgentsService()
    result = svc.analyze("NVDA", mock=True)
    assert result["ticker"] == "NVDA"
    assert result["decision"] in ["BUY", "HOLD", "SELL", "OVERWEIGHT", "UNDERWEIGHT"]
    assert "metrics" in result
    assert "target_price" in result["metrics"]
    assert "stop_loss" in result["metrics"]
    assert "theses" in result
    assert len(result["theses"]["bull_thesis"]) > 0
    assert len(result["theses"]["bear_thesis"]) > 0
    assert "agent_reports" in result


@pytest.mark.unit
def test_service_watchlist_operations():
    """Test watchlist retrieval and modifications."""
    svc = TradingAgentsService()
    initial_count = len(svc.get_watchlist())
    
    svc.add_to_watchlist("GOOGL")
    assert "GOOGL" in svc.get_watchlist()
    assert len(svc.get_watchlist()) == initial_count + 1

    svc.remove_from_watchlist("GOOGL")
    assert "GOOGL" not in svc.get_watchlist()


@pytest.mark.unit
def test_service_chat():
    """Verify contextual Q&A chat assistant."""
    svc = TradingAgentsService()
    reply = svc.chat("NVDA", "What are the primary bull drivers and risk factors?")
    assert len(reply) > 20
    assert "NVDA" in reply


@pytest.mark.unit
def test_handler_health():
    """Test GET /api/health handler."""
    req = MockHttpRequest(method="GET", url="http://localhost/api/health")
    resp = handle_health(req)
    assert resp.status_code == 200
    body = json.loads(resp.get_body().decode("utf-8"))
    assert body["status"] == "healthy"
    assert body["service"] == "TradingAgentsAPI"


@pytest.mark.unit
def test_handler_analyze():
    """Test POST /api/analyze handler."""
    req = MockHttpRequest(
        method="POST",
        url="http://localhost/api/analyze",
        body={"ticker": "NVDA", "mock": True}
    )
    resp = handle_analyze(req)
    assert resp.status_code == 200
    body = json.loads(resp.get_body().decode("utf-8"))
    assert body["ticker"] == "NVDA"
    assert body["status"] == "COMPLETED"


@pytest.mark.unit
def test_handler_get_report():
    """Test GET /api/reports/{ticker} handler."""
    req = MockHttpRequest(
        method="GET",
        url="http://localhost/api/reports/NVDA",
        route_params={"ticker": "NVDA"}
    )
    resp = handle_get_report(req)
    assert resp.status_code == 200
    body = json.loads(resp.get_body().decode("utf-8"))
    assert body["ticker"] == "NVDA"


@pytest.mark.unit
def test_handler_watchlist_lifecycle():
    """Test watchlist GET and POST handlers."""
    # GET
    get_req = MockHttpRequest(method="GET", url="http://localhost/api/watchlist")
    get_resp = handle_watchlist_get(get_req)
    assert get_resp.status_code == 200

    # POST
    post_req = MockHttpRequest(
        method="POST",
        url="http://localhost/api/watchlist",
        body={"ticker": "MSFT"}
    )
    post_resp = handle_watchlist_post(post_req)
    assert post_resp.status_code == 200
    body = json.loads(post_resp.get_body().decode("utf-8"))
    assert "MSFT" in body["watchlist"]


@pytest.mark.unit
def test_handler_chat():
    """Test POST /api/chat handler."""
    req = MockHttpRequest(
        method="POST",
        url="http://localhost/api/chat",
        body={"ticker": "NVDA", "message": "Why buy NVDA?"}
    )
    resp = handle_chat(req)
    assert resp.status_code == 200
    body = json.loads(resp.get_body().decode("utf-8"))
    assert body["ticker"] == "NVDA"
    assert len(body["reply"]) > 0


@pytest.mark.unit
def test_handler_docs():
    """Test GET /api/docs documentation handler."""
    req = MockHttpRequest(method="GET", url="http://localhost/api/docs")
    resp = handle_docs(req)
    assert resp.status_code == 200
    assert b"TradingAgentsAPI" in resp.get_body()
