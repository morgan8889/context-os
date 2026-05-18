"""Sentence embedding model wrapper using all-mpnet-base-v2.

Lazy singleton: model loads on first call, not at import time.
CPU-only, 768-dimensional output, normalized vectors.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

MODEL_NAME = "all-mpnet-base-v2"
EMBEDDING_DIM = 768

_model: SentenceTransformer | None = None


class EmbeddingModel:
    """Wrapper around sentence-transformers SentenceTransformer model.

    Uses all-mpnet-base-v2 (768-dim, 110M params) for high-quality technical
    text embeddings. Vectors are L2-normalized for cosine similarity comparison.

    The model is loaded lazily on first use to avoid blocking application startup.
    """

    def __init__(self) -> None:
        self._model: SentenceTransformer | None = None

    def _load(self) -> SentenceTransformer:
        """Load the model if not yet loaded.

        Returns:
            Loaded SentenceTransformer model instance.
        """
        if self._model is None:
            logger.info("Loading embedding model: %s", MODEL_NAME)
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(MODEL_NAME)
            logger.info("Embedding model loaded (dim=%d)", EMBEDDING_DIM)
        return self._model

    def encode(self, text: str) -> list[float]:
        """Encode a single text string to a normalized 768-dim embedding.

        Args:
            text: Text to encode. Empty strings produce a zero-like vector.

        Returns:
            List of 768 floats representing the normalized embedding.
        """
        if not text or not text.strip():
            return [0.0] * EMBEDDING_DIM

        model = self._load()
        embedding = model.encode(
            text,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embedding.tolist()

    def encode_batch(
        self,
        texts: list[str],
        batch_size: int = 32,
    ) -> list[list[float]]:
        """Encode multiple texts in batches.

        Args:
            texts: List of texts to encode.
            batch_size: Number of texts per batch (default 32).

        Returns:
            List of 768-dim embedding lists, one per input text.
        """
        if not texts:
            return []

        model = self._load()
        embeddings = model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [e.tolist() for e in embeddings]


_embedding_model: EmbeddingModel | None = None


def get_embedding_model() -> EmbeddingModel:
    """Return the module-level singleton EmbeddingModel.

    The model instance is shared across all calls within a process.
    The underlying SentenceTransformer is loaded lazily on first encode() call.

    Returns:
        Singleton EmbeddingModel instance.
    """
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = EmbeddingModel()
    return _embedding_model
