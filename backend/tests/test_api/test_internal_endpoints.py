"""
Internal API endpoint tests - Full Pipeline integration.

Tests the testing-only endpoint that exercises the full pipeline.
"""

import pytest
from unittest.mock import patch, AsyncMock


class TestFullPipeline:
    """Tests for POST /internal/full-pipeline."""

    def test_returns_200_for_valid_request(self, client, sample_class_id, sample_teacher_id):
        """POST /internal/full-pipeline should return 200."""
        with patch('app.api.v1.internal.generate_notes') as mock_notes, \
             patch('app.api.v1.internal.generate_test') as mock_test, \
             patch('app.api.v1.internal.solve_question') as mock_solver:

            mock_notes.return_value = {
                "title": "Test notes",
                "contents": "Test content",
                "teacher_notes": "Test teacher notes"
            }
            mock_test.return_value = {
                "title": "Test quiz",
                "questions": []
            }
            mock_solver.return_value = {"question": "Q", "answer_explained": "A"}

            response = client.post(
                "/api/v1/internal/full-pipeline",
                json={
                    "class_id": sample_class_id,
                    "teacher_id": sample_teacher_id,
                    "subject": "Алгебра",
                    "topic_definition": "Квадратні рівняння"
                }
            )

            assert response.status_code == 200

    def test_response_matches_contract(self, client, sample_class_id, sample_teacher_id):
        """Response: {notes, test, answer_key}."""
        with patch('app.api.v1.internal.generate_notes') as mock_notes, \
             patch('app.api.v1.internal.generate_test') as mock_test, \
             patch('app.api.v1.internal.solve_question') as mock_solver:

            mock_notes.return_value = {
                "title": "Урок: Квадратні рівняння",
                "contents": "# Зміст уроку\n\nМатеріал...",
                "teacher_notes": "Зверніть увагу на слабкі теми"
            }
            mock_test.return_value = {
                "title": "Тест: Квадратні рівняння",
                "questions": [
                    {
                        "question": "2 + 2 = ?",
                        "type": "multiple_choice",
                        "difficulty": "easy",
                        "answer_options": [
                            {"answer": "3", "correct": False},
                            {"answer": "4", "correct": True},
                            {"answer": "5", "correct": False},
                            {"answer": "6", "correct": False}
                        ],
                        "explanation": "Просте додавання",
                        "topic": "Арифметика",
                        "subtopics": []
                    }
                ]
            }
            mock_solver.return_value = {"question": "2 + 2 = ?", "answer_explained": "2 + 2 = 4"}

            response = client.post(
                "/api/v1/internal/full-pipeline",
                json={
                    "class_id": sample_class_id,
                    "teacher_id": sample_teacher_id,
                    "subject": "Алгебра",
                    "topic_definition": "Квадратні рівняння"
                }
            )

            assert response.status_code == 200
            data = response.json()

            # Check structure
            assert "notes" in data
            assert "test" in data
            assert "answer_key" in data

            # Check notes
            assert "title" in data["notes"]
            assert "contents" in data["notes"]
            assert "teacher_notes" in data["notes"]

            # Check test
            assert "title" in data["test"]
            assert "questions" in data["test"]

            # Check answer_key
            assert "solutions" in data["answer_key"]
            assert isinstance(data["answer_key"]["solutions"], list)

    def test_validates_request(self, client):
        """Should return 422 for missing required fields."""
        response = client.post(
            "/api/v1/internal/full-pipeline",
            json={
                "class_id": 1,
                # Missing teacher_id, subject, topic_definition
            }
        )

        assert response.status_code == 422

    def test_returns_404_for_unknown_class(self, client, sample_teacher_id):
        """Should return 404 for unknown class_id."""
        response = client.post(
            "/api/v1/internal/full-pipeline",
            json={
                "class_id": 999999999,
                "teacher_id": sample_teacher_id,
                "subject": "Алгебра",
                "topic_definition": "Квадратні рівняння"
            }
        )

        assert response.status_code == 404

    def test_solves_each_generated_question(self, client, sample_class_id, sample_teacher_id):
        """Should call solver for each generated question."""
        with patch('app.api.v1.internal.generate_notes') as mock_notes, \
             patch('app.api.v1.internal.generate_test') as mock_test, \
             patch('app.api.v1.internal.solve_question') as mock_solver:

            mock_notes.return_value = {
                "title": "Notes",
                "contents": "Content",
                "teacher_notes": "Teacher notes"
            }
            # 3 test questions
            mock_test.return_value = {
                "title": "Test",
                "questions": [
                    {
                        "question": f"Q{i}",
                        "type": "open",
                        "difficulty": "easy",
                        "answer_options": [],
                        "explanation": "Exp",
                        "topic": "Topic",
                        "subtopics": []
                    }
                    for i in range(3)
                ]
            }
            mock_solver.side_effect = [
                {"question": "Q0", "answer_explained": "A0"},
                {"question": "Q1", "answer_explained": "A1"},
                {"question": "Q2", "answer_explained": "A2"},
            ]

            response = client.post(
                "/api/v1/internal/full-pipeline",
                json={
                    "class_id": sample_class_id,
                    "teacher_id": sample_teacher_id,
                    "subject": "Алгебра",
                    "topic_definition": "Тест"
                }
            )

            assert response.status_code == 200
            data = response.json()

            # Solver should be called 3 times (once per question)
            assert mock_solver.call_count == 3

            # Answer key should have 3 solutions
            assert len(data["answer_key"]["solutions"]) == 3

    @pytest.mark.slow
    def test_llm_integration(self, client, sample_class_id, sample_teacher_id):
        """Integration test with real LLM (marked slow)."""
        response = client.post(
            "/api/v1/internal/full-pipeline",
            json={
                "class_id": sample_class_id,
                "teacher_id": sample_teacher_id,
                "subject": "Алгебра",
                "topic_definition": "Квадратні рівняння"
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Should have notes
        assert len(data["notes"]["contents"]) > 100

        # Should have questions
        assert len(data["test"]["questions"]) > 0

        # Should have solutions matching questions
        assert len(data["answer_key"]["solutions"]) == len(data["test"]["questions"])
