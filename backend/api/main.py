
import json
import logging
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from backend.agents.planner_agent import PlannerAgent
    from backend.memory.memory_manager import (
        get_past_interactions,
        save_interaction,
        update_approval,
        get_all_customers,
        get_recent_conversations,
    )
except ModuleNotFoundError:
    from agents.planner_agent import PlannerAgent
    from memory.memory_manager import (
        get_past_interactions,
        save_interaction,
        update_approval,
        get_all_customers,
        get_recent_conversations,
    )

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="NBA Platform", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions: Dict[str, Dict[str, Any]] = {}
planner_agent = PlannerAgent()


class AnalyzeRequest(BaseModel):
    customer_id: str
    input_text: str
    session_id: str
    input_type: str = "meeting_transcript"


class ApprovalRequest(BaseModel):
    session_id: str | None = None
    approved: bool
    feedback: str = ""


def _normalize_interaction(item: Dict[str, Any]) -> Dict[str, Any]:
    recommendations = item.get("recommendations", [])
    if isinstance(recommendations, str):
        try:
            recommendations = json.loads(recommendations)
        except Exception:
            recommendations = []
    return {
        **item,
        "recommendations": recommendations,
        "approved": bool(item.get("approved", False)),
    }


@app.post("/api/analyze")
async def analyze(request: AnalyzeRequest):
    try:
        result = planner_agent.run(
            request.customer_id,
            request.input_text,
            request.session_id,
            input_type=request.input_type,
        )
        sessions[request.session_id] = result
        return {
            "session_id": request.session_id,
            "recommendations": result.get("recommendations", []),
            "risk_analysis": result.get("risk_analysis", {}),
            "ingested_data": result.get("ingested_data", {}),
            "customer_id": request.customer_id,
            "input_type": request.input_type,
            "status": "awaiting_approval",
            "interaction_id": result.get("interaction_id"),
        }
    except Exception as exc:
        logger.exception("Analyze endpoint failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/approve")
async def approve_legacy(request: ApprovalRequest):
    try:
        session_id = request.session_id or ""
        session = sessions.get(session_id)
        if session:
            session["hitl_approved"] = request.approved
        return approve_interaction(session_id or "", request)
    except Exception as exc:
        logger.exception("Approval endpoint failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/approve/{interaction_id}")
async def approve_interaction(interaction_id: str, request: ApprovalRequest):
    try:
        updated = update_approval(
            interaction_id,
            request.approved,
            request.feedback,
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Interaction not found")
        return {
            "status": "approved" if request.approved else "rejected",
            "message": "Approval updated",
            "interaction_id": interaction_id,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Approval endpoint failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/customer/{customer_id}/history")
async def history(customer_id: str):
    try:
        interactions = get_past_interactions(customer_id)
        return [_normalize_interaction(item) for item in interactions]
    except Exception as exc:
        logger.exception("History endpoint failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/customers")
async def customers():
    """
    Returns the live customer list, derived from real interaction history
    rather than a hardcoded array. Any customer_id ever analyzed shows up
    here automatically.
    """
    try:
        return get_all_customers()
    except Exception as exc:
        logger.exception("Customers endpoint failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/playbooks")
async def playbooks():
    """
    Returns the actual documents currently stored in the ChromaDB
    knowledge_base collection, with their real metadata. This will always
    match whatever is truly loaded, rather than a hardcoded list that can
    drift out of sync with the vector store.
    """
    try:
        return planner_agent.retrieval_agent.get_all_knowledge_docs()
    except Exception as exc:
        logger.exception("Playbooks endpoint failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/knowledge-base/status")
async def knowledge_base_status():
    """Live ChromaDB connection state + real document count."""
    try:
        return planner_agent.retrieval_agent.get_knowledge_base_status()
    except Exception as exc:
        logger.exception("Knowledge base status endpoint failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/conversations")
async def conversations(limit: int = 20):
    """
    Returns the most recent real interactions across all customers, derived
    from what was actually submitted on the Dashboard (input_text/input_type),
    instead of 3 hardcoded sample cards.
    """
    try:
        return get_recent_conversations(limit)
    except Exception as exc:
        logger.exception("Conversations endpoint failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/reports/summary")
async def reports_summary():
    """
    Platform-wide totals across every customer, separate from the
    per-customer numbers shown on the Dashboard/Recommendations tabs.
    """
    try:
        all_customers = get_all_customers()
        total_customers = len(all_customers)
        all_interactions = []
        for c in all_customers:
            all_interactions.extend(get_past_interactions(c["id"]))
        total_interactions = len(all_interactions)
        approved_count = sum(1 for i in all_interactions if i.get("approved"))
        approval_rate = round((approved_count / total_interactions) * 100) if total_interactions else 0
        confidences = []
        for interaction in all_interactions:
            recs = interaction.get("recommendations", [])
            if isinstance(recs, str):
                try:
                    recs = json.loads(recs)
                except Exception:
                    recs = []
            for rec in recs:
                if isinstance(rec, dict) and "confidence" in rec:
                    confidences.append(float(rec["confidence"]))
        avg_confidence = round(sum(confidences) / len(confidences), 2) if confidences else 0.0
        return {
            "total_customers": total_customers,
            "total_interactions": total_interactions,
            "approval_rate": approval_rate,
            "avg_confidence": avg_confidence,
        }
    except Exception as exc:
        logger.exception("Reports summary endpoint failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.exception_handler(HTTPException)
async def http_exception_handler(_, exc: HTTPException):
    return {"detail": exc.detail}, exc.status_code
