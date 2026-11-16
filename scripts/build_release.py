#!/usr/bin/env python3
"""Build the Claude Skill ZIP, MCPB bundle, source ZIP, and checksums."""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


def add_tree(archive: zipfile.ZipFile, source: Path, prefix: str, exclude: set[str] | None = None) -> None:
    excluded = exclude or set()
    for path in sorted(source.rglob("*")):
        if not path.is_file() or any(part in excluded for part in path.parts):
            continue
        relative = path.relative_to(source).as_posix()
        archive.write(path, f"{prefix}/{relative}" if prefix else relative)


def build_skill() -> Path:
    target = DIST / "ucie-engineering-skill.zip"
    skill_root = ROOT / "skill" / "ucie-engineering"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        add_tree(archive, skill_root, "ucie-engineering", {"__pycache__"})
    return target


def build_mcpb() -> Path:
    target = DIST / "ucie-engineering.mcpb"
    source = ROOT / "mcp-server"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in ("manifest.json", "pyproject.toml", "README.md"):
            archive.write(source / name, name)
        add_tree(archive, source / "ucie_mcp", "ucie_mcp", {"__pycache__"})
    return target


def build_source(root: Path = ROOT, dist: Path = DIST) -> Path:
    """Archive only Git-indexed files; never sweep untracked local workspace files."""
    dist.mkdir(parents=True, exist_ok=True)
    target = dist / "ucie-claude-engineering-source.zip"
    try:
        tracked = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            check=True,
            capture_output=True,
        ).stdout
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(
            "Building the source archive requires a Git checkout with an accessible index."
        ) from exc

    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for raw_path in tracked.split(b"\0"):
            if not raw_path:
                continue
            relative = Path(os.fsdecode(raw_path))
            if relative.is_absolute() or ".." in relative.parts:
                raise RuntimeError(f"Unsafe tracked path returned by Git: {relative}")
            if not relative.parts or relative.parts[0] == "dist":
                continue
            path = root / relative
            if path.is_symlink() or not path.is_file():
                continue
            archive.write(path, relative.as_posix())
    return target


def main() -> None:
    DIST.mkdir(exist_ok=True)
    artifacts = [build_skill(), build_mcpb(), build_source()]
    checksum_lines = []
    for path in artifacts:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        checksum_lines.append(f"{digest}  {path.name}")
    (DIST / "SHA256SUMS.txt").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    print("Built:")
    for path in artifacts:
        print(f"  {path.relative_to(ROOT)} ({path.stat().st_size} bytes)")
    print(f"  dist/SHA256SUMS.txt")


if __name__ == "__main__":
    main()
