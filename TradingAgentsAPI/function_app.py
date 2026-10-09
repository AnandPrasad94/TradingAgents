"""Azure Functions v2 Entry Point for TradingAgentsAPI (Subdirectory deployment)."""

import os
import sys
from pathlib import Path

# Ensure repo root is on sys.path if deployed from this folder
root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

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

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="health", methods=["GET", "OPTIONS"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    return handle_health(req)


@app.route(route="analyze", methods=["POST", "OPTIONS"])
def analyze(req: func.HttpRequest) -> func.HttpResponse:
    return handle_analyze(req)


@app.route(route="reports/{ticker}", methods=["GET", "OPTIONS"])
def get_report(req: func.HttpRequest) -> func.HttpResponse:
    return handle_get_report(req)


@app.route(route="reports", methods=["GET", "OPTIONS"])
def list_reports(req: func.HttpRequest) -> func.HttpResponse:
    return handle_list_reports(req)


@app.route(route="watchlist", methods=["GET", "POST", "DELETE", "OPTIONS"])
def watchlist(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "POST":
        return handle_watchlist_post(req)
    elif req.method == "DELETE":
        return handle_watchlist_delete(req)
    return handle_watchlist_get(req)


@app.route(route="chat", methods=["POST", "OPTIONS"])
def chat(req: func.HttpRequest) -> func.HttpResponse:
    return handle_chat(req)


@app.route(route="docs", methods=["GET", "OPTIONS"])
def docs(req: func.HttpRequest) -> func.HttpResponse:
    return handle_docs(req)


@app.route(route="", methods=["GET", "OPTIONS"])
def index(req: func.HttpRequest) -> func.HttpResponse:
    return handle_docs(req)
