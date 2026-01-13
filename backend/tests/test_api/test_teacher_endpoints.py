"""
Teacher API endpoint tests - TDD approach.

Tests are written FIRST, then implementation is verified.
"""

import pytest
from unittest.mock import patch


class TestEP1GetTeacher:
    """Tests for EP1: GET /teacher/{id}."""

    def test_returns_200_for_valid_teacher(self, client, sample_teacher_id):
        """GET /teacher/{id} should return 200 with classes."""
        response = client.get(f"/api/v1/teacher/{sample_teacher_id}")

        assert response.status_code == 200
        data = response.json()
        assert "classes" in data
        assert isinstance(data["classes"], list)

    def test_returns_404_for_unknown_teacher(self, client):
        """GET /teacher/999999 should return 404."""
        response = client.get("/api/v1/teacher/999999999")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_response_matches_contract(self, client, sample_teacher_id):
        """Response should match: {classes: [{class_id, class_number, subject}]}."""
        response = client.get(f"/api/v1/teacher/{sample_teacher_id}")

        assert response.status_code == 200
        data = response.json()
        assert "classes" in data

        if len(data["classes"]) > 0:
            cls = data["classes"][0]
            assert "class_id" in cls
            assert "class_number" in cls
            assert "subject" in cls
            # Validate types
            assert isinstance(cls["class_id"], int)
            assert isinstance(cls["class_number"], int)
            assert isinstance(cls["subject"], str)


class TestEP2GetStudents:
    """Tests for EP2: POST /teacher/students."""

    def test_returns_200_for_valid_request(self, client, valid_teacher_class_subject):
        """POST /teacher/students should return 200 with students."""
        teacher_id, class_id, subject = valid_teacher_class_subject

        response = client.post(
            "/api/v1/teacher/students",
            json={
                "class_id": class_id,
                "teacher_id": teacher_id,
                "subject": subject
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "students" in data
        assert isinstance(data["students"], list)

    def test_returns_404_for_unknown_class(self, client):
        """Should return 404 for unknown class_id."""
        response = client.post(
            "/api/v1/teacher/students",
            json={
                "class_id": 999999999,
                "teacher_id": 1,
                "subject": "Алгебра"
            }
        )

        assert response.status_code == 404

    def test_response_matches_contract(self, client, valid_teacher_class_subject):
        """Response: {students: [{student_id, subject_level, average_subject_grade}]}."""
        teacher_id, class_id, subject = valid_teacher_class_subject

        response = client.post(
            "/api/v1/teacher/students",
            json={
                "class_id": class_id,
                "teacher_id": teacher_id,
                "subject": subject
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "students" in data

        if len(data["students"]) > 0:
            student = data["students"][0]
            assert "student_id" in student
            assert "subject_level" in student
            assert "average_subject_grade" in student
            # Validate types
            assert isinstance(student["student_id"], int)
            assert student["subject_level"] in ["weak", "medium", "strong"]
            assert isinstance(student["average_subject_grade"], (int, float))

    def test_validates_request_body(self, client):
        """Should return 422 for missing required fields."""
        response = client.post(
            "/api/v1/teacher/students",
            json={"class_id": 1}  # Missing teacher_id and subject
        )

        assert response.status_code == 422


class TestEP5GetStudentDetails:
    """Tests for EP5: POST /teacher/student/details."""

    def test_returns_200_for_valid_request(self, client, valid_teacher_class_subject, data_loader):
        """POST /teacher/student/details should return 200."""
        teacher_id, class_id, subject = valid_teacher_class_subject

        # Get a valid student for this class/subject
        students = data_loader.get_class_students(class_id, subject)
        if not students:
            pytest.skip("No students in class")
        student_id = students[0].student_id

        response = client.post(
            "/api/v1/teacher/student/details",
            json={
                "class_id": class_id,
                "subject": subject,
                "teacher_id": teacher_id,
                "student_id": student_id
            }
        )

        assert response.status_code == 200

    def test_returns_404_for_unknown_student(self, client, valid_teacher_class_subject):
        """Should return 404 for unknown student_id."""
        teacher_id, class_id, subject = valid_teacher_class_subject

        response = client.post(
            "/api/v1/teacher/student/details",
            json={
                "class_id": class_id,
                "subject": subject,
                "teacher_id": teacher_id,
                "student_id": 999999999
            }
        )

        assert response.status_code == 404

    def test_response_matches_contract(self, client, valid_teacher_class_subject, data_loader):
        """Response: {average_subject_grade, level, skipped_lessons, problematic_topics}."""
        teacher_id, class_id, subject = valid_teacher_class_subject

        # Get a valid student
        students = data_loader.get_class_students(class_id, subject)
        if not students:
            pytest.skip("No students in class")
        student_id = students[0].student_id

        response = client.post(
            "/api/v1/teacher/student/details",
            json={
                "class_id": class_id,
                "subject": subject,
                "teacher_id": teacher_id,
                "student_id": student_id
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert "average_subject_grade" in data
        assert "level" in data
        assert "skipped_lessons" in data
        assert "problematic_topics" in data

        # Validate types
        assert isinstance(data["average_subject_grade"], (int, float))
        assert data["level"] in ["weak", "medium", "strong"]
        assert isinstance(data["skipped_lessons"], list)
        assert isinstance(data["problematic_topics"], list)

        # Validate skipped_lessons structure
        for lesson in data["skipped_lessons"]:
            assert "date" in lesson
            assert "topic" in lesson

        # Validate problematic_topics structure
        for topic in data["problematic_topics"]:
            assert "topic" in topic
            assert "average_score" in topic


class TestEP6GetRecommendation:
    """Tests for EP6: POST /teacher/student/recommendation."""

    @pytest.fixture
    def mock_llm_response(self):
        """Mock LLM response for testing."""
        return "Молодець! Ти показуєш хороші результати. Рекомендую звернути увагу на теми з нижчими оцінками."

    def test_returns_200_for_valid_request(self, client, valid_teacher_class_subject, data_loader):
        """POST /teacher/student/recommendation should return 200."""
        teacher_id, class_id, subject = valid_teacher_class_subject

        # Get a valid student
        students = data_loader.get_class_students(class_id, subject)
        if not students:
            pytest.skip("No students in class")
        student_id = students[0].student_id

        with patch('app.api.v1.teacher.generate_recommendation') as mock_gen:
            mock_gen.return_value = "Рекомендація для учня."

            response = client.post(
                "/api/v1/teacher/student/recommendation",
                json={
                    "student_id": student_id,
                    "subject": subject
                }
            )

            assert response.status_code == 200

    def test_returns_404_for_unknown_student(self, client):
        """Should return 404 for unknown student_id."""
        response = client.post(
            "/api/v1/teacher/student/recommendation",
            json={
                "student_id": 999999999,
                "subject": "Алгебра"
            }
        )

        assert response.status_code == 404

    def test_response_matches_contract(self, client, valid_teacher_class_subject, data_loader):
        """Response: {feedback: str}."""
        teacher_id, class_id, subject = valid_teacher_class_subject

        # Get a valid student
        students = data_loader.get_class_students(class_id, subject)
        if not students:
            pytest.skip("No students in class")
        student_id = students[0].student_id

        with patch('app.api.v1.teacher.generate_recommendation') as mock_gen:
            mock_gen.return_value = "Рекомендація для учня."

            response = client.post(
                "/api/v1/teacher/student/recommendation",
                json={
                    "student_id": student_id,
                    "subject": subject
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
            "/api/v1/teacher/student/recommendation",
            json={"student_id": 1}  # Missing subject
        )

        assert response.status_code == 422

    @pytest.mark.slow
    def test_llm_integration(self, client, valid_teacher_class_subject, data_loader):
        """Integration test with real LLM (marked slow)."""
        teacher_id, class_id, subject = valid_teacher_class_subject

        students = data_loader.get_class_students(class_id, subject)
        if not students:
            pytest.skip("No students in class")
        student_id = students[0].student_id

        response = client.post(
            "/api/v1/teacher/student/recommendation",
            json={
                "student_id": student_id,
                "subject": subject
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "feedback" in data
        assert len(data["feedback"]) > 50  # Should be substantial feedback


class TestEP3GenerateNotes:
    """Tests for EP3: POST /teacher/notes/by-level and /teacher/notes/individual."""

    def test_level_notes_returns_200(self, client, valid_teacher_class_subject):
        """POST /teacher/notes/by-level should return 200."""
        teacher_id, class_id, subject = valid_teacher_class_subject

        with patch('app.api.v1.teacher.generate_level_notes') as mock_gen:
            mock_gen.return_value = {
                "title": "Квадратні рівняння",
                "contents": "# Зміст уроку...",
                "teacher_notes": "Нотатки для вчителя..."
            }

            response = client.post(
                "/api/v1/teacher/notes/by-level",
                json={
                    "class_id": class_id,
                    "teacher_id": teacher_id,
                    "subject": subject,
                    "level_list": ["weak", "medium"],
                    "topic_definition": "Квадратні рівняння та їх розв'язання"
                }
            )

            assert response.status_code == 200

    def test_level_notes_response_matches_contract(self, client, valid_teacher_class_subject):
        """Response: {title, contents, teacher_notes}."""
        teacher_id, class_id, subject = valid_teacher_class_subject

        with patch('app.api.v1.teacher.generate_level_notes') as mock_gen:
            mock_gen.return_value = {
                "title": "Test Title",
                "contents": "Test Contents",
                "teacher_notes": "Test Notes"
            }

            response = client.post(
                "/api/v1/teacher/notes/by-level",
                json={
                    "class_id": class_id,
                    "teacher_id": teacher_id,
                    "subject": subject,
                    "level_list": ["weak"],
                    "topic_definition": "Test topic"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert "title" in data
            assert "contents" in data
            assert "teacher_notes" in data
            assert isinstance(data["title"], str)
            assert isinstance(data["contents"], str)
            assert isinstance(data["teacher_notes"], str)

    def test_level_notes_validates_request(self, client):
        """Should return 422 for missing required fields."""
        response = client.post(
            "/api/v1/teacher/notes/by-level",
            json={
                "class_id": 1,
                "subject": "Алгебра"
                # Missing teacher_id, level_list, topic_definition
            }
        )

        assert response.status_code == 422

    def test_individual_notes_returns_200(self, client, valid_teacher_class_subject, data_loader):
        """POST /teacher/notes/individual should return 200."""
        teacher_id, class_id, subject = valid_teacher_class_subject

        # Get a valid student
        students = data_loader.get_class_students(class_id, subject)
        if not students:
            pytest.skip("No students in class")
        student_id = students[0].student_id

        with patch('app.api.v1.teacher.generate_individual_notes') as mock_gen:
            mock_gen.return_value = {
                "title": "Індивідуальний конспект",
                "contents": "# Зміст...",
                "teacher_notes": "Рекомендації..."
            }

            response = client.post(
                "/api/v1/teacher/notes/individual",
                json={
                    "class_id": class_id,
                    "teacher_id": teacher_id,
                    "subject": subject,
                    "student_list": [student_id],
                    "topic_definition": "Квадратні рівняння"
                }
            )

            assert response.status_code == 200

    def test_individual_notes_validates_request(self, client):
        """Should return 422 for missing required fields."""
        response = client.post(
            "/api/v1/teacher/notes/individual",
            json={
                "class_id": 1,
                "subject": "Алгебра"
                # Missing teacher_id, student_list, topic_definition
            }
        )

        assert response.status_code == 422

    @pytest.mark.slow
    def test_level_notes_llm_integration(self, client, valid_teacher_class_subject):
        """Integration test with real LLM for level notes."""
        teacher_id, class_id, subject = valid_teacher_class_subject

        response = client.post(
            "/api/v1/teacher/notes/by-level",
            json={
                "class_id": class_id,
                "teacher_id": teacher_id,
                "subject": subject,
                "level_list": ["medium"],
                "topic_definition": "Квадратні рівняння та дискримінант"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "title" in data
        assert "contents" in data
        assert len(data["contents"]) > 100  # Should be substantial

    @pytest.mark.slow
    def test_individual_notes_llm_integration(self, client, valid_teacher_class_subject, data_loader):
        """Integration test with real LLM for individual notes."""
        teacher_id, class_id, subject = valid_teacher_class_subject

        students = data_loader.get_class_students(class_id, subject)
        if not students:
            pytest.skip("No students in class")
        student_id = students[0].student_id

        response = client.post(
            "/api/v1/teacher/notes/individual",
            json={
                "class_id": class_id,
                "teacher_id": teacher_id,
                "subject": subject,
                "student_list": [student_id],
                "topic_definition": "Квадратні рівняння"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "title" in data
        assert "contents" in data
        assert len(data["contents"]) > 100


class TestEP4GenerateTest:
    """Tests for EP4: POST /teacher/test."""

    def test_returns_200_for_valid_request(self, client, valid_teacher_class_subject):
        """POST /teacher/test should return 200."""
        teacher_id, class_id, subject = valid_teacher_class_subject

        with patch('app.api.v1.teacher.generate_test_pool') as mock_gen:
            mock_gen.return_value = {
                "title": "Тест: Квадратні рівняння",
                "questions": [
                    {
                        "question": "Що таке дискримінант?",
                        "type": "multiple_choice",
                        "difficulty": "easy",
                        "options": ["A) D = b² - 4ac", "B) D = b² + 4ac", "C) D = a² - bc", "D) D = 2ac"],
                        "correct_answer": "A",
                        "explanation": "Дискримінант D = b² - 4ac",
                        "topic": "Дискримінант"
                    }
                ]
            }

            response = client.post(
                "/api/v1/teacher/test",
                json={
                    "class_id": class_id,
                    "teacher_id": teacher_id,
                    "subject": subject,
                    "topic_definition": "Квадратні рівняння"
                }
            )

            assert response.status_code == 200

    def test_response_matches_contract(self, client, valid_teacher_class_subject):
        """Response: {title, questions: [{question, type, difficulty, ...}]}."""
        teacher_id, class_id, subject = valid_teacher_class_subject

        with patch('app.api.v1.teacher.generate_test_pool') as mock_gen:
            mock_gen.return_value = {
                "title": "Test Title",
                "questions": [
                    {
                        "question": "Q1",
                        "type": "multiple_choice",
                        "difficulty": "easy",
                        "options": ["A", "B", "C", "D"],
                        "correct_answer": "A",
                        "explanation": "Explanation",
                        "topic": "Topic"
                    },
                    {
                        "question": "Q2",
                        "type": "open",
                        "difficulty": "medium",
                        "explanation": "Explanation",
                        "topic": "Topic"
                    }
                ]
            }

            response = client.post(
                "/api/v1/teacher/test",
                json={
                    "class_id": class_id,
                    "teacher_id": teacher_id,
                    "subject": subject,
                    "topic_definition": "Test topic"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert "title" in data
            assert "questions" in data
            assert isinstance(data["questions"], list)
            assert len(data["questions"]) >= 1

            # Check question structure
            q = data["questions"][0]
            assert "question" in q
            assert "type" in q
            assert "difficulty" in q

    def test_validates_request(self, client):
        """Should return 422 for missing required fields."""
        response = client.post(
            "/api/v1/teacher/test",
            json={
                "class_id": 1,
                "subject": "Алгебра"
                # Missing teacher_id, topic_definition
            }
        )

        assert response.status_code == 422

    @pytest.mark.slow
    def test_llm_integration(self, client, valid_teacher_class_subject):
        """Integration test with real LLM for test generation."""
        teacher_id, class_id, subject = valid_teacher_class_subject

        response = client.post(
            "/api/v1/teacher/test",
            json={
                "class_id": class_id,
                "teacher_id": teacher_id,
                "subject": subject,
                "topic_definition": "Квадратні рівняння та дискримінант"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "title" in data
        assert "questions" in data
        assert len(data["questions"]) >= 5  # Should generate multiple questions


class TestEP7Solver:
    """Tests for EP7: POST /solver."""

    def test_returns_200_for_valid_request(self, client):
        """POST /solver should return 200."""
        with patch('app.api.v1.teacher.solve_question') as mock_solve:
            mock_solve.return_value = "x = 2 або x = -2"

            response = client.post(
                "/api/v1/solver",
                json={
                    "subject": "Алгебра",
                    "grade": 8,
                    "question": "Розв'яжіть рівняння: x² - 4 = 0"
                }
            )

            assert response.status_code == 200

    def test_response_matches_contract(self, client):
        """Response: {question: str, answer_explained: str}."""
        with patch('app.api.v1.teacher.solve_question') as mock_solve:
            mock_solve.return_value = "x² - 4 = 0 означає (x-2)(x+2) = 0, тому x = 2 або x = -2"

            response = client.post(
                "/api/v1/solver",
                json={
                    "subject": "Алгебра",
                    "grade": 8,
                    "question": "Розв'яжіть рівняння: x² - 4 = 0"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert "question" in data
            assert "answer_explained" in data
            assert isinstance(data["question"], str)
            assert isinstance(data["answer_explained"], str)

    def test_validates_request_body(self, client):
        """Should return 422 for missing required fields."""
        response = client.post(
            "/api/v1/solver",
            json={"question": "Test"}  # Missing subject and grade
        )

        assert response.status_code == 422

    def test_validates_grade_range(self, client):
        """Should return 422 for invalid grade (must be 8 or 9)."""
        response = client.post(
            "/api/v1/solver",
            json={
                "subject": "Алгебра",
                "grade": 10,  # Invalid - only 8 or 9 allowed
                "question": "Test question"
            }
        )

        assert response.status_code == 422

    @pytest.mark.slow
    def test_llm_integration_algebra(self, client):
        """Integration test with real LLM for algebra (marked slow)."""
        response = client.post(
            "/api/v1/solver",
            json={
                "subject": "Алгебра",
                "grade": 8,
                "question": "Розв'яжіть рівняння: x² - 4 = 0"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "question" in data
        assert "answer_explained" in data
        # Should mention x = 2 or x = -2 somewhere in the answer
        answer = data["answer_explained"].lower()
        assert "2" in answer  # Should contain the solution

    @pytest.mark.slow
    def test_llm_integration_ukrainian(self, client):
        """Integration test with real LLM for Ukrainian language (marked slow)."""
        response = client.post(
            "/api/v1/solver",
            json={
                "subject": "Українська мова",
                "grade": 8,
                "question": "Що таке складнопідрядне речення?"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "answer_explained" in data
        assert len(data["answer_explained"]) > 50  # Should be substantial

    @pytest.mark.slow
    def test_llm_integration_history(self, client):
        """Integration test with real LLM for history (marked slow)."""
        response = client.post(
            "/api/v1/solver",
            json={
                "subject": "Історія України",
                "grade": 8,
                "question": "Коли була Запорозька Січ?"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "answer_explained" in data
        assert len(data["answer_explained"]) > 50  # Should be substantial
