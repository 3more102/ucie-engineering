#!/usr/bin/env python3
"""Recompute SHA-256 checksums for the final release artifacts."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARTIFACTS = (
    "ucie-engineering-skill.zip",
    "ucie-engineering.mcpb",
    "ucie-claude-engineering-source.zip",
)


def write_checksums(dist: Path, names: tuple[str, ...] = DEFAULT_ARTIFACTS) -> Path:
    lines = []
    for name in names:
        artifact = dist / name
        if not artifact.is_file():
            raise FileNotFoundError(f"Release artifact not found: {artifact}")
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        lines.append(f"{digest}  {name}")
    output = dist / "SHA256SUMS.txt"
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def main() -> int:
    dist = ROOT / "dist"
    try:
        output = write_checksums(dist)
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Updated final artifact checksums: {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
