
import logging
import os
from typing import Any, Dict, List

from dotenv import load_dotenv

try:
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
except Exception:
    GoogleGenerativeAIEmbeddings = None

try:
    import chromadb
except Exception:
    chromadb = None

try:
    from backend.data.knowledge_docs import KNOWLEDGE_DOCS
except ModuleNotFoundError:
    from data.knowledge_docs import KNOWLEDGE_DOCS

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

logger = logging.getLogger(__name__)


class RetrievalAgent:
    def __init__(self) -> None:
        self.client = None
        self.knowledge_base_collection = None
        self.customer_interactions_collection = None
        self.embeddings = None
        self._initialize_vector_store()

    def _initialize_vector_store(self) -> None:
        try:
            if chromadb is None:
                return
            host = os.getenv("CHROMA_HOST", "localhost")
            port = int(os.getenv("CHROMA_PORT", "8001"))
            self.client = chromadb.HttpClient(host=host, port=port)
            self.knowledge_base_collection = self.client.get_or_create_collection(name="knowledge_base")
            self.customer_interactions_collection = self.client.get_or_create_collection(name="customer_interactions")
            self._init_embeddings()
            self._preload_knowledge_docs()
        except Exception as exc:
            logger.warning("ChromaDB initialization failed for retrieval: %s", exc)
            self.client = None
            self.knowledge_base_collection = None
            self.customer_interactions_collection = None

    def _init_embeddings(self) -> None:
        try:
            if GoogleGenerativeAIEmbeddings is None:
                return
            api_key = os.getenv("GOOGLE_API_KEY", "")
            if not api_key or "your_gemini_api_key_here" in api_key:
                return
            self.embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=api_key)
        except Exception as exc:
            logger.warning("Embeddings init failed: %s", exc)
            self.embeddings = None

    def ingest_knowledge_doc(self, text: str, doc_id: str, metadata: Dict[str, Any]) -> None:
        try:
            if self.knowledge_base_collection is None:
                return
            self.knowledge_base_collection.add(ids=[doc_id], documents=[text], metadatas=[metadata])
        except Exception as exc:
            logger.warning("Knowledge doc ingest failed: %s", exc)

    def get_all_knowledge_docs(self) -> List[Dict[str, Any]]:
        """
        Returns every document actually stored in the knowledge_base
        ChromaDB collection, with its real metadata (title/category/type),
        instead of a hardcoded list that can drift from what's truly loaded.
        """
        try:
            if self.knowledge_base_collection is None:
                return [
                    {"id": doc["id"], "text": doc["text"], **doc["metadata"]}
                    for doc in KNOWLEDGE_DOCS
                ]
            if self.knowledge_base_collection.count() == 0:
                self._preload_knowledge_docs()
            result = self.knowledge_base_collection.get()
            ids = result.get("ids", [])
            documents = result.get("documents", [])
            metadatas = result.get("metadatas", [])
            docs = []
            for i, doc_id in enumerate(ids):
                metadata = metadatas[i] if i < len(metadatas) and metadatas[i] else {}
                docs.append({
                    "id": doc_id,
                    "text": documents[i] if i < len(documents) else "",
                    "title": metadata.get("title", doc_id),
                    "category": metadata.get("category", "general"),
                    "type": metadata.get("type", "document"),
                })
            return docs
        except Exception as exc:
            logger.warning("get_all_knowledge_docs failed: %s", exc)
            return [
                {"id": doc["id"], "text": doc["text"], **doc["metadata"]}
                for doc in KNOWLEDGE_DOCS
            ]

    def get_knowledge_base_status(self) -> Dict[str, Any]:
        """Live connection + document count, instead of a hardcoded string."""
        try:
            if self.knowledge_base_collection is None:
                return {"connected": False, "document_count": 0}
            count = self.knowledge_base_collection.count()
            return {"connected": True, "document_count": count}
        except Exception as exc:
            logger.warning("get_knowledge_base_status failed: %s", exc)
            return {"connected": False, "document_count": 0}

    def retrieve(self, query: str, n_results: int = 5) -> List[str]:
        try:
            if self.knowledge_base_collection is None:
                return self._fallback_retrieve(query, n_results)
            if self.knowledge_base_collection.count() == 0:
                self._preload_knowledge_docs()
            results = self.knowledge_base_collection.query(query_texts=[query], n_results=n_results)
            documents = results.get("documents", [[]])[0]
            if documents:
                return [str(doc) for doc in documents]
            return self._fallback_retrieve(query, n_results)
        except Exception as exc:
            logger.warning("Retrieval failed: %s", exc)
            return self._fallback_retrieve(query, n_results)

    def _preload_knowledge_docs(self) -> None:
        try:
            if self.knowledge_base_collection is None:
                return
            if self.knowledge_base_collection.count() > 0:
                return
            for doc in KNOWLEDGE_DOCS:
                self.ingest_knowledge_doc(doc["text"], doc["id"], doc["metadata"])
        except Exception as exc:
            logger.warning("Knowledge preload failed: %s", exc)

    def _fallback_retrieve(self, query: str, n_results: int = 5) -> List[str]:
        lowered = query.lower()
        results = []
        for doc in KNOWLEDGE_DOCS:
            text = doc["text"].lower()
            if any(term in text for term in ["churn", "onboarding", "expansion", "support", "executive", "qbr", "renewal", "feedback"]):
                if any(term in lowered for term in ["churn", "onboarding", "expansion", "support", "executive", "qbr", "renewal", "feedback"]):
                    results.append(doc["text"])
        return results[:n_results]
