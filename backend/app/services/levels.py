"""
Level Computation Utilities

Centralized quartile-based level assignment for students.

Algorithm (from architecture.md):
- weak: score < Q1 (25th percentile)
- medium: Q1 <= score <= Q3
- strong: score > Q3 (75th percentile)
"""

from typing import Sequence

from app.models.enums import Level


def compute_quartiles(scores: Sequence[float]) -> tuple[float, float]:
    """
    Compute Q1 (25th percentile) and Q3 (75th percentile).

    Args:
        scores: Sequence of numeric scores

    Returns:
        Tuple of (Q1, Q3)
    """
    if not scores:
        return 0.0, 0.0

    sorted_scores = sorted(scores)
    n = len(sorted_scores)

    if n == 1:
        return sorted_scores[0], sorted_scores[0]

    # Q1: 25th percentile using linear interpolation
    q1_idx = (n - 1) * 0.25
    q1_lower = int(q1_idx)
    q1_frac = q1_idx - q1_lower
    if q1_lower + 1 < n:
        q1 = sorted_scores[q1_lower] * (1 - q1_frac) + sorted_scores[q1_lower + 1] * q1_frac
    else:
        q1 = sorted_scores[q1_lower]

    # Q3: 75th percentile using linear interpolation
    q3_idx = (n - 1) * 0.75
    q3_lower = int(q3_idx)
    q3_frac = q3_idx - q3_lower
    if q3_lower + 1 < n:
        q3 = sorted_scores[q3_lower] * (1 - q3_frac) + sorted_scores[q3_lower + 1] * q3_frac
    else:
        q3 = sorted_scores[q3_lower]

    return q1, q3


def assign_level(score: float, q1: float, q3: float) -> Level:
    """
    Assign level based on score and quartile thresholds.

    Args:
        score: Student's score
        q1: First quartile (25th percentile)
        q3: Third quartile (75th percentile)

    Returns:
        Level.WEAK if score < Q1
        Level.STRONG if score > Q3
        Level.MEDIUM otherwise
    """
    if score < q1:
        return Level.WEAK
    elif score > q3:
        return Level.STRONG
    else:
        return Level.MEDIUM


def compute_level(score: float, all_scores: Sequence[float]) -> Level:
    """
    Compute level for a score given all scores in the group.

    Convenience function that computes quartiles and assigns level.

    Args:
        score: Student's score to classify
        all_scores: All scores in the comparison group

    Returns:
        Level enum value
    """
    q1, q3 = compute_quartiles(all_scores)
    return assign_level(score, q1, q3)


def compute_median_level(selected_scores: Sequence[float], all_scores: Sequence[float]) -> str:
    """
    Compute median level for selected students relative to class.

    Takes the median score of selected students and compares it to
    class quartiles to determine level.

    Args:
        selected_scores: Scores of selected students
        all_scores: All scores in the class (for quartile computation)

    Returns:
        Level string: "weak" | "medium" | "strong"
    """
    if not selected_scores:
        return "medium"

    # Get median score of selected students
    sorted_selected = sorted(selected_scores)
    n = len(sorted_selected)
    if n % 2 == 0:
        median = (sorted_selected[n // 2 - 1] + sorted_selected[n // 2]) / 2
    else:
        median = sorted_selected[n // 2]

    # Compare to class quartiles
    q1, q3 = compute_quartiles(all_scores)

    return assign_level(median, q1, q3).value


def calculate_percentile(score: float, sorted_scores: Sequence[float]) -> float:
    """
    Calculate percentile rank of a score.

    Args:
        score: The score to rank
        sorted_scores: All scores (will be sorted if not already)

    Returns:
        Percentile (0-100)
    """
    if not sorted_scores:
        return 50.0

    scores = sorted(sorted_scores)
    n = len(scores)
    count_below = sum(1 for s in scores if s < score)
    count_equal = sum(1 for s in scores if s == score)

    # Percentile formula: (count_below + 0.5 * count_equal) / n * 100
    return (count_below + 0.5 * count_equal) / n * 100
