"""
Tests for Student API Stubs (T6)

Expected Behavior:
-----------------
Student endpoints serve the student-facing test flow:
1. Get test exercises (without answers)
2. Submit answers
3. View results
4. View personalized summary

All endpoints return MOCK data for now - will be connected to real services later.

Endpoints:
- GET  /api/v1/student/{student_id}/test?test_id=X     -> Get test exercises
- POST /api/v1/student/submit                          -> Submit answers
- GET  /api/v1/student/{student_id}/result/{test_id}   -> Get results
- GET  /api/v1/student/{student_id}/summary/{test_id}  -> Get personalized summary
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


# =============================================================================
# T6.1: GET /student/{student_id}/test - Get test exercises
# =============================================================================


class TestGetStudentTest:
    """Tests for GET /api/v1/student/{student_id}/test endpoint."""

    def test_returns_test_exercises(self, client):
        """Should return test exercises for student."""
        response = client.get("/api/v1/student/101/test", params={"test_id": "test_001"})

        assert response.status_code == 200
        data = response.json()
        assert "test_id" in data
        assert "exercises" in data
        assert isinstance(data["exercises"], list)

    def test_exercises_have_required_fields(self, client):
        """Each exercise should have question, type, options (if MC)."""
        response = client.get("/api/v1/student/101/test", params={"test_id": "test_001"})

        data = response.json()
        for exercise in data["exercises"]:
            assert "id" in exercise
            assert "question" in exercise
            assert "type" in exercise
            assert "difficulty" in exercise

    def test_exercises_do_not_contain_answers(self, client):
        """Exercises should NOT contain correct_answer field."""
        response = client.get("/api/v1/student/101/test", params={"test_id": "test_001"})

        data = response.json()
        for exercise in data["exercises"]:
            assert "correct_answer" not in exercise
            # Options should be plain strings (no "correct" markers)
            if "options" in exercise and exercise["options"]:
                # Options are list of strings, not dicts with "correct" field
                for opt in exercise["options"]:
                    assert isinstance(opt, str)

    def test_returns_time_limit(self, client):
        """Response should include time limit in minutes."""
        response = client.get("/api/v1/student/101/test", params={"test_id": "test_001"})

        data = response.json()
        assert "time_limit_minutes" in data
        assert isinstance(data["time_limit_minutes"], (int, type(None)))

    def test_returns_8_to_12_exercises(self, client):
        """Mock should return 8-12 exercises."""
        response = client.get("/api/v1/student/101/test", params={"test_id": "test_001"})

        data = response.json()
        assert 8 <= len(data["exercises"]) <= 12

    def test_requires_test_id(self, client):
        """Should return 422 if test_id not provided."""
        response = client.get("/api/v1/student/101/test")

        assert response.status_code == 422

    def test_invalid_student_id_format(self, client):
        """Should handle invalid student ID gracefully."""
        response = client.get("/api/v1/student/invalid/test", params={"test_id": "test_001"})

        # Either 422 (validation) or 404 (not found) is acceptable
        assert response.status_code in [404, 422]


# =============================================================================
# T6.2: POST /student/submit - Submit answers
# =============================================================================


class TestSubmitAnswers:
    """Tests for POST /api/v1/student/submit endpoint."""

    def test_submit_answers_success(self, client):
        """Should accept valid answer submission."""
        payload = {
            "student_id": 101,
            "test_id": "test_001",
            "answers": [
                {"exercise_id": "ex_001", "answer": "B", "time_spent_seconds": 45},
                {"exercise_id": "ex_002", "answer": "x = 5", "time_spent_seconds": 120},
            ]
        }

        response = client.post("/api/v1/student/submit", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "submission_id" in data
        assert data["status"] == "received"

    def test_returns_submission_id(self, client):
        """Should return a unique submission ID."""
        payload = {
            "student_id": 101,
            "test_id": "test_001",
            "answers": []
        }

        response = client.post("/api/v1/student/submit", json=payload)

        data = response.json()
        assert data["submission_id"] is not None
        assert len(data["submission_id"]) > 0

    def test_accepts_empty_answers(self, client):
        """Should accept submission with empty answers (student gave up)."""
        payload = {
            "student_id": 101,
            "test_id": "test_001",
            "answers": []
        }

        response = client.post("/api/v1/student/submit", json=payload)

        assert response.status_code == 200

    def test_requires_student_id(self, client):
        """Should require student_id field."""
        payload = {
            "test_id": "test_001",
            "answers": []
        }

        response = client.post("/api/v1/student/submit", json=payload)

        assert response.status_code == 422

    def test_requires_test_id(self, client):
        """Should require test_id field."""
        payload = {
            "student_id": 101,
            "answers": []
        }

        response = client.post("/api/v1/student/submit", json=payload)

        assert response.status_code == 422

    def test_answer_structure_validated(self, client):
        """Each answer should have exercise_id and answer."""
        payload = {
            "student_id": 101,
            "test_id": "test_001",
            "answers": [
                {"exercise_id": "ex_001"}  # missing 'answer'
            ]
        }

        response = client.post("/api/v1/student/submit", json=payload)

        assert response.status_code == 422


# =============================================================================
# T6.3: GET /student/{student_id}/result/{test_id} - Get results
# =============================================================================


class TestGetResult:
    """Tests for GET /api/v1/student/{student_id}/result/{test_id} endpoint."""

    def test_returns_result(self, client):
        """Should return test result."""
        response = client.get("/api/v1/student/101/result/test_001")

        assert response.status_code == 200
        data = response.json()
        assert "score" in data
        assert "percentage" in data

    def test_result_has_score_fields(self, client):
        """Result should have all score-related fields."""
        response = client.get("/api/v1/student/101/result/test_001")

        data = response.json()
        assert "correct_count" in data
        assert "total_count" in data
        assert 0 <= data["percentage"] <= 100

    def test_result_has_subtopic_analysis(self, client):
        """Result should have correct/failed subtopics."""
        response = client.get("/api/v1/student/101/result/test_001")

        data = response.json()
        assert "correct_subtopics" in data
        assert "failed_subtopics" in data
        assert isinstance(data["correct_subtopics"], list)
        assert isinstance(data["failed_subtopics"], list)

    def test_result_has_error_patterns(self, client):
        """Result should have error pattern analysis."""
        response = client.get("/api/v1/student/101/result/test_001")

        data = response.json()
        assert "error_patterns" in data
        assert isinstance(data["error_patterns"], list)

    def test_result_has_class_percentile(self, client):
        """Result should include class percentile."""
        response = client.get("/api/v1/student/101/result/test_001")

        data = response.json()
        assert "class_percentile" in data
        assert 0 <= data["class_percentile"] <= 100

    def test_mock_returns_realistic_result(self, client):
        """Mock result should be realistic (e.g., 60-80%)."""
        response = client.get("/api/v1/student/101/result/test_001")

        data = response.json()
        # Mock should return something plausible
        assert data["correct_count"] <= data["total_count"]


# =============================================================================
# T6.4: GET /student/{student_id}/summary/{test_id} - Get personalized summary
# =============================================================================


class TestGetSummary:
    """Tests for GET /api/v1/student/{student_id}/summary/{test_id} endpoint."""

    def test_returns_summary(self, client):
        """Should return personalized summary."""
        response = client.get("/api/v1/student/101/summary/test_001")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_summary_has_result_section(self, client):
        """Summary should have result overview section."""
        response = client.get("/api/v1/student/101/summary/test_001")

        data = response.json()
        assert "result_section" in data

    def test_summary_has_prerequisites_review(self, client):
        """Summary should have prerequisites review (if applicable)."""
        response = client.get("/api/v1/student/101/summary/test_001")

        data = response.json()
        assert "prerequisites_review" in data

    def test_summary_has_mistakes_analysis(self, client):
        """Summary should have detailed mistakes analysis."""
        response = client.get("/api/v1/student/101/summary/test_001")

        data = response.json()
        assert "mistakes_analysis" in data

    def test_summary_has_practice_exercises(self, client):
        """Summary should include practice exercises."""
        response = client.get("/api/v1/student/101/summary/test_001")

        data = response.json()
        assert "practice_exercises" in data
        assert isinstance(data["practice_exercises"], list)

    def test_summary_has_recommendations(self, client):
        """Summary should have next-step recommendations."""
        response = client.get("/api/v1/student/101/summary/test_001")

        data = response.json()
        assert "recommendations" in data

    def test_summary_content_is_structured(self, client):
        """Summary content should be structured (not just raw text)."""
        response = client.get("/api/v1/student/101/summary/test_001")

        data = response.json()
        # At least one section should have meaningful content
        has_content = any([
            data.get("result_section"),
            data.get("mistakes_analysis"),
            data.get("recommendations")
        ])
        assert has_content


# =============================================================================
# T6.5: Error handling
# =============================================================================


class TestStudentAPIErrors:
    """Error handling tests for student endpoints."""

    def test_nonexistent_student_test(self, client):
        """Should handle nonexistent test gracefully."""
        response = client.get("/api/v1/student/101/test", params={"test_id": "nonexistent"})

        # Stub might return mock data or 404
        assert response.status_code in [200, 404]

    def test_nonexistent_result(self, client):
        """Should handle nonexistent result gracefully."""
        response = client.get("/api/v1/student/999/result/nonexistent")

        # Stub might return mock data or 404
        assert response.status_code in [200, 404]

    def test_invalid_json_submit(self, client):
        """Should reject invalid JSON in submit."""
        response = client.post(
            "/api/v1/student/submit",
            content="not json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422
