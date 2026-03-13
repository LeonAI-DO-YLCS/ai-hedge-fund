#!/usr/bin/env python3
"""Quick validator for design-system-creator skill structure and metadata."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from common import parse_frontmatter


REQUIRED_PATHS = [
    "SKILL.md",
    "agents/openai.yaml",
    "references/schemas.md",
    "evals/evals.json",
    "scripts/run_eval.py",
    "scripts/run_loop.py",
    "scripts/aggregate_benchmark.py",
    "scripts/improve_description.py",
    "scripts/package_skill.py",
]

FORBIDDEN_PROJECT_COUPLING = [
    "/src/",
    "app/frontend",
    "this repository",
    "ai-hedge-fund",
    "project-specific",
]


def validate(skill_dir: Path) -> tuple[bool, list[str]]:
    errors: list[str] = []

    for rel in REQUIRED_PATHS:
        if not (skill_dir / rel).exists():
            errors.append(f"Missing required path: {rel}")

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return False, errors

    try:
        frontmatter, _raw, _body = parse_frontmatter(skill_md)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Frontmatter parse failed: {exc}")
        return False, errors

    name = frontmatter.get("name", "")
    description = frontmatter.get("description", "")

    if not re.match(r"^[a-z0-9-]+$", name):
        errors.append("Frontmatter name must be hyphen-case")

    if not description:
        errors.append("Frontmatter description is required")

    if len(description) > 1024:
        errors.append("Description exceeds 1024 characters")

    lowered = description.lower()
    for marker in FORBIDDEN_PROJECT_COUPLING:
        if marker in lowered:
            errors.append(f"Description contains project-coupled marker: {marker}")

    evals_path = skill_dir / "evals" / "evals.json"
    if evals_path.exists():
        try:
            evals_doc = json.loads(evals_path.read_text(encoding="utf-8"))
            evals = evals_doc.get("evals", [])
            if not isinstance(evals, list) or not evals:
                errors.append("evals/evals.json must contain a non-empty 'evals' array")
            ids = set()
            for item in evals:
                eval_id = item.get("id")
                if not eval_id or eval_id in ids:
                    errors.append(f"Invalid or duplicate eval id: {eval_id}")
                ids.add(eval_id)
                if "expected_trigger" not in item:
                    errors.append(f"Missing expected_trigger for eval: {eval_id}")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"evals/evals.json is invalid JSON: {exc}")

    return len(errors) == 0, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate design-system-creator skill folder.")
    parser.add_argument("skill_dir", help="Path to skill directory")
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    ok, errors = validate(skill_dir)
    if ok:
        print("Skill is valid.")
        return 0

    print("Skill validation failed:")
    for err in errors:
        print(f"- {err}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
