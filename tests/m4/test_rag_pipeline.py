"""Tests for RAG Pipeline (M4.6)."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from skos.m4.domain.ai_models import ChatMessage, ChatRequest, ChatResponse
from skos.m4.domain.rag_models import RAGContext, RAGQuery, RAGResult
from skos.m4.domain.search_models import RankedDocument, SemanticQuery, SemanticSearchResult
from skos.m4.infrastructure.ports.rag_pipeline_port import RAGPipelinePort, RAGError
from skos.m4.application.services.rag_pipeline_service import RAGPipelineService


class TestDomainModels:
    def test_rag_query_creation(self) -> None:
        q = RAGQuery(question="What is AI?", top_k=3)
        assert q.question == "What is AI?"
        assert q.top_k == 3
        assert q.system_prompt is None

    def test_rag_query_with_system_prompt(self) -> None:
        q = RAGQuery(question="test", system_prompt="Be concise")
        assert q.system_prompt == "Be concise"

    def test_rag_context_defaults(self) -> None:
        c = RAGContext(documents=[], total_found=0)
        assert c.query_time_ms == 0.0

    def test_rag_result_defaults(self) -> None:
        q = RAGQuery(question="x")
        c = RAGContext(documents=[], total_found=0)
        r = ChatResponse(content="ok", model="m")
        result = RAGResult(query=q, context=c, response=r)
        assert result.total_time_ms == 0.0


class TestRAGPipelinePort:
    def test_rag_pipeline_port_is_abc(self) -> None:
        assert hasattr(RAGPipelinePort, "answer")
        assert hasattr(RAGPipelinePort, "health_check")


class TestRAGPipelineService:
    @pytest.fixture
    def mock_deps(self) -> dict[str, MagicMock]:
        search = MagicMock()
        search.search.return_value = SemanticSearchResult(
            query=SemanticQuery(text="test"),
            results=[
                RankedDocument(id="d1", text="AI is artificial intelligence.", similarity_score=0.95, rank=1),
                RankedDocument(id="d2", text="ML is a subset of AI.", similarity_score=0.85, rank=2),
            ],
            total_found=2,
            query_time_ms=12.0,
        )
        search.health_check.return_value = True

        ai = MagicMock()
        ai.chat.return_value = ChatResponse(content="AI stands for artificial intelligence.", model="gpt-4")
        ai.health_check.return_value = True

        config = MagicMock()
        config.get.side_effect = lambda key, default=None: {
            "m4.rag.default_top_k": 5,
            "m4.rag.system_prompt": "You are a helpful assistant.",
        }.get(key, default)

        bus = MagicMock()
        return {"search": search, "ai": ai, "config": config, "bus": bus}

    def test_answer_returns_rag_result(self, mock_deps: dict[str, MagicMock]) -> None:
        service = RAGPipelineService(
            mock_deps["search"], mock_deps["ai"], mock_deps["config"], mock_deps["bus"]
        )
        query = RAGQuery(question="What is AI?", top_k=2)
        result = service.answer(query)
        assert isinstance(result, RAGResult)
        assert result.query.question == "What is AI?"
        assert result.context.total_found == 2
        assert result.response.content == "AI stands for artificial intelligence."

    def answer_delegates_search(self, mock_deps: dict[str, MagicMock]) -> None:
        service = RAGPipelineService(
            mock_deps["search"], mock_deps["ai"], mock_deps["config"], mock_deps["bus"]
        )
        service.answer(RAGQuery(question="test"))
        mock_deps["search"].search.assert_called_once()

    def test_answer_delegates_chat(self, mock_deps: dict[str, MagicMock]) -> None:
        service = RAGPipelineService(
            mock_deps["search"], mock_deps["ai"], mock_deps["config"], mock_deps["bus"]
        )
        service.answer(RAGQuery(question="test"))
        mock_deps["ai"].chat.assert_called_once()

    def test_answer_emits_event(self, mock_deps: dict[str, MagicMock]) -> None:
        service = RAGPipelineService(
            mock_deps["search"], mock_deps["ai"], mock_deps["config"], mock_deps["bus"]
        )
        service.answer(RAGQuery(question="test"))
        calls = mock_deps["bus"].publish.call_args_list
        assert any("rag.response_generated" in str(c) for c in calls)

    def test_answer_with_no_documents(self, mock_deps: dict[str, MagicMock]) -> None:
        mock_deps["search"].search.return_value = SemanticSearchResult(
            query=SemanticQuery(text="test"),
            results=[],
            total_found=0,
        )
        service = RAGPipelineService(
            mock_deps["search"], mock_deps["ai"], mock_deps["config"], mock_deps["bus"]
        )
        result = service.answer(RAGQuery(question="test"))
        assert result.context.total_found == 0
        mock_deps["ai"].chat.assert_called_once()

    def test_answer_emits_failed_event_on_error(self, mock_deps: dict[str, MagicMock]) -> None:
        mock_deps["search"].search.side_effect = RuntimeError("search failed")
        service = RAGPipelineService(
            mock_deps["search"], mock_deps["ai"], mock_deps["config"], mock_deps["bus"]
        )
        with pytest.raises(RAGError):
            service.answer(RAGQuery(question="test"))
        calls = mock_deps["bus"].publish.call_args_list
        assert any("rag.failed" in str(c) for c in calls)

    def test_health_check_delegates(self, mock_deps: dict[str, MagicMock]) -> None:
        service = RAGPipelineService(
            mock_deps["search"], mock_deps["ai"], mock_deps["config"], mock_deps["bus"]
        )
        assert service.health_check() is True

    def test_custom_system_prompt(self, mock_deps: dict[str, MagicMock]) -> None:
        service = RAGPipelineService(
            mock_deps["search"], mock_deps["ai"], mock_deps["config"], mock_deps["bus"]
        )
        service.answer(RAGQuery(question="test", system_prompt="Be very concise"))
        call_args = mock_deps["ai"].chat.call_args
        messages = call_args[0][0].messages
        assert any("Be very concise" in m.content for m in messages)
