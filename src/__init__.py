"""Project package bootstrap."""

from __future__ import annotations

from dotenv import find_dotenv, load_dotenv

# Load .env early for every `src.*` entrypoint/import path.
load_dotenv(find_dotenv(usecwd=True), override=False)
