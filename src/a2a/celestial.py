"""Celestial body schema used by the A2A ingestion layer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


@dataclass(slots=True)
class CelestialBody:
    """Canonical structure for repositories and agents inside the sanctuary graph."""

    id: str
    name: str
    kind: str
    mass: float
    atmosphere: Dict[str, Any]
    gravity: float
    orbitals: List[str] = field(default_factory=list)
    source_path: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the object into JSON-safe primitives."""
        return asdict(self)

    @classmethod
    def from_repository_metrics(
        cls,
        path: Path,
        *,
        file_count: int,
        code_line_count: int,
        dominant_languages: List[str],
        seismic_signature: str,
    ) -> "CelestialBody":
        """Generate a body with deterministic physical properties from repository metrics."""
        normalized_mass = max(1.0, round(code_line_count / 200.0 + file_count * 0.2, 2))
        gravity = round(min(100.0, normalized_mass * 1.5), 2)
        atmosphere = {
            "intent": "collaborative",
            "thermal_profile": "stable",
            "languages": dominant_languages,
            "seismic_trace": {
                "files": file_count,
                "code_lines": code_line_count,
                "signature": seismic_signature,
            },
        }
        return cls(
            id=f"repo::{path.name.lower().replace(' ', '-')}",
            name=path.name,
            kind="repository",
            mass=normalized_mass,
            atmosphere=atmosphere,
            gravity=gravity,
            source_path=str(path),
        )
