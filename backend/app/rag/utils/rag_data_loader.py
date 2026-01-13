"""
Data loader for Agentic RAG - loads textbook pages, TOC, and questions.
"""

import pandas as pd
from pathlib import Path
from typing import Optional

from ..config import get_settings, get_data_path, get_embedding_path


class DataLoader:
    """
    Load and cache data from parquet files.

    Provides access to:
    - Benchmark questions (lms_questions_dev.parquet)
    - Textbook pages with embeddings (pages_for_hackathon.parquet)
    - Table of Contents with topics (toc_for_hackathon_with_subtopics.parquet)
    """

    def __init__(self, theory_only: bool = True):
        """
        Initialize data loader.

        Args:
            theory_only: If True, filter textbook pages to only include
                        pages with contains_theory=True in page_metadata.
                        This reduces noise from exercises and TOC pages.
        """
        self._benchmark_questions: Optional[pd.DataFrame] = None
        self._textbook_pages: Optional[pd.DataFrame] = None
        self._textbook_pages_all: Optional[pd.DataFrame] = None  # Unfiltered
        self._toc: Optional[pd.DataFrame] = None
        self._theory_only = theory_only

    def load_benchmark_questions(self) -> pd.DataFrame:
        """Load benchmark questions from lms_questions_dev.parquet."""
        if self._benchmark_questions is None:
            path = get_data_path("lms_questions_dev.parquet")
            self._benchmark_questions = pd.read_parquet(path)
            print(f"[DataLoader] Loaded {len(self._benchmark_questions)} benchmark questions")
        return self._benchmark_questions

    def load_textbook_pages(self) -> pd.DataFrame:
        """
        Load textbook pages with embeddings.

        If theory_only=True, filters to pages where contains_theory=True.
        This significantly improves RAG quality by removing exercise pages.
        """
        if self._textbook_pages is None:
            path = get_embedding_path("pages_for_hackathon.parquet")
            all_pages = pd.read_parquet(path)
            self._textbook_pages_all = all_pages

            if self._theory_only:
                # Filter to theory pages only
                def has_theory(metadata):
                    if isinstance(metadata, dict):
                        return metadata.get("contains_theory", False)
                    return False

                theory_pages = all_pages[
                    all_pages["page_metadata"].apply(has_theory)
                ]
                self._textbook_pages = theory_pages
                print(f"[DataLoader] Loaded {len(theory_pages)}/{len(all_pages)} theory pages (filtered)")
            else:
                self._textbook_pages = all_pages
                print(f"[DataLoader] Loaded {len(all_pages)} textbook pages (all)")

        return self._textbook_pages

    def load_toc(self) -> pd.DataFrame:
        """Load Table of Contents with topics and embeddings."""
        if self._toc is None:
            path = get_embedding_path("toc_for_hackathon_with_subtopics.parquet")
            self._toc = pd.read_parquet(path)
            print(f"[DataLoader] Loaded {len(self._toc)} TOC topics")
        return self._toc

    def get_pages_for_subject_grade(
        self,
        subject: str,
        grade: int
    ) -> pd.DataFrame:
        """Get textbook pages filtered by subject and grade."""
        pages = self.load_textbook_pages()
        return pages[
            (pages["global_discipline_name"] == subject) &
            (pages["grade"] == grade)
        ]

    def get_topics_for_subject_grade(
        self,
        subject: str,
        grade: int
    ) -> pd.DataFrame:
        """Get TOC topics filtered by subject and grade."""
        toc = self.load_toc()
        return toc[
            (toc["global_discipline_name"] == subject) &
            (toc["grade"] == grade)
        ]

    def get_question_by_id(self, question_id: str) -> Optional[dict]:
        """Get a single question by ID."""
        questions = self.load_benchmark_questions()
        matches = questions[questions["question_id"] == question_id]
        if len(matches) > 0:
            return matches.iloc[0].to_dict()
        return None

    def get_question_by_index(self, idx: int) -> Optional[dict]:
        """Get a single question by index."""
        questions = self.load_benchmark_questions()
        if 0 <= idx < len(questions):
            return questions.iloc[idx].to_dict()
        return None


# Global instance
_data_loader: Optional[DataLoader] = None


def get_data_loader(theory_only: bool = True) -> DataLoader:
    """
    Get singleton data loader instance.

    Args:
        theory_only: Filter to theory pages only (default True for better RAG)
    """
    global _data_loader
    if _data_loader is None:
        _data_loader = DataLoader(theory_only=theory_only)
    return _data_loader


def reset_data_loader():
    """Reset data loader (for testing with different settings)."""
    global _data_loader
    _data_loader = None
