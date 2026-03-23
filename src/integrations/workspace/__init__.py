"""
Google Workspace Integration for Neurohumogenistic Agent

Provides unified access to:
- Gmail API (Partner Advantage, PSF communications)
- Google Keep API (Genesis Mission notes)
- Google Tasks API (Execution queue)
- Google Drive API (DOE FOA assets)
- Google Docs API (SOW, VAF documents)
"""

from .client import GoogleWorkspaceClient
from .gmail import GmailClient
from .keep import KeepClient
from .tasks import TasksClient
from .drive import DriveClient

__all__ = [
    "GoogleWorkspaceClient",
    "GmailClient",
    "KeepClient",
    "TasksClient",
    "DriveClient",
]
