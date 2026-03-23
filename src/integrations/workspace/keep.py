"""Google Keep client for Genesis Mission notes."""

from typing import Any
import structlog

logger = structlog.get_logger(__name__)


class KeepClient:
    """
    Google Keep client for Genesis Conductor Strategic Plan notes.

    Note: Google Keep API has limited access. This client provides
    abstraction for when full API access becomes available.
    """

    def __init__(self, workspace_client: Any):
        self.workspace = workspace_client

    async def get_genesis_notes(self) -> list[dict]:
        """Get notes labeled with Genesis Conductor tags."""
        notes = await self.workspace.get_keep_notes()
        return [n for n in notes if "genesis" in str(n.get("labels", [])).lower()]

    async def get_doe_mission_notes(self) -> list[dict]:
        """Get notes related to DOE mission alignment."""
        notes = await self.workspace.get_keep_notes()
        return [n for n in notes if "doe" in str(n.get("labels", [])).lower() or "mission" in str(n.get("labels", [])).lower()]
