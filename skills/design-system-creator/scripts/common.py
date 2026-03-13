#!/usr/bin/env python3
"""Shared helpers for design-system-creator scripts."""

from __future__ import annotations

import json
import random
import re
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path: str | Path, data: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "eval"


def ensure_dir(path: str | Path) -> Path:
    target = Path(path)
    target.mkdir(parents=True, exist_ok=True)
    return target


def split_train_holdout(items: list[dict[str, Any]], holdout_ratio: float, seed: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not items:
        return [], []

    rng = random.Random(seed)
    shuffled = items[:]
    rng.shuffle(shuffled)

    holdout_count = int(len(shuffled) * holdout_ratio)
    if holdout_count <= 0 and len(shuffled) > 1:
        holdout_count = 1
    if holdout_count >= len(shuffled):
        holdout_count = max(1, len(shuffled) - 1)

    holdout = shuffled[:holdout_count]
    train = shuffled[holdout_count:]
    return train, holdout


def parse_frontmatter(skill_md_path: str | Path) -> tuple[dict[str, str], str, str]:
    content = Path(skill_md_path).read_text(encoding="utf-8")
    if not content.startswith("---\n"):
        raise ValueError("SKILL.md must begin with YAML frontmatter")

    end = content.find("\n---\n", 4)
    if end == -1:
        raise ValueError("Invalid SKILL.md frontmatter delimiters")

    raw_frontmatter = content[4:end]
    body = content[end + 5 :]

    parsed: dict[str, str] = {}
    for line in raw_frontmatter.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        parsed[key.strip()] = value.strip().strip('"').strip("'")

    return parsed, raw_frontmatter, body


def write_frontmatter(skill_md_path: str | Path, frontmatter: dict[str, str], body: str) -> None:
    lines = ["---"]
    for key, value in frontmatter.items():
        escaped = value.replace('"', '\\"')
        lines.append(f'{key}: "{escaped}"')
    lines.append("---")
    lines.append("")
    lines.append(body.lstrip("\n"))
    Path(skill_md_path).write_text("\n".join(lines), encoding="utf-8")
