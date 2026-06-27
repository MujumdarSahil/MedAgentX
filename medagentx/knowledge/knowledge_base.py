from typing import Any, Dict, List
import logging

logger = logging.getLogger(__name__)


class KnowledgeBase:
    """Lightweight in-memory knowledge store (no vector DB)."""

    def __init__(self):
        self._docs: List[Dict[str, Any]] = [
            {
                "condition": "Upper respiratory infection",
                "content": "Common symptoms include cough, fever, sore throat; usually viral.",
                "tags": ["cough", "fever"],
            },
            {
                "condition": "Influenza",
                "content": "Fever with cough and myalgias may indicate influenza; confirm with testing.",
                "tags": ["fever", "cough"],
            },
            {
                "condition": "Allergic rhinitis",
                "content": "Sneezing and congestion without fever may suggest allergic rhinitis.",
                "tags": ["sneeze", "congestion"],
            },
        ]

    async def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Return simple relevance matches based on substring/tag presence."""
        query_lower = query.lower()
        scored = []
        for doc in self._docs:
            score = 0
            if query_lower in doc.get("content", "").lower():
                score += 2
            for tag in doc.get("tags", []):
                if tag in query_lower:
                    score += 1
            if score > 0:
                scored.append((score, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:top_k]]

    async def add_document(self, doc: Dict[str, Any]) -> None:
        self._docs.append(doc)

