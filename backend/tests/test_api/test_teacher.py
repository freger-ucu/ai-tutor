"""
Tests for Teacher API Stubs (T7)

Expected Behavior:
-----------------
Teacher endpoints serve the lesson preparation flow:
1. Analyze class (get insights, clusters)
2. Generate lesson content
3. Generate test pool
4. Create personalized tests per cluster
5. View post-test report
6. Full pipeline (all-in-one)

All endpoints return MOCK data for now - will be connected to real services later.

Endpoints:
- POST /api/v1/teacher/analyze-class           -> Class analysis & clustering
- POST /api/v1/teacher/generate-lesson         -> Generate teacher lesson (Конспект #1)
- POST /api/v1/teacher/generate-test-pool      -> Generate exercise pool
- POST /api/v1/teacher/create-personalized-tests -> Split tests by cluster
- POST /api/v1/teacher/generate-report         -> Post-test class report
- POST /api/v1/teacher/full-pipeline           -> All steps combined
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
# T7.1: POST /teacher/analyze-class - Class analysis
# =============================================================================


class TestAnalyzeClass:
    """Tests for POST /api/v1/teacher/analyze-class endpoint."""

    def test_returns_class_analysis(self, client):
        """Should return class analysis with all sections."""
        payload = {
            "class_id": 1,
            "subject": "Алгебра",
            "topic": "Квадратні рівняння"
        }

        response = client.post("/api/v1/teacher/analyze-class", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "topic_routing" in data
        assert "class_insights" in data
        assert "cluster_assignments" in data

    def test_topic_routing_result(self, client):
        """Topic routing should map query to topic_id."""
        payload = {
            "class_id": 1,
            "subject": "Алгебра",
            "topic": "Квадратні рівняння"
        }

        response = client.post("/api/v1/teacher/analyze-class", json=payload)

        data = response.json()
        topic = data["topic_routing"]
        assert "topic_id" in topic
        assert "topic_name" in topic
        assert "prerequisites" in topic

    def test_class_insights_structure(self, client):
        """Class insights should have cluster distribution, absences, weak topics."""
        payload = {
            "class_id": 1,
            "subject": "Алгебра",
            "topic": "Квадратні рівняння"
        }

        response = client.post("/api/v1/teacher/analyze-class", json=payload)

        data = response.json()
        insights = data["class_insights"]
        assert "cluster_distribution" in insights
        assert "missed_prerequisites" in insights
        assert "weak_topics" in insights

    def test_cluster_assignments_list(self, client):
        """Cluster assignments should be a list of student->cluster mappings."""
        payload = {
            "class_id": 1,
            "subject": "Алгебра",
            "topic": "Квадратні рівняння"
        }

        response = client.post("/api/v1/teacher/analyze-class", json=payload)

        data = response.json()
        assignments = data["cluster_assignments"]
        assert isinstance(assignments, list)
        if len(assignments) > 0:
            assert "student_id" in assignments[0]
            assert "cluster_type" in assignments[0] or "cluster_id" in assignments[0]

    def test_requires_all_fields(self, client):
        """Should require class_id, subject, and topic."""
        # Missing topic
        payload = {"class_id": 1, "subject": "Алгебра"}
        response = client.post("/api/v1/teacher/analyze-class", json=payload)
        assert response.status_code == 422


# =============================================================================
# T7.2: POST /teacher/generate-lesson - Generate lesson
# =============================================================================


class TestGenerateLesson:
    """Tests for POST /api/v1/teacher/generate-lesson endpoint."""

    def test_returns_lesson_content(self, client):
        """Should return structured lesson content."""
        payload = {
            "class_id": 1,
            "subject": "Алгебра",
            "topic_id": "topic_001",
            "grade": 8
        }

        response = client.post("/api/v1/teacher/generate-lesson", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "lesson_content" in data

    def test_lesson_has_insights_summary(self, client):
        """Lesson should include insights summary for teacher."""
        payload = {
            "class_id": 1,
            "subject": "Алгебра",
            "topic_id": "topic_001",
            "grade": 8
        }

        response = client.post("/api/v1/teacher/generate-lesson", json=payload)

        data = response.json()
        assert "insights_summary" in data

    def test_lesson_has_control_questions(self, client):
        """Lesson should include control questions."""
        payload = {
            "class_id": 1,
            "subject": "Алгебра",
            "topic_id": "topic_001",
            "grade": 8
        }

        response = client.post("/api/v1/teacher/generate-lesson", json=payload)

        data = response.json()
        assert "control_questions" in data
        assert isinstance(data["control_questions"], list)

    def test_lesson_has_sources(self, client):
        """Lesson should reference textbook sources."""
        payload = {
            "class_id": 1,
            "subject": "Алгебра",
            "topic_id": "topic_001",
            "grade": 8
        }

        response = client.post("/api/v1/teacher/generate-lesson", json=payload)

        data = response.json()
        assert "sources" in data

    def test_accepts_class_insights(self, client):
        """Should optionally accept pre-computed class insights."""
        payload = {
            "class_id": 1,
            "subject": "Алгебра",
            "topic_id": "topic_001",
            "grade": 8,
            "class_insights": {
                "cluster_distribution": {"weak": 3, "medium": 5, "strong": 2},
                "weak_topics": ["Системи рівнянь"]
            }
        }

        response = client.post("/api/v1/teacher/generate-lesson", json=payload)

        assert response.status_code == 200


# =============================================================================
# T7.3: POST /teacher/generate-test-pool - Generate exercises
# =============================================================================


class TestGenerateTestPool:
    """Tests for POST /api/v1/teacher/generate-test-pool endpoint."""

    def test_returns_exercise_pool(self, client):
        """Should return pool of exercises."""
        payload = {
            "topic_id": "topic_001",
            "subject": "Алгебра",
            "grade": 8
        }

        response = client.post("/api/v1/teacher/generate-test-pool", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "pool" in data
        assert isinstance(data["pool"], list)

    def test_pool_has_15_to_20_exercises(self, client):
        """Pool should contain 15-20 exercises by default."""
        payload = {
            "topic_id": "topic_001",
            "subject": "Алгебра",
            "grade": 8
        }

        response = client.post("/api/v1/teacher/generate-test-pool", json=payload)

        data = response.json()
        assert 15 <= len(data["pool"]) <= 20

    def test_exercises_have_metadata(self, client):
        """Each exercise should have difficulty, type, subtopic."""
        payload = {
            "topic_id": "topic_001",
            "subject": "Алгебра",
            "grade": 8
        }

        response = client.post("/api/v1/teacher/generate-test-pool", json=payload)

        data = response.json()
        for ex in data["pool"]:
            assert "id" in ex
            assert "question" in ex
            assert "difficulty" in ex
            assert "type" in ex

    def test_exercises_have_correct_answer(self, client):
        """Pool exercises should include correct_answer (teacher view)."""
        payload = {
            "topic_id": "topic_001",
            "subject": "Алгебра",
            "grade": 8
        }

        response = client.post("/api/v1/teacher/generate-test-pool", json=payload)

        data = response.json()
        for ex in data["pool"]:
            assert "correct_answer" in ex

    def test_returns_validation_report(self, client):
        """Should include validation report for exercises."""
        payload = {
            "topic_id": "topic_001",
            "subject": "Алгебра",
            "grade": 8
        }

        response = client.post("/api/v1/teacher/generate-test-pool", json=payload)

        data = response.json()
        assert "validation_report" in data

    def test_custom_pool_size(self, client):
        """Should accept custom pool_size parameter."""
        payload = {
            "topic_id": "topic_001",
            "subject": "Алгебра",
            "grade": 8,
            "pool_size": 10
        }

        response = client.post("/api/v1/teacher/generate-test-pool", json=payload)

        data = response.json()
        # Mock might not respect exact size, but should accept param
        assert response.status_code == 200


# =============================================================================
# T7.4: POST /teacher/create-personalized-tests - Personalize by cluster
# =============================================================================


class TestCreatePersonalizedTests:
    """Tests for POST /api/v1/teacher/create-personalized-tests endpoint."""

    def test_returns_tests_by_cluster(self, client):
        """Should return tests split by cluster."""
        payload = {
            "pool_id": "pool_001",
            "cluster_assignments": [
                {"student_id": 1, "cluster_type": "weak"},
                {"student_id": 2, "cluster_type": "medium"},
                {"student_id": 3, "cluster_type": "strong"},
            ]
        }

        response = client.post("/api/v1/teacher/create-personalized-tests", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "tests_by_cluster" in data

    def test_has_all_three_clusters(self, client):
        """Should have tests for weak, medium, strong."""
        payload = {
            "pool_id": "pool_001",
            "cluster_assignments": [
                {"student_id": 1, "cluster_type": "weak"},
            ]
        }

        response = client.post("/api/v1/teacher/create-personalized-tests", json=payload)

        data = response.json()
        clusters = data["tests_by_cluster"]
        assert "weak" in clusters
        assert "medium" in clusters
        assert "strong" in clusters

    def test_weak_has_easier_exercises(self, client):
        """Weak cluster should have more easy exercises."""
        payload = {
            "pool_id": "pool_001",
            "cluster_assignments": [
                {"student_id": 1, "cluster_type": "weak"},
            ]
        }

        response = client.post("/api/v1/teacher/create-personalized-tests", json=payload)

        data = response.json()
        weak_test = data["tests_by_cluster"]["weak"]
        if len(weak_test) > 0:
            difficulties = [ex.get("difficulty") for ex in weak_test]
            # Should have mostly easy/medium
            assert "easy" in difficulties or "medium" in difficulties

    def test_returns_student_assignments(self, client):
        """Should return student -> cluster mapping."""
        payload = {
            "pool_id": "pool_001",
            "cluster_assignments": [
                {"student_id": 1, "cluster_type": "weak"},
                {"student_id": 2, "cluster_type": "strong"},
            ]
        }

        response = client.post("/api/v1/teacher/create-personalized-tests", json=payload)

        data = response.json()
        assert "student_test_assignments" in data


# =============================================================================
# T7.5: POST /teacher/generate-report - Post-test report
# =============================================================================


class TestGenerateReport:
    """Tests for POST /api/v1/teacher/generate-report endpoint."""

    def test_returns_class_report(self, client):
        """Should return post-test class report."""
        payload = {
            "class_id": 1,
            "test_id": "test_001",
            "student_results": [
                {"student_id": 1, "score": 75, "percentage": 75},
                {"student_id": 2, "score": 85, "percentage": 85},
            ]
        }

        response = client.post("/api/v1/teacher/generate-report", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "class_stats" in data

    def test_report_has_class_stats(self, client):
        """Report should include class statistics."""
        payload = {
            "class_id": 1,
            "test_id": "test_001",
            "student_results": []
        }

        response = client.post("/api/v1/teacher/generate-report", json=payload)

        data = response.json()
        stats = data["class_stats"]
        # Should have average, distribution, etc.
        assert isinstance(stats, dict)

    def test_report_has_problem_topics(self, client):
        """Report should identify problem topics."""
        payload = {
            "class_id": 1,
            "test_id": "test_001",
            "student_results": []
        }

        response = client.post("/api/v1/teacher/generate-report", json=payload)

        data = response.json()
        assert "problem_topics" in data

    def test_report_has_attention_students(self, client):
        """Report should identify students needing attention."""
        payload = {
            "class_id": 1,
            "test_id": "test_001",
            "student_results": []
        }

        response = client.post("/api/v1/teacher/generate-report", json=payload)

        data = response.json()
        assert "students_needing_attention" in data

    def test_report_has_recommendations(self, client):
        """Report should include teacher recommendations."""
        payload = {
            "class_id": 1,
            "test_id": "test_001",
            "student_results": []
        }

        response = client.post("/api/v1/teacher/generate-report", json=payload)

        data = response.json()
        assert "recommendations" in data


# =============================================================================
# T7.6: POST /teacher/full-pipeline - All-in-one
# =============================================================================


class TestFullPipeline:
    """Tests for POST /api/v1/teacher/full-pipeline endpoint."""

    def test_returns_full_pipeline_result(self, client):
        """Should return combined result of all steps."""
        payload = {
            "class_id": 1,
            "subject": "Алгебра",
            "topic": "Квадратні рівняння",
            "grade": 8
        }

        response = client.post("/api/v1/teacher/full-pipeline", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "class_analysis" in data
        assert "teacher_lesson" in data
        assert "test_pool" in data
        assert "personalized_tests" in data

    def test_class_analysis_included(self, client):
        """Full pipeline should include class analysis."""
        payload = {
            "class_id": 1,
            "subject": "Алгебра",
            "topic": "Квадратні рівняння",
            "grade": 8
        }

        response = client.post("/api/v1/teacher/full-pipeline", json=payload)

        data = response.json()
        assert "cluster_assignments" in data["class_analysis"]

    def test_lesson_included(self, client):
        """Full pipeline should include generated lesson."""
        payload = {
            "class_id": 1,
            "subject": "Алгебра",
            "topic": "Квадратні рівняння",
            "grade": 8
        }

        response = client.post("/api/v1/teacher/full-pipeline", json=payload)

        data = response.json()
        assert "lesson_content" in data["teacher_lesson"]

    def test_all_fields_required(self, client):
        """Should require all fields for full pipeline."""
        # Missing grade
        payload = {
            "class_id": 1,
            "subject": "Алгебра",
            "topic": "Квадратні рівняння"
        }

        response = client.post("/api/v1/teacher/full-pipeline", json=payload)

        assert response.status_code == 422


# =============================================================================
# T7.7: Error handling
# =============================================================================


class TestTeacherAPIErrors:
    """Error handling tests for teacher endpoints."""

    def test_invalid_json(self, client):
        """Should reject invalid JSON."""
        response = client.post(
            "/api/v1/teacher/analyze-class",
            content="not json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    def test_empty_body(self, client):
        """Should reject empty request body."""
        response = client.post("/api/v1/teacher/analyze-class", json={})

        assert response.status_code == 422

    def test_handles_unicode_topic(self, client):
        """Should handle Ukrainian topic names."""
        payload = {
            "class_id": 1,
            "subject": "Українська мова",
            "topic": "Складнопідрядні речення з кількома підрядними"
        }

        response = client.post("/api/v1/teacher/analyze-class", json=payload)

        # Should not error, mock or real data
        assert response.status_code in [200, 404]
