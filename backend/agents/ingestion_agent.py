
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

try:
    import chromadb
except Exception:
    chromadb = None

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

logger = logging.getLogger(__name__)


class IngestionAgent:
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
            self.collection = self.client.get_or_create_collection(name="customer_interactions")
        except Exception as exc:
            logger.warning("ChromaDB initialization failed: %s", exc)
            self.client = None
            self.collection = None

    def _get_llm(self):
        if ChatGoogleGenerativeAI is None:
            return None
        api_key = os.getenv("GOOGLE_API_KEY", "")
        if not api_key or "your_gemini_api_key_here" in api_key:
            return None
        return ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=api_key, temperature=0.2)

    def process(self, raw_text: str, input_type: str = "meeting_transcript") -> Dict[str, Any]:
        try:
            if not raw_text or not raw_text.strip():
                return self._fallback_structure("", input_type)

            preprocessed = self._preprocess_by_type(raw_text, input_type)

            llm = self._get_llm()
            if llm is None:
                return self._fallback_structure(raw_text, input_type, preprocessed)

            type_instructions = {
                "meeting_transcript": "This is a meeting transcript with multiple speakers. Focus on what the customer said, not the rep.",
                "customer_email": "This is a customer email. The Subject line and the body's main ask matter most; sign-offs and pleasantries do not.",
                "crm_note": "This is a short CRM note, often just a few structured fields (Status, Stage, Next Step, etc) plus a brief free-text comment. Treat each field as a direct signal rather than narrative.",
            }
            instruction = type_instructions.get(input_type, type_instructions["meeting_transcript"])

            prompt = (
                f"{instruction} "
                "Extract structured customer success insights from the text below. "
                "Return ONLY valid JSON with these keys: sentiment, key_topics, complaints, urgency_level, action_items, churn_signals. "
                "Use values that match the content."
                f"\n\nInput type: {input_type}"
                f"\n\nText:\n{preprocessed['body']}"
            )
            response = llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            parsed = self._safe_json_parse(content)
            if parsed:
                return {
                    "sentiment": parsed.get("sentiment", "neutral"),
                    "key_topics": parsed.get("key_topics", []),
                    "complaints": parsed.get("complaints", []),
                    "urgency_level": parsed.get("urgency_level", "medium"),
                    "action_items": parsed.get("action_items", []),
                    "churn_signals": parsed.get("churn_signals", []),
                    "input_type": input_type,
                    "extracted_fields": preprocessed.get("fields", {}),
                }
            return self._fallback_structure(raw_text, input_type, preprocessed)
        except Exception as exc:
            logger.exception("Ingestion failed")
            return self._fallback_structure(raw_text, input_type)

    def _preprocess_by_type(self, raw_text: str, input_type: str) -> Dict[str, Any]:
        """
        Adjusts what counts as the 'body' to analyze and pulls out
        type-specific structured fields before the LLM/fallback ever sees it.
        """
        if input_type == "customer_email":
            return self._preprocess_email(raw_text)
        if input_type == "crm_note":
            return self._preprocess_crm_note(raw_text)
        # meeting_transcript and anything unrecognized: use as-is
        return {"body": raw_text, "fields": {}}

    def _preprocess_email(self, raw_text: str) -> Dict[str, Any]:
        """
        Pulls common email headers (From/To/Subject/Date) out of the body so
        the analysis focuses on the actual message, while still surfacing the
        subject line as a strong signal (it's prepended back into the body).
        """
        fields: Dict[str, str] = {}
        body_lines: List[str] = []
        header_pattern = re.compile(r"^\s*(from|to|subject|date|cc|bcc)\s*:\s*(.+)$", re.IGNORECASE)

        for line in raw_text.splitlines():
            match = header_pattern.match(line)
            if match:
                key = match.group(1).lower()
                fields[key] = match.group(2).strip()
            else:
                body_lines.append(line)

        body = "\n".join(body_lines).strip()
        if fields.get("subject"):
            body = f"Subject: {fields['subject']}\n\n{body}"
        return {"body": body or raw_text, "fields": fields}

    def _preprocess_crm_note(self, raw_text: str) -> Dict[str, Any]:
        """
        CRM notes are often short 'Field: value' lines (Status, Stage, ARR,
        Next Step, Renewal Date) plus a one or two line free-text comment.
        Pull the fields out explicitly so they read as direct signals instead
        of being buried in prose.
        """
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

        field_summary = "; ".join(f"{k.replace('_', ' ').title()}: {v}" for k, v in fields.items())
        comment = " ".join(comment_lines)
        body = f"{field_summary}\n\nNotes: {comment}".strip() if field_summary or comment else raw_text
        return {"body": body, "fields": fields}

    def chunk_and_embed(self, raw_text: str, customer_id: str) -> List[Dict[str, Any]]:
        try:
            if not raw_text or not raw_text.strip():
                return []
            chunks = self._chunk_text(raw_text, 500, 50)
            if self.collection is None:
                return [{"customer_id": customer_id, "chunks": len(chunks)}]
            for index, chunk in enumerate(chunks):
                doc_id = f"{customer_id}:{index}"
                self.collection.add(ids=[doc_id], documents=[chunk], metadatas=[{"customer_id": customer_id, "chunk_index": index}])
            return [{"customer_id": customer_id, "chunks": len(chunks)}]
        except Exception as exc:
            logger.exception("Chunk embedding failed")
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

    def _safe_json_parse(self, content: str) -> Dict[str, Any]:
        try:
            text = re.sub(r"```json|```", "", content).strip()
            return json.loads(text)
        except Exception:
            return {}

    def _fallback_structure(self, raw_text: str, input_type: str = "meeting_transcript", preprocessed: Dict[str, Any] = None) -> Dict[str, Any]:
        body = (preprocessed or {}).get("body") or raw_text
        fields = (preprocessed or {}).get("fields") or {}
        lowered = body.lower()

        complaints = []
        if "pricing" in lowered:
            complaints.append("pricing concerns")
        if "support" in lowered or "bug" in lowered:
            complaints.append("product support issue")
        if "feature" in lowered and "confused" in lowered:
            complaints.append("feature confusion")

        urgency = "medium"
        if any(word in lowered for word in ["urgent", "churn", "cancel", "competitor", "critical"]):
            urgency = "high"
        # CRM notes often carry the urgency directly in a status field
        status_field = fields.get("status", "").lower()
        if any(word in status_field for word in ["at risk", "churn", "critical", "urgent"]):
            urgency = "high"

        topics = []
        if "onboarding" in lowered:
            topics.append("onboarding")
        if "renewal" in lowered:
            topics.append("renewal")
        if "support" in lowered:
            topics.append("support")
        if fields.get("subject"):
            topics.append("email: " + fields["subject"])
        if fields.get("stage"):
            topics.append("stage: " + fields["stage"])

        return {
            "sentiment": "negative" if any(word in lowered for word in ["frustrated", "angry", "disappointed"]) else "neutral",
            "key_topics": topics or ["customer engagement"],
            "complaints": complaints,
            "urgency_level": urgency,
            "action_items": ["follow up with the customer"],
            "churn_signals": ["mentions of churn risk" if "churn" in lowered else "declining engagement"],
            "input_type": input_type,
            "extracted_fields": fields,
        }
