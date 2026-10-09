"""HTTP handlers and request dispatchers for Azure Functions v2."""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

try:
    import azure.functions as func
except ImportError:
    # Lightweight mock for local development and unit tests when azure-functions is not installed
    class func:
        class HttpRequest:
            def __init__(self, method="GET", url="", headers=None, params=None, body=b""):
                self.method = method
                self.url = url
                self.headers = headers or {}
                self.params = params or {}
                self._body = body
            def get_json(self):
                return json.loads(self._body.decode("utf-8")) if self._body else {}
        class HttpResponse:
            def __init__(self, body="", status_code=200, headers=None, mimetype="application/json"):
                self.body = body.encode("utf-8") if isinstance(body, str) else body
                self.status_code = status_code
                self.headers = headers or {}
                self.mimetype = mimetype
            def get_body(self):
                return self.body

from .service import trading_service

logger = logging.getLogger("tradingagents_api")

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
}


def _cors_response() -> func.HttpResponse:
    """Preflight OPTIONS response."""
    return func.HttpResponse(
        body="",
        status_code=204,
        headers=CORS_HEADERS,
    )


def json_response(payload: Any, status_code: int = 200) -> func.HttpResponse:
    """Serialize response payload to JSON with CORS headers."""
    headers = dict(CORS_HEADERS)
    headers["Content-Type"] = "application/json"
    
    if hasattr(payload, "model_dump"):
        data = payload.model_dump()
    elif hasattr(payload, "dict"):
        data = payload.dict()
    else:
        data = payload

    return func.HttpResponse(
        body=json.dumps(data, indent=2),
        status_code=status_code,
        headers=headers,
        mimetype="application/json",
    )


def error_response(message: str, status_code: int = 400, details: Optional[Any] = None) -> func.HttpResponse:
    """Standardized error JSON."""
    payload = {
        "error": message,
        "status_code": status_code,
        "timestamp": datetime.now().isoformat(),
    }
    if details:
        payload["details"] = details
    return json_response(payload, status_code=status_code)


def handle_health(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/health: Health check and diagnostic status."""
    if req.method == "OPTIONS":
        return _cors_response()

    payload = {
        "status": "healthy",
        "service": "TradingAgentsAPI",
        "version": "0.6.0",
        "runtime": "Azure Functions Python v2",
        "timestamp": datetime.now().isoformat(),
        "azure_region": os.environ.get("REGION_NAME", os.environ.get("LOCATION", "Azure Cloud")),
        "llm_provider": os.environ.get("TRADINGAGENTS_LLM_PROVIDER", "openai/azure_openai/grok"),
        "endpoints": [
            "GET /api/health",
            "POST /api/analyze",
            "GET /api/reports/{ticker}",
            "GET /api/reports",
            "GET /api/watchlist",
            "POST /api/watchlist",
            "DELETE /api/watchlist",
            "POST /api/chat",
            "GET /api/docs"
        ]
    }
    return json_response(payload)


def handle_analyze(req: func.HttpRequest) -> func.HttpResponse:
    """POST /api/analyze: Trigger or retrieve multi-agent stock analysis."""
    if req.method == "OPTIONS":
        return _cors_response()

    try:
        body = req.get_json() if req.method == "POST" else {}
    except Exception as e:
        return error_response(f"Invalid JSON body: {str(e)}", status_code=400)

    ticker = body.get("ticker") or req.params.get("ticker")
    if not ticker:
        return error_response("Missing required parameter 'ticker'.", status_code=400)

    trade_date = body.get("trade_date") or req.params.get("trade_date")
    asset_type = body.get("asset_type", "stock")
    risk_profile = body.get("risk_profile", "Neutral")
    selected_analysts = body.get("selected_analysts")
    mock = body.get("mock", False)
    force_refresh = body.get("force_refresh", False)

    try:
        result = trading_service.analyze(
            ticker=ticker,
            trade_date=trade_date,
            asset_type=asset_type,
            risk_profile=risk_profile,
            selected_analysts=selected_analysts,
            mock=mock,
            force_refresh=force_refresh,
        )
        return json_response(result, status_code=200)
    except Exception as e:
        logger.exception("Analysis execution failed for %s", ticker)
        return error_response(f"Analysis failed: {str(e)}", status_code=500)


def handle_get_report(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/reports/{ticker}: Retrieve latest report for a specific ticker."""
    if req.method == "OPTIONS":
        return _cors_response()

    ticker = req.route_params.get("ticker") if hasattr(req, "route_params") and req.route_params else None
    if not ticker:
        ticker = req.params.get("ticker")
    if not ticker:
        return error_response("Ticker symbol required in route or query param.", status_code=400)

    report = trading_service.get_report(ticker)
    if not report:
        return error_response(f"No report found for ticker '{ticker}'.", status_code=404)

    return json_response(report)


def handle_list_reports(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/reports: List all generated reports in cache."""
    if req.method == "OPTIONS":
        return _cors_response()

    reports = trading_service.list_reports()
    return json_response({
        "reports": reports,
        "count": len(reports),
        "timestamp": datetime.now().isoformat(),
    })


def handle_watchlist_get(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/watchlist: Return bookmarked tickers."""
    if req.method == "OPTIONS":
        return _cors_response()

    tickers = trading_service.get_watchlist()
    return json_response({
        "watchlist": tickers,
        "count": len(tickers),
        "timestamp": datetime.now().isoformat(),
    })


def handle_watchlist_post(req: func.HttpRequest) -> func.HttpResponse:
    """POST /api/watchlist: Add ticker to watchlist."""
    if req.method == "OPTIONS":
        return _cors_response()

    try:
        body = req.get_json()
        ticker = body.get("ticker")
    except Exception:
        ticker = req.params.get("ticker")

    if not ticker:
        return error_response("Ticker symbol is required.", status_code=400)

    updated = trading_service.add_to_watchlist(ticker)
    return json_response({
        "message": f"Added {ticker.upper()} to watchlist",
        "watchlist": updated,
        "count": len(updated),
    })


def handle_watchlist_delete(req: func.HttpRequest) -> func.HttpResponse:
    """DELETE /api/watchlist: Remove ticker from watchlist."""
    if req.method == "OPTIONS":
        return _cors_response()

    ticker = req.params.get("ticker")
    if not ticker:
        try:
            body = req.get_json()
            ticker = body.get("ticker")
        except Exception:
            pass

    if not ticker:
        return error_response("Ticker symbol is required.", status_code=400)

    updated = trading_service.remove_from_watchlist(ticker)
    return json_response({
        "message": f"Removed {ticker.upper()} from watchlist",
        "watchlist": updated,
        "count": len(updated),
    })


def handle_chat(req: func.HttpRequest) -> func.HttpResponse:
    """POST /api/chat: Contextual AI assistant conversation."""
    if req.method == "OPTIONS":
        return _cors_response()

    try:
        body = req.get_json()
        ticker = body.get("ticker", "NVDA")
        message = body.get("message", "")
    except Exception as e:
        return error_response(f"Invalid JSON: {str(e)}", status_code=400)

    if not message:
        return error_response("Message cannot be empty.", status_code=400)

    reply = trading_service.chat(ticker, message)
    return json_response({
        "ticker": ticker.upper(),
        "reply": reply,
        "source": "Grok AI Multi-Agent Node",
        "timestamp": datetime.now().isoformat(),
    })


def handle_docs(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/docs: Interactive HTML documentation with endpoints and curl examples."""
    if req.method == "OPTIONS":
        return _cors_response()

    html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>TradingAgentsAPI - Azure Functions Documentation</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 font-sans p-6 min-h-screen">
  <div class="max-w-4xl mx-auto space-y-6">
    <div class="border-b border-slate-800 pb-4">
      <div class="flex items-center gap-2">
        <span class="text-2xl font-black bg-gradient-to-r from-purple-400 to-emerald-400 bg-clip-text text-transparent">TradingAgentsAPI</span>
        <span class="text-xs bg-purple-900/60 text-purple-300 px-2 py-0.5 rounded border border-purple-500/30">v0.6.0 Azure Functions</span>
      </div>
      <p class="text-xs text-slate-400 mt-1">Institutional Multi-Agent Financial Research Desk deployed on Azure Functions Python v2</p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div class="bg-slate-900 p-4 rounded-xl border border-slate-800">
        <div class="text-xs font-semibold text-emerald-400 uppercase tracking-wide">POST /api/analyze</div>
        <p class="text-xs text-slate-300 mt-1">Initiates 7-agent pipeline (Market, Sentiment, News, Fundamentals, Bull vs Bear, Risk Manager).</p>
        <pre class="bg-slate-950 p-2.5 rounded text-[11px] text-purple-300 mt-2 overflow-x-auto">curl -X POST "https://&lt;app&gt;.azurewebsites.net/api/analyze" \\
  -H "Content-Type: application/json" \\
  -d '{"ticker": "NVDA", "risk_profile": "Neutral", "mock": false}'</pre>
      </div>

      <div class="bg-slate-900 p-4 rounded-xl border border-slate-800">
        <div class="text-xs font-semibold text-cyan-400 uppercase tracking-wide">GET /api/reports/{ticker}</div>
        <p class="text-xs text-slate-300 mt-1">Fetches latest synthesized research report, target prices, and theses.</p>
        <pre class="bg-slate-950 p-2.5 rounded text-[11px] text-cyan-300 mt-2 overflow-x-auto">curl "https://&lt;app&gt;.azurewebsites.net/api/reports/NVDA"</pre>
      </div>

      <div class="bg-slate-900 p-4 rounded-xl border border-slate-800">
        <div class="text-xs font-semibold text-purple-400 uppercase tracking-wide">POST /api/chat</div>
        <p class="text-xs text-slate-300 mt-1">Contextual Q&A with Grok AI analyst tied to the current report state.</p>
        <pre class="bg-slate-950 p-2.5 rounded text-[11px] text-purple-300 mt-2 overflow-x-auto">curl -X POST "https://&lt;app&gt;.azurewebsites.net/api/chat" \\
  -H "Content-Type: application/json" \\
  -d '{"ticker": "NVDA", "message": "Why is the target price set to $215?"}'</pre>
      </div>

      <div class="bg-slate-900 p-4 rounded-xl border border-slate-800">
        <div class="text-xs font-semibold text-amber-400 uppercase tracking-wide">GET /api/health</div>
        <p class="text-xs text-slate-300 mt-1">Readiness probe for Azure App Service & monitoring.</p>
        <pre class="bg-slate-950 p-2.5 rounded text-[11px] text-amber-300 mt-2 overflow-x-auto">curl "https://&lt;app&gt;.azurewebsites.net/api/health"</pre>
      </div>
    </div>
  </div>
</body>
</html>"""

    return func.HttpResponse(
        body=html,
        status_code=200,
        headers={"Content-Type": "text/html"},
        mimetype="text/html",
    )
