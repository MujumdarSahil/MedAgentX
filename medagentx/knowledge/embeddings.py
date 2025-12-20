"""
Adaptive memory & embeddings system for MedAgentX.

Supports:
- OpenAI embeddings (if API key provided)
- HuggingFace sentence transformers (fallback)
- In-memory storage for symptom/diagnosis context
- Similarity search to enrich evidence
"""

import os
import logging
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

# Try to import OpenAI embeddings
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Try to import sentence transformers
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


class EmbeddingEngine:
    """Embedding engine with fallback support."""
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding engine.
        
        Args:
            api_key: OpenAI API key (optional)
            model_name: HuggingFace model name for fallback
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model_name
        self.openai_client = None
        self.sentence_model = None
        self.embedding_method = None
        
        # Initialize embedding method
        if OPENAI_AVAILABLE and self.api_key:
            try:
                self.openai_client = OpenAI(api_key=self.api_key)
                self.embedding_method = "openai"
                logger.info("Using OpenAI embeddings")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
                self.embedding_method = None
        
        if self.embedding_method is None and SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.sentence_model = SentenceTransformer(model_name)
                self.embedding_method = "sentence_transformers"
                logger.info(f"Using HuggingFace sentence transformers: {model_name}")
            except Exception as e:
                logger.warning(f"Failed to initialize sentence transformers: {e}")
                self.embedding_method = None
        
        if self.embedding_method is None:
            logger.warning("No embedding method available. Using simple keyword matching fallback.")
            self.embedding_method = "fallback"
    
    async def embed(self, text: str) -> List[float]:
        """
        Generate embedding for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        if not text:
            return []
        
        if self.embedding_method == "openai" and self.openai_client:
            try:
                response = self.openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input=text
                )
                return response.data[0].embedding
            except Exception as e:
                logger.error(f"OpenAI embedding error: {e}")
                # Fallback to sentence transformers
                if self.sentence_model:
                    return self.sentence_model.encode(text).tolist()
                return []
        
        elif self.embedding_method == "sentence_transformers" and self.sentence_model:
            try:
                return self.sentence_model.encode(text).tolist()
            except Exception as e:
                logger.error(f"Sentence transformer embedding error: {e}")
                return []
        
        else:
            # Fallback: simple keyword-based representation
            return self._fallback_embed(text)
    
    def _fallback_embed(self, text: str) -> List[float]:
        """Simple fallback embedding using keyword frequency."""
        # This is a very basic fallback - in production, you'd want something better
        keywords = text.lower().split()
        # Create a simple frequency-based vector (limited dimensions)
        vector = [0.0] * 50
        for i, keyword in enumerate(keywords[:50]):
            vector[i] = len(keyword) / 20.0  # Simple normalization
        return vector
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if not vec1 or not vec2:
            return 0.0
        
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        # Ensure same length
        min_len = min(len(vec1), len(vec2))
        vec1 = vec1[:min_len]
        vec2 = vec2[:min_len]
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))


class AdaptiveMemory:
    """Adaptive memory system for storing symptom/diagnosis context with embeddings."""
    
    def __init__(self, embedding_engine: Optional[EmbeddingEngine] = None):
        """
        Initialize adaptive memory.
        
        Args:
            embedding_engine: Embedding engine instance
        """
        self.embedding_engine = embedding_engine or EmbeddingEngine()
        self.memory_store: List[Dict[str, Any]] = []
        self.max_memory_size = 1000  # Limit memory size
    
    async def store(self, symptoms: str, diagnosis_context: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Store symptom/diagnosis context in memory.
        
        Args:
            symptoms: Symptom text
            diagnosis_context: Diagnosis or condition context
            metadata: Additional metadata
            
        Returns:
            Memory entry ID
        """
        # Create combined text for embedding
        combined_text = f"{symptoms} {diagnosis_context}"
        embedding = await self.embedding_engine.embed(combined_text)
        
        from datetime import datetime
        entry = {
            "id": f"mem_{len(self.memory_store)}",
            "symptoms": symptoms,
            "diagnosis_context": diagnosis_context,
            "embedding": embedding,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
        }
        
        self.memory_store.append(entry)
        
        # Limit memory size
        if len(self.memory_store) > self.max_memory_size:
            self.memory_store = self.memory_store[-self.max_memory_size:]
        
        return entry["id"]
    
    async def search_similar(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar symptom/diagnosis contexts.
        
        Args:
            query: Search query
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of similar memory entries with similarity scores
        """
        if not self.memory_store:
            return []
        
        query_embedding = await self.embedding_engine.embed(query)
        if not query_embedding:
            return []
        
        # Calculate similarities
        similarities: List[Tuple[float, Dict[str, Any]]] = []
        for entry in self.memory_store:
            if not entry.get("embedding"):
                continue
            
            similarity = self.embedding_engine.cosine_similarity(
                query_embedding,
                entry["embedding"]
            )
            
            if similarity >= similarity_threshold:
                similarities.append((similarity, entry))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[0], reverse=True)
        
        # Return top_k results with similarity scores
        results = []
        for similarity, entry in similarities[:top_k]:
            result = {
                "symptoms": entry["symptoms"],
                "diagnosis_context": entry["diagnosis_context"],
                "similarity": float(similarity),
                "metadata": entry.get("metadata", {}),
            }
            results.append(result)
        
        return results
    
    def clear(self) -> None:
        """Clear all memory entries."""
        self.memory_store.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        return {
            "total_entries": len(self.memory_store),
            "max_size": self.max_memory_size,
            "embedding_method": self.embedding_engine.embedding_method,
        }

