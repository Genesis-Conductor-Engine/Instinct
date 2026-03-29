"""Google Drive client for DOE FOA assets."""

from typing import Any, Optional
import structlog

logger = structlog.get_logger(__name__)


class DriveClient:
    """
    Google Drive client for DOE FOA assets and documentation.

    Manages:
    - DE-FOA-0003612 Phase I application materials
    - Project Vivarium technical addenda
    - Alpha Persistence logs
    """

    def __init__(self, workspace_client: Any):
        self.workspace = workspace_client

    async def get_doe_assets(self, foa_number: str = "DE-FOA-0003612") -> list[dict]:
        """Get DOE FOA-related files."""
        query = f"name contains '{foa_number}' or fullText contains '{foa_number}'"
        return await self.workspace.get_drive_files(query=query)

    async def get_project_vivarium_docs(self) -> list[dict]:
        """Get Project Vivarium documentation."""
        query = "name contains 'Vivarium' or fullText contains 'Vivarium'"
        return await self.workspace.get_drive_files(query=query)

    async def get_document_content(self, doc_id: str) -> dict:
        """Get content of a Google Doc."""
        return await self.workspace.get_document_content(doc_id)
