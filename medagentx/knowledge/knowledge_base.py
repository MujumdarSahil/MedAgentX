"""
Knowledge Base for MedAgentX.

Manages medical knowledge storage and retrieval.
Supports multiple knowledge sources and retrieval strategies.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from medagentx.knowledge.retrieval import (
    RetrievalEngine,
    RetrievalStrategy,
    HybridRetrievalEngine,
)

logger = logging.getLogger(__name__)


class KnowledgeBase:
    """
    Knowledge base for medical information.
    
    Manages:
    - Multiple knowledge sources
    - Document indexing
    - Retrieval operations
    - Knowledge graph (conceptual)
    """
    
    def __init__(
        self,
        retrieval_engine: Optional[RetrievalEngine] = None,
    ):
        """
        Initialize knowledge base.
        
        Args:
            retrieval_engine: Retrieval engine to use
        """
        self.retrieval_engine = retrieval_engine or HybridRetrievalEngine()
        self._documents: List[Dict[str, Any]] = []
        self._knowledge_graph: Dict[str, Any] = {}  # Placeholder for KG
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        strategy: Optional[RetrievalStrategy] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search the knowledge base.
        
        Args:
            query: Search query
            top_k: Number of results
            strategy: Optional retrieval strategy override
            filters: Optional filters (source, date, type, etc.)
            
        Returns:
            List of retrieved knowledge items
        """
        try:
            results = await self.retrieval_engine.search(
                query=query,
                top_k=top_k,
                filters=filters,
            )
            
            # Enrich results with metadata
            for result in results:
                result["retrieved_at"] = datetime.now()
                result["knowledge_base"] = "medagentx"
            
            return results
        
        except Exception as e:
            logger.error(f"Knowledge base search error: {e}", exc_info=True)
            return []
    
    async def add_documents(
        self,
        documents: List[Dict[str, Any]],
        source: Optional[str] = None,
    ) -> None:
        """
        Add documents to the knowledge base.
        
        Args:
            documents: List of documents to add
            source: Source identifier for these documents
        """
        # Add metadata
        for doc in documents:
            doc["source"] = source or "user_uploaded"
            doc["added_at"] = datetime.now()
            if "id" not in doc:
                doc["id"] = f"doc_{len(self._documents)}"
        
        self._documents.extend(documents)
        
        # Add to retrieval engine
        await self.retrieval_engine.add_documents(documents)
        
        logger.info(f"Added {len(documents)} documents to knowledge base")
    
    async def retrieve_with_rag(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        Retrieve with RAG (Retrieval-Augmented Generation) context.
        
        Args:
            query: Query string
            context: Additional context
            top_k: Number of retrieval results
            
        Returns:
            Dict with retrieved context and metadata
        """
        # Retrieve relevant documents
        retrieved = await self.search(query, top_k=top_k)
        
        # Format as RAG context
        context_text = "\n\n".join([
            f"Document {i+1}:\n{item.get('content', '')}"
            for i, item in enumerate(retrieved)
        ])
        
        return {
            "query": query,
            "retrieved_documents": retrieved,
            "context": context_text,
            "metadata": {
                "num_documents": len(retrieved),
                "strategy": str(self.retrieval_engine.strategy),
            },
        }
    
    async def retrieve_with_cag(
        self,
        query: str,
        existing_context: str,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        Retrieve with CAG (Context-Augmented Generation).
        
        Uses existing context to improve retrieval.
        
        Args:
            query: Query string
            existing_context: Existing context to augment
            top_k: Number of retrieval results
            
        Returns:
            Enhanced context
        """
        # Combine query with existing context for better retrieval
        enhanced_query = f"{query}\n\nContext: {existing_context}"
        
        retrieved = await self.search(enhanced_query, top_k=top_k)
        
        # Augment existing context with retrieved information
        augmented_context = f"{existing_context}\n\nAdditional Information:\n"
        augmented_context += "\n\n".join([
            item.get("content", "")
            for item in retrieved
        ])
        
        return {
            "query": query,
            "original_context": existing_context,
            "augmented_context": augmented_context,
            "retrieved_documents": retrieved,
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        return {
            "total_documents": len(self._documents),
            "retrieval_strategy": str(self.retrieval_engine.strategy),
            "sources": list(set(doc.get("source", "unknown") for doc in self._documents)),
        }

