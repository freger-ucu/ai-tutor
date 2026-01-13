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
)
from app.models.enums import Level
from app.services.data_loader import DataLoader, get_data_loader
from app.services.levels import compute_quartiles, assign_level, calculate_percentile


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

        # Calculate quartiles using shared utility
        q1, q3 = compute_quartiles(scores)

        # Assign students to clusters using shared utility
        for student in students:
            level = assign_level(student.average_subject_grade, q1, q3)
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
        scores = [s.average_subject_grade for s in students]
        q1, q3 = compute_quartiles(scores)

        # Calculate percentile using shared utility
        percentile = calculate_percentile(student.average_subject_grade, scores)

        # Determine cluster using shared utility
        cluster_type = assign_level(student.average_subject_grade, q1, q3)

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


# Singleton instance
_clustering_service: Optional[ClusteringService] = None


def get_clustering_service() -> ClusteringService:
    """Get or create the singleton ClusteringService instance."""
    global _clustering_service
    if _clustering_service is None:
        _clustering_service = ClusteringService()
    return _clustering_service
