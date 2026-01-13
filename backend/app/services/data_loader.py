"""
Data Loader Service

Loads and processes hackathon data files (benchmark_scores, benchmark_absences).
Provides fast lookups for teacher classes, student lists, student details, etc.
"""

from pathlib import Path
from typing import Optional

import pandas as pd

from app.models.domain import (
    ClassInfo,
    ProblematicTopic,
    SkippedLesson,
    StudentSummary,
)
from app.models.enums import Level
from app.services.levels import compute_quartiles, assign_level


# =============================================================================
# REQUIRED FILTERS (from architecture.md)
# =============================================================================
CURRENT_ACADEMIC_YEAR = "2025-2026"
SUPPORTED_SUBJECTS = ["Алгебра", "Українська мова", "Історія України"]


class DataLoader:
    """
    Loads parquet data and provides lookup methods for API endpoints.

    Supports:
    - EP1: get_teacher_classes(teacher_id) - teacher's classes and subjects
    - EP2: get_class_students(class_id, subject) - students with levels
    - EP3.1: get_students_by_level(class_id, subject, levels) - filter by level
    - EP5: get_student_details(student_id, class_id, subject) - detailed info
    - EP8: get_student_info(student_id) - student's class and subjects
    """

    def __init__(self, data_path: Optional[Path] = None):
        """
        Initialize DataLoader with data directory.

        Args:
            data_path: Path to directory containing parquet files.
                       Defaults to backend/data/

        Raises:
            FileNotFoundError: If required parquet files are missing.
        """
        if data_path is None:
            # Default: backend/data/ relative to this file's location
            data_path = Path(__file__).parent.parent.parent / "data"

        self.data_path = Path(data_path)
        self.scores_df: Optional[pd.DataFrame] = None
        self.absences_df: Optional[pd.DataFrame] = None

        # Indexes for fast lookups
        self._teacher_classes: dict[int, list[ClassInfo]] = {}
        self._class_students: dict[tuple[int, str], list[StudentSummary]] = {}

        # Load data on init
        self._load_data()
        self._build_indexes()

    def _load_data(self) -> None:
        """
        Load data from parquet files into memory.

        Applies required filters from architecture.md:
        1. academic_year == '2025-2026'
        2. discipline_name in SUPPORTED_SUBJECTS
        3. For multi-class students, use latest class
        """
        scores_path = self.data_path / "benchmark_scores.parquet"
        absences_path = self.data_path / "benchmark_absences.parquet"

        # Check both files exist before loading
        if not scores_path.exists():
            raise FileNotFoundError(f"Scores file not found: {scores_path}")
        if not absences_path.exists():
            raise FileNotFoundError(f"Absences file not found: {absences_path}")

        # Load scores data
        self.scores_df = pd.read_parquet(scores_path)

        # FILTER 1: Current academic year only
        self.scores_df = self.scores_df[
            self.scores_df["academic_year"] == CURRENT_ACADEMIC_YEAR
        ]

        # FILTER 2: Supported subjects only
        self.scores_df = self.scores_df[
            self.scores_df["discipline_name"].isin(SUPPORTED_SUBJECTS)
        ]

        # FILTER 3: For multi-class students, keep only latest class
        self.scores_df = self._resolve_student_classes(self.scores_df)

        # Type conversions
        self.scores_df["teacher_id"] = self.scores_df["teacher_id"].astype(int)
        self.scores_df["student_id"] = self.scores_df["student_id"].astype(int)
        self.scores_df["class_id"] = self.scores_df["class_id"].astype(int)
        self.scores_df["score_numeric"] = self.scores_df["score_numeric"].astype(int)

        # Load absences data
        self.absences_df = pd.read_parquet(absences_path)

        # Apply same filters to absences
        self.absences_df = self.absences_df[
            self.absences_df["academic_year"] == CURRENT_ACADEMIC_YEAR
        ]
        self.absences_df = self.absences_df[
            self.absences_df["discipline_name"].isin(SUPPORTED_SUBJECTS)
        ]

        # Type conversions
        self.absences_df["student_id"] = self.absences_df["student_id"].astype(int)
        self.absences_df["class_id"] = self.absences_df["class_id"].astype(int)

    def _resolve_student_classes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Resolve multi-class students to their latest class.

        22 students appear in 2 classes (transfers). For each student,
        keep only records from their most recent class (by lesson_date).
        """
        # Find students with multiple classes
        student_classes = df.groupby("student_id")["class_id"].nunique()
        multi_class_students = student_classes[student_classes > 1].index.tolist()

        if not multi_class_students:
            return df

        # For each multi-class student, find their latest class
        latest_classes = {}
        for student_id in multi_class_students:
            student_df = df[df["student_id"] == student_id]
            # Get the class_id from the row with the latest lesson_date
            latest_row = student_df.loc[student_df["lesson_date"].idxmax()]
            latest_classes[student_id] = latest_row["class_id"]

        # Filter: keep rows where student is NOT multi-class OR is in their latest class
        def keep_row(row):
            student_id = row["student_id"]
            if student_id not in latest_classes:
                return True  # Not a multi-class student, keep all
            return row["class_id"] == latest_classes[student_id]

        return df[df.apply(keep_row, axis=1)]

    def _build_indexes(self) -> None:
        """Build lookup indexes for faster queries."""
        if self.scores_df is None or self.scores_df.empty:
            return

        # Build teacher -> classes index
        self._teacher_classes = {}
        unique_classes = self.scores_df.groupby(
            ["teacher_id", "class_id", "grade", "discipline_name"]
        ).size().reset_index(name="count")

        for _, row in unique_classes.iterrows():
            teacher_id = int(row["teacher_id"])
            if teacher_id not in self._teacher_classes:
                self._teacher_classes[teacher_id] = []

            self._teacher_classes[teacher_id].append(
                ClassInfo(
                    class_id=int(row["class_id"]),
                    class_number=int(row["grade"]),
                    subject=row["discipline_name"]
                )
            )

        # Build (class_id, subject) -> students index with levels
        self._class_students = {}
        for (class_id, subject), group in self.scores_df.groupby(
            ["class_id", "discipline_name"]
        ):
            student_avgs = group.groupby("student_id")["score_numeric"].mean()

            # Calculate quartiles for level assignment using shared utility
            scores_list = student_avgs.tolist()
            q1, q3 = compute_quartiles(scores_list)

            students = []
            for student_id, avg_grade in student_avgs.items():
                level = assign_level(float(avg_grade), q1, q3)
                students.append(
                    StudentSummary(
                        student_id=int(student_id),
                        subject_level=level,
                        average_subject_grade=round(float(avg_grade), 2)
                    )
                )

            students.sort(key=lambda s: s.student_id)
            self._class_students[(int(class_id), subject)] = students

    # =========================================================================
    # EP1: Get Teacher Classes
    # =========================================================================

    def get_teacher_classes(self, teacher_id: int) -> list[ClassInfo]:
        """
        Get list of classes taught by a teacher.

        Args:
            teacher_id: Teacher identifier

        Returns:
            List of ClassInfo with class_id, class_number (grade), and subject
        """
        return self._teacher_classes.get(teacher_id, [])

    # =========================================================================
    # EP2: Get Class Students
    # =========================================================================

    def get_class_students(
        self,
        class_id: int,
        subject: str,
        teacher_id: Optional[int] = None
    ) -> list[StudentSummary]:
        """
        Get students in a class for a specific subject with their levels.

        Args:
            class_id: Class identifier
            subject: Subject name (Ukrainian string)
            teacher_id: Optional teacher filter (for validation, not used in lookup)

        Returns:
            List of StudentSummary with student_id, level, and average grade
        """
        return self._class_students.get((class_id, subject), [])

    # =========================================================================
    # EP3.1 Support: Get Students by Level
    # =========================================================================

    def get_students_by_level(
        self,
        class_id: int,
        subject: str,
        levels: list[Level]
    ) -> list[StudentSummary]:
        """
        Get students filtered by level(s).

        Args:
            class_id: Class identifier
            subject: Subject name
            levels: List of levels to filter by

        Returns:
            List of StudentSummary matching the specified levels
        """
        all_students = self.get_class_students(class_id, subject)
        return [s for s in all_students if s.subject_level in levels]

    # =========================================================================
    # EP5: Get Student Details
    # =========================================================================

    def get_student_details(
        self,
        student_id: int,
        class_id: int,
        subject: str
    ) -> Optional[dict]:
        """
        Get detailed info about a student for a specific subject.

        Args:
            student_id: Student identifier
            class_id: Class identifier
            subject: Subject name

        Returns:
            Dict with average_grade, level, skipped_lessons, problematic_topics
            or None if student not found
        """
        if self.scores_df is None or self.scores_df.empty:
            return None

        # Get student's scores for this class/subject
        mask = (
            (self.scores_df["student_id"] == student_id) &
            (self.scores_df["class_id"] == class_id) &
            (self.scores_df["discipline_name"] == subject)
        )
        student_scores = self.scores_df[mask]

        if student_scores.empty:
            return None

        # Get from pre-computed index
        class_students = self.get_class_students(class_id, subject)
        student_summary = next(
            (s for s in class_students if s.student_id == student_id),
            None
        )

        if student_summary is None:
            return None

        # Get skipped lessons
        skipped_lessons = self._get_skipped_lessons(student_id, class_id, subject)

        # Get problematic topics (topics with low scores)
        problematic_topics = self._get_problematic_topics(student_scores)

        return {
            "average_subject_grade": student_summary.average_subject_grade,
            "level": student_summary.subject_level,
            "skipped_lessons": skipped_lessons,
            "problematic_topics": problematic_topics
        }

    def _get_skipped_lessons(
        self,
        student_id: int,
        class_id: int,
        subject: str
    ) -> list[SkippedLesson]:
        """Get list of lessons skipped by a student."""
        if self.absences_df is None or self.absences_df.empty:
            return []

        mask = (
            (self.absences_df["student_id"] == student_id) &
            (self.absences_df["class_id"] == class_id) &
            (self.absences_df["discipline_name"] == subject)
        )
        absences = self.absences_df[mask]

        skipped = []
        for _, row in absences.iterrows():
            # Handle date conversion
            date_val = row.get("lesson_date", "")
            if pd.notna(date_val):
                if hasattr(date_val, "strftime"):
                    date_str = date_val.strftime("%Y-%m-%d")
                else:
                    date_str = str(date_val)
            else:
                date_str = ""

            skipped.append(
                SkippedLesson(
                    date=date_str,
                    topic=str(row.get("topic_name", ""))
                )
            )

        return skipped

    def _get_problematic_topics(
        self,
        student_scores: pd.DataFrame
    ) -> list[ProblematicTopic]:
        """
        Get topics where student scores below average.

        Problematic = average score for topic is below 6 (50% on 0-12 scale)
        """
        if student_scores.empty:
            return []

        # Group by topic and calculate average
        topic_avgs = student_scores.groupby("topic_name")["score_numeric"].mean()

        # Filter topics with avg below 6
        problematic = []
        for topic, avg in topic_avgs.items():
            if avg < 6:  # Below 50%
                problematic.append(
                    ProblematicTopic(
                        topic=str(topic),
                        average_score=round(float(avg), 2)
                    )
                )

        # Sort by score (worst first)
        problematic.sort(key=lambda p: p.average_score)
        return problematic

    def _get_good_topics(
        self,
        student_scores: pd.DataFrame
    ) -> list[str]:
        """
        Get topics where student scores well (>= 10).

        Used for EP6 recommendation to highlight strengths.
        """
        if student_scores.empty:
            return []

        # Group by topic and calculate average
        topic_avgs = student_scores.groupby("topic_name")["score_numeric"].mean()

        # Filter topics with avg >= 10
        good_topics = [
            str(topic) for topic, avg in topic_avgs.items()
            if avg >= 10
        ]

        return sorted(good_topics)

    def _get_missed_topics(
        self,
        student_id: int,
        class_id: int,
        subject: str
    ) -> list[str]:
        """
        Get topics from missed lessons.

        Used for EP6 recommendation to suggest catching up.
        """
        skipped = self._get_skipped_lessons(student_id, class_id, subject)
        return [lesson.topic for lesson in skipped if lesson.topic]

    # =========================================================================
    # EP6: Get Student Recommendation Data
    # =========================================================================

    def get_student_recommendation_data(
        self,
        student_id: int,
        subject: str
    ) -> Optional[dict]:
        """
        Get all data needed for EP6 recommendation generation.

        Args:
            student_id: Student identifier
            subject: Subject name

        Returns:
            Dict with average_grade, level, good_topics, bad_topics, missed_topics
            or None if student not found
        """
        if self.scores_df is None or self.scores_df.empty:
            return None

        # Get student info to find their class
        student_info = self.get_student_info(student_id)
        if student_info is None:
            return None

        class_id = student_info["class_id"]

        # Check if student has this subject
        if subject not in student_info["subjects"]:
            return None

        # Get student's scores for this subject
        mask = (
            (self.scores_df["student_id"] == student_id) &
            (self.scores_df["class_id"] == class_id) &
            (self.scores_df["discipline_name"] == subject)
        )
        student_scores = self.scores_df[mask]

        if student_scores.empty:
            return None

        # Get from pre-computed index
        class_students = self.get_class_students(class_id, subject)
        student_summary = next(
            (s for s in class_students if s.student_id == student_id),
            None
        )

        if student_summary is None:
            return None

        # Get topics
        good_topics = self._get_good_topics(student_scores)
        problematic_topics = self._get_problematic_topics(student_scores)
        bad_topics = [t.topic for t in problematic_topics]
        missed_topics = self._get_missed_topics(student_id, class_id, subject)

        return {
            "average_grade": student_summary.average_subject_grade,
            "level": student_summary.subject_level.value,
            "good_topics": good_topics,
            "bad_topics": bad_topics,
            "missed_topics": missed_topics
        }

    # =========================================================================
    # EP8: Get Student Info
    # =========================================================================

    def get_student_info(self, student_id: int) -> Optional[dict]:
        """
        Get student's class and subjects.

        Args:
            student_id: Student identifier

        Returns:
            Dict with class_id, class_number, and subjects list
            or None if student not found
        """
        if self.scores_df is None or self.scores_df.empty:
            return None

        # Get all records for this student
        student_data = self.scores_df[self.scores_df["student_id"] == student_id]

        if student_data.empty:
            return None

        # Get class info (assume student is in one class)
        class_id = int(student_data["class_id"].iloc[0])
        class_number = int(student_data["grade"].iloc[0])

        # Get unique subjects
        subjects = student_data["discipline_name"].unique().tolist()

        return {
            "class_id": class_id,
            "class_number": class_number,
            "subjects": sorted(subjects)
        }

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def teacher_exists(self, teacher_id: int) -> bool:
        """Check if teacher exists in data."""
        return teacher_id in self._teacher_classes

    def student_exists(self, student_id: int) -> bool:
        """Check if student exists in data."""
        if self.scores_df is None or self.scores_df.empty:
            return False
        return student_id in self.scores_df["student_id"].values

    def get_all_teacher_ids(self) -> list[int]:
        """Get list of all teacher IDs in data."""
        return sorted(self._teacher_classes.keys())

    def get_all_student_ids(self) -> list[int]:
        """Get list of all student IDs in data."""
        if self.scores_df is None or self.scores_df.empty:
            return []
        return sorted(self.scores_df["student_id"].unique().tolist())

    def get_class_info(self, class_id: int) -> Optional[dict]:
        """
        Get class info by class_id.

        Returns:
            dict with 'class_id', 'class_number' or None if not found.
        """
        if self.scores_df is None or self.scores_df.empty:
            return None

        class_data = self.scores_df[self.scores_df["class_id"] == class_id]
        if class_data.empty:
            return None

        # Get class_number (grade) from the first matching row
        class_number = int(class_data["grade"].iloc[0])

        return {
            "class_id": class_id,
            "class_number": class_number
        }

    def get_level_gap_warnings(
        self,
        class_id: int,
        subject: str,
        level: str
    ) -> list[str]:
        """
        Get problematic topics for students at a given level in a class.

        Used for EP3.1 to warn teachers about common gaps.

        Args:
            class_id: Class ID
            subject: Subject name
            level: Student level (weak/medium/strong)

        Returns:
            List of topic names that students at this level struggle with.
        """
        if self.scores_df is None or self.scores_df.empty:
            return []

        # Get students in this class/subject at the specified level
        students = self.get_class_students(class_id, subject)
        if not students:
            return []

        # Filter to students at the specified level
        level_students = [s for s in students if s.subject_level.value == level]
        if not level_students:
            return []

        student_ids = [s.student_id for s in level_students]

        # Get scores for these students
        # Note: column is 'discipline_name' in scores_df
        mask = (
            (self.scores_df["class_id"] == class_id) &
            (self.scores_df["discipline_name"] == subject) &
            (self.scores_df["student_id"].isin(student_ids))
        )
        level_scores = self.scores_df[mask]

        if level_scores.empty:
            return []

        # Find topics with low average scores (< 6)
        # Note: column is 'score_numeric' in scores_df
        topic_scores = level_scores.groupby("topic_name")["score_numeric"].mean()
        problematic = topic_scores[topic_scores < 6].sort_values()

        # Return top 5 problematic topics
        return problematic.head(5).index.tolist()


# Singleton instance for app-wide use
_data_loader: Optional[DataLoader] = None


def get_data_loader() -> DataLoader:
    """Get or create the singleton DataLoader instance."""
    global _data_loader
    if _data_loader is None:
        _data_loader = DataLoader()
    return _data_loader
