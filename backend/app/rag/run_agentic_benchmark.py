#!/usr/bin/env python3
"""
Agentic RAG Benchmark Runner

Usage:
    # Full benchmark (V4 Enhanced)
    python scripts/agentic_rag_solution/run_agentic_benchmark.py

    # Limited test
    python scripts/agentic_rag_solution/run_agentic_benchmark.py --limit 20

    # Single subject
    python scripts/agentic_rag_solution/run_agentic_benchmark.py --subject "Українська мова"

    # Single question test
    python scripts/agentic_rag_solution/run_agentic_benchmark.py --test --question-idx 0
"""

import os
import sys
import asyncio
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict

import pandas as pd
from tqdm import tqdm

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set working directory for data loading
os.chdir(project_root)

from scripts.agentic_rag_solution.graph import solve_question, solve_question_with_state
from scripts.agentic_rag_solution.utils.data_loader import get_data_loader


async def run_benchmark(
    limit: Optional[int] = None,
    subject_filter: Optional[str] = None,
    grade_filter: Optional[int] = None,
    output_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run the full benchmark evaluation.

    Args:
        limit: Maximum number of questions to evaluate
        subject_filter: Filter by subject name
        grade_filter: Filter by grade
        output_path: Path to save results CSV

    Returns:
        Dict with evaluation metrics
    """
    version = "V4-ENHANCED"

    print("\n" + "=" * 60)
    print(f"  AGENTIC RAG BENCHMARK ({version})")
    print("=" * 60)

    # Load questions
    data_loader = get_data_loader()
    questions_df = data_loader.load_benchmark_questions()

    # Apply filters
    if subject_filter:
        questions_df = questions_df[questions_df["global_discipline_name"] == subject_filter]
        print(f"  Filtered by subject: {subject_filter}")

    if grade_filter:
        questions_df = questions_df[questions_df["grade"] == grade_filter]
        print(f"  Filtered by grade: {grade_filter}")

    if limit:
        questions_df = questions_df.head(limit)
        print(f"  Limited to: {limit} questions")

    total_questions = len(questions_df)
    print(f"  Total questions: {total_questions}")
    print("=" * 60 + "\n")

    # Metrics tracking
    correct = 0
    total = 0
    results = []
    subject_metrics = defaultdict(lambda: {"correct": 0, "total": 0, "llm_calls": 0})
    grade_metrics = defaultdict(lambda: {"correct": 0, "total": 0})
    total_llm_calls = 0

    # Process questions
    for idx, row in tqdm(questions_df.iterrows(), total=total_questions, desc="Evaluating"):
        question = row.to_dict()

        # Solve question
        result = await solve_question(question)

        # Check correctness
        correct_indices = question.get("correct_answer_indices", [])
        is_correct = result.answer_index in correct_indices

        if is_correct:
            correct += 1
            subject_metrics[question["global_discipline_name"]]["correct"] += 1
            grade_metrics[question["grade"]]["correct"] += 1

        total += 1
        subject_metrics[question["global_discipline_name"]]["total"] += 1
        subject_metrics[question["global_discipline_name"]]["llm_calls"] += result.llm_calls
        grade_metrics[question["grade"]]["total"] += 1
        total_llm_calls += result.llm_calls

        # Store result
        results.append({
            "question_id": question.get("question_id"),
            "subject": question.get("global_discipline_name"),
            "grade": question.get("grade"),
            "predicted": result.answer_index,
            "correct": correct_indices[0] if correct_indices else -1,
            "is_correct": is_correct,
            "confidence": result.confidence,
            "llm_calls": result.llm_calls,
            "reasoning": result.reasoning if result.reasoning else "",
        })

    # Calculate metrics
    accuracy = correct / total if total > 0 else 0
    avg_llm_calls = total_llm_calls / total if total > 0 else 0

    # Print results
    print("\n" + "=" * 60)
    print("  RESULTS")
    print("=" * 60)
    print(f"\n  OVERALL ACCURACY: {accuracy:.1%} ({correct}/{total})")
    print(f"  AVG LLM CALLS: {avg_llm_calls:.2f} per question")
    print(f"  TOTAL LLM CALLS: {total_llm_calls}")

    print("\n  BY SUBJECT:")
    for subject, metrics in sorted(subject_metrics.items()):
        subj_acc = metrics["correct"] / metrics["total"] if metrics["total"] > 0 else 0
        avg_calls = metrics["llm_calls"] / metrics["total"] if metrics["total"] > 0 else 0
        print(f"    {subject}: {subj_acc:.1%} ({metrics['correct']}/{metrics['total']}) | avg calls: {avg_calls:.1f}")

    print("\n  BY GRADE:")
    for grade, metrics in sorted(grade_metrics.items()):
        grade_acc = metrics["correct"] / metrics["total"] if metrics["total"] > 0 else 0
        print(f"    Grade {grade}: {grade_acc:.1%} ({metrics['correct']}/{metrics['total']})")

    # Save results
    if output_path:
        results_df = pd.DataFrame(results)
        results_df.to_csv(output_path, index=False)
        print(f"\n  Results saved to: {output_path}")

    print("\n" + "=" * 60)

    return {
        "accuracy": accuracy,
        "correct": correct,
        "total": total,
        "avg_llm_calls": avg_llm_calls,
        "subject_metrics": dict(subject_metrics),
        "grade_metrics": dict(grade_metrics),
        "results": results,
    }


async def test_single_question(
    question_idx: Optional[int] = None,
    question_id: Optional[str] = None,
) -> None:
    """
    Test a single question with detailed output.
    """
    version = "V4-ENHANCED"

    print("\n" + "=" * 60)
    print(f"  SINGLE QUESTION TEST ({version})")
    print("=" * 60)

    data_loader = get_data_loader()

    if question_id:
        question = data_loader.get_question_by_id(question_id)
    else:
        question = data_loader.get_question_by_index(question_idx or 0)

    if not question:
        print("Question not found!")
        return

    print(f"\n  Question ID: {question.get('question_id')}")
    print(f"  Subject: {question.get('global_discipline_name')}")
    print(f"  Grade: {question.get('grade')}")
    print(f"\n  Text: {question.get('question_text')}")
    print(f"\n  Answers:")
    for i, ans in enumerate(question.get('answers', [])):
        marker = "→" if i in question.get('correct_answer_indices', []) else " "
        print(f"    {marker} {i}) {ans}")

    print("\n" + "-" * 60)
    print("  SOLVING...")
    print("-" * 60)

    # Get full state for debugging
    state = await solve_question_with_state(question)

    print(f"\n  Retrieved docs: {len(state.get('retrieved_docs', []))}")
    print(f"  Retrieval score: {state.get('retrieval_score', 0):.3f}")
    print(f"  Context quality: {state.get('context_quality', 0):.3f}")
    print(f"  Agent decision: {state.get('agent_decision', 'N/A')}")
    print(f"  Question type: {state.get('question_type', 'N/A')}")
    print(f"  Complexity: {state.get('complexity', 'N/A')}")
    print(f"  Retry count: {state.get('retry_count', 0)}")

    print(f"\n  Final answer: {state.get('final_answer_index', 'N/A')}")
    print(f"  Confidence: {state.get('final_confidence', 0):.2f}")
    print(f"  Used SC: {state.get('used_self_consistency', False)}")
    print(f"  LLM calls: {state.get('llm_calls_count', 0)}")

    correct_indices = question.get('correct_answer_indices', [])
    is_correct = state.get('final_answer_index', -1) in correct_indices
    print(f"\n  RESULT: {'✓ CORRECT' if is_correct else '✗ WRONG'}")

    print(f"\n  Reasoning:\n{state.get('final_reasoning', 'N/A')}")

    if state.get('error_message'):
        print(f"\n  Error: {state.get('error_message')}")

    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Agentic RAG Benchmark Runner")
    parser.add_argument("--limit", type=int, help="Limit number of questions")
    parser.add_argument("--subject", type=str, help="Filter by subject")
    parser.add_argument("--grade", type=int, help="Filter by grade")
    parser.add_argument("--output", type=str, help="Output CSV path")
    parser.add_argument("--test", action="store_true", help="Test single question mode")
    parser.add_argument("--question-idx", type=int, help="Question index for test mode")
    parser.add_argument("--question-id", type=str, help="Question ID for test mode")

    args = parser.parse_args()

    if args.test:
        asyncio.run(test_single_question(
            question_idx=args.question_idx,
            question_id=args.question_id,
        ))
    else:
        # Generate default output path
        output_path = args.output
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"agentic_rag_v4_results_{timestamp}.csv"

        asyncio.run(run_benchmark(
            limit=args.limit,
            subject_filter=args.subject,
            grade_filter=args.grade,
            output_path=output_path,
        ))


if __name__ == "__main__":
    main()
