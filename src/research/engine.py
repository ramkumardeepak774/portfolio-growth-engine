"""LLM-powered research analysis engine.

Uses OpenAI (or compatible) for:
- Earnings report summarization
- Risk factor detection
- Business quality classification
- Moat analysis
- Debt risk scoring
- Growth consistency scoring
- Management guidance extraction
"""

from __future__ import annotations

import json
import logging
from datetime import date
from typing import Optional

from openai import OpenAI

from ..config import get_settings

logger = logging.getLogger(__name__)


class ResearchEngine:
    """AI research engine for stock analysis.

    Philosophy: AI is good at information compression, anomaly detection,
    and screening — NOT at predicting prices.
    """

    def __init__(self):
        settings = get_settings()
        self._client = OpenAI(api_key=settings.openai_api_key) if settings.has_openai else None
        self._model = settings.openai_model

    def _chat(self, system: str, user: str, json_mode: bool = False) -> str:
        """Send a chat completion request."""
        if not self._client:
            return '{"error": "OpenAI API key not configured"}'

        kwargs = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.3,
            "max_tokens": 2000,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = self._client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""

    def summarize_earnings(self, symbol: str, earnings_data: dict) -> dict:
        """Summarize quarterly earnings report.

        Returns:
            {summary, beats, management_guidance, risk_factors, key_highlights}
        """
        system = """You are a senior equity research analyst focused on Indian markets.
Analyze the earnings data and provide a concise research summary.
Be factual. Highlight what matters for long-term investors.
Respond in JSON format."""

        user = f"""Analyze earnings for {symbol}:

{json.dumps(earnings_data, indent=2, default=str)}

Return JSON with:
- summary: 2-3 sentence earnings summary
- beat_or_miss: "beat" / "miss" / "inline"
- revenue_trend: "accelerating" / "stable" / "decelerating"
- profit_trend: "improving" / "stable" / "deteriorating"
- management_guidance: key forward-looking statements (if available)
- risk_factors: list of risk factors identified
- key_highlights: list of 3-5 most important takeaways
- score: 1-10 rating on earnings quality"""

        try:
            result = self._chat(system, user, json_mode=True)
            return json.loads(result)
        except Exception as e:
            logger.warning(f"Earnings summarization failed for {symbol}: {e}")
            return {"error": str(e)}

    def analyze_business_quality(self, symbol: str, fundamentals: dict) -> dict:
        """Classify business quality based on fundamentals.

        Scores: moat, growth consistency, capital efficiency, management quality.
        """
        system = """You are a value investor in the tradition of Buffett and Munger.
Analyze the fundamentals and classify business quality.
Focus on durable competitive advantages, capital allocation, and consistency.
Be skeptical and evidence-based. Respond in JSON."""

        user = f"""Analyze business quality for {symbol}:

{json.dumps(fundamentals, indent=2, default=str)}

Return JSON with:
- business_quality_grade: A/B/C/D/F
- moat_type: "none" / "weak" / "moderate" / "strong" / "wide"
- moat_sources: list of moat sources (brand, network effect, switching costs, cost advantage, patents, regulation)
- growth_consistency_score: 1-10 (10 = revenue/profit grew consistently every year)
- capital_efficiency_score: 1-10 (ROE, ROCE, FCF generation)
- debt_risk_score: 1-10 (1 = very risky debt, 10 = fortress balance sheet)
- management_quality_indicators: list of positive/negative signals
- red_flags: list of concerns
- green_flags: list of positives
- investment_thesis_potential: 1-2 sentence thesis if this is investable
- overall_score: 1-100 composite business quality score"""

        try:
            result = self._chat(system, user, json_mode=True)
            return json.loads(result)
        except Exception as e:
            logger.warning(f"Business quality analysis failed for {symbol}: {e}")
            return {"error": str(e)}

    def detect_risk_factors(self, symbol: str, all_data: dict) -> dict:
        """Detect risk factors from combined data (fundamentals + news + insider)."""
        system = """You are a risk analyst. Identify ALL risks — financial, operational,
sector, macro, governance. Be thorough but don't be alarmist. Rate severity.
Respond in JSON."""

        # Truncate data to stay within context
        data_str = json.dumps(all_data, indent=2, default=str)[:6000]

        user = f"""Analyze risk factors for {symbol}:

{data_str}

Return JSON with:
- risk_factors: list of objects, each with:
  - risk: description
  - category: "financial" / "operational" / "sector" / "macro" / "governance" / "valuation"
  - severity: "low" / "medium" / "high" / "critical"
  - likelihood: "low" / "medium" / "high"
- overall_risk_level: "low" / "medium" / "high" / "very_high"
- risk_score: 1-10 (10 = very risky)
- biggest_concern: single most important risk
- mitigants: list of factors that reduce risk"""

        try:
            result = self._chat(system, user, json_mode=True)
            return json.loads(result)
        except Exception as e:
            logger.warning(f"Risk analysis failed for {symbol}: {e}")
            return {"error": str(e)}

    def compare_quarters(self, symbol: str, q1_data: dict, q2_data: dict) -> dict:
        """Compare two quarters and identify trends."""
        system = """You are a financial analyst comparing quarterly results.
Identify meaningful changes, trends, and inflection points.
Distinguish between one-off events and structural shifts. Respond in JSON."""

        user = f"""Compare quarters for {symbol}:

Previous Quarter:
{json.dumps(q1_data, indent=2, default=str)[:3000]}

Latest Quarter:
{json.dumps(q2_data, indent=2, default=str)[:3000]}

Return JSON with:
- changes: list of significant changes with direction and magnitude
- trend: "improving" / "stable" / "deteriorating"
- inflection_points: any major shifts detected
- concerns: new concerns that emerged
- positives: new positive developments
- summary: 2-3 sentence comparison"""

        try:
            result = self._chat(system, user, json_mode=True)
            return json.loads(result)
        except Exception as e:
            logger.warning(f"Quarter comparison failed for {symbol}: {e}")
            return {"error": str(e)}

    def generate_research_note(
        self,
        symbol: str,
        fundamentals: dict,
        earnings: list[dict] | None = None,
        news: list[dict] | None = None,
        insider: list[dict] | None = None,
        sentiment: dict | None = None,
    ) -> dict:
        """Generate a comprehensive research note for a stock.

        This is the main "agentic" analysis function that combines all data sources.
        """
        system = """You are a senior equity research analyst producing a research note
for an Indian market investor. Be thorough but concise. Use data to support every claim.
Do NOT predict price. Focus on:
1. Business quality and moat
2. Growth trajectory and consistency
3. Valuation relative to quality
4. Key risks and mitigants
5. What would make this a great long-term investment (or not)
Respond in JSON."""

        context_parts = [f"Fundamentals:\n{json.dumps(fundamentals, indent=2, default=str)[:3000]}"]
        if earnings:
            context_parts.append(f"Recent Earnings:\n{json.dumps(earnings[:3], indent=2, default=str)[:1500]}")
        if news:
            context_parts.append(f"Recent News:\n{json.dumps(news[:5], indent=2, default=str)[:1500]}")
        if insider:
            context_parts.append(f"Insider Trading:\n{json.dumps(insider[:5], indent=2, default=str)[:1000]}")
        if sentiment:
            context_parts.append(f"Social Sentiment:\n{json.dumps(sentiment, indent=2, default=str)[:500]}")

        context = "\n\n".join(context_parts)

        user = f"""Generate research note for {symbol}:

{context}

Return JSON with:
- title: research note title
- date: "{date.today().isoformat()}"
- recommendation: "strong_buy" / "buy" / "hold" / "reduce" / "avoid"
- conviction: "very_high" / "high" / "medium" / "low"
- summary: 3-5 sentence executive summary
- business_quality: {{grade, moat, key_strengths}}
- growth_analysis: {{trend, drivers, sustainability}}
- valuation_assessment: {{is_expensive, relative_value, margin_of_safety}}
- risk_assessment: {{top_risks, risk_level, invalidation_triggers}}
- insider_signal: bullish/bearish/neutral based on insider data
- sentiment_signal: market sentiment summary
- catalysts: upcoming events that could move the stock
- investment_thesis: 2-3 sentences — why own this for 3-5 years
- scores: {{business_quality: 1-10, growth: 1-10, valuation: 1-10, risk: 1-10, overall: 1-100}}"""

        try:
            result = self._chat(system, user, json_mode=True)
            return json.loads(result)
        except Exception as e:
            logger.warning(f"Research note generation failed for {symbol}: {e}")
            return {"error": str(e)}

    def analyze_portfolio_risks(self, portfolio_data: dict) -> dict:
        """Analyze portfolio-level risks — concentration, correlation, macro exposure."""
        system = """You are a portfolio risk manager. Analyze the portfolio for systemic risks,
concentration risks, and blind spots. Be direct and actionable. Respond in JSON."""

        user = f"""Analyze portfolio risk:

{json.dumps(portfolio_data, indent=2, default=str)[:5000]}

Return JSON with:
- risk_level: "low" / "medium" / "high" / "critical"
- concentration_risks: list of concentration issues
- sector_risks: sector-specific concerns
- macro_risks: macro factors that could hurt this portfolio
- correlation_concerns: highly correlated positions
- missing_diversification: what's missing from this portfolio
- worst_case_scenario: what could go 50%+ wrong
- recommendations: top 3 actionable risk reduction steps
- portfolio_health_score: 1-100"""

        try:
            result = self._chat(system, user, json_mode=True)
            return json.loads(result)
        except Exception as e:
            logger.warning(f"Portfolio risk analysis failed: {e}")
            return {"error": str(e)}
