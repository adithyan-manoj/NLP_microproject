#!/usr/bin/env python3
"""
CLI Script to execute NLP and Retrieval Evaluation Benchmark for CricInsight.
Evaluates Intent Accuracy, Entity Resolution, Format Normalization, Latency,
and Fallback Frequency across providers.
"""

import sys
import asyncio
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.evaluation.benchmark_runner import BenchmarkRunner

async def main():
    print(f"==================================================")
    print(f"  CRICINSIGHT — NLP EVALUATION BENCHMARK RUNNER")
    print(f"==================================================")
    print(f"Running labelled questions benchmark...\n")

    summary = await BenchmarkRunner.run_evaluation()

    print(f"--- Benchmark Results ---")
    print(f"Questions Evaluated:      {summary.get('total_benchmark_questions')}")
    print(f"Intent Accuracy:          {summary.get('intent_accuracy')}%")
    print(f"Entity Precision:         {summary.get('entity_precision')}%")
    print(f"Entity Recall:            {summary.get('entity_recall')}%")
    print(f"Entity F1-Score:          {summary.get('entity_f1')}%")
    print(f"Format Accuracy:          {summary.get('format_accuracy')}%")
    print(f"Clarification Accuracy:   {summary.get('clarification_accuracy')}%")
    print(f"Average Latency:          {summary.get('average_latency_ms')} ms")
    print(f"Fallback Frequency:       {summary.get('fallback_frequency')}%")
    print(f"Primary Provider:         {summary.get('primary_provider')}")
    print(f"Fallback Provider:        {summary.get('fallback_provider')}")
    print(f"==================================================\n")

if __name__ == "__main__":
    asyncio.run(main())
