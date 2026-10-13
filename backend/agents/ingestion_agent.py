import logging
import os
import re
from typing import Any, Dict, List

from dotenv import load_dotenv

try:
    import chromadb
except Exception:
    chromadb = None

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
logger = logging.getLogger(__name__)


class IngestionAgent:
    """
    SPEED FIX: Removed ALL LLM calls from ingestion.
    Pure keyword-based extraction — runs in under 0.1 seconds.
    The risk agent does not need LLM-quality ingestion — it reads
    raw_text directly for scoring.
    """

    def __init__(self) -> None:
        self.client = None
        self.collection = None
        self._initialize_vector_store()

    def _initialize_vector_store(self) -> None:
        try:
            if chromadb is None:
                return
            host = os.getenv("CHROMA_HOST", "localhost")
            port = int(os.getenv("CHROMA_PORT", "8001"))
            self.client = chromadb.HttpClient(host=host, port=port)
            self.collection = self.client.get_or_create_collection(
                name="customer_interactions"
            )
        except Exception as exc:
            logger.warning("ChromaDB initialization failed: %s", exc)

    def process(self, raw_text: str, input_type: str = "meeting_transcript") -> Dict[str, Any]:
        """Instant keyword-based extraction — no LLM, no network call."""
        try:
            if not raw_text or not raw_text.strip():
                return self._build_structure("", input_type, {})

            preprocessed = self._preprocess_by_type(raw_text, input_type)
            return self._build_structure(raw_text, input_type, preprocessed)
        except Exception as exc:
            logger.exception("Ingestion failed: %s", exc)
            return self._build_structure(raw_text, input_type, {})

    def _preprocess_by_type(self, raw_text: str, input_type: str) -> Dict[str, Any]:
        if input_type == "customer_email":
            return self._preprocess_email(raw_text)
        if input_type == "crm_note":
            return self._preprocess_crm_note(raw_text)
        return {"body": raw_text, "fields": {}}

    def _preprocess_email(self, raw_text: str) -> Dict[str, Any]:
        fields: Dict[str, str] = {}
        body_lines: List[str] = []
        header_pattern = re.compile(
            r"^\s*(from|to|subject|date|cc|bcc)\s*:\s*(.+)$", re.IGNORECASE
        )
        for line in raw_text.splitlines():
            match = header_pattern.match(line)
            if match:
                fields[match.group(1).lower()] = match.group(2).strip()
            else:
                body_lines.append(line)
        body = "\n".join(body_lines).strip()
        if fields.get("subject"):
            body = f"Subject: {fields['subject']}\n\n{body}"
        return {"body": body or raw_text, "fields": fields}

    def _preprocess_crm_note(self, raw_text: str) -> Dict[str, Any]:
        fields: Dict[str, str] = {}
        comment_lines: List[str] = []
        field_pattern = re.compile(r"^\s*([A-Za-z][A-Za-z0-9 _/]{1,30})\s*:\s*(.+)$")
        for line in raw_text.splitlines():
            match = field_pattern.match(line)
            if match:
                key = match.group(1).strip().lower().replace(" ", "_")
                fields[key] = match.group(2).strip()
            elif line.strip():
                comment_lines.append(line.strip())
        field_summary = "; ".join(
            f"{k.replace('_', ' ').title()}: {v}" for k, v in fields.items()
        )
        comment = " ".join(comment_lines)
        body = (
            f"{field_summary}\n\nNotes: {comment}".strip()
            if field_summary or comment
            else raw_text
        )
        return {"body": body, "fields": fields}

    def _build_structure(
        self, raw_text: str, input_type: str, preprocessed: Dict[str, Any]
    ) -> Dict[str, Any]:
        body = preprocessed.get("body") or raw_text
        fields = preprocessed.get("fields") or {}
        lowered = body.lower()

        # Sentiment
        neg_words = ["frustrated", "angry", "disappointed", "terrible",
                     "horrible", "furious", "unhappy", "annoyed"]
        pos_words = ["love", "great", "fantastic", "excellent", "amazing",
                     "happy", "satisfied", "wonderful"]
        if any(w in lowered for w in neg_words):
            sentiment = "negative"
        elif any(w in lowered for w in pos_words):
            sentiment = "positive"
        else:
            sentiment = "neutral"

        # Complaints
        complaints = []
        if any(w in lowered for w in ["pricing", "expensive", "cost", "price"]):
            complaints.append("pricing concerns")
        if any(w in lowered for w in ["support", "ticket", "bug", "response time", "outage"]):
            complaints.append("support and reliability issues")
        if any(w in lowered for w in ["confus", "difficult", "hard to use", "complex"]):
            complaints.append("product usability confusion")
        if any(w in lowered for w in ["slow", "performance", "crash", "broken"]):
            complaints.append("performance and stability issues")

        # Urgency
        status_field = fields.get("status", "").lower()
        if any(w in lowered for w in ["cancel", "switching", "terminate",
                                       "will not renew", "evaluating alternatives",
                                       "competitor"]) or \
           any(w in status_field for w in ["at risk", "churn", "critical"]):
            urgency = "critical"
        elif any(w in lowered for w in ["frustrated", "angry", "escalate",
                                         "renewal risk", "losing confidence",
                                         "not renew", "outage"]):
            urgency = "high"
        elif any(w in lowered for w in ["concern", "issue", "problem",
                                         "slow", "confused"]):
            urgency = "medium"
        else:
            urgency = "low"

        # Churn signals
        churn_signals = []
        churn_phrases = [
            "switching", "switch to", "competitor", "cancel",
            "will not renew", "not renew", "evaluating alternatives",
            "evaluating salesforce", "evaluating hubspot",
            "losing confidence", "leaving", "terminate",
        ]
        for phrase in churn_phrases:
            if phrase in lowered:
                churn_signals.append(f"Customer mentioned: {phrase}")

        # Topics
        topics = []
        topic_map = [
            ("onboarding", ["onboarding", "getting started", "adoption"]),
            ("renewal", ["renewal", "renew", "contract"]),
            ("support", ["support", "ticket", "response time"]),
            ("pricing", ["pricing", "cost", "expensive"]),
            ("expansion", ["expand", "new team", "more seats", "upgrade"]),
        ]
        for topic, keywords in topic_map:
            if any(k in lowered for k in keywords):
                topics.append(topic)
        if fields.get("subject"):
            topics.append(f"email: {fields['subject']}")
        if fields.get("stage"):
            topics.append(f"stage: {fields['stage']}")

        return {
            "sentiment": sentiment,
            "key_topics": topics or ["customer engagement"],
            "complaints": complaints,
            "urgency_level": urgency,
            "action_items": ["follow up with customer", "review account health"],
            "churn_signals": churn_signals or (
                ["potential churn risk detected"] if urgency in ["high", "critical"] else []
            ),
            "input_type": input_type,
            "extracted_fields": fields,
            "raw_text": raw_text,
        }

    def chunk_and_embed(self, raw_text: str, customer_id: str) -> List[Dict[str, Any]]:
        try:
            if not raw_text or not raw_text.strip():
                return []
            chunks = self._chunk_text(raw_text, 500, 50)
            if self.collection is None:
                return [{"customer_id": customer_id, "chunks": len(chunks)}]
            for index, chunk in enumerate(chunks):
                doc_id = f"{customer_id}:{index}"
                self.collection.add(
                    ids=[doc_id],
                    documents=[chunk],
                    metadatas=[{"customer_id": customer_id, "chunk_index": index}],
                )
            return [{"customer_id": customer_id, "chunks": len(chunks)}]
        except Exception as exc:
            logger.exception("Chunk embedding failed: %s", exc)
            return []

    def _chunk_text(self, text: str, size: int, overlap: int) -> List[str]:
        chunks: List[str] = []
        start = 0
        while start < len(text):
            end = min(len(text), start + size)
            chunk = text[start:end]
            if chunk.strip():
                chunks.append(chunk.strip())
            start += size - overlap
        return chunks
