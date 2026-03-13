#!/usr/bin/env python3
"""Generate and optionally apply description improvements from benchmark failures."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from common import parse_frontmatter, save_json, write_frontmatter, load_json


def keyword_candidates(prompt: str) -> list[str]:
    cleaned = re.sub(r"[^a-z0-9\s]", " ", prompt.lower())
    tokens = [t for t in cleaned.split() if len(t) > 3]
    stop = {
        "create",
        "build",
        "using",
        "with",
        "from",
        "this",
        "that",
        "have",
        "your",
        "into",
        "full",
        "plus",
        "must",
        "need",
        "design",
        "system",
    }
    return [t for t in tokens if t not in stop]


def summarize_failures(benchmark: dict) -> tuple[list[str], list[str]]:
    false_negatives: list[str] = []
    false_positives: list[str] = []

    for result in benchmark.get("eval_results", []):
        expected = bool(result.get("expected_trigger"))
        predicted = bool(result.get("with_skill", {}).get("trigger_predicted"))

        if expected and not predicted:
            false_negatives.append(result["id"])
        if (not expected) and predicted:
            false_positives.append(result["id"])

    return false_negatives, false_positives


def improve_description_text(current: str, benchmark: dict, evals: dict) -> str:
    false_negatives, false_positives = summarize_failures(benchmark)

    prompts_by_id = {item["id"]: item["prompt"] for item in evals.get("evals", [])}

    positive_terms: list[str] = []
    for eval_id in false_negatives:
        positive_terms.extend(keyword_candidates(prompts_by_id.get(eval_id, ""))[:3])

    negative_terms: list[str] = []
    for eval_id in false_positives:
        negative_terms.extend(keyword_candidates(prompts_by_id.get(eval_id, ""))[:3])

    positive_hint = ""
    if positive_terms:
        unique_positive = sorted(set(positive_terms))[:6]
        positive_hint = " Prioritize prompts involving " + ", ".join(unique_positive) + "."

    negative_hint = ""
    if negative_terms:
        unique_negative = sorted(set(negative_terms))[:6]
        negative_hint = " Do not trigger for " + ", ".join(unique_negative) + " unless design-system outputs are explicitly requested."

    candidate = (current.rstrip(".") + "." + positive_hint + negative_hint).strip()
    # Keep text concise enough for frontmatter
    if len(candidate) > 1000:
        candidate = candidate[:997].rstrip() + "..."
    return candidate


def main() -> int:
    parser = argparse.ArgumentParser(description="Improve SKILL.md description from benchmark outcomes.")
    parser.add_argument("--skill-file", required=True, help="Path to SKILL.md")
    parser.add_argument("--benchmark", required=True, help="Path to benchmark.json")
    parser.add_argument("--evals", required=True, help="Path to evals JSON")
    parser.add_argument("--analysis-output", help="Optional path to write improvement analysis JSON")
    parser.add_argument("--in-place", action="store_true", help="Write the improved description back to SKILL.md")
    args = parser.parse_args()

    skill_file = Path(args.skill_file).resolve()
    benchmark = load_json(Path(args.benchmark).resolve())
    evals = load_json(Path(args.evals).resolve())

    frontmatter, _raw, body = parse_frontmatter(skill_file)
    current_description = frontmatter.get("description", "")
    if not current_description:
        raise ValueError("SKILL.md frontmatter missing description")

    candidate = improve_description_text(current_description, benchmark, evals)

    false_negatives, false_positives = summarize_failures(benchmark)
    analysis = {
        "current_description": current_description,
        "candidate_description": candidate,
        "false_negatives": false_negatives,
        "false_positives": false_positives,
    }

    if args.analysis_output:
        save_json(Path(args.analysis_output).resolve(), analysis)

    if args.in_place:
        frontmatter["description"] = candidate
        write_frontmatter(skill_file, frontmatter, body)
        print("Updated SKILL.md description in place.")
    else:
        print(candidate)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
