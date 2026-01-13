#!/usr/bin/env python3
"""
Compare different LLM models on the benchmark.

Usage:
    python scripts/agentic_rag_solution/compare_models.py --limit 20
"""

import os
import sys
import asyncio
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from collections import defaultdict

import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

# Load .env file
load_dotenv()

from openai import AsyncOpenAI
from scripts.agentic_rag_solution.utils.data_loader import get_data_loader
from scripts.agentic_rag_solution.state import create_initial_state
from scripts.agentic_rag_solution.nodes.smart_retrieve import smart_retrieve_node


# Model configurations
MODELS = {
    "mamay": {
        "api_key": os.getenv("API_KEY", "sk-VbzOVVk7InXaN-9t9BM60g"),
        "base_url": "http://146.59.127.106:4000",
        "model": "mamay",
    },
    "gpt-5-mini": {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-5-mini",
    },
}


PROMPT_TEMPLATE = """Ти — експерт з {subject}.

{context}

## ПИТАННЯ ({grade} клас):
{question}

## ВАРІАНТИ:
{options}

Проаналізуй кожен варіант і обери правильний.
Поверни JSON: {{"answer": 0-3, "reasoning": "пояснення"}}"""


async def test_model(
    model_name: str,
    questions_df: pd.DataFrame,
) -> Dict[str, Any]:
    """Test a single model on all questions."""

    config = MODELS[model_name]

    if not config["api_key"]:
        print(f"  ERROR: No API key for {model_name}")
        return {"error": f"No API key for {model_name}"}

    client = AsyncOpenAI(
        api_key=config["api_key"],
        base_url=config["base_url"],
    )

    correct = 0
    total = len(questions_df)
    subject_metrics = defaultdict(lambda: {"correct": 0, "total": 0})
    results = []

    for idx, row in tqdm(questions_df.iterrows(), total=total, desc=f"  {model_name}", leave=False):
        question = row.to_dict()

        # Get retrieval context (same for all models)
        state = create_initial_state(question)
        retrieval_result = await smart_retrieve_node(state)
        context_text = retrieval_result.get("context_text", "")

        # Format prompt
        answers = question.get("answers", [])
        options = "\n".join([f"{i}) {ans}" for i, ans in enumerate(answers)])

        prompt = PROMPT_TEMPLATE.format(
            subject=question.get("global_discipline_name", ""),
            context=context_text if context_text else "Контекст не знайдено.",
            grade=question.get("grade", ""),
            question=question.get("question_text", ""),
            options=options,
        )

        # Call model
        try:
            # gpt-5-mini: max_completion_tokens, no temperature (only default 1)
            if "gpt-5" in config["model"]:
                response = await client.chat.completions.create(
                    model=config["model"],
                    messages=[{"role": "user", "content": prompt}],
                    max_completion_tokens=500,
                    response_format={"type": "json_object"},
                )
            else:
                response = await client.chat.completions.create(
                    model=config["model"],
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    max_tokens=500,
                    response_format={"type": "json_object"},
                )
            result_text = response.choices[0].message.content

            # Parse JSON
            import json
            try:
                result = json.loads(result_text)
                answer_index = result.get("answer", 0)
            except:
                answer_index = 0

        except Exception as e:
            print(f"    Error: {e}")
            answer_index = 0

        # Check correctness
        correct_indices = question.get("correct_answer_indices", [])
        is_correct = answer_index in correct_indices

        if is_correct:
            correct += 1
            subject_metrics[question["global_discipline_name"]]["correct"] += 1
        subject_metrics[question["global_discipline_name"]]["total"] += 1

        results.append({
            "question_id": question.get("question_id"),
            "subject": question.get("global_discipline_name"),
            "predicted": answer_index,
            "correct": correct_indices[0] if correct_indices else -1,
            "is_correct": is_correct,
        })

    accuracy = correct / total if total > 0 else 0

    return {
        "model": model_name,
        "accuracy": accuracy,
        "correct": correct,
        "total": total,
        "subject_metrics": dict(subject_metrics),
        "results": results,
    }


async def compare_models(
    limit: int = 20,
    models_to_test: Optional[list] = None,
) -> Dict[str, Any]:
    """Compare multiple models on the benchmark."""

    print("\n" + "=" * 70)
    print("  MODEL COMPARISON")
    print("=" * 70)

    # Load questions
    data_loader = get_data_loader()
    questions_df = data_loader.load_benchmark_questions().head(limit)

    print(f"  Testing on {len(questions_df)} questions")

    if models_to_test is None:
        models_to_test = list(MODELS.keys())

    print(f"  Models: {models_to_test}")
    print("=" * 70 + "\n")

    # Test each model
    results = []
    for model_name in models_to_test:
        print(f"\nTesting: {model_name}")
        print("-" * 40)

        result = await test_model(model_name, questions_df)
        results.append(result)

        if "error" not in result:
            print(f"  Accuracy: {result['accuracy']:.1%} ({result['correct']}/{result['total']})")

            print("  By subject:")
            for subject, metrics in sorted(result["subject_metrics"].items()):
                subj_acc = metrics["correct"] / metrics["total"] if metrics["total"] > 0 else 0
                print(f"    {subject}: {subj_acc:.1%} ({metrics['correct']}/{metrics['total']})")

    # Summary
    print("\n" + "=" * 70)
    print("  COMPARISON SUMMARY")
    print("=" * 70)
    print(f"\n  {'Model':<20} {'Accuracy':>10} {'Correct':>10}")
    print("-" * 45)

    for r in sorted(results, key=lambda x: -x.get("accuracy", 0)):
        if "error" not in r:
            print(f"  {r['model']:<20} {r['accuracy']:>10.1%} {r['correct']:>7}/{r['total']}")
        else:
            print(f"  {r['model']:<20} {'ERROR':>10}")

    print("=" * 70)

    return {"results": results}


def main():
    parser = argparse.ArgumentParser(description="Compare LLM models")
    parser.add_argument("--limit", type=int, default=20, help="Number of questions")
    parser.add_argument("--models", nargs="+", help="Models to test")

    args = parser.parse_args()

    asyncio.run(compare_models(
        limit=args.limit,
        models_to_test=args.models,
    ))


if __name__ == "__main__":
    main()
