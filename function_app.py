"""Azure Functions v2 Entry Point for TradingAgentsAPI.

This file is automatically indexed by the Azure Functions host runtime.
"""

import logging
import azure.functions as func

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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tradingagents_api")

# Initialize Azure Functions Python v2 application
# Anonymous auth level allows mobile client / web clients to call endpoints directly.
# For production enterprise deployments, set to func.AuthLevel.FUNCTION or integrate Azure Easy Auth / Entra ID.
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="health", methods=["GET", "OPTIONS"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    """Readiness and liveness probe."""
    return handle_health(req)


@app.route(route="analyze", methods=["POST", "OPTIONS"])
def analyze(req: func.HttpRequest) -> func.HttpResponse:
    """Execute or retrieve multi-agent stock research analysis."""
    return handle_analyze(req)


@app.route(route="reports/{ticker}", methods=["GET", "OPTIONS"])
def get_report(req: func.HttpRequest) -> func.HttpResponse:
    """Fetch synthesized research report for a specific ticker."""
    return handle_get_report(req)


@app.route(route="reports", methods=["GET", "OPTIONS"])
def list_reports(req: func.HttpRequest) -> func.HttpResponse:
    """List recent research reports stored in cache."""
    return handle_list_reports(req)


@app.route(route="watchlist", methods=["GET", "POST", "DELETE", "OPTIONS"])
def watchlist(req: func.HttpRequest) -> func.HttpResponse:
    """Manage user watchlist (GET, POST, DELETE)."""
    if req.method == "POST":
        return handle_watchlist_post(req)
    elif req.method == "DELETE":
        return handle_watchlist_delete(req)
    return handle_watchlist_get(req)


@app.route(route="chat", methods=["POST", "OPTIONS"])
def chat(req: func.HttpRequest) -> func.HttpResponse:
    """Interactive Q&A with Grok AI analyst tied to report context."""
    return handle_chat(req)


@app.route(route="docs", methods=["GET", "OPTIONS"])
def docs(req: func.HttpRequest) -> func.HttpResponse:
    """Interactive web documentation and curl instructions."""
    return handle_docs(req)


@app.route(route="", methods=["GET", "OPTIONS"])
def index(req: func.HttpRequest) -> func.HttpResponse:
    """Root redirect to documentation."""
    return handle_docs(req)
