# TradingAgentsAPI - Azure Functions Deployment Guide

This repository contains **TradingAgentsAPI**, a production-ready REST API built on the **Azure Functions Python v2 Programming Model**. It exposes the full institutional multi-agent stock research capabilities of `TradingAgents` directly over HTTP.

---

## 1. System Architecture & Endpoints

The API is defined in `function_app.py` using Python v2 decorators (`@app.route`). It supports CORS for mobile and web frontend clients, structured JSON input/output, and intelligent fallback/mock mode for fast testing.

| Method | Endpoint | Description |
|---|---|---|
| **GET** | `/api/health` | Service health status, environment diagnostics & readiness probe |
| **POST** | `/api/analyze` | Execute or retrieve 7-agent stock analysis (Market, Sentiment, News, Fundamentals, Bull/Bear debate, Risk) |
| **GET** | `/api/reports/{ticker}` | Retrieve latest research report, target prices, and theses for a ticker |
| **GET** | `/api/reports` | List all cached research reports |
| **GET** | `/api/watchlist` | Retrieve saved tickers from watchlist |
| **POST** | `/api/watchlist` | Add a ticker to watchlist (`{"ticker": "NVDA"}`) |
| **DELETE** | `/api/watchlist` | Remove a ticker from watchlist |
| **POST** | `/api/chat` | Interactive Grok AI financial assistant Q&A tied to ticker context |
| **GET** | `/api/docs` | Interactive web documentation & curl snippets |

---

## 2. Deployment Methods

### Method 1: Continuous Deployment via GitHub Actions (Recommended)

This repository includes `.github/workflows/azure-functions.yml`.

1. **Create an Azure Function App** in the Azure Portal or via Azure CLI:
   - **Runtime stack:** Python
   - **Version:** 3.11 or 3.12
   - **OS:** Linux
   - **Plan:** Flex Consumption, Consumption (Serverless), or Premium (EP1)

2. **Download the Publish Profile:**
   - In Azure Portal, navigate to your Function App.
   - Click **Get publish profile** on the Overview toolbar and copy the contents.

3. **Add GitHub Secret:**
   - In your GitHub repo, go to **Settings > Secrets and variables > Actions**.
   - Create a new repository secret named `AZURE_FUNCTIONAPP_PUBLISH_PROFILE` and paste the publish profile XML.
   - (Optional) Add `AZURE_FUNCTIONAPP_NAME` with your function app name (e.g. `TradingAgentsAPI`).

4. **Push to Main:**
   - Every `git push` to `main` will automatically build, test, and deploy the function app!

---

### Method 2: Deployment via Azure CLI

You can deploy directly using the Azure CLI from your local terminal:

```bash
# 1. Login to Azure
az login

# 2. Create a Resource Group
az group create --name TradingAgents-RG --location eastus

# 3. Create a Storage Account
az storage account create \
  --name tradingagentsstorage \
  --location eastus \
  --resource-group TradingAgents-RG \
  --sku Standard_LRS

# 4. Create the Linux Python Function App (Consumption or Premium)
az functionapp create \
  --resource-group TradingAgents-RG \
  --consumption-plan-location eastus \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --name TradingAgentsAPI \
  --storage-account tradingagentsstorage \
  --os-type Linux

# 5. Deploy the repository
az functionapp deployment source config-zip \
  --resource-group TradingAgents-RG \
  --name TradingAgentsAPI \
  --src <zip-file-of-repo>
```

Or deploy directly from GitHub source:

```bash
az functionapp deployment source config \
  --name TradingAgentsAPI \
  --resource-group TradingAgents-RG \
  --repo-url https://github.com/AnandPrasad94/TradingAgents.git \
  --branch main \
  --manual-integration
```

---

### Method 3: Deployment via Azure Functions Core Tools

If you have `azure-functions-core-tools` installed:

```bash
# Test locally
func start

# Publish directly to Azure
func azure functionapp publish <YourFunctionAppName> --build remote
```

---

### Method 4: Visual Studio Code

1. Install the **Azure Functions** extension in VS Code.
2. Sign in to your Azure Account in the Azure sidebar.
3. Open the `TradingAgents` folder in VS Code.
4. Click the **Deploy to Function App...** icon (the blue up-arrow).
5. Select your subscription and target Function App.
6. Deployment will complete in under 2 minutes.

---

## 3. Environment Variables & App Settings

Configure these in the Azure Portal under **Settings > Configuration > Application settings** or via CLI:

```bash
az functionapp config appsettings set --name TradingAgentsAPI --resource-group TradingAgents-RG --settings \
  TRADINGAGENTS_LLM_PROVIDER="openai" \
  OPENAI_API_KEY="sk-..." \
  AZURE_OPENAI_API_KEY="..." \
  AZURE_OPENAI_ENDPOINT="https://<resource>.openai.azure.com/" \
  AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o-mini" \
  ANTHROPIC_API_KEY="sk-ant-..." \
  GEMINI_API_KEY="..." \
  XAI_API_KEY="..."
```

> [!NOTE]
> If no LLM API keys are configured, the API automatically runs in graceful **sandbox/mock mode**, returning institutional-grade structured research for tickers (NVDA, AAPL, TSLA, BTC-USD) without crashing or incurring API charges.

---

## 4. API Usage Examples

### 1. Health Probe
```bash
curl -X GET "https://<your-app>.azurewebsites.net/api/health"
```
**Response:**
```json
{
  "status": "healthy",
  "service": "TradingAgentsAPI",
  "version": "0.6.0",
  "runtime": "Azure Functions Python v2",
  "llm_provider": "openai/azure_openai/grok"
}
```

### 2. Analyze Stock Ticker
```bash
curl -X POST "https://<your-app>.azurewebsites.net/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "NVDA",
    "risk_profile": "Neutral",
    "mock": false
  }'
```

**Response:**
```json
{
  "task_id": "NVDA_20261009_143000",
  "ticker": "NVDA",
  "trade_date": "2026-10-09",
  "asset_type": "stock",
  "decision": "BUY",
  "confidence": 88.5,
  "summary": "Multi-agent committee recommends Strong BUY for NVDA. Blackwell architecture GPU shipments and hyperscaler CapEx commitments provide strong earnings visibility.",
  "metrics": {
    "target_price": 215.00,
    "stop_loss": 162.00,
    "confidence_score": 88.5,
    "risk_level": "Moderate",
    "recommended_allocation": "6.5%",
    "grok_sentiment_score": 86.0
  },
  "theses": {
    "bull_thesis": "Accelerating Blackwell enterprise AI GPU shipments...",
    "bear_thesis": "Elevated P/E valuation multiples leave minimal margin for execution slip-ups..."
  },
  "status": "COMPLETED"
}
```

### 3. Ask Grok AI Financial Assistant
```bash
curl -X POST "https://<your-app>.azurewebsites.net/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "NVDA",
    "message": "Why was the target price set to $215?"
  }'
```

### 4. Interactive Docs
Visit `https://<your-app>.azurewebsites.net/api/docs` in your browser.
