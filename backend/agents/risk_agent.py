
import json
import logging
import os
import re
from typing import Any, Dict, List

from dotenv import load_dotenv

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except Exception:
    ChatGoogleGenerativeAI = None

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

logger = logging.getLogger(__name__)


class RiskAnalysisAgent:
    def __init__(self) -> None:
        self.llm = None

    def _get_llm(self):
        if ChatGoogleGenerativeAI is None:
            return None
        api_key = os.getenv("GOOGLE_API_KEY", "")
        if not api_key or "your_gemini_api_key_here" in api_key:
            return None
        return ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=api_key, temperature=0.2)

    def analyze(self, ingested_data: Dict[str, Any], retrieved_context: List[str]) -> Dict[str, Any]:
        try:
            llm = self._get_llm()
            if llm is None:
                return self._fallback_analysis(ingested_data, retrieved_context)
            prompt = (
                "You are a customer success risk analyst. Analyze the provided customer interaction data and return ONLY a valid JSON object. "
                "Use exactly these keys: churn_risk_score, expansion_opportunity, missing_information, urgency, key_signals, recommended_focus. "
                "For churn_risk_score: use 0-100 integer. Score 70+ if customer mentions switching, competitor evaluation, or cancellation. "
                "Score 50-69 for frustrated customers with unresolved issues. Score 20-49 for neutral/minor concerns. Score below 20 for healthy accounts. "
                "For urgency: use 'critical' if score>=75, 'high' if score>=55, 'medium' if score>=35, else 'low'."
                f"\n\nIngested data: {json.dumps(ingested_data, default=str)}\n\nRetrieved context: {json.dumps(retrieved_context, default=str)}"
            )
            response = llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            parsed = self._safe_json_parse(content)
            if parsed:
                raw_score = int(parsed.get("churn_risk_score", 40))
                # Enforce minimum score based on raw text signals — LLM sometimes
                # underestimates when it focuses on tone rather than explicit language
                raw_lower = str(ingested_data.get("raw_text", "")).lower()
                churn_keywords = ["switching", "switch to", "competitor", "cancel",
                                  "evaluating alternatives", "not renew", "leaving"]
                if any(w in raw_lower for w in churn_keywords) and raw_score < 60:
                    raw_score = max(raw_score, 65)
                urgency_val = parsed.get("urgency", "medium")
                if raw_score >= 75 and urgency_val not in ("critical", "high"):
                    urgency_val = "critical"
                elif raw_score >= 55 and urgency_val == "low":
                    urgency_val = "medium"
                return {
                    "churn_risk_score": raw_score,
                    "expansion_opportunity": bool(parsed.get("expansion_opportunity", False)),
                    "missing_information": parsed.get("missing_information", []),
                    "urgency": urgency_val,
                    "key_signals": parsed.get("key_signals", []),
                    "recommended_focus": parsed.get("recommended_focus", "Focus on customer retention and adoption"),
                }
            return self._fallback_analysis(ingested_data, retrieved_context)
        except Exception as exc:
            logger.exception("Risk analysis failed")
            return self._fallback_analysis(ingested_data, retrieved_context)

    def _fallback_analysis(self, ingested_data: Dict[str, Any], retrieved_context: List[str]) -> Dict[str, Any]:
        # Read raw transcript text for accurate scoring
        raw_text = str(ingested_data.get("raw_text", "")).lower()
        urgency_from_ingestion = ingested_data.get("urgency_level", "medium")

        # Start with base score
        score = 20

        # Critical churn words = very high risk
        critical_words = ["cancel", "cancellation", "switching", "switch to",
                         "competitor", "considering switching", "considering a competitor",
                         "evaluating a competitor", "will not renew", "wont renew", "not renew",
                         "terminate", "leaving", "evaluating alternatives",
                         "evaluating other", "alternative vendor", "salesforce",
                         "hubspot", "losing confidence"]
        for word in critical_words:
            if word in raw_text:
                score += 20
                break  # count only once even if multiple critical words match

        # High risk words
        high_words = ["frustrated", "disappointed", "angry", "outage",
                     "broken", "not working", "escalate", "renewal risk",
                     "stopped using", "no longer using", "leadership team"]
        for word in high_words:
            if word in raw_text:
                score += 8

        # Medium risk words
        medium_words = ["slow support", "slow response", "pricing", "expensive",
                       "confused", "confusing", "issue", "problem", "concern",
                       "support ticket", "not happy"]
        for word in medium_words:
            if word in raw_text:
                score += 4

        # Expansion signals reduce score
        expansion_words = ["expand", "expansion", "upgrade", "more users",
                          "new team", "new department", "love it", "fantastic",
                          "great product", "very happy", "excellent"]
        expansion = any(w in raw_text for w in expansion_words)
        if expansion:
            score -= 25

        # Use ingestion urgency as extra signal
        if urgency_from_ingestion == "critical":
            score += 15
        elif urgency_from_ingestion == "high":
            score += 8
        elif urgency_from_ingestion == "low":
            score -= 10

        # Add from complaints and churn signals
        score += len(ingested_data.get("complaints", [])) * 5
        score += len(ingested_data.get("churn_signals", [])) * 8

        # Clamp between 5 and 97
        score = max(5, min(97, score))

        # Derive urgency from final score
        if score >= 75:
            final_urgency = "critical"
        elif score >= 55:
            final_urgency = "high"
        elif score >= 35:
            final_urgency = "medium"
        else:
            final_urgency = "low"

        # Build meaningful signals
        signals = []
        if any(w in raw_text for w in critical_words):
            signals.append("Customer mentioned switching to a competitor or cancellation")
        if any(w in raw_text for w in ["support", "ticket", "response time", "outage"]):
            signals.append("Customer raised support and reliability concerns")
        if any(w in raw_text for w in ["renew", "renewal", "contract"]):
            signals.append("Customer mentioned renewal risk")
        if ingested_data.get("complaints"):
            signals.append("Customer cited a product or support issue")
        if ingested_data.get("churn_signals"):
            signals.append("Customer showed churn risk language")
        if retrieved_context:
            signals.append("Relevant playbook guidance was matched")
        if expansion:
            signals.append("Customer showed expansion and growth signals")
        if not signals:
            signals = ["Customer engagement needs monitoring"]

        focus = ("Immediate executive outreach required — high churn risk detected."
                 if score >= 70 else
                 "Schedule recovery call and address concerns within 48 hours."
                 if score >= 45 else
                 "Account is healthy — focus on expansion and success planning.")

        return {
            "churn_risk_score": score,
            "expansion_opportunity": expansion,
            "missing_information": ["recent usage metrics", "renewal date"],
            "urgency": final_urgency,
            "key_signals": signals[:4],
            "recommended_focus": focus,
        }

    def _safe_json_parse(self, content: str) -> Dict[str, Any]:
        try:
            text = re.sub(r"```json|```", "", content).strip()
            return json.loads(text)
        except Exception:
            return {}
