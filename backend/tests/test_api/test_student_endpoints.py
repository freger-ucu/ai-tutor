"""
Student API endpoint tests - TDD approach.

Tests are written FIRST, then implementation is verified.
"""

import pytest
from unittest.mock import patch


class TestEP8GetStudent:
    """Tests for EP8: GET /student/{id}."""

    def test_returns_200_for_valid_student(self, client, sample_student_id):
        """GET /student/{id} should return 200."""
        response = client.get(f"/api/v1/student/{sample_student_id}")

        assert response.status_code == 200
        data = response.json()
        assert "class_id" in data
        assert "class_number" in data
        assert "subjects" in data

    def test_returns_404_for_unknown_student(self, client):
        """GET /student/999999 should return 404."""
        response = client.get("/api/v1/student/999999999")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_response_matches_contract(self, client, sample_student_id):
        """Response: {class_id, class_number, subjects: [...]}."""
        response = client.get(f"/api/v1/student/{sample_student_id}")

        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert "class_id" in data
        assert "class_number" in data
        assert "subjects" in data

        # Validate types
        assert isinstance(data["class_id"], int)
        assert isinstance(data["class_number"], int)
        assert isinstance(data["subjects"], list)
        assert all(isinstance(s, str) for s in data["subjects"])

        # Validate values
        assert data["class_number"] in [8, 9]  # Only grades 8 and 9
        assert len(data["subjects"]) > 0  # Student should have at least one subject


class TestEP10TestFeedback:
    """Tests for EP10: POST /student/test-feedback."""

    def test_returns_200_for_valid_request(self, client, sample_student_id):
        """POST /student/test-feedback should return 200."""
        with patch('app.api.v1.student.generate_test_feedback') as mock_gen:
            mock_gen.return_value = "Гарний результат! Продовжуй в тому ж дусі."

            response = client.post(
                "/api/v1/student/test-feedback",
                json={
                    "student_id": sample_student_id,
                    "teacher_id": 1,
                    "subject": "Алгебра",
                    "questions": [
                        {
                            "question": "2 + 2 = ?",
                            "answer": "4",
                            "correct": True,
                            "topic": "Арифметика",
                            "subtopics": []
                        },
                        {
                            "question": "3 * 3 = ?",
                            "answer": "6",
                            "correct": False,
                            "topic": "Арифметика",
                            "subtopics": []
                        }
                    ]
                }
            )

            assert response.status_code == 200

    def test_response_matches_contract(self, client, sample_student_id):
        """Response: {feedback: str}."""
        with patch('app.api.v1.student.generate_test_feedback') as mock_gen:
            mock_gen.return_value = "Результат тесту: 5/10. Рекомендую звернути увагу на теми..."

            response = client.post(
                "/api/v1/student/test-feedback",
                json={
                    "student_id": sample_student_id,
                    "teacher_id": 1,
                    "subject": "Алгебра",
                    "questions": [
                        {
                            "question": "Test question",
                            "answer": "Test answer",
                            "correct": True,
                            "topic": "Test topic",
                            "subtopics": []
                        }
                    ]
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert "feedback" in data
            assert isinstance(data["feedback"], str)
            assert len(data["feedback"]) > 0

    def test_validates_request_body(self, client):
        """Should return 422 for missing required fields."""
        response = client.post(
            "/api/v1/student/test-feedback",
            json={
                "student_id": 1,
                "subject": "Алгебра"
                # Missing teacher_id and questions
            }
        )

        assert response.status_code == 422

    def test_empty_questions_list(self, client, sample_student_id):
        """Should handle empty questions list."""
        with patch('app.api.v1.student.generate_test_feedback') as mock_gen:
            mock_gen.return_value = "Тест не містить питань."

            response = client.post(
                "/api/v1/student/test-feedback",
                json={
                    "student_id": sample_student_id,
                    "teacher_id": 1,
                    "subject": "Алгебра",
                    "questions": []
                }
            )

            # Should still return 200 with appropriate feedback
            assert response.status_code == 200

    def test_groups_incorrect_by_topic(self, client, sample_student_id):
        """Should properly process questions with different topics."""
        with patch('app.api.v1.student.generate_test_feedback') as mock_gen:
            mock_gen.return_value = "Зверни увагу на теми: Арифметика, Геометрія."

            response = client.post(
                "/api/v1/student/test-feedback",
                json={
                    "student_id": sample_student_id,
                    "teacher_id": 1,
                    "subject": "Алгебра",
                    "questions": [
                        {"question": "Q1", "answer": "A1", "correct": True, "topic": "Арифметика", "subtopics": []},
                        {"question": "Q2", "answer": "A2", "correct": False, "topic": "Арифметика", "subtopics": []},
                        {"question": "Q3", "answer": "A3", "correct": False, "topic": "Геометрія", "subtopics": []},
                        {"question": "Q4", "answer": "A4", "correct": True, "topic": "Геометрія", "subtopics": []},
                    ]
                }
            )

            assert response.status_code == 200

    def test_groups_by_topic_and_subtopics(self, client, sample_student_id):
        """Should group answers by topic/subtopics per architecture.md."""
        with patch('app.api.v1.student.generate_test_feedback') as mock_gen:
            mock_gen.return_value = "Зверни увагу на підтеми."

            response = client.post(
                "/api/v1/student/test-feedback",
                json={
                    "student_id": sample_student_id,
                    "teacher_id": 1,
                    "subject": "Алгебра",
                    "questions": [
                        {
                            "question": "Q1",
                            "answer": "A1",
                            "correct": True,
                            "topic": "Квадратні рівняння",
                            "subtopics": ["дискримінант", "формула коренів"]
                        },
                        {
                            "question": "Q2",
                            "answer": "A2",
                            "correct": False,
                            "topic": "Квадратні рівняння",
                            "subtopics": ["теорема Вієта"]
                        },
                        {
                            "question": "Q3",
                            "answer": "A3",
                            "correct": False,
                            "topic": "Квадратні рівняння",
                            "subtopics": []  # No subtopics
                        },
                    ]
                }
            )

            assert response.status_code == 200
            # Verify mock was called with correct grouping
            mock_gen.assert_called_once()
            call_kwargs = mock_gen.call_args[1]
            # Should have separate keys for different subtopic combinations
            assert "Квадратні рівняння > дискримінант, формула коренів" in str(call_kwargs)
            assert "Квадратні рівняння > теорема Вієта" in str(call_kwargs)
            assert "Квадратні рівняння" in str(call_kwargs)  # Plain topic without subtopics

    @pytest.mark.slow
    def test_llm_integration(self, client, sample_student_id):
        """Integration test with real LLM (marked slow)."""
        response = client.post(
            "/api/v1/student/test-feedback",
            json={
                "student_id": sample_student_id,
                "teacher_id": 1,
                "subject": "Алгебра",
                "questions": [
                    {"question": "2 + 2 = ?", "answer": "4", "correct": True, "topic": "Арифметика", "subtopics": []},
                    {"question": "3 * 3 = ?", "answer": "6", "correct": False, "topic": "Множення", "subtopics": []},
                ]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "feedback" in data
        assert len(data["feedback"]) > 50  # Should be substantial feedback


class TestEP9CheckOpenQuestion:
    """Tests for EP9: POST /student/check-open."""

    def test_returns_200_for_valid_request(self, client, sample_student_id):
        """POST /student/check-open should return 200."""
        with patch('app.api.v1.student.check_open_question') as mock_check:
            mock_check.return_value = {"correct": True, "feedback": "Правильно!"}

            response = client.post(
                "/api/v1/student/check-open",
                json={
                    "student_id": sample_student_id,
                    "subject": "Алгебра",
                    "topic": "Квадратні рівняння",
                    "subtopics": ["дискримінант"],
                    "question": "Коли квадратне рівняння не має дійсних коренів?",
                    "answer": "Коли дискримінант менше нуля"
                }
            )

            assert response.status_code == 200

    def test_response_matches_contract(self, client, sample_student_id):
        """Response: {correct: bool, feedback: str}."""
        with patch('app.api.v1.student.check_open_question') as mock_check:
            mock_check.return_value = {
                "correct": True,
                "feedback": "Правильно! Коли D < 0, рівняння не має дійсних коренів."
            }

            response = client.post(
                "/api/v1/student/check-open",
                json={
                    "student_id": sample_student_id,
                    "subject": "Алгебра",
                    "topic": "Квадратні рівняння",
                    "subtopics": [],
                    "question": "Test question",
                    "answer": "Test answer"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert "correct" in data
            assert "feedback" in data
            assert isinstance(data["correct"], bool)
            assert isinstance(data["feedback"], str)

    def test_validates_request_body(self, client):
        """Should return 422 for missing required fields."""
        response = client.post(
            "/api/v1/student/check-open",
            json={
                "student_id": 1,
                "subject": "Алгебра"
                # Missing topic, question, answer
            }
        )

        assert response.status_code == 422

    def test_handles_empty_answer(self, client, sample_student_id):
        """Should handle empty answer gracefully."""
        with patch('app.api.v1.student.check_open_question') as mock_check:
            mock_check.return_value = {
                "correct": False,
                "feedback": "Ти не дав відповіді. Спробуй подумати над питанням."
            }

            response = client.post(
                "/api/v1/student/check-open",
                json={
                    "student_id": sample_student_id,
                    "subject": "Алгебра",
                    "topic": "Квадратні рівняння",
                    "subtopics": [],
                    "question": "Test question",
                    "answer": ""  # Empty answer
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["correct"] is False

    def test_handles_empty_subtopics(self, client, sample_student_id):
        """Should work with empty subtopics list."""
        with patch('app.api.v1.student.check_open_question') as mock_check:
            mock_check.return_value = {"correct": True, "feedback": "Молодець!"}

            response = client.post(
                "/api/v1/student/check-open",
                json={
                    "student_id": sample_student_id,
                    "subject": "Історія України",
                    "topic": "Запорозька Січ",
                    "subtopics": [],  # Empty
                    "question": "Хто був першим гетьманом?",
                    "answer": "Дмитро Вишневецький"
                }
            )

            assert response.status_code == 200

    @pytest.mark.slow
    def test_llm_integration_correct_answer(self, client, sample_student_id):
        """Integration test with correct answer (marked slow)."""
        response = client.post(
            "/api/v1/student/check-open",
            json={
                "student_id": sample_student_id,
                "subject": "Алгебра",
                "topic": "Квадратні рівняння",
                "subtopics": ["дискримінант"],
                "question": "Коли квадратне рівняння не має дійсних коренів?",
                "answer": "Коли дискримінант менше нуля, тобто D < 0"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "correct" in data
        assert "feedback" in data
        # This should be marked as correct
        assert data["correct"] is True

    @pytest.mark.slow
    def test_llm_integration_incorrect_answer(self, client, sample_student_id):
        """Integration test with incorrect answer (marked slow)."""
        response = client.post(
            "/api/v1/student/check-open",
            json={
                "student_id": sample_student_id,
                "subject": "Алгебра",
                "topic": "Квадратні рівняння",
                "subtopics": ["дискримінант"],
                "question": "Коли квадратне рівняння не має дійсних коренів?",
                "answer": "Коли дискримінант більше нуля"  # Wrong!
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "correct" in data
        assert "feedback" in data
        # This should be marked as incorrect
        assert data["correct"] is False
        assert len(data["feedback"]) > 20  # Should have explanation
