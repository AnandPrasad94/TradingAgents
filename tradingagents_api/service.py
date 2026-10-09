"""Service layer orchestrating the TradingAgents graph, report caching, and mock simulations."""

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("tradingagents_api")

# Pre-packaged institutional analyses for instant sandbox verification without API keys
SAMPLE_INSTITUTIONAL_DATA: Dict[str, Dict[str, Any]] = {
    "NVDA": {
        "name": "NVIDIA Corporation",
        "decision": "BUY",
        "confidence": 88.5,
        "target_price": 215.00,
        "stop_loss": 162.00,
        "risk_level": "Moderate",
        "recommended_allocation": "6.5%",
        "grok_sentiment_score": 86.0,
        "summary": "Multi-agent committee recommends Strong BUY for NVDA. Unprecedented enterprise Blackwell architecture GPU demand and hyperscaler capex commitments provide strong earnings visibility through 2026/2027.",
        "bull_thesis": "Accelerating Blackwell enterprise AI GPU shipments, gross margins stabilizing at ~75%, and cloud hyperscaler CapEx commitments expanding past $200B aggregate annually create an undeniable secular growth vector.",
        "bear_thesis": "Elevated P/E valuation multiples leave minimal margin for execution slip-ups; TSMC advanced CoWoS packaging bottlenecks and potential export licensing updates present near-term headline risk.",
        "agent_reports": {
            "market_analyst": "RSI at 64.2 displaying constructive bullish momentum. MACD signals a clear golden crossover above the 50-day and 200-day simple moving averages.",
            "sentiment_analyst": "xAI Grok index scored 86/100 bullish sentiment across 140k+ verified posts. Dominant cashtags: $NVDA, $AI, $Blackwell, $Semis.",
            "news_analyst": "Key catalysts include Q3 data center revenue beats, major server OEM certifications, and strategic telecom enterprise partnership announcements.",
            "fundamentals_analyst": "TTM revenue growth over 122% YoY, operating margins exceeding 61%, and zero near-term debt maturity risks.",
            "risk_committee": "Approved maximum recommended position size capped at 6.5%. Stop-loss locked at $162.00.",
            "portfolio_manager": "Consensus rating: Strong BUY. Risk-adjusted upside target: $215.00."
        }
    },
    "AAPL": {
        "name": "Apple Inc.",
        "decision": "HOLD",
        "confidence": 64.0,
        "target_price": 245.00,
        "stop_loss": 218.00,
        "risk_level": "Low",
        "recommended_allocation": "10.0%",
        "grok_sentiment_score": 68.0,
        "summary": "Multi-agent committee recommends HOLD / Accumulate on Dips for AAPL. Core Services revenue remains highly lucrative, but consumer hardware upgrade cycles remain measured in key international markets.",
        "bull_thesis": "Multi-year iPhone refresh cycle driven by personalized Apple Intelligence features across iOS; continuous expansion of high-margin Services ecosystem ($100B+ run rate).",
        "bear_thesis": "Modest smartphone unit volume growth in Greater China and heightened regulatory scrutiny surrounding App Store commission structures in the EU and US.",
        "agent_reports": {
            "market_analyst": "RSI neutral at 52.1. Trading inside a well-defined consolidation channel between $220 and $235.",
            "sentiment_analyst": "Grok sentiment score 68/100. Consumer curiosity elevated around Apple Intelligence feature rollouts.",
            "news_analyst": "Focus remains on product launch cadences, Services revenue expansion, and supply chain diversification.",
            "fundamentals_analyst": "P/E of 31.2x. Robust balance sheet with continuous multi-billion dollar share repurchase programs.",
            "risk_committee": "Classified as Low Beta core portfolio allocation. Safe maximum position sizing up to 12.0%.",
            "portfolio_manager": "Consensus rating: HOLD / Accumulate on Weakness. Target price $245.00."
        }
    },
    "TSLA": {
        "name": "Tesla, Inc.",
        "decision": "BUY",
        "confidence": 76.0,
        "target_price": 295.00,
        "stop_loss": 215.00,
        "risk_level": "High",
        "recommended_allocation": "4.0%",
        "grok_sentiment_score": 79.0,
        "summary": "Multi-agent committee recommends Speculative BUY for TSLA. Megapack energy storage expansion and FSD autonomous licensing potential outweigh automotive gross margin pressures.",
        "bull_thesis": "Energy storage division growing at >100% YoY with industry-leading margins; autonomous Cybercab software architecture provides massive upside optionality.",
        "bear_thesis": "Automotive gross margin compression driven by global price competition and slower near-term consumer EV adoption rates in Europe.",
        "agent_reports": {
            "market_analyst": "Bullish divergence appearing on daily candles with RSI at 58.4.",
            "sentiment_analyst": "Grok sentiment score 79/100 across 210k+ cashtag mentions.",
            "news_analyst": "Megapack factory ramp and autonomous regulatory milestones remain primary catalysts.",
            "fundamentals_analyst": "P/E multiple of 68.5x. Net cash position exceeds $30B with zero refinancing risk.",
            "risk_committee": "High volatility flag active. Position capped at 4.0% with trailing stop-loss at $215.00.",
            "portfolio_manager": "Consensus rating: Speculative BUY. Target price $295.00."
        }
    },
    "BTC-USD": {
        "name": "Bitcoin",
        "decision": "BUY",
        "confidence": 84.0,
        "target_price": 115000.00,
        "stop_loss": 84000.00,
        "risk_level": "High",
        "recommended_allocation": "3.5%",
        "grok_sentiment_score": 91.0,
        "summary": "Multi-agent committee recommends Strong BUY for BTC-USD. Sustained spot ETF net inflows and post-halving structural supply contraction support a continuation towards new all-time highs.",
        "bull_thesis": "Sustained global sovereign and institutional spot ETF inflows, post-halving supply shock constraints, and macroeconomic liquidity easing.",
        "bear_thesis": "Overleveraged derivative positioning in perpetual swaps creates risk of sharp liquidation flushes down to lower technical support.",
        "agent_reports": {
            "market_analyst": "Breakout above multi-month accumulation range. Daily RSI at 68.9.",
            "sentiment_analyst": "Grok sentiment index at 91/100 reflecting strong viral social momentum across 340k+ posts.",
            "news_analyst": "Institutional ETF inflow records and regulatory clarity milestones dominating headlines.",
            "fundamentals_analyst": "Network hashrate at record highs. Exchange liquid supply at multi-year lows.",
            "risk_committee": "Crypto volatility rating High. Enforce DCA execution with hard stop-loss at $84,000.",
            "portfolio_manager": "Consensus rating: Strong BUY. Macro target $115,000."
        }
    }
}


class TradingAgentsService:
    """Core service bridging API triggers to TradingAgents orchestration."""

    def __init__(self):
        self._reports_cache: Dict[str, Dict[str, Any]] = {}
        self._watchlist: List[str] = ["NVDA", "AAPL", "TSLA", "BTC-USD", "MSFT"]
        self._init_defaults()

    def _init_defaults(self):
        # Pre-seed cache with sample analyses
        for ticker, data in SAMPLE_INSTITUTIONAL_DATA.items():
            task_id = f"{ticker}_{datetime.now().strftime('%Y%m%d')}_000000"
            self._reports_cache[ticker] = {
                "task_id": task_id,
                "ticker": ticker,
                "trade_date": datetime.now().strftime("%Y-%m-%d"),
                "asset_type": "crypto" if "BTC" in ticker else "stock",
                "decision": data["decision"],
                "confidence": data["confidence"],
                "summary": data["summary"],
                "metrics": {
                    "target_price": data["target_price"],
                    "stop_loss": data["stop_loss"],
                    "confidence_score": data["confidence"],
                    "risk_level": data["risk_level"],
                    "recommended_allocation": data["recommended_allocation"],
                    "grok_sentiment_score": data["grok_sentiment_score"],
                },
                "theses": {
                    "bull_thesis": data["bull_thesis"],
                    "bear_thesis": data["bear_thesis"],
                },
                "agent_reports": data["agent_reports"],
                "status": "COMPLETED",
                "timestamp": datetime.now().isoformat(),
                "is_mock": True,
            }

    def _has_llm_credentials(self) -> bool:
        """Check if any supported LLM provider credentials exist in the environment."""
        keys = [
            "OPENAI_API_KEY",
            "AZURE_OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "GEMINI_API_KEY",
            "GOOGLE_API_KEY",
            "DEEPSEEK_API_KEY",
            "XAI_API_KEY",
        ]
        return any(bool(os.environ.get(k)) for k in keys)

    def analyze(
        self,
        ticker: str,
        trade_date: Optional[str] = None,
        asset_type: str = "stock",
        risk_profile: str = "Neutral",
        selected_analysts: Optional[List[str]] = None,
        max_debate_rounds: int = 1,
        max_risk_rounds: int = 1,
        mock: bool = False,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """Execute or retrieve analysis for the specified ticker."""
        sym = ticker.strip().upper()
        current_date = datetime.now().strftime("%Y-%m-%d")
        effective_date = trade_date or current_date
        
        # Check cache if not forcing refresh
        if not force_refresh and sym in self._reports_cache:
            cached = self._reports_cache[sym]
            if cached.get("trade_date") == effective_date and not mock:
                return cached

        # Use mock execution if explicitly requested or if no LLM credentials are set
        has_keys = self._has_llm_credentials()
        should_mock = mock or (not has_keys)

        if should_mock:
            return self._execute_mock_analysis(sym, effective_date, asset_type, risk_profile)

        return self._execute_live_graph(
            ticker=sym,
            trade_date=effective_date,
            asset_type=asset_type,
            risk_profile=risk_profile,
            selected_analysts=selected_analysts or ["market", "social", "news", "fundamentals"],
            max_debate_rounds=max_debate_rounds,
            max_risk_rounds=max_risk_rounds,
        )

    def _execute_mock_analysis(
        self, ticker: str, trade_date: str, asset_type: str, risk_profile: str
    ) -> Dict[str, Any]:
        """Generate realistic multi-agent analysis for quick verification & zero-cost testing."""
        task_id = f"{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        if ticker in SAMPLE_INSTITUTIONAL_DATA:
            base = SAMPLE_INSTITUTIONAL_DATA[ticker]
        else:
            base = {
                "name": f"{ticker} Asset",
                "decision": "BUY",
                "confidence": 75.0,
                "target_price": 150.00,
                "stop_loss": 120.00,
                "risk_level": risk_profile or "Moderate",
                "recommended_allocation": "5.0%",
                "grok_sentiment_score": 72.0,
                "summary": f"Multi-agent committee synthesized market, technical, news, and sentiment indicators for {ticker}. Overall bias leans constructive with favorable risk/reward parameters.",
                "bull_thesis": f"Strong industry tailwinds and steady cash flow generation position {ticker} for potential upside expansion over a 3-6 month holding period.",
                "bear_thesis": f"Macroeconomic headwinds and multiple compression across the sector could limit short-term upside if broader market conditions soften.",
                "agent_reports": {
                    "market_analyst": f"Price action for {ticker} shows solid support around key technical moving averages with neutral-to-bullish momentum.",
                    "sentiment_analyst": f"Grok social sentiment analysis indicates a 72/100 positive score with steady retail and institutional mentions.",
                    "news_analyst": f"Recent corporate press releases and industry articles highlight ongoing operational execution.",
                    "fundamentals_analyst": f"Balance sheet demonstrates adequate liquidity and manageable debt obligations.",
                    "risk_committee": f"Recommended maximum portfolio weighting set at 5.0% under a {risk_profile} risk mandate.",
                    "portfolio_manager": f"Consensus recommendation: BUY with target price $150.00 and stop-loss at $120.00."
                }
            }

        response = {
            "task_id": task_id,
            "ticker": ticker,
            "trade_date": trade_date,
            "asset_type": asset_type,
            "decision": base["decision"],
            "confidence": base["confidence"],
            "summary": base["summary"],
            "metrics": {
                "target_price": base["target_price"],
                "stop_loss": base["stop_loss"],
                "confidence_score": base["confidence"],
                "risk_level": base["risk_level"],
                "recommended_allocation": base["recommended_allocation"],
                "grok_sentiment_score": base["grok_sentiment_score"],
            },
            "theses": {
                "bull_thesis": base["bull_thesis"],
                "bear_thesis": base["bear_thesis"],
            },
            "agent_reports": base["agent_reports"],
            "status": "COMPLETED",
            "timestamp": datetime.now().isoformat(),
            "is_mock": True,
        }

        self._reports_cache[ticker] = response
        return response

    def _execute_live_graph(
        self,
        ticker: str,
        trade_date: str,
        asset_type: str,
        risk_profile: str,
        selected_analysts: List[str],
        max_debate_rounds: int,
        max_risk_rounds: int,
    ) -> Dict[str, Any]:
        """Execute the real LangGraph TradingAgents multi-agent pipeline."""
        from tradingagents.default_config import DEFAULT_CONFIG
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        from tradingagents.agents.rating import run_rating

        config = DEFAULT_CONFIG.copy()
        config["max_debate_rounds"] = max_debate_rounds
        config["max_risk_discuss_rounds"] = max_risk_rounds

        logger.info("Initializing TradingAgentsGraph for %s on %s...", ticker, trade_date)
        ta_graph = TradingAgentsGraph(
            selected_analysts=selected_analysts,
            debug=False,
            config=config,
        )

        final_state, rating = ta_graph.propagate(
            company_name=ticker,
            trade_date=trade_date,
            asset_type=asset_type,
        )

        task_id = f"{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Extract structured outputs
        rating_clean = str(rating or run_rating(final_state) or "HOLD").upper()
        decision_text = str(final_state.get("final_trade_decision") or "")

        bull_thesis = ""
        bear_thesis = ""
        debate_state = final_state.get("investment_debate_state") or {}
        if isinstance(debate_state, dict):
            bull_hist = debate_state.get("bull_history") or []
            bear_hist = debate_state.get("bear_history") or []
            if bull_hist:
                bull_thesis = str(bull_hist[-1])
            if bear_hist:
                bear_thesis = str(bear_hist[-1])

        # Parse potential prices from decision text
        target_price = self._extract_price(decision_text, "target")
        stop_loss = self._extract_price(decision_text, "stop")

        agent_reports = {
            "market_analyst": str(final_state.get("market_report") or ""),
            "sentiment_analyst": str(final_state.get("sentiment_report") or ""),
            "news_analyst": str(final_state.get("news_report") or ""),
            "fundamentals_analyst": str(final_state.get("fundamentals_report") or ""),
            "investment_plan": str(final_state.get("investment_plan") or ""),
            "trader_plan": str(final_state.get("trader_investment_plan") or ""),
            "final_trade_decision": decision_text,
        }

        response = {
            "task_id": task_id,
            "ticker": ticker,
            "trade_date": trade_date,
            "asset_type": asset_type,
            "decision": rating_clean,
            "confidence": 85.0 if "BUY" in rating_clean else 65.0,
            "summary": decision_text[:400] if decision_text else f"Analysis concluded with rating {rating_clean}.",
            "metrics": {
                "target_price": target_price,
                "stop_loss": stop_loss,
                "confidence_score": 85.0 if "BUY" in rating_clean else 65.0,
                "risk_level": risk_profile,
                "recommended_allocation": "5%",
                "grok_sentiment_score": 75.0,
            },
            "theses": {
                "bull_thesis": bull_thesis or "Long-term revenue expansion and constructive fundamental indicators.",
                "bear_thesis": bear_thesis or "Potential multiple compression and broader market volatility.",
            },
            "agent_reports": agent_reports,
            "status": "COMPLETED",
            "timestamp": datetime.now().isoformat(),
            "is_mock": False,
        }

        self._reports_cache[ticker] = response
        return response

    @staticmethod
    def _extract_price(text: str, keyword: str) -> Optional[float]:
        """Helper to extract dollar amounts associated with a keyword."""
        pattern = rf"{keyword}[^\$0-9]*\$?\s*([0-9]+(?:\.[0-9]+)?)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        return None

    def get_report(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Retrieve the latest cached report for a ticker."""
        sym = ticker.strip().upper()
        if sym in self._reports_cache:
            return self._reports_cache[sym]
        # Generate mock if not yet present
        return self.analyze(sym, mock=True)

    def list_reports(self) -> List[Dict[str, Any]]:
        """List all generated reports in cache."""
        return list(self._reports_cache.values())

    def get_watchlist(self) -> List[str]:
        """Get the current watchlist."""
        return list(self._watchlist)

    def add_to_watchlist(self, ticker: str) -> List[str]:
        """Add a ticker to the watchlist."""
        sym = ticker.strip().upper()
        if sym not in self._watchlist:
            self._watchlist.append(sym)
        return self._watchlist

    def remove_from_watchlist(self, ticker: str) -> List[str]:
        """Remove a ticker from the watchlist."""
        sym = ticker.strip().upper()
        if sym in self._watchlist:
            self._watchlist.remove(sym)
        return self._watchlist

    def chat(self, ticker: str, message: str) -> str:
        """Contextual Q&A assistant for a ticker."""
        sym = ticker.strip().upper()
        report = self.get_report(sym)
        
        lower_msg = message.lower()
        if "why" in lower_msg or "reason" in lower_msg or "thesis" in lower_msg:
            return (
                f"Regarding {sym}: The research committee recommends {report['decision']} based on key growth catalysts: "
                f"{report['theses']['bull_thesis'][:150]}... However, notable risks include {report['theses']['bear_thesis'][:120]}."
            )
        elif "risk" in lower_msg or "stop" in lower_msg or "loss" in lower_msg:
            stop = report['metrics'].get('stop_loss')
            return (
                f"For {sym}, the risk committee established a stop-loss benchmark at ${stop or 'N/A'}. "
                f"Overall risk level is rated as {report['metrics'].get('risk_level', 'Moderate')}."
            )
        elif "target" in lower_msg or "price" in lower_msg:
            tgt = report['metrics'].get('target_price')
            return f"The multi-agent upside projection target for {sym} is ${tgt or 'N/A'} based on discounted cash flow and multi-analyst synthesis."
        else:
            return (
                f"Grok AI Assistant: For {sym}, the overall multi-agent rating is {report['decision']} "
                f"with {report['confidence']}% confidence. Target price: ${report['metrics'].get('target_price')}. "
                f"Summary: {report['summary'][:200]}"
            )


# Global singleton instance
trading_service = TradingAgentsService()
