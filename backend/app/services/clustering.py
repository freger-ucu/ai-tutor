"""
Clustering Service (T5)

Clusters students into weak/medium/strong groups based on grades.

Algorithm:
1. Get all students in a class for a subject
2. Calculate average score per student (already done by DataLoader)
3. Compute Q1 (25th percentile) and Q3 (75th percentile)
4. Assign clusters:
   - weak: score < Q1
   - medium: Q1 <= score <= Q3
   - strong: score > Q3
"""

from typing import Optional

from app.models.domain import (
    ClusterAssignment,
    ClusterDistribution,
    StudentCluster,
    StudentSummary,
)
from app.models.enums import Level
from app.services.data_loader import DataLoader, get_data_loader


class ClusteringService:
    """
    Service for clustering students by performance.

    Uses quartile-based clustering:
    - weak: bottom 25% (score < Q1)
    - medium: middle 50% (Q1 <= score <= Q3)
    - strong: top 25% (score > Q3)
    """

    def __init__(self, data_loader: Optional[DataLoader] = None):
        """
        Initialize ClusteringService.

        Args:
            data_loader: DataLoader instance. Uses singleton if not provided.
        """
        self._data_loader = data_loader

    @property
    def data_loader(self) -> DataLoader:
        """Get DataLoader (lazy initialization)."""
        if self._data_loader is None:
            self._data_loader = get_data_loader()
        return self._data_loader

    def cluster_students(
        self,
        class_id: int,
        subject: str
    ) -> list[StudentCluster]:
        """
        Cluster all students in a class by performance.

        Args:
            class_id: Class identifier
            subject: Subject name

        Returns:
            List of 3 StudentCluster objects (weak, medium, strong)
        """
        students = self.data_loader.get_class_students(class_id, subject)

        # Initialize empty clusters
        clusters = {
            Level.WEAK: [],
            Level.MEDIUM: [],
            Level.STRONG: [],
        }

        if not students:
            # Return empty clusters
            return [
                StudentCluster(
                    cluster_type=level,
                    student_ids=[],
                    avg_score=0.0,
                    score_range=(0.0, 0.0)
                )
                for level in [Level.WEAK, Level.MEDIUM, Level.STRONG]
            ]

        # Get scores for quartile calculation
        scores = [s.average_subject_grade for s in students]

        # Calculate quartiles
        q1, q3 = self._compute_quartiles(scores)

        # Assign students to clusters
        for student in students:
            level = self._assign_cluster(student.average_subject_grade, q1, q3)
            clusters[level].append(student)

        # Build result
        result = []
        for level in [Level.WEAK, Level.MEDIUM, Level.STRONG]:
            cluster_students = clusters[level]
            if cluster_students:
                cluster_scores = [s.average_subject_grade for s in cluster_students]
                result.append(
                    StudentCluster(
                        cluster_type=level,
                        student_ids=[s.student_id for s in cluster_students],
                        avg_score=round(sum(cluster_scores) / len(cluster_scores), 2),
                        score_range=(min(cluster_scores), max(cluster_scores))
                    )
                )
            else:
                result.append(
                    StudentCluster(
                        cluster_type=level,
                        student_ids=[],
                        avg_score=0.0,
                        score_range=(0.0, 0.0)
                    )
                )

        return result

    def get_cluster_for_student(
        self,
        student_id: int,
        class_id: int,
        subject: str
    ) -> Optional[ClusterAssignment]:
        """
        Get cluster assignment for a specific student.

        Args:
            student_id: Student identifier
            class_id: Class identifier
            subject: Subject name

        Returns:
            ClusterAssignment or None if student not found
        """
        students = self.data_loader.get_class_students(class_id, subject)

        if not students:
            return None

        # Find the student
        student = next((s for s in students if s.student_id == student_id), None)
        if student is None:
            return None

        # Get all scores for percentile calculation
        scores = sorted([s.average_subject_grade for s in students])
        q1, q3 = self._compute_quartiles(scores)

        # Calculate percentile
        percentile = self._calculate_percentile(student.average_subject_grade, scores)

        # Determine cluster
        cluster_type = self._assign_cluster(student.average_subject_grade, q1, q3)

        return ClusterAssignment(
            student_id=student_id,
            cluster_type=cluster_type,
            avg_score=student.average_subject_grade,
            percentile=round(percentile, 1)
        )

    def get_cluster_distribution(
        self,
        class_id: int,
        subject: str
    ) -> ClusterDistribution:
        """
        Get distribution of students across clusters.

        Args:
            class_id: Class identifier
            subject: Subject name

        Returns:
            ClusterDistribution with counts and percentages
        """
        clusters = self.cluster_students(class_id, subject)

        weak = next(c for c in clusters if c.cluster_type == Level.WEAK)
        medium = next(c for c in clusters if c.cluster_type == Level.MEDIUM)
        strong = next(c for c in clusters if c.cluster_type == Level.STRONG)

        total = len(weak.student_ids) + len(medium.student_ids) + len(strong.student_ids)

        if total == 0:
            return ClusterDistribution(
                weak_count=0,
                medium_count=0,
                strong_count=0,
                weak_percentage=0.0,
                medium_percentage=0.0,
                strong_percentage=0.0,
                total_count=0
            )

        return ClusterDistribution(
            weak_count=len(weak.student_ids),
            medium_count=len(medium.student_ids),
            strong_count=len(strong.student_ids),
            weak_percentage=round(len(weak.student_ids) / total * 100, 1),
            medium_percentage=round(len(medium.student_ids) / total * 100, 1),
            strong_percentage=round(len(strong.student_ids) / total * 100, 1),
            total_count=total
        )

    def _compute_quartiles(self, scores: list[float]) -> tuple[float, float]:
        """
        Compute Q1 (25th percentile) and Q3 (75th percentile).

        Args:
            scores: List of scores

        Returns:
            Tuple of (Q1, Q3)
        """
        if not scores:
            return 0.0, 0.0

        sorted_scores = sorted(scores)
        n = len(sorted_scores)

        if n == 1:
            # Single score: Q1 = Q3 = score
            return sorted_scores[0], sorted_scores[0]

        # Q1: 25th percentile
        q1_idx = (n - 1) * 0.25
        q1_lower = int(q1_idx)
        q1_frac = q1_idx - q1_lower
        if q1_lower + 1 < n:
            q1 = sorted_scores[q1_lower] * (1 - q1_frac) + sorted_scores[q1_lower + 1] * q1_frac
        else:
            q1 = sorted_scores[q1_lower]

        # Q3: 75th percentile
        q3_idx = (n - 1) * 0.75
        q3_lower = int(q3_idx)
        q3_frac = q3_idx - q3_lower
        if q3_lower + 1 < n:
            q3 = sorted_scores[q3_lower] * (1 - q3_frac) + sorted_scores[q3_lower + 1] * q3_frac
        else:
            q3 = sorted_scores[q3_lower]

        return q1, q3

    def _assign_cluster(self, score: float, q1: float, q3: float) -> Level:
        """
        Assign a cluster based on score and quartiles.

        Args:
            score: Student's score
            q1: First quartile
            q3: Third quartile

        Returns:
            Level (WEAK, MEDIUM, or STRONG)
        """
        if score < q1:
            return Level.WEAK
        elif score > q3:
            return Level.STRONG
        else:
            return Level.MEDIUM

    def _calculate_percentile(self, score: float, sorted_scores: list[float]) -> float:
        """
        Calculate percentile rank of a score.

        Args:
            score: The score to rank
            sorted_scores: All scores in sorted order

        Returns:
            Percentile (0-100)
        """
        if not sorted_scores:
            return 50.0

        n = len(sorted_scores)
        count_below = sum(1 for s in sorted_scores if s < score)
        count_equal = sum(1 for s in sorted_scores if s == score)

        # Percentile formula: (count_below + 0.5 * count_equal) / n * 100
        percentile = (count_below + 0.5 * count_equal) / n * 100
        return percentile


# Singleton instance
_clustering_service: Optional[ClusteringService] = None


def get_clustering_service() -> ClusteringService:
    """Get or create the singleton ClusteringService instance."""
    global _clustering_service
    if _clustering_service is None:
        _clustering_service = ClusteringService()
    return _clustering_service
