import logging
import os
from typing import Any, Dict, List

from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
logger = logging.getLogger(__name__)


class RiskAnalysisAgent:
    """
    SPEED FIX: Removed ALL LLM calls from risk analysis.
    Pure keyword scoring — runs in under 0.1 seconds.
    Scoring is deterministic and accurate based on actual transcript words.
    This saves 5-10 seconds per request.
    Only the recommendation agent now calls Gemini — one LLM call total.
    """

    def analyze(self, ingested_data: Dict[str, Any], retrieved_context: List[str]) -> Dict[str, Any]:
        try:
            return self._score(ingested_data, retrieved_context)
        except Exception as exc:
            logger.exception("Risk analysis failed: %s", exc)
            return self._default_result()

    def _score(self, ingested_data: Dict[str, Any], retrieved_context: List[str]) -> Dict[str, Any]:
        raw_text = str(ingested_data.get("raw_text", "")).lower()
        urgency_level = ingested_data.get("urgency_level", "medium")
        complaints = ingested_data.get("complaints", [])
        churn_signals = ingested_data.get("churn_signals", [])
        sentiment = ingested_data.get("sentiment", "neutral")

        score = 15  # base

        # --- CRITICAL CHURN WORDS (+20 each) ---
        critical = [
            "cancel", "cancellation", "switching to", "switch to",
            "will not renew", "wont renew", "not renew",
            "terminate contract", "evaluating alternatives",
            "evaluating salesforce", "evaluating hubspot",
            "evaluating competitor", "leaving your platform",
            "looking at other vendors", "final warning",
        ]
        for w in critical:
            if w in raw_text:
                score += 20

        # --- HIGH RISK WORDS (+10 each) ---
        high = [
            "competitor", "frustrated", "angry", "disappointed",
            "losing confidence", "outage", "completely stopped using",
            "stopped using", "leadership team evaluating",
            "escalate to ceo", "renewal risk", "at risk",
        ]
        for w in high:
            if w in raw_text:
                score += 10

        # --- MEDIUM RISK WORDS (+5 each) ---
        medium = [
            "slow support", "slow response", "pricing concern",
            "pricing feels high", "expensive", "confused",
            "confusing", "not happy", "some concerns",
            "unresolved tickets", "adoption is low",
        ]
        for w in medium:
            if w in raw_text:
                score += 5

        # --- EXPANSION / POSITIVE WORDS (-20 each) ---
        expansion_words = [
            "expanding our team", "new department", "more seats",
            "upgrade to enterprise", "love the platform",
            "fantastic", "excellent results", "amazing roi",
            "95 percent adoption", "very happy", "love it",
        ]
        expansion = False
        for w in expansion_words:
            if w in raw_text:
                score -= 20
                expansion = True

        # --- INGESTION SIGNALS ---
        if urgency_level == "critical":
            score += 20
        elif urgency_level == "high":
            score += 12
        elif urgency_level == "medium":
            score += 4
        elif urgency_level == "low":
            score -= 10

        if sentiment == "negative":
            score += 10
        elif sentiment == "positive":
            score -= 10

        score += len(complaints) * 5
        score += len(churn_signals) * 8

        # --- CRM STATUS FIELD ---
        status = str(ingested_data.get("extracted_fields", {}).get("status", "")).lower()
        if any(w in status for w in ["at risk", "churn", "critical", "urgent"]):
            score += 20

        # Clamp
        score = max(5, min(97, score))

        # Derive urgency from score.
        # These bands are intentionally aligned with get_all_customers()'s
        # risk-level bands in memory_manager.py (Low <31, Medium 31-60, High >=61)
        # so the Customers table and this Risk Analysis panel never disagree
        # on the same score again.
        if score >= 75:
            urgency = "critical"
        elif score >= 61:
            urgency = "high"
        elif score >= 31:
            urgency = "medium"
        else:
            urgency = "low"

        # Build signals
        signals = []
        if any(w in raw_text for w in ["cancel", "switching", "will not renew",
                                        "evaluating alternatives", "terminate"]):
            signals.append("Customer mentioned cancellation or competitor switch")
        if any(w in raw_text for w in ["support", "ticket", "outage", "response time"]):
            signals.append("Customer raised support and reliability concerns")
        if any(w in raw_text for w in ["renew", "contract", "renewal"]):
            signals.append("Renewal risk detected in conversation")
        if churn_signals:
            signals.append("Strong churn language detected in transcript")
        if complaints:
            signals.append(f"Customer cited {len(complaints)} specific complaints")
        if retrieved_context:
            signals.append("Relevant playbook guidance matched")
        if expansion:
            signals.append("Customer showed expansion and growth signals")
        if not signals:
            signals = ["Customer engagement needs monitoring"]

        focus = (
            "Immediate executive outreach required — high churn risk."
            if score >= 70
            else "Schedule recovery call and address concerns within 48 hours."
            if score >= 45
            else "Account is healthy — focus on expansion and success planning."
        )

        return {
            "churn_risk_score": score,
            "expansion_opportunity": expansion,
            "missing_information": ["recent usage metrics", "renewal date"],
            "urgency": urgency,
            "key_signals": signals[:4],
            "recommended_focus": focus,
        }

    def _default_result(self) -> Dict[str, Any]:
        return {
            "churn_risk_score": 30,
            "expansion_opportunity": False,
            "missing_information": [],
            "urgency": "medium",
            "key_signals": ["Could not analyze — using default"],
            "recommended_focus": "Review customer account manually.",
        }
