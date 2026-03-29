from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.a2a import export_jsonl, ingest_repositories, ingest_repository


def test_ingest_repository_builds_celestial_body(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text("print('hello')\n", encoding="utf-8")
    (tmp_path / "lib.rs").write_text("fn main() {}\n", encoding="utf-8")

    body = ingest_repository(tmp_path)

    assert body.kind == "repository"
    assert body.mass >= 1.0
    assert body.gravity >= 1.5
    assert "languages" in body.atmosphere
    assert set(body.atmosphere["languages"]) == {"python", "rust"}
    assert len(body.atmosphere["seismic_trace"]["signature"]) == 64


def test_ingest_repository_ignores_cached_directories(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text("print('root')\n", encoding="utf-8")
    ignored = tmp_path / "node_modules"
    ignored.mkdir()
    (ignored / "ignored.py").write_text("print('should_not_count')\n", encoding="utf-8")

    body = ingest_repository(tmp_path)
    assert body.atmosphere["seismic_trace"]["files"] == 1


def test_ingest_repositories_supports_multiple_roots(tmp_path: Path) -> None:
    left = tmp_path / "left"
    right = tmp_path / "right"
    left.mkdir()
    right.mkdir()
    (left / "a.py").write_text("x = 1\n", encoding="utf-8")
    (right / "b.go").write_text("package main\n", encoding="utf-8")

    bodies = ingest_repositories([left, right])

    assert len(bodies) == 2
    assert {body.name for body in bodies} == {"left", "right"}


def test_export_jsonl_writes_one_object_per_line(tmp_path: Path) -> None:
    (tmp_path / "agent.py").write_text("x = 1\n", encoding="utf-8")
    body = ingest_repository(tmp_path)

    output_file = tmp_path / "out" / "bodies.jsonl"
    export_jsonl([body], output_file)

    lines = output_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    assert '"kind": "repository"' in lines[0]
