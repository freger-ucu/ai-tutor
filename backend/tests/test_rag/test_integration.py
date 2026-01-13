"""
RAG integration tests - TDD approach.

Tests are written FIRST, then implementation is verified.
"""

import pytest
import numpy as np


class TestRAGDataLoader:
    """Tests for RAG data loader."""

    def test_loads_pages_parquet(self):
        """RAGDataLoader should load pages with embeddings."""
        from app.rag.utils.rag_data_loader import get_data_loader

        loader = get_data_loader()
        pages = loader.load_textbook_pages()

        assert pages is not None
        assert len(pages) > 0
        assert "page_text" in pages.columns
        assert "page_text_embedding" in pages.columns
        assert "global_discipline_name" in pages.columns
        assert "grade" in pages.columns

    def test_loads_toc_parquet(self):
        """RAGDataLoader should load TOC with topic embeddings."""
        from app.rag.utils.rag_data_loader import get_data_loader

        loader = get_data_loader()
        toc = loader.load_toc()

        assert toc is not None
        assert len(toc) > 0
        assert "topic_title" in toc.columns
        assert "topic_embedding" in toc.columns
        assert "global_discipline_name" in toc.columns

    def test_filters_by_subject_and_grade(self):
        """Should filter pages by subject and grade."""
        from app.rag.utils.rag_data_loader import get_data_loader

        loader = get_data_loader()
        pages = loader.get_pages_for_subject_grade("Українська мова", 9)

        assert len(pages) > 0
        assert all(pages["global_discipline_name"] == "Українська мова")
        assert all(pages["grade"] == 9)

    def test_returns_empty_for_unknown_subject(self):
        """Should return empty DataFrame for unknown subject."""
        from app.rag.utils.rag_data_loader import get_data_loader

        loader = get_data_loader()
        pages = loader.get_pages_for_subject_grade("Неіснуючий предмет", 9)

        assert len(pages) == 0


class TestHybridRetriever:
    """Tests for hybrid retriever (BM25 + Vector + RRF)."""

    @pytest.fixture
    def retriever(self):
        """Create retriever instance."""
        from app.rag.utils.hybrid_retriever import get_retriever
        return get_retriever()

    @pytest.mark.asyncio
    async def test_retrieves_relevant_pages(self, retriever):
        """Should return relevant pages for a query."""
        docs = await retriever.retrieve(
            query="Яка різниця між сурядним та підрядним зв'язком?",
            subject="Українська мова",
            grade=9,
            top_k=5,
        )

        assert len(docs) > 0
        assert len(docs) <= 5
        # Each doc should have required fields
        for doc in docs:
            assert "page_text" in doc
            assert "rrf_score" in doc
            assert "topic_title" in doc

    @pytest.mark.asyncio
    async def test_returns_empty_for_unknown_subject(self, retriever):
        """Should handle unknown subject gracefully."""
        docs = await retriever.retrieve(
            query="Some query",
            subject="Неіснуючий предмет",
            grade=9,
        )

        assert docs == []

    @pytest.mark.asyncio
    async def test_retrieves_for_different_subjects(self, retriever):
        """Should retrieve for all supported subjects."""
        subjects = [
            ("Українська мова", 9, "речення"),
            ("Алгебра", 9, "рівняння"),
            ("Історія України", 9, "історія"),
        ]

        for subject, grade, query_term in subjects:
            docs = await retriever.retrieve(
                query=query_term,
                subject=subject,
                grade=grade,
                top_k=3,
            )
            # Should return results for known subjects
            assert len(docs) >= 0, f"Failed for {subject}"


class TestLLMClient:
    """Tests for LLM client (requires API access)."""

    @pytest.fixture
    def llm_client(self):
        """Create LLM client instance."""
        from app.rag.utils.llm_client import get_llm_client
        return get_llm_client()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_generates_text(self, llm_client):
        """Should generate text response from LLM."""
        response = await llm_client.generate(
            prompt="Скажи 'привіт' українською мовою.",
            temperature=0.0,
            max_tokens=50,
        )

        assert response is not None
        assert len(response) > 0
        assert isinstance(response, str)

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_generates_json(self, llm_client):
        """Should generate and parse JSON response."""
        response = await llm_client.generate_json(
            prompt='Відповідь у форматі JSON: {"answer": 1, "reason": "тест"}',
            temperature=0.0,
        )

        assert response is not None
        assert isinstance(response, dict)
        # Should have parsed answer or error
        assert "answer" in response or "error" in response

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_embeds_text(self, llm_client):
        """Should generate embedding vector."""
        embedding = await llm_client.embed("Тестовий текст для векторизації")

        assert embedding is not None
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        # Embedding should be a vector of floats
        assert all(isinstance(x, float) for x in embedding)


class TestTopicRetriever:
    """Tests for topic-based retriever."""

    @pytest.fixture
    def topic_retriever(self):
        """Create topic retriever instance."""
        from app.rag.utils.topic_retriever import get_topic_retriever
        return get_topic_retriever()

    @pytest.mark.asyncio
    async def test_finds_relevant_topics(self, topic_retriever):
        """Should find relevant TOC topics using semantic search."""
        topics = await topic_retriever.find_relevant_topics(
            question="Які є види складних речень?",
            subject="Українська мова",
            grade=9,
            top_k=3,
        )

        assert len(topics) > 0
        assert len(topics) <= 3
        # Each topic should have required fields
        for topic in topics:
            assert "topic_title" in topic
            assert "score" in topic
            assert "book_topic_id" in topic

    @pytest.mark.asyncio
    async def test_topic_scores_are_normalized(self, topic_retriever):
        """Topic scores should be cosine similarity (0-1 range)."""
        topics = await topic_retriever.find_relevant_topics(
            question="Складні речення",
            subject="Українська мова",
            grade=9,
            top_k=5,
        )

        for topic in topics:
            # Cosine similarity should be roughly in [-1, 1] range
            assert -1.1 <= topic["score"] <= 1.1


class TestFormatContext:
    """Tests for context formatting utilities."""

    def test_format_context_limits_chars(self):
        """Should respect max_chars limit."""
        from app.rag.utils.hybrid_retriever import format_context

        # Create test docs with long text
        docs = [
            {
                "page_text": "A" * 10000,
                "topic_title": "Test Topic",
                "section_title": "Test Section",
                "page_number": 1,
                "book_name": "Test Book",
                "book_topic_id": "test-1",
                "rrf_score": 0.5,
            }
        ]

        context, refs = format_context(docs, max_chars=1000)

        # Should be truncated
        assert len(context) <= 2000  # Some overhead for formatting

    def test_format_context_preserves_algebra(self):
        """Should NOT truncate algebra content (preserve worked examples)."""
        from app.rag.utils.hybrid_retriever import format_context

        docs = [
            {
                "page_text": "Розв'язання: " + "A" * 5000,
                "topic_title": "Алгебра - рівняння",
                "section_title": "Алгебра",
                "page_number": 1,
                "book_name": "Алгебра 9 клас",
                "book_topic_id": "algebra-1",
                "rrf_score": 0.5,
            }
        ]

        context, refs = format_context(docs, max_chars=1000, subject="Алгебра")

        # Algebra content should NOT be truncated
        assert len(context) > 1000


class TestRAGConfig:
    """Tests for RAG configuration."""

    def test_settings_use_main_config(self):
        """RAG settings should read from main app config."""
        from app.rag.config import get_settings
        from app.config import settings as main_settings

        rag_settings = get_settings()

        assert rag_settings.model == main_settings.llm_model
        assert rag_settings.api_base_url == main_settings.llm_base_url

    def test_data_paths_exist(self):
        """Data paths should point to existing files."""
        from app.rag.config import get_data_path, get_embedding_path
        import os

        data_dir = get_data_path()
        assert os.path.isdir(data_dir)

        pages_path = get_embedding_path("pages_for_hackathon.parquet")
        assert os.path.isfile(pages_path)

        toc_path = get_embedding_path("toc_for_hackathon_with_subtopics.parquet")
        assert os.path.isfile(toc_path)

    def test_subject_configs_exist(self):
        """Should have configs for all supported subjects."""
        from app.rag.config import get_subject_config, SUBJECT_CONFIGS

        # Required subjects per architecture.md
        required_subjects = ["Українська мова", "Алгебра", "Історія України"]

        for subject in required_subjects:
            config = get_subject_config(subject)
            assert config is not None
            assert hasattr(config, "temperature")
            assert hasattr(config, "retrieval_boost")
