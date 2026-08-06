"""Knowledge Engine specific models.

Imports domain models for convenience. Future engine-specific
dataclasses (e.g., EmbeddingVector, RAGContext) will live here.
"""
from app.backend.domain.models import SearchResult, SemanticQuery  # noqa: F401
