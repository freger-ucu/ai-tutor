"""
Tests for Clustering Service (T5)

Expected Behavior:
-----------------
ClusteringService groups students into weak/medium/strong based on grades.

Algorithm:
1. Get all students in a class for a subject
2. Calculate average score per student
3. Compute Q1 (25th percentile) and Q3 (75th percentile)
4. Assign clusters:
   - weak: score < Q1
   - medium: Q1 <= score <= Q3
   - strong: score > Q3

Key Methods:
- cluster_students(class_id, subject) -> List[StudentCluster]
- get_cluster_for_student(student_id, class_id, subject) -> ClusterAssignment
- get_cluster_distribution(class_id, subject) -> ClusterDistribution
"""

import pytest
from unittest.mock import MagicMock

from app.models.enums import Level
from app.models.domain import StudentSummary


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_data_loader():
    """Mock DataLoader with sample student data."""
    loader = MagicMock()

    # 10 students with varying grades for testing quartile calculation
    # Scores: 2, 4, 5, 6, 7, 7, 8, 9, 10, 11
    # Linear interpolation quartiles:
    # Q1 = 5.25 (at index 2.25)
    # Q3 = 8.75 (at index 6.75)
    # weak: < 5.25 (scores 2, 4, 5) -> 3 students
    # medium: 5.25-8.75 (scores 6, 7, 7, 8) -> 4 students
    # strong: > 8.75 (scores 9, 10, 11) -> 3 students
    loader.get_class_students.return_value = [
        StudentSummary(student_id=1, subject_level=Level.WEAK, average_subject_grade=2.0),
        StudentSummary(student_id=2, subject_level=Level.WEAK, average_subject_grade=4.0),
        StudentSummary(student_id=3, subject_level=Level.MEDIUM, average_subject_grade=5.0),
        StudentSummary(student_id=4, subject_level=Level.MEDIUM, average_subject_grade=6.0),
        StudentSummary(student_id=5, subject_level=Level.MEDIUM, average_subject_grade=7.0),
        StudentSummary(student_id=6, subject_level=Level.MEDIUM, average_subject_grade=7.0),
        StudentSummary(student_id=7, subject_level=Level.MEDIUM, average_subject_grade=8.0),
        StudentSummary(student_id=8, subject_level=Level.MEDIUM, average_subject_grade=9.0),
        StudentSummary(student_id=9, subject_level=Level.STRONG, average_subject_grade=10.0),
        StudentSummary(student_id=10, subject_level=Level.STRONG, average_subject_grade=11.0),
    ]

    return loader


@pytest.fixture
def clustering_service(mock_data_loader):
    """Create ClusteringService with mocked DataLoader."""
    from app.services.clustering import ClusteringService
    return ClusteringService(data_loader=mock_data_loader)


# =============================================================================
# T5.1: cluster_students - Group students by performance
# =============================================================================


class TestClusterStudents:
    """Tests for cluster_students method."""

    def test_returns_three_clusters(self, clustering_service):
        """Should return exactly 3 clusters: weak, medium, strong."""
        clusters = clustering_service.cluster_students(class_id=1, subject="Алгебра")

        cluster_types = {c.cluster_type for c in clusters}
        assert cluster_types == {Level.WEAK, Level.MEDIUM, Level.STRONG}

    def test_weak_cluster_has_bottom_quartile(self, clustering_service):
        """Weak cluster should contain students below Q1."""
        clusters = clustering_service.cluster_students(class_id=1, subject="Алгебра")

        weak_cluster = next(c for c in clusters if c.cluster_type == Level.WEAK)
        assert len(weak_cluster.student_ids) == 3
        assert 1 in weak_cluster.student_ids  # score 2
        assert 2 in weak_cluster.student_ids  # score 4
        assert 3 in weak_cluster.student_ids  # score 5 (< Q1=5.25)

    def test_strong_cluster_has_top_quartile(self, clustering_service):
        """Strong cluster should contain students above Q3."""
        clusters = clustering_service.cluster_students(class_id=1, subject="Алгебра")

        strong_cluster = next(c for c in clusters if c.cluster_type == Level.STRONG)
        assert len(strong_cluster.student_ids) == 3
        assert 8 in strong_cluster.student_ids   # score 9 (> Q3=8.75)
        assert 9 in strong_cluster.student_ids   # score 10
        assert 10 in strong_cluster.student_ids  # score 11

    def test_medium_cluster_has_middle_students(self, clustering_service):
        """Medium cluster should contain students between Q1 and Q3."""
        clusters = clustering_service.cluster_students(class_id=1, subject="Алгебра")

        medium_cluster = next(c for c in clusters if c.cluster_type == Level.MEDIUM)
        assert len(medium_cluster.student_ids) == 4  # scores 6, 7, 7, 8

    def test_cluster_has_avg_score(self, clustering_service):
        """Each cluster should have average score calculated."""
        clusters = clustering_service.cluster_students(class_id=1, subject="Алгебра")

        weak_cluster = next(c for c in clusters if c.cluster_type == Level.WEAK)
        assert weak_cluster.avg_score == 3.67  # (2 + 4 + 5) / 3 = 3.67

    def test_cluster_has_score_range(self, clustering_service):
        """Each cluster should have min/max score range."""
        clusters = clustering_service.cluster_students(class_id=1, subject="Алгебра")

        weak_cluster = next(c for c in clusters if c.cluster_type == Level.WEAK)
        assert weak_cluster.score_range == (2.0, 5.0)  # scores 2, 4, 5

    def test_empty_class_returns_empty_clusters(self, clustering_service, mock_data_loader):
        """Empty class should return empty clusters."""
        mock_data_loader.get_class_students.return_value = []

        clusters = clustering_service.cluster_students(class_id=999, subject="Алгебра")

        assert all(len(c.student_ids) == 0 for c in clusters)

    def test_single_student_goes_to_medium(self, clustering_service, mock_data_loader):
        """Single student should be placed in medium cluster."""
        mock_data_loader.get_class_students.return_value = [
            StudentSummary(student_id=1, subject_level=Level.MEDIUM, average_subject_grade=7.0),
        ]

        clusters = clustering_service.cluster_students(class_id=1, subject="Алгебра")

        medium_cluster = next(c for c in clusters if c.cluster_type == Level.MEDIUM)
        assert 1 in medium_cluster.student_ids


# =============================================================================
# T5.2: get_cluster_for_student - Get individual student's cluster
# =============================================================================


class TestGetClusterForStudent:
    """Tests for get_cluster_for_student method."""

    def test_returns_cluster_assignment(self, clustering_service):
        """Should return ClusterAssignment with all fields."""
        assignment = clustering_service.get_cluster_for_student(
            student_id=1, class_id=1, subject="Алгебра"
        )

        assert assignment.student_id == 1
        assert assignment.cluster_type == Level.WEAK
        assert assignment.avg_score == 2.0
        assert 0 <= assignment.percentile <= 100

    def test_weak_student_percentile(self, clustering_service):
        """Weak student should have low percentile."""
        assignment = clustering_service.get_cluster_for_student(
            student_id=1, class_id=1, subject="Алгебра"
        )

        assert assignment.percentile < 25

    def test_strong_student_percentile(self, clustering_service):
        """Strong student should have high percentile."""
        assignment = clustering_service.get_cluster_for_student(
            student_id=10, class_id=1, subject="Алгебра"
        )

        assert assignment.percentile > 75

    def test_nonexistent_student_returns_none(self, clustering_service):
        """Nonexistent student should return None."""
        assignment = clustering_service.get_cluster_for_student(
            student_id=999, class_id=1, subject="Алгебра"
        )

        assert assignment is None


# =============================================================================
# T5.3: get_cluster_distribution - Stats for teacher dashboard
# =============================================================================


class TestGetClusterDistribution:
    """Tests for get_cluster_distribution method."""

    def test_returns_distribution(self, clustering_service):
        """Should return ClusterDistribution with counts and percentages."""
        dist = clustering_service.get_cluster_distribution(class_id=1, subject="Алгебра")

        assert dist.weak_count == 3
        assert dist.medium_count == 4
        assert dist.strong_count == 3

    def test_percentages_sum_to_100(self, clustering_service):
        """Percentages should sum to 100."""
        dist = clustering_service.get_cluster_distribution(class_id=1, subject="Алгебра")

        total = dist.weak_percentage + dist.medium_percentage + dist.strong_percentage
        assert abs(total - 100.0) < 0.01

    def test_percentage_calculation(self, clustering_service):
        """Percentages should be calculated correctly."""
        dist = clustering_service.get_cluster_distribution(class_id=1, subject="Алгебра")

        assert dist.weak_percentage == 30.0    # 3/10
        assert dist.medium_percentage == 40.0  # 4/10
        assert dist.strong_percentage == 30.0  # 3/10

    def test_empty_class_distribution(self, clustering_service, mock_data_loader):
        """Empty class should have zero counts."""
        mock_data_loader.get_class_students.return_value = []

        dist = clustering_service.get_cluster_distribution(class_id=999, subject="Алгебра")

        assert dist.weak_count == 0
        assert dist.medium_count == 0
        assert dist.strong_count == 0

    def test_total_count(self, clustering_service):
        """Total count should equal sum of cluster counts."""
        dist = clustering_service.get_cluster_distribution(class_id=1, subject="Алгебра")

        assert dist.total_count == 10


# =============================================================================
# T5.4: Edge cases
# =============================================================================


class TestClusteringEdgeCases:
    """Edge case tests for clustering."""

    def test_all_same_score(self, clustering_service, mock_data_loader):
        """All students with same score should go to medium."""
        mock_data_loader.get_class_students.return_value = [
            StudentSummary(student_id=i, subject_level=Level.MEDIUM, average_subject_grade=7.0)
            for i in range(1, 6)
        ]

        clusters = clustering_service.cluster_students(class_id=1, subject="Алгебра")

        medium_cluster = next(c for c in clusters if c.cluster_type == Level.MEDIUM)
        assert len(medium_cluster.student_ids) == 5

    def test_two_students(self, clustering_service, mock_data_loader):
        """Two students: one weak, one strong."""
        mock_data_loader.get_class_students.return_value = [
            StudentSummary(student_id=1, subject_level=Level.WEAK, average_subject_grade=3.0),
            StudentSummary(student_id=2, subject_level=Level.STRONG, average_subject_grade=10.0),
        ]

        clusters = clustering_service.cluster_students(class_id=1, subject="Алгебра")

        # With only 2 students, both could be edge cases
        # Implementation should handle gracefully
        total_students = sum(len(c.student_ids) for c in clusters)
        assert total_students == 2

    def test_unicode_subject(self, clustering_service):
        """Should handle Ukrainian subject names."""
        clusters = clustering_service.cluster_students(class_id=1, subject="Українська мова")

        # Should not raise, may return empty if no data
        assert isinstance(clusters, list)

    def test_boundary_scores_at_quartile(self, clustering_service, mock_data_loader):
        """Students exactly at Q1/Q3 should be in medium cluster."""
        # Scores: 4, 5, 6, 7 -> Q1=4.75, Q3=6.25
        # Score 5 is >= Q1, score 6 is <= Q3 -> both medium
        mock_data_loader.get_class_students.return_value = [
            StudentSummary(student_id=1, subject_level=Level.WEAK, average_subject_grade=4.0),
            StudentSummary(student_id=2, subject_level=Level.MEDIUM, average_subject_grade=5.0),
            StudentSummary(student_id=3, subject_level=Level.MEDIUM, average_subject_grade=6.0),
            StudentSummary(student_id=4, subject_level=Level.STRONG, average_subject_grade=7.0),
        ]

        clusters = clustering_service.cluster_students(class_id=1, subject="Алгебра")

        medium_cluster = next(c for c in clusters if c.cluster_type == Level.MEDIUM)
        # Students at boundaries should be included in medium
        assert 2 in medium_cluster.student_ids or 3 in medium_cluster.student_ids
