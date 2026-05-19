"""A2A ingestion utilities for converting repositories into CelestialBody objects."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

from .celestial import CelestialBody

IGNORED_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache"}
SOURCE_EXTENSIONS = {
    ".py": "python",
    ".rs": "rust",
    ".go": "go",
    ".swift": "swift",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".cpp": "cpp",
    ".c": "c",
    ".h": "c",
    ".java": "java",
}


def _iter_source_files(root: Path) -> Iterable[Path]:
    """Walk repository sources while pruning ignored folders."""
    for current_root, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for filename in files:
            file_path = Path(current_root) / filename
            if file_path.suffix.lower() in SOURCE_EXTENSIONS:
                yield file_path


def _collect_metrics(root: Path) -> Tuple[int, int, List[str], str]:
    file_count = 0
    code_lines = 0
    language_counts: Dict[str, int] = {}
    signature_hasher = hashlib.sha256()

    for file_path in sorted(_iter_source_files(root)):
        file_count += 1
        language = SOURCE_EXTENSIONS[file_path.suffix.lower()]
        language_counts[language] = language_counts.get(language, 0) + 1

        content = file_path.read_text(encoding="utf-8", errors="ignore")
        code_lines += sum(1 for line in content.splitlines() if line.strip())

        relative_name = file_path.relative_to(root).as_posix()
        signature_hasher.update(relative_name.encode("utf-8"))
        signature_hasher.update(content.encode("utf-8", errors="ignore"))

    dominant_languages = [
        item[0] for item in sorted(language_counts.items(), key=lambda pair: pair[1], reverse=True)
    ][:3]
    return file_count, code_lines, dominant_languages, signature_hasher.hexdigest()


def ingest_repository(path: Path) -> CelestialBody:
    """Convert a repository path into a CelestialBody with inferred properties."""
    resolved = path.expanduser().resolve()
    if not resolved.exists() or not resolved.is_dir():
        raise FileNotFoundError(f"Repository path not found: {resolved}")

    file_count, code_line_count, dominant_languages, seismic_signature = _collect_metrics(resolved)
    return CelestialBody.from_repository_metrics(
        resolved,
        file_count=file_count,
        code_line_count=code_line_count,
        dominant_languages=dominant_languages,
        seismic_signature=seismic_signature,
    )


def ingest_repositories(paths: Sequence[Path]) -> List[CelestialBody]:
    """Convert many repositories into a list of CelestialBody objects."""
    return [ingest_repository(path) for path in paths]


def export_jsonl(bodies: List[CelestialBody], output_path: Path) -> None:
    """Write one CelestialBody per line to a JSONL file."""
    output = output_path.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for body in bodies:
            handle.write(json.dumps(body.to_dict(), ensure_ascii=False) + "\n")
