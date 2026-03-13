#!/usr/bin/env python3
"""Validate and package skill directory as a .skill archive."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import zipfile

from common import parse_frontmatter
from quick_validate import validate


EXCLUDE_DIRS = {"__pycache__", ".pytest_cache"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo"}


def should_include(path: Path) -> bool:
    parts = set(path.parts)
    if parts & EXCLUDE_DIRS:
        return False
    if path.suffix in EXCLUDE_SUFFIXES:
        return False
    if "-workspace" in path.as_posix():
        return False
    return True


def package(skill_dir: Path, output_dir: Path) -> Path:
    ok, errors = validate(skill_dir)
    if not ok:
        raise ValueError("Validation failed: " + "; ".join(errors))

    frontmatter, _raw, _body = parse_frontmatter(skill_dir / "SKILL.md")
    skill_name = frontmatter["name"]

    output_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = output_dir / f"{skill_name}.skill"

    with zipfile.ZipFile(artifact_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for root, _dirs, files in os.walk(skill_dir):
            root_path = Path(root)
            for file_name in files:
                file_path = root_path / file_name
                if not should_include(file_path):
                    continue
                rel = file_path.relative_to(skill_dir)
                archive.write(file_path, rel)

    return artifact_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Package a skill folder as .skill archive")
    parser.add_argument("skill_dir", help="Path to skill directory")
    parser.add_argument("output_dir", nargs="?", default="dist", help="Output directory for .skill artifact")
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    output_dir = Path(args.output_dir).resolve()

    artifact = package(skill_dir, output_dir)
    print(f"Packaged skill: {artifact}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
