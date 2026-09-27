import hashlib
import json
import math
import os
import re
from typing import List


class EmbeddingService:
    """
    Embedding service abstraction for FinPilot RAG.
    Produces deterministic 384-dimensional normalized dense vectors.
    """

    DIMENSIONS: int = 384

    def __init__(self, model_name: str = "finpilot-dense-384"):
        self.model_name = os.environ.get("EMBEDDING_MODEL", model_name)

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate a 384-dimensional normalized dense vector representation of input text.
        Combines token unigram/bigram feature hashing with term frequency weighting.
        """
        if not text or not text.strip():
            return [0.0] * self.DIMENSIONS

        vector = [0.0] * self.DIMENSIONS
        # Tokenize and clean text
        tokens = re.findall(r"\b[a-zA-Z0-9_\$₹\.-]{2,}\b", text.lower())
        if not tokens:
            return [0.0] * self.DIMENSIONS

        # Feature hashing for unigrams and bigrams
        all_features = list(tokens)
        for i in range(len(tokens) - 1):
            all_features.append(f"{tokens[i]}_{tokens[i+1]}")

        for feature in all_features:
            h = int(hashlib.sha256(feature.encode("utf-8")).hexdigest(), 16)
            index = h % self.DIMENSIONS
            sign = 1.0 if (h >> 9) & 1 else -1.0
            vector[index] += sign * (1.0 + math.log(1.0 + all_features.count(feature)))

        # L2 Normalization
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            vector = [round(x / norm, 6) for x in vector]

        return vector

    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Calculate cosine similarity between two normalized vectors."""
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a, b in zip(vec_a, vec_b)))  # already normalized but safe
        # for normalized vectors dot_product is cosine similarity
        return max(0.0, min(1.0, float(dot_product)))

    @staticmethod
    def serialize_vector(vector: List[float]) -> str:
        """Serialize float vector to JSON string for persistent relational storage."""
        return json.dumps(vector)

    @staticmethod
    def deserialize_vector(vector_str: str) -> List[float]:
        """Deserialize JSON string into float vector."""
        if not vector_str:
            return []
        try:
            return json.loads(vector_str)
        except Exception:
            return []


# Global singleton instance
embedding_service = EmbeddingService()
