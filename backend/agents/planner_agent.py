import logging
from concurrent.futures import ThreadPoolExecutor
from typing import TypedDict, Any, Dict, List

from langgraph.graph import END, StateGraph

try:
    from backend.agents.ingestion_agent import IngestionAgent
    from backend.agents.retrieval_agent import RetrievalAgent
    from backend.agents.risk_agent import RiskAnalysisAgent
    from backend.agents.recommendation_agent import RecommendationAgent
    from backend.memory.memory_manager import get_past_interactions, save_interaction
except ModuleNotFoundError:
    from agents.ingestion_agent import IngestionAgent
    from agents.retrieval_agent import RetrievalAgent
    from agents.risk_agent import RiskAnalysisAgent
    from agents.recommendation_agent import RecommendationAgent
    from memory.memory_manager import get_past_interactions, save_interaction

logger = logging.getLogger(__name__)


class AgentState(TypedDict, total=False):
    customer_id: str
    input_text: str
    input_type: str
    ingested_data: Dict[str, Any]
    retrieved_context: List[str]
    risk_analysis: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    hitl_approved: bool
    session_id: str
    interaction_id: str
    error: str


class PlannerAgent:
    def __init__(self) -> None:
        self.ingestion_agent = IngestionAgent()
        self.retrieval_agent = RetrievalAgent()
        self.risk_agent = RiskAnalysisAgent()
        self.recommendation_agent = RecommendationAgent()
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(AgentState)
        workflow.add_node("ingest_and_retrieve_node", self._ingest_and_retrieve_node)
        workflow.add_node("analyze_node", self._analyze_node)
        workflow.add_node("recommend_node", self._recommend_node)
        workflow.add_node("hitl_node", self._hitl_node)
        workflow.add_node("memory_node", self._memory_node)

        workflow.add_edge("ingest_and_retrieve_node", "analyze_node")
        workflow.add_edge("analyze_node", "recommend_node")
        workflow.add_edge("recommend_node", "hitl_node")
        workflow.add_edge("hitl_node", "memory_node")
        workflow.add_edge("memory_node", END)
        workflow.set_entry_point("ingest_and_retrieve_node")
        return workflow.compile()

    def _ingest_and_retrieve_node(self, state: AgentState) -> AgentState:
        """
        SPEED FIX: ingestion is now instant (no LLM).
        Run ingestion and retrieval together in parallel threads.
        Both finish in under 1 second combined.
        """
        raw_text = state.get("input_text", "")
        input_type = state.get("input_type", "meeting_transcript")

        def run_ingest():
            ingested = self.ingestion_agent.process(raw_text, input_type)
            ingested["raw_text"] = raw_text
            return ingested

        def run_retrieve():
            # SPEED FIX: only fetch 3 results instead of 5
            return self.retrieval_agent.retrieve(raw_text, n_results=3)

        errors = []
        with ThreadPoolExecutor(max_workers=2) as executor:
            ingest_future = executor.submit(run_ingest)
            retrieve_future = executor.submit(run_retrieve)

            try:
                state["ingested_data"] = ingest_future.result(timeout=10)
            except Exception as exc:
                logger.exception("Ingestion failed")
                state["ingested_data"] = {"raw_text": raw_text}
                errors.append(str(exc))

            try:
                state["retrieved_context"] = retrieve_future.result(timeout=10)
            except Exception as exc:
                logger.exception("Retrieval failed")
                state["retrieved_context"] = []
                errors.append(str(exc))

        state["error"] = "; ".join(errors)
        return state

    def _analyze_node(self, state: AgentState) -> AgentState:
        """
        SPEED FIX: risk analysis is now instant (no LLM).
        Keyword scoring completes in under 0.05 seconds.
        """
        try:
            state["risk_analysis"] = self.risk_agent.analyze(
                state.get("ingested_data", {}),
                state.get("retrieved_context", []),
            )
            state["error"] = ""
        except Exception as exc:
            logger.exception("Risk analysis node failed")
            state["error"] = str(exc)
        return state

    def _recommend_node(self, state: AgentState) -> AgentState:
        """
        Only ONE Gemini call now happens here.
        All previous LLM calls (ingestion + risk) have been removed.
        Total time = 1 Gemini call instead of 3.
        """
        try:
            customer_id = state.get("customer_id", "")
            history = []
            if customer_id:
                history = get_past_interactions(customer_id) or []
            state["recommendations"] = self.recommendation_agent.generate(
                state.get("risk_analysis", {}),
                state.get("retrieved_context", []),
                customer_history=history,
                customer_id=customer_id,
            )
            state["error"] = ""
        except Exception as exc:
            logger.exception("Recommendation node failed")
            state["error"] = str(exc)
        return state

    def _hitl_node(self, state: AgentState) -> AgentState:
        try:
            state["hitl_approved"] = False
            state["error"] = ""
        except Exception as exc:
            logger.exception("HITL node failed")
            state["error"] = str(exc)
        return state

    def _memory_node(self, state: AgentState) -> AgentState:
        try:
            risk_analysis = state.get("risk_analysis", {})
            interaction_id = save_interaction(
                state.get("customer_id", "unknown"),
                state.get("recommendations", []),
                input_text=state.get("input_text", ""),
                input_type=state.get("input_type", "meeting_transcript"),
                risk_score=int(risk_analysis.get("churn_risk_score", 0)),
                urgency=str(risk_analysis.get("urgency", "")),
                key_signals=risk_analysis.get("key_signals", []),
                expansion_opportunity=bool(risk_analysis.get("expansion_opportunity", False)),
            )
            state["interaction_id"] = interaction_id
            state["error"] = ""
        except Exception as exc:
            logger.exception("Memory node failed")
            state["error"] = str(exc)
        return state

    def run(self, customer_id: str, input_text: str, session_id: str,
            input_type: str = "meeting_transcript") -> Dict[str, Any]:
        initial_state: AgentState = {
            "customer_id": customer_id,
            "input_text": input_text,
            "input_type": input_type,
            "ingested_data": {},
            "retrieved_context": [],
            "risk_analysis": {},
            "recommendations": [],
            "hitl_approved": False,
            "session_id": session_id,
            "error": "",
        }
        try:
            final_state = self.graph.invoke(initial_state)
            logger.info("Planner workflow completed for %s", session_id)
            return final_state
        except Exception as exc:
            logger.exception("Planner workflow failed")
            return {**initial_state, "error": str(exc)}
