import json
import logging
import os
import uuid
from typing import Any, Dict, List

from supabase import create_client

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
_FALLBACK_STORE: List[Dict[str, Any]] = []

# Tracks whether we've already tried to migrate the schema this session
_schema_migrated = False


def get_client():
    try:
        if not SUPABASE_URL or not SUPABASE_KEY or "your_supabase" in str(SUPABASE_URL).lower():
            return None
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as exc:
        logger.warning("Supabase client unavailable: %s", exc)
        return None


def ensure_schema(client) -> None:
    """
    Attempts to add any missing columns to the interactions table using
    Supabase's rpc / raw SQL endpoint. Safe to call repeatedly — uses
    IF NOT EXISTS so it's a no-op when columns already exist.
    """
    global _schema_migrated
    if _schema_migrated:
        return
    _schema_migrated = True
    try:
        # Run each ALTER TABLE individually so a single failure doesn't
        # block the others from executing.
        statements = [
            "ALTER TABLE interactions ADD COLUMN IF NOT EXISTS input_text TEXT DEFAULT '';",
            "ALTER TABLE interactions ADD COLUMN IF NOT EXISTS input_type TEXT DEFAULT 'meeting_transcript';",
            "ALTER TABLE interactions ADD COLUMN IF NOT EXISTS risk_score INTEGER DEFAULT 0;",
            "ALTER TABLE interactions ADD COLUMN IF NOT EXISTS urgency TEXT DEFAULT '';",
            "ALTER TABLE interactions ADD COLUMN IF NOT EXISTS key_signals JSONB DEFAULT '[]';",
            "ALTER TABLE interactions ADD COLUMN IF NOT EXISTS expansion_opportunity BOOLEAN DEFAULT FALSE;",
        ]
        for sql in statements:
            try:
                client.rpc("exec_sql", {"query": sql}).execute()
            except Exception as e:
                # rpc("exec_sql") usually doesn't exist on a default Supabase
                # project (it's not a built-in RPC) — that's expected. We fall
                # back to the progressive retry in save_interaction, but if the
                # interactions table genuinely lacks these columns, every save
                # will silently drop input_text/input_type until the columns
                # are added manually. Log at WARNING (not DEBUG) so this is
                # visible instead of hidden.
                logger.warning(
                    "Automatic schema migration unavailable (%s). If the "
                    "Conversations page is missing transcript text or always "
                    "shows 'meeting_transcript', run this SQL in the Supabase "
                    "SQL editor once: ALTER TABLE interactions ADD COLUMN IF "
                    "NOT EXISTS input_text TEXT DEFAULT ''; ALTER TABLE "
                    "interactions ADD COLUMN IF NOT EXISTS input_type TEXT "
                    "DEFAULT 'meeting_transcript';",
                    e,
                )
                break
        logger.info("Schema migration check completed")
    except Exception as exc:
        logger.debug("ensure_schema failed (non-critical): %s", exc)


def _normalize_recommendations(recommendations: Any) -> List[Dict[str, Any]]:
    if isinstance(recommendations, str):
        try:
            parsed = json.loads(recommendations)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            return []
    if isinstance(recommendations, list):
        return recommendations
    return []


def _normalize_list_field(value: Any) -> List[Any]:
    """
    Same shape-normalization as _normalize_recommendations, but generic for
    any jsonb-list column (e.g. key_signals) that may come back from Supabase
    as an already-parsed list or as a raw JSON string depending on client
    config.
    """
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            return []
    if isinstance(value, list):
        return value
    return []


def get_past_interactions(customer_id: str) -> List[Dict[str, Any]]:
    try:
        client = get_client()
        if client is None:
            return [item for item in _FALLBACK_STORE if item.get("customer_id") == customer_id]

        result = client.table("interactions") \
            .select("*") \
            .eq("customer_id", customer_id) \
            .order("created_at", desc=True) \
            .limit(10) \
            .execute()
        interactions = result.data or []
        return [
            {
                **item,
                "recommendations": _normalize_recommendations(item.get("recommendations", [])),
                "key_signals": _normalize_list_field(item.get("key_signals", [])),
            }
            for item in interactions
        ]
    except Exception as exc:
        logger.error("Memory fetch failed: %s", exc)
        return [item for item in _FALLBACK_STORE if item.get("customer_id") == customer_id]


def get_all_customers() -> List[Dict[str, Any]]:
    """
    Builds the customer list dynamically from real interaction history.
    Returns one row per customer_id with their most recent interaction's
    risk info and timestamp.
    """
    try:
        client = get_client()
        if client is None:
            source = _FALLBACK_STORE
        else:
            result = client.table("interactions") \
                .select("*") \
                .order("created_at", desc=True) \
                .limit(500) \
                .execute()
            source = result.data or []

        latest_by_customer: Dict[str, Dict[str, Any]] = {}
        for item in source:
            customer_id = item.get("customer_id")
            if not customer_id:
                continue
            if customer_id not in latest_by_customer:
                latest_by_customer[customer_id] = item

        customers = []
        for customer_id, item in latest_by_customer.items():
            recs = _normalize_recommendations(item.get("recommendations", []))
            # Prefer stored risk_score from the risk agent for accuracy — this is
            # the SAME risk_score/urgency the Dashboard's Risk Analysis panel
            # displays, so both views stay consistent. Fall back to
            # recommendation priorities only for older rows that predate the
            # risk_score column.
            stored_risk_score = item.get("risk_score")
            stored_urgency = str(item.get("urgency") or "").lower()
            if stored_risk_score is not None:
                score = int(stored_risk_score)
                # Thresholds aligned with the Risk Agent's own bands:
                # 0-30 = Low, 31-60 = Medium, 61-100 = High.
                if score >= 61:
                    risk = "High"
                elif score >= 31:
                    risk = "Medium"
                else:
                    risk = "Low"

                # Status mapping per spec:
                #   Low    -> Healthy
                #   Medium -> Healthy or At Risk (use urgency as the tiebreaker,
                #             since it's already computed by the same Risk Agent
                #             call rather than a new calculation)
                #   High   -> At Risk
                if risk == "High":
                    status = "At Risk"
                elif risk == "Medium":
                    status = "At Risk" if stored_urgency in ("high", "critical") else "Healthy"
                else:
                    status = "Healthy"
            else:
                priorities = [r.get("priority", "").lower() for r in recs if isinstance(r, dict)]
                if "high" in priorities:
                    risk = "High"
                elif "medium" in priorities:
                    risk = "Medium"
                else:
                    risk = "Low"
                status = "At Risk" if risk == "High" else "Healthy"

            customers.append({
                "id": customer_id,
                "risk": risk,
                "risk_score": stored_risk_score,
                "last_interaction": item.get("created_at", "now"),
                "status": status,
                "approved": bool(item.get("approved", False)),
            })

        customers.sort(key=lambda c: c.get("last_interaction") or "", reverse=True)
        return customers
    except Exception as exc:
        logger.error("get_all_customers failed: %s", exc)
        return []


def get_recent_conversations(limit: int = 20) -> List[Dict[str, Any]]:
    """
    Returns the most recent interactions across all customers.
    Each row includes the full input_text (truncated for preview) and the
    actual input_type so the Conversations page never shows 'unknown'.
    """
    try:
        client = get_client()
        if client is None:
            source = sorted(_FALLBACK_STORE, key=lambda x: x.get("created_at", ""), reverse=True)[:limit]
        else:
            result = client.table("interactions") \
                .select("*") \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()
            source = result.data or []

        conversations = []
        for item in source:
            text = item.get("input_text", "") or ""
            raw_type = item.get("input_type") or "meeting_transcript"
            conversations.append({
                "id": item.get("id"),
                "customer_id": item.get("customer_id", "unknown"),
                "input_type": raw_type,
                "summary": (text[:200] + "…") if len(text) > 200 else text,
                "has_text": bool(text.strip()),
                "created_at": item.get("created_at", "now"),
                "approved": bool(item.get("approved", False)),
                "risk_score": item.get("risk_score"),
                "urgency": item.get("urgency", ""),
            })
        return conversations
    except Exception as exc:
        logger.error("get_recent_conversations failed: %s", exc)
        return []


def get_approved_actions(customer_id: str) -> List[str]:
    """Returns list of already approved recommendation titles or action names."""
    try:
        interactions = get_past_interactions(customer_id)
        approved: List[str] = []
        for interaction in interactions:
            recs = _normalize_recommendations(interaction.get("recommendations", []))
            for rec in recs:
                if rec.get("approved") is True or interaction.get("approved") is True:
                    title = rec.get("action") or rec.get("title") or rec.get("name") or ""
                    if title:
                        approved.append(title.lower().strip())
        return approved
    except Exception as exc:
        logger.error("Approved actions fetch failed: %s", exc)
        return []


def save_interaction(
    customer_id: str,
    recommendations: List[Dict[str, Any]],
    approved: bool = False,
    feedback: str = "",
    input_text: str = "",
    input_type: str = "meeting_transcript",
    risk_score: int = 0,
    urgency: str = "",
    key_signals: List[str] | None = None,
    expansion_opportunity: bool = False,
) -> str:
    """
    Saves an interaction row. Uses a progressive fallback strategy so that
    interactions are never lost if the Supabase schema is missing newer
    columns (input_text, input_type, risk_score, urgency, key_signals,
    expansion_opportunity).

    Retry order:
      1. Full payload  (all columns)
      2. Without key_signals / expansion_opportunity  (older table)
      3. Without risk_score / urgency either  (in case those don't exist yet)
      4. Without input_text / input_type either  (minimal legacy schema)
      5. In-memory fallback store  (if Supabase is unreachable)
    """
    client = get_client()
    key_signals = key_signals or []

    # Always include everything in the in-memory store even if Supabase rejects it
    full_payload = {
        "customer_id": customer_id,
        "recommendations": json.dumps(recommendations),
        "approved": approved,
        "feedback": feedback,
        "input_text": input_text,
        "input_type": input_type,
        "risk_score": risk_score,
        "urgency": urgency,
        "key_signals": json.dumps(key_signals),
        "expansion_opportunity": expansion_opportunity,
    }

    if client is None:
        interaction_id = str(uuid.uuid4())
        _FALLBACK_STORE.append({"id": interaction_id, **full_payload, "created_at": "now"})
        logger.info("Saved interaction for %s in fallback store (no Supabase)", customer_id)
        return interaction_id

    # Try to add missing columns proactively (no-op if already exist)
    ensure_schema(client)

    # --- Attempt 1: full payload (everything, including key_signals/expansion) ---
    try:
        response = client.table("interactions").insert(full_payload).execute()
        data = response.data or []
        interaction_id = data[0].get("id") if data else str(uuid.uuid4())
        logger.info("Saved interaction for %s (full schema)", customer_id)
        return str(interaction_id)
    except Exception as exc1:
        logger.warning("Full-payload save failed (%s) — retrying without key_signals/expansion_opportunity", exc1)

    # --- Attempt 2: without key_signals / expansion_opportunity ---
    payload_v1b = {
        "customer_id": customer_id,
        "recommendations": json.dumps(recommendations),
        "approved": approved,
        "feedback": feedback,
        "input_text": input_text,
        "input_type": input_type,
        "risk_score": risk_score,
        "urgency": urgency,
    }
    try:
        response = client.table("interactions").insert(payload_v1b).execute()
        data = response.data or []
        interaction_id = data[0].get("id") if data else str(uuid.uuid4())
        logger.warning(
            "Saved interaction for %s WITHOUT key_signals/expansion_opportunity — "
            "those columns are missing from the 'interactions' table. Clicking "
            "this customer later will restore the risk score and urgency but "
            "not the original key signals list. Run the ALTER TABLE statements "
            "(see ensure_schema) to fix this for future analyses.",
            customer_id,
        )
        # Keep the full version in the fallback store so in-process reads
        # (if Supabase read-back is used anywhere) still have everything.
        _FALLBACK_STORE.append({"id": interaction_id, **full_payload, "created_at": "now"})
        return str(interaction_id)
    except Exception as exc1b:
        logger.warning("v1b save failed (%s) — retrying without risk_score/urgency", exc1b)

    # --- Attempt 3: without risk_score / urgency ---
    payload_v2 = {
        "customer_id": customer_id,
        "recommendations": json.dumps(recommendations),
        "approved": approved,
        "feedback": feedback,
        "input_text": input_text,
        "input_type": input_type,
    }
    try:
        response = client.table("interactions").insert(payload_v2).execute()
        data = response.data or []
        interaction_id = data[0].get("id") if data else str(uuid.uuid4())
        logger.info("Saved interaction for %s (v2 schema: no risk_score/urgency)", customer_id)
        _FALLBACK_STORE.append({"id": interaction_id, **full_payload, "created_at": "now"})
        return str(interaction_id)
    except Exception as exc2:
        logger.warning("v2 save failed (%s) — retrying minimal payload", exc2)

    # --- Attempt 4: minimal legacy schema ---
    payload_minimal = {
        "customer_id": customer_id,
        "recommendations": json.dumps(recommendations),
        "approved": approved,
        "feedback": feedback,
    }
    try:
        response = client.table("interactions").insert(payload_minimal).execute()
        data = response.data or []
        interaction_id = data[0].get("id") if data else str(uuid.uuid4())
        logger.warning(
            "Saved interaction for %s using the MINIMAL legacy schema — "
            "input_text/input_type/risk_score/urgency/key_signals were NOT "
            "persisted to Supabase for this row because the 'interactions' "
            "table is missing those columns. Run the ALTER TABLE statements "
            "(see ensure_schema) in the Supabase SQL editor to fix this "
            "permanently.",
            customer_id,
        )
        # Still keep in fallback store so get_recent_conversations returns the text
        _FALLBACK_STORE.append({"id": interaction_id, **full_payload, "created_at": "now"})
        return str(interaction_id)
    except Exception as exc3:
        logger.error("All Supabase save attempts failed: %s", exc3)

    # --- Attempt 5: in-memory only ---
    interaction_id = str(uuid.uuid4())
    _FALLBACK_STORE.append({"id": interaction_id, **full_payload, "created_at": "now"})
    logger.warning("Interaction %s saved to in-memory fallback only", interaction_id)
    return interaction_id


def _apply_rec_approval(recommendations: Any, rec_index: int | None, approved: bool) -> Any:
    """Stamp approved/status onto a single recommendation inside the list,
    leaving the others untouched. Returns the (possibly modified) list."""
    if isinstance(recommendations, str):
        try:
            recommendations = json.loads(recommendations)
        except Exception:
            recommendations = []
    if not isinstance(recommendations, list):
        return recommendations
    if rec_index is not None and 0 <= rec_index < len(recommendations):
        rec = recommendations[rec_index]
        if isinstance(rec, dict):
            rec["approved"] = approved
            rec["status"] = "approved" if approved else "rejected"
    return recommendations


def update_approval(
    interaction_id: str,
    approved: bool,
    feedback: str = "",
    rec_index: int | None = None,
) -> bool:
    try:
        client = get_client()
        if client is None:
            for item in _FALLBACK_STORE:
                if str(item.get("id")) == str(interaction_id):
                    item["recommendations"] = _apply_rec_approval(
                        item.get("recommendations", []), rec_index, approved
                    )
                    # Overall flag stays True once any single recommendation
                    # has been approved, so existing dashboard stats keep working.
                    item["approved"] = item.get("approved", False) or approved
                    item["feedback"] = feedback
                    return True
            return False

        # Fetch the current row first so we can patch just one recommendation
        # inside the JSON array without clobbering the others.
        existing = client.table("interactions").select("recommendations, approved").eq("id", interaction_id).execute()
        current_recs = existing.data[0].get("recommendations") if existing.data else []
        patched_recs = _apply_rec_approval(current_recs, rec_index, approved)
        overall_approved = bool(existing.data[0].get("approved")) if existing.data else False
        overall_approved = overall_approved or approved

        result = client.table("interactions") \
            .update({
                "approved": overall_approved,
                "feedback": feedback,
                "recommendations": patched_recs,
            }) \
            .eq("id", interaction_id) \
            .execute()
        # Also update fallback store in case it was saved there
        for item in _FALLBACK_STORE:
            if str(item.get("id")) == str(interaction_id):
                item["recommendations"] = patched_recs
                item["approved"] = overall_approved
                item["feedback"] = feedback
        return bool(result.data)
    except Exception as exc:
        logger.error("Approval update failed: %s", exc)
        for item in _FALLBACK_STORE:
            if str(item.get("id")) == str(interaction_id):
                item["recommendations"] = _apply_rec_approval(
                    item.get("recommendations", []), rec_index, approved
                )
                item["approved"] = item.get("approved", False) or approved
                item["feedback"] = feedback
                return True
        return False
