"""Application service for RAG (Retrieval Augmented Generation) pipeline.

Orchestrates: semantic search → context building → prompt augmentation → generation.
Talks to SemanticSearchService and AIService, never to concrete adapters.
"""
from __future__ import annotations

import time
from typing import Any

from skos.m4.domain.ai_models import ChatMessage, ChatRequest, ChatResponse
from skos.m4.domain.rag_models import RAGContext, RAGQuery, RAGResult
from skos.m4.domain.search_models import SemanticQuery
from skos.m4.application.services.ai_service import AIService
from skos.m4.application.services.semantic_search_service import SemanticSearchService
from skos.m4.infrastructure.ports.config_port import ConfigurationPort
from skos.m4.infrastructure.ports.event_bus_port import EventBusPort
from skos.m4.infrastructure.ports.rag_pipeline_port import RAGPipelinePort, RAGError


class RAGPipelineService(RAGPipelinePort):
    """High-level RAG pipeline orchestrator.

    Dependencies:
        - SemanticSearchService: retrieves relevant documents
        - AIService: generates responses from augmented prompts
        - ConfigurationPort: reads RAG config
        - EventBusPort: publishes RAG events
    """

    DEFAULT_SYSTEM_PROMPT: str = (
        "You are a helpful assistant. Use the provided context to answer the question. "
        "If the context does not contain the answer, say so clearly."
    )

    def __init__(
        self,
        semantic_search: SemanticSearchService,
        ai_service: AIService,
        config: ConfigurationPort,
        event_bus: EventBusPort,
    ) -> None:
        self._search = semantic_search
        self._ai = ai_service
        self._config = config
        self._bus = event_bus
        self._default_top_k = config.get("m4.rag.default_top_k", default=5)
        self._system_prompt = config.get("m4.rag.system_prompt", default=self.DEFAULT_SYSTEM_PROMPT)

    def answer(self, query: RAGQuery) -> RAGResult:
        """Execute full RAG: retrieve → build context → augment prompt → generate."""
        start = time.perf_counter()
        try:
            # 1. Semantic search
            search_query = SemanticQuery(
                text=query.question,
                top_k=query.top_k or self._default_top_k,
                filter_metadata=query.filter_metadata,
                min_similarity=query.min_similarity,
            )
            search_result = self._search.search(search_query)

            context = RAGContext(
                documents=search_result.results,
                total_found=search_result.total_found,
                query_time_ms=search_result.query_time_ms,
            )

            # 2. Build augmented prompt
            messages = self._build_messages(query, context)
            chat_request = ChatRequest(messages=messages)

            # 3. Generate response
            response = self._ai.chat(chat_request)

            elapsed_ms = (time.perf_counter() - start) * 1000

            result = RAGResult(
                query=query,
                context=context,
                response=response,
                total_time_ms=elapsed_ms,
            )

            self._bus.publish(
                "rag.events",
                {
                    "event": "rag.response_generated",
                    "question": query.question,
                    "context_docs": len(context.documents),
                    "total_time_ms": elapsed_ms,
                },
            )
            return result

        except Exception as exc:
            self._bus.publish(
                "rag.events",
                {
                    "event": "rag.failed",
                    "question": query.question,
                    "error": str(exc),
                },
            )
            raise RAGError(f"RAG pipeline failed: {exc}") from exc

    def _build_messages(self, query: RAGQuery, context: RAGContext) -> list[ChatMessage]:
        """Build chat messages with retrieved context."""
        system_prompt = query.system_prompt or self._system_prompt

        if context.documents:
            context_text = "\n\n".join(
                f"[Document {i+1}] {doc.text}"
                for i, doc in enumerate(context.documents)
            )
            system_content = (
                f"{system_prompt}\n\n"
                f"Context:\n{context_text}"
            )
        else:
            system_content = system_prompt

        return [
            ChatMessage(role="system", content=system_content),
            ChatMessage(role="user", content=query.question),
        ]

    def health_check(self) -> bool:
        return self._search.health_check() and self._ai.health_check()
