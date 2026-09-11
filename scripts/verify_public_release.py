"""Fail fast if common secrets or non-public artifacts appear in this repo.

This guard is intentionally dependency-free. It cannot prove a release is safe;
reviewers must still inspect every staged change before publishing.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ALLOWED_SUFFIXES = {".md", ".json", ".py", ".gitignore", ".txt", ".license", ".png", ".jpg", ".jpeg", ".webp"}
BINARY_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
FORBIDDEN_PATH_PARTS = {".env", "raw", "private", "customer", "secrets", "__pycache__"}
PATTERNS = {
    "OpenAI-style key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "Syntarus-style key": re.compile(r"\bsk_mem_[A-Za-z0-9_-]{20,}\b"),
    "Mem0-style key": re.compile(r"\bm0-[A-Za-z0-9_-]{20,}\b"),
    "Zep-style key": re.compile(r"\bz_[A-Za-z0-9._-]{60,}\b"),
    "JWT-like token": re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    "Private key block": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}


def main() -> int:
    failures: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        relative = path.relative_to(ROOT)
        lower_parts = {part.lower() for part in relative.parts}
        # Running the dependency-free verifier or its tests may create local
        # interpreter bytecode. It is not a release artifact and is ignored by
        # git; do not make a clean checkout fail merely because it was tested.
        if "__pycache__" in lower_parts or path.suffix.lower() == ".pyc":
            continue
        if lower_parts & FORBIDDEN_PATH_PARTS:
            failures.append(f"forbidden path component: {relative}")
            continue
        if path.suffix.lower() not in ALLOWED_SUFFIXES and path.name not in {"LICENSE", ".gitignore"}:
            failures.append(f"unexpected file type: {relative}")
            continue
        if path.suffix.lower() in BINARY_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for label, pattern in PATTERNS.items():
            if pattern.search(text):
                failures.append(f"possible {label}: {relative}")
    if failures:
        print("Public-release verification failed:")
        print("\n".join(f"- {failure}" for failure in failures))
        return 1
    print("Public-release verification passed: no prohibited paths or common secret patterns found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
