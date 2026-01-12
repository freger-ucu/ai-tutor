"""Tests for DataLoader service (T1)."""

import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.models.domain import ClassInfo, StudentSummary
from app.models.enums import Level


# =============================================================================
# FIXTURES - Sample test data
# =============================================================================


@pytest.fixture
def sample_scores_df():
    """Create sample scores DataFrame matching actual CSV structure."""
    return pd.DataFrame([
        # Teacher 4 teaches class 1 (grade 8) Algebra
        {"school_id": 1, "academic_year": "2024-2025", "semester": 1, "class_id": 1, "grade": 8,
         "discipline_name": "Алгебра", "teacher_id": 4, "lesson_date": "2024-09-02",
         "score_numeric": 10, "topic_name": "Квадратні рівняння", "student_id": 101},
        {"school_id": 1, "academic_year": "2024-2025", "semester": 1, "class_id": 1, "grade": 8,
         "discipline_name": "Алгебра", "teacher_id": 4, "lesson_date": "2024-09-03",
         "score_numeric": 11, "topic_name": "Дискримінант", "student_id": 101},
        {"school_id": 1, "academic_year": "2024-2025", "semester": 1, "class_id": 1, "grade": 8,
         "discipline_name": "Алгебра", "teacher_id": 4, "lesson_date": "2024-09-02",
         "score_numeric": 5, "topic_name": "Квадратні рівняння", "student_id": 102},
        {"school_id": 1, "academic_year": "2024-2025", "semester": 1, "class_id": 1, "grade": 8,
         "discipline_name": "Алгебра", "teacher_id": 4, "lesson_date": "2024-09-03",
         "score_numeric": 4, "topic_name": "Дискримінант", "student_id": 102},
        {"school_id": 1, "academic_year": "2024-2025", "semester": 1, "class_id": 1, "grade": 8,
         "discipline_name": "Алгебра", "teacher_id": 4, "lesson_date": "2024-09-02",
         "score_numeric": 7, "topic_name": "Квадратні рівняння", "student_id": 103},
        # Teacher 4 also teaches class 2 (grade 8) Geometry
        {"school_id": 1, "academic_year": "2024-2025", "semester": 1, "class_id": 2, "grade": 8,
         "discipline_name": "Геометрія", "teacher_id": 4, "lesson_date": "2024-09-02",
         "score_numeric": 8, "topic_name": "Теорема Піфагора", "student_id": 201},
        # Teacher 13 teaches class 1 (grade 9) Algebra
        {"school_id": 1, "academic_year": "2024-2025", "semester": 1, "class_id": 3, "grade": 9,
         "discipline_name": "Алгебра", "teacher_id": 13, "lesson_date": "2024-09-02",
         "score_numeric": 9, "topic_name": "Системи рівнянь", "student_id": 301},
    ])


@pytest.fixture
def sample_absences_df():
    """Create sample absences DataFrame matching actual CSV structure."""
    return pd.DataFrame([
        {"school_id": 1, "academic_year": "2024-2025", "semester": 1, "class_id": 1, "grade": 8,
         "discipline_name": "Алгебра", "teacher_id": 4, "lesson_date": "2024-09-05",
         "absence_reason": "Поважна причина", "topic_name": "Теорема Вієта", "student_id": 102},
        {"school_id": 1, "academic_year": "2024-2025", "semester": 1, "class_id": 1, "grade": 8,
         "discipline_name": "Алгебра", "teacher_id": 4, "lesson_date": "2024-09-06",
         "absence_reason": "Через хворобу", "topic_name": "Корені рівняння", "student_id": 102},
        {"school_id": 1, "academic_year": "2024-2025", "semester": 1, "class_id": 1, "grade": 8,
         "discipline_name": "Алгебра", "teacher_id": 4, "lesson_date": "2024-09-05",
         "absence_reason": "Поважна причина", "topic_name": "Теорема Вієта", "student_id": 103},
    ])


@pytest.fixture
def data_loader(sample_scores_df, sample_absences_df):
    """Create DataLoader with sample data."""
    from app.services.data_loader import DataLoader

    with patch.object(DataLoader, '_load_data') as mock_load:
        loader = DataLoader.__new__(DataLoader)
        loader.scores_df = sample_scores_df
        loader.absences_df = sample_absences_df
        loader._build_indexes()
        return loader


# =============================================================================
# TESTS - DataLoader initialization
# =============================================================================


class TestDataLoaderInit:
    """Tests for DataLoader initialization."""

    def test_load_missing_scores_file(self, tmp_path):
        """DataLoader raises error if scores file is missing."""
        from app.services.data_loader import DataLoader

        with pytest.raises(FileNotFoundError):
            DataLoader(data_path=tmp_path)

    def test_load_missing_absences_file(self, tmp_path, sample_scores_df):
        """DataLoader raises error if absences file is missing."""
        from app.services.data_loader import DataLoader

        # Create only scores file
        sample_scores_df.to_parquet(tmp_path / "benchmark_scores.parquet")

        with pytest.raises(FileNotFoundError):
            DataLoader(data_path=tmp_path)

    def test_load_valid_files(self, tmp_path, sample_scores_df, sample_absences_df):
        """DataLoader loads valid parquet files."""
        from app.services.data_loader import DataLoader

        # Create both files
        sample_scores_df.to_parquet(tmp_path / "benchmark_scores.parquet")
        sample_absences_df.to_parquet(tmp_path / "benchmark_absences.parquet")

        loader = DataLoader(data_path=tmp_path)
        assert loader.scores_df is not None
        assert loader.absences_df is not None


# =============================================================================
# TESTS - get_teacher_classes (EP1)
# =============================================================================


class TestGetTeacherClasses:
    """Tests for get_teacher_classes method (EP1)."""

    def test_existing_teacher(self, data_loader):
        """Returns classes for existing teacher."""
        classes = data_loader.get_teacher_classes(4)

        assert len(classes) == 2
        assert all(isinstance(c, ClassInfo) for c in classes)

        subjects = {c.subject for c in classes}
        assert "Алгебра" in subjects
        assert "Геометрія" in subjects

    def test_teacher_class_details(self, data_loader):
        """Returns correct class details."""
        classes = data_loader.get_teacher_classes(4)

        algebra_class = next(c for c in classes if c.subject == "Алгебра")
        assert algebra_class.class_id == 1
        assert algebra_class.class_number == 8

    def test_nonexistent_teacher(self, data_loader):
        """Returns empty list for nonexistent teacher."""
        classes = data_loader.get_teacher_classes(999)
        assert classes == []

    def test_teacher_with_single_class(self, data_loader):
        """Returns single class for teacher with one class."""
        classes = data_loader.get_teacher_classes(13)
        assert len(classes) == 1
        assert classes[0].subject == "Алгебра"
        assert classes[0].class_number == 9

    def test_negative_teacher_id(self, data_loader):
        """Returns empty list for negative teacher ID."""
        classes = data_loader.get_teacher_classes(-1)
        assert classes == []

    def test_zero_teacher_id(self, data_loader):
        """Returns empty list for zero teacher ID."""
        classes = data_loader.get_teacher_classes(0)
        assert classes == []


# =============================================================================
# TESTS - get_class_students (EP2)
# =============================================================================


class TestGetClassStudents:
    """Tests for get_class_students method (EP2)."""

    def test_existing_class(self, data_loader):
        """Returns students for existing class."""
        students = data_loader.get_class_students(1, "Алгебра")

        assert len(students) == 3
        assert all(isinstance(s, StudentSummary) for s in students)

    def test_student_levels_computed(self, data_loader):
        """Student levels are computed from percentiles."""
        students = data_loader.get_class_students(1, "Алгебра")

        # Student 101 has avg 10.5 - should be strong
        # Student 102 has avg 4.5 - should be weak
        # Student 103 has avg 7.0 - should be medium

        levels = {s.student_id: s.subject_level for s in students}
        assert levels[101] == Level.STRONG
        assert levels[102] == Level.WEAK
        assert levels[103] == Level.MEDIUM

    def test_average_grades_computed(self, data_loader):
        """Average grades are computed correctly."""
        students = data_loader.get_class_students(1, "Алгебра")

        avgs = {s.student_id: s.average_subject_grade for s in students}
        assert avgs[101] == 10.5  # (10 + 11) / 2
        assert avgs[102] == 4.5   # (5 + 4) / 2
        assert avgs[103] == 7.0   # single score

    def test_nonexistent_class(self, data_loader):
        """Returns empty list for nonexistent class."""
        students = data_loader.get_class_students(999, "Алгебра")
        assert students == []

    def test_wrong_subject_for_class(self, data_loader):
        """Returns empty list if subject doesn't match class."""
        students = data_loader.get_class_students(1, "Геометрія")  # Class 1 has Algebra
        assert students == []

    def test_empty_subject(self, data_loader):
        """Returns empty list for empty subject."""
        students = data_loader.get_class_students(1, "")
        assert students == []

    def test_negative_class_id(self, data_loader):
        """Returns empty list for negative class ID."""
        students = data_loader.get_class_students(-1, "Алгебра")
        assert students == []


# =============================================================================
# TESTS - get_student_details (EP5)
# =============================================================================


class TestGetStudentDetails:
    """Tests for get_student_details method (EP5)."""

    def test_existing_student(self, data_loader):
        """Returns details for existing student."""
        details = data_loader.get_student_details(102, 1, "Алгебра")

        assert details is not None
        assert details["average_subject_grade"] == 4.5
        assert details["level"] == Level.WEAK

    def test_skipped_lessons(self, data_loader):
        """Returns skipped lessons for student."""
        details = data_loader.get_student_details(102, 1, "Алгебра")

        assert len(details["skipped_lessons"]) == 2
        topics = {l.topic for l in details["skipped_lessons"]}
        assert "Теорема Вієта" in topics
        assert "Корені рівняння" in topics

    def test_student_no_absences(self, data_loader):
        """Returns empty skipped_lessons for student with no absences."""
        details = data_loader.get_student_details(101, 1, "Алгебра")
        assert details["skipped_lessons"] == []

    def test_problematic_topics(self, data_loader):
        """Returns problematic topics (low scores)."""
        details = data_loader.get_student_details(102, 1, "Алгебра")

        # Student 102 has low scores, should have problematic topics
        assert len(details["problematic_topics"]) > 0

    def test_nonexistent_student(self, data_loader):
        """Returns None for nonexistent student."""
        details = data_loader.get_student_details(999, 1, "Алгебра")
        assert details is None

    def test_student_wrong_class(self, data_loader):
        """Returns None if student not in specified class."""
        details = data_loader.get_student_details(101, 2, "Алгебра")  # Student 101 is in class 1
        assert details is None

    def test_student_wrong_subject(self, data_loader):
        """Returns None if student doesn't have specified subject."""
        details = data_loader.get_student_details(101, 1, "Геометрія")
        assert details is None


# =============================================================================
# TESTS - get_student_info (EP8)
# =============================================================================


class TestGetStudentInfo:
    """Tests for get_student_info method (EP8)."""

    def test_existing_student(self, data_loader):
        """Returns info for existing student."""
        info = data_loader.get_student_info(101)

        assert info is not None
        assert info["class_id"] == 1
        assert info["class_number"] == 8
        assert "Алгебра" in info["subjects"]

    def test_student_subjects(self, data_loader):
        """Returns all subjects for student."""
        info = data_loader.get_student_info(101)

        # Student 101 only has Algebra in test data
        assert len(info["subjects"]) >= 1
        assert "Алгебра" in info["subjects"]

    def test_nonexistent_student(self, data_loader):
        """Returns None for nonexistent student."""
        info = data_loader.get_student_info(999)
        assert info is None

    def test_negative_student_id(self, data_loader):
        """Returns None for negative student ID."""
        info = data_loader.get_student_info(-1)
        assert info is None


# =============================================================================
# TESTS - get_students_by_level (for EP3.1)
# =============================================================================


class TestGetStudentsByLevel:
    """Tests for get_students_by_level method (EP3.1 support)."""

    def test_get_weak_students(self, data_loader):
        """Returns weak students."""
        students = data_loader.get_students_by_level(1, "Алгебра", [Level.WEAK])

        assert len(students) == 1
        assert students[0].student_id == 102

    def test_get_strong_students(self, data_loader):
        """Returns strong students."""
        students = data_loader.get_students_by_level(1, "Алгебра", [Level.STRONG])

        assert len(students) == 1
        assert students[0].student_id == 101

    def test_get_multiple_levels(self, data_loader):
        """Returns students from multiple levels."""
        students = data_loader.get_students_by_level(
            1, "Алгебра", [Level.WEAK, Level.STRONG]
        )

        assert len(students) == 2
        ids = {s.student_id for s in students}
        assert 101 in ids  # strong
        assert 102 in ids  # weak

    def test_get_all_levels(self, data_loader):
        """Returns all students when all levels specified."""
        students = data_loader.get_students_by_level(
            1, "Алгебра", [Level.WEAK, Level.MEDIUM, Level.STRONG]
        )

        assert len(students) == 3

    def test_empty_level_list(self, data_loader):
        """Returns empty list for empty level list."""
        students = data_loader.get_students_by_level(1, "Алгебра", [])
        assert students == []


# =============================================================================
# TESTS - Edge cases and error handling
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_unicode_subjects(self, data_loader):
        """Handles Ukrainian subject names correctly."""
        classes = data_loader.get_teacher_classes(4)
        subjects = [c.subject for c in classes]

        assert any("Алгебра" in s for s in subjects)
        assert any("Геометрія" in s for s in subjects)

    def test_large_student_id(self, data_loader):
        """Handles large student IDs - returns None if not found."""
        info = data_loader.get_student_info(999999999)
        assert info is None

    def test_special_characters_in_topic(self, data_loader):
        """Handles special characters in topic names."""
        details = data_loader.get_student_details(102, 1, "Алгебра")

        # Check that topics with Ukrainian characters work
        for lesson in details["skipped_lessons"]:
            assert isinstance(lesson.topic, str)

    def test_concurrent_access(self, data_loader):
        """DataLoader is thread-safe for reads."""
        import concurrent.futures

        def read_data():
            return data_loader.get_teacher_classes(4)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(read_data) for _ in range(100)]
            results = [f.result() for f in futures]

        assert all(len(r) == 2 for r in results)


# =============================================================================
# TESTS - Data consistency
# =============================================================================


class TestDataConsistency:
    """Tests for data consistency."""

    def test_student_in_class_matches_class_students(self, data_loader):
        """Student info class matches class student list."""
        info = data_loader.get_student_info(101)
        students = data_loader.get_class_students(info["class_id"], "Алгебра")

        student_ids = {s.student_id for s in students}
        assert 101 in student_ids

    def test_teacher_classes_have_students(self, data_loader):
        """All teacher classes have at least one student."""
        classes = data_loader.get_teacher_classes(4)

        for cls in classes:
            students = data_loader.get_class_students(cls.class_id, cls.subject)
            assert len(students) > 0, f"Class {cls.class_id} has no students"

    def test_grade_boundaries_respected(self, data_loader):
        """All grades are within 0-12 range."""
        students = data_loader.get_class_students(1, "Алгебра")

        for s in students:
            assert 0 <= s.average_subject_grade <= 12
