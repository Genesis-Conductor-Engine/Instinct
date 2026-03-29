"""
Unified Google Workspace Client

Provides single interface for all Google Workspace APIs used by
the Neurohumogenistic Workspace Integration.
"""

import asyncio
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class WorkspaceConfig:
    """Configuration for Google Workspace API access."""
    credentials_path: str = "credentials.json"
    token_path: str = "token.json"
    scopes: list[str] = field(default_factory=lambda: [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/keep.readonly",
        "https://www.googleapis.com/auth/tasks.readonly",
        "https://www.googleapis.com/auth/tasks",
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/documents.readonly",
    ])
    # Filter labels for Partner Advantage communications
    gmail_labels: list[str] = field(default_factory=lambda: [
        "partner-advantage",
        "psf",
        "pipeline",
        "deal-registration",
    ])


class GoogleWorkspaceClient:
    """
    Unified client for Google Workspace APIs.

    Implements lazy loading of individual service clients and
    provides async wrappers for synchronous Google API calls.
    """

    def __init__(self, config: Optional[WorkspaceConfig] = None):
        self.config = config or WorkspaceConfig()
        self._credentials = None
        self._gmail = None
        self._keep = None
        self._tasks = None
        self._drive = None
        self._docs = None
        self._initialized = False

        logger.info(
            "workspace_client.created",
            credentials_path=self.config.credentials_path
        )

    async def initialize(self) -> bool:
        """
        Initialize Google API credentials and services.

        Returns True if successful, False otherwise.
        """
        if self._initialized:
            return True

        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request

            creds = None

            # Load existing token
            token_path = Path(self.config.token_path)
            if token_path.exists():
                creds = Credentials.from_authorized_user_file(
                    str(token_path),
                    self.config.scopes
                )

            # Refresh or create new credentials
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    creds_path = Path(self.config.credentials_path)
                    if not creds_path.exists():
                        logger.error(
                            "workspace_client.credentials_missing",
                            path=self.config.credentials_path
                        )
                        return False

                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(creds_path),
                        self.config.scopes
                    )
                    creds = flow.run_local_server(port=0)

                # Save credentials
                with open(token_path, "w") as token:
                    token.write(creds.to_json())

            self._credentials = creds
            self._initialized = True

            logger.info("workspace_client.initialized")
            return True

        except ImportError:
            logger.error(
                "workspace_client.missing_dependencies",
                hint="pip install google-auth-oauthlib google-api-python-client"
            )
            return False
        except Exception as e:
            logger.error("workspace_client.init_failed", error=str(e))
            return False

    def _get_gmail_service(self) -> Any:
        """Get Gmail API service."""
        if not self._gmail:
            from googleapiclient.discovery import build
            self._gmail = build("gmail", "v1", credentials=self._credentials)
        return self._gmail

    def _get_tasks_service(self) -> Any:
        """Get Tasks API service."""
        if not self._tasks:
            from googleapiclient.discovery import build
            self._tasks = build("tasks", "v1", credentials=self._credentials)
        return self._tasks

    def _get_drive_service(self) -> Any:
        """Get Drive API service."""
        if not self._drive:
            from googleapiclient.discovery import build
            self._drive = build("drive", "v3", credentials=self._credentials)
        return self._drive

    def _get_docs_service(self) -> Any:
        """Get Docs API service."""
        if not self._docs:
            from googleapiclient.discovery import build
            self._docs = build("docs", "v1", credentials=self._credentials)
        return self._docs

    async def _run_in_executor(self, func: Any, *args) -> Any:
        """Run synchronous Google API call in executor."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args)

    async def get_emails(
        self,
        query: str = "",
        max_results: int = 100
    ) -> list[dict]:
        """
        Fetch emails matching query.

        Args:
            query: Gmail search query (e.g., "label:partner-advantage")
            max_results: Maximum number of emails to return

        Returns:
            List of email dictionaries with id, subject, snippet, from, labels
        """
        if not self._initialized:
            await self.initialize()

        if not self._credentials:
            logger.warning("workspace_client.not_authenticated")
            return []

        try:
            service = self._get_gmail_service()

            # List messages
            def list_messages():
                return service.users().messages().list(
                    userId="me",
                    q=query,
                    maxResults=max_results
                ).execute()

            result = await self._run_in_executor(list_messages)
            messages = result.get("messages", [])

            emails = []
            for msg in messages:
                def get_message(msg_id):
                    return service.users().messages().get(
                        userId="me",
                        id=msg_id,
                        format="metadata",
                        metadataHeaders=["Subject", "From", "Date"]
                    ).execute()

                full_msg = await self._run_in_executor(get_message, msg["id"])

                # Extract headers
                headers = {h["name"]: h["value"] for h in full_msg.get("payload", {}).get("headers", [])}

                emails.append({
                    "id": msg["id"],
                    "thread_id": full_msg.get("threadId"),
                    "subject": headers.get("Subject", ""),
                    "from": headers.get("From", ""),
                    "date": headers.get("Date", ""),
                    "snippet": full_msg.get("snippet", ""),
                    "labels": full_msg.get("labelIds", []),
                })

            logger.info(
                "workspace_client.emails_fetched",
                count=len(emails),
                query=query
            )

            return emails

        except Exception as e:
            logger.error("workspace_client.get_emails_failed", error=str(e))
            return []

    async def get_keep_notes(self) -> list[dict]:
        """
        Fetch Google Keep notes.

        Note: Google Keep API has limited public access.
        This implementation uses workarounds where available.

        Returns:
            List of note dictionaries with id, title, content, labels, pinned
        """
        if not self._initialized:
            await self.initialize()

        # Google Keep API is restricted. Using mock data for development.
        # In production, use Google Keep API with domain-wide delegation
        # or export notes through Google Takeout.

        logger.warning(
            "workspace_client.keep_api_limited",
            hint="Using mock data. Enable Keep API access for production."
        )

        return self._get_mock_keep_notes()

    def _get_mock_keep_notes(self) -> list[dict]:
        """Return mock Keep notes for development."""
        return [
            {
                "id": "keep_001",
                "title": "Genesis Conductor Strategic Plan",
                "content": """Wolfspeed SiC scrap integration - High priority
Skywater Technologies partnership proposal - Draft ready
Strategic portfolio alignment with 13 revenue streams""",
                "labels": ["strategic", "genesis-conductor"],
                "pinned": True,
            },
            {
                "id": "keep_002",
                "title": "Genesis Mission Alignment Tasks",
                "content": """Generate Technical Addendum for Project Vivarium
Prepare Alpha Persistence logs example
DE-FOA-0003612 Phase I application matrix
DOE milestone tracking""",
                "labels": ["doe", "mission"],
                "pinned": True,
            },
            {
                "id": "keep_003",
                "title": "Thermodynamic Recovery",
                "content": """Mycology (1-3 hours) - Personal research time
Cold Snap rest periods scheduled
Cognitive recovery protocols active""",
                "labels": ["personal", "recovery"],
                "pinned": False,
            },
        ]

    async def get_tasks(self, task_list_id: str = "@default") -> list[dict]:
        """
        Fetch Google Tasks from a task list.

        Args:
            task_list_id: Task list ID (default: primary list)

        Returns:
            List of task dictionaries with id, title, notes, due, status
        """
        if not self._initialized:
            await self.initialize()

        if not self._credentials:
            logger.warning("workspace_client.not_authenticated")
            return []

        try:
            service = self._get_tasks_service()

            def list_tasks():
                return service.tasks().list(
                    tasklist=task_list_id,
                    showCompleted=False,
                    showHidden=False
                ).execute()

            result = await self._run_in_executor(list_tasks)
            items = result.get("items", [])

            tasks = []
            for item in items:
                tasks.append({
                    "id": item.get("id"),
                    "title": item.get("title", ""),
                    "notes": item.get("notes", ""),
                    "due": item.get("due"),
                    "status": item.get("status"),
                    "task_list": task_list_id,
                })

            logger.info(
                "workspace_client.tasks_fetched",
                count=len(tasks),
                list_id=task_list_id
            )

            return tasks

        except Exception as e:
            logger.error("workspace_client.get_tasks_failed", error=str(e))
            return []


    def _get_mock_tasks(self) -> list[dict]:
        """Return mock tasks for development."""
        return [
            {
                "id": "task_001",
                "title": "Launch Prototypes on prototypes.genesisconductor.io",
                "notes": "Deploy staging environment with full telemetry",
                "due": None,
                "status": "needsAction",
                "task_list": "@default",
            },
            {
                "id": "task_002",
                "title": "Enable OpenTelemetry ingestion API",
                "notes": "Feed η_thermo metrics to Diamond Vault UI with useOptimistic",
                "due": None,
                "status": "needsAction",
                "task_list": "@default",
            },
            {
                "id": "task_003",
                "title": "Configure Cloudflare Worker pareto-audit",
                "notes": "Wire to pareto.genesisconductor.io for pipeline filtering",
                "due": None,
                "status": "needsAction",
                "task_list": "@default",
            },
        ]

    async def get_drive_files(
        self,
        query: str = "",
        folder_id: Optional[str] = None,
        max_results: int = 100
    ) -> list[dict]:
        """
        Fetch files from Google Drive.

        Args:
            query: Drive search query
            folder_id: Optional folder to search within
            max_results: Maximum number of files to return

        Returns:
            List of file dictionaries with id, name, mimeType, webViewLink
        """
        if not self._initialized:
            await self.initialize()

        if not self._credentials:
            logger.warning("workspace_client.not_authenticated")
            return []

        try:
            service = self._get_drive_service()

            # Build query
            q = query
            if folder_id:
                q = f"'{folder_id}' in parents"
                if query:
                    q += f" and {query}"

            def list_files():
                return service.files().list(
                    q=q,
                    pageSize=max_results,
                    fields="files(id, name, mimeType, webViewLink, modifiedTime)"
                ).execute()

            result = await self._run_in_executor(list_files)
            files = result.get("files", [])

            logger.info(
                "workspace_client.drive_files_fetched",
                count=len(files),
                query=query
            )

            return files

        except Exception as e:
            logger.error("workspace_client.get_drive_files_failed", error=str(e))
            return []

    async def get_document_content(self, document_id: str) -> dict:
        """
        Fetch Google Docs document content.

        Args:
            document_id: Document ID

        Returns:
            Document dictionary with title and body content
        """
        if not self._initialized:
            await self.initialize()

        if not self._credentials:
            logger.warning("workspace_client.not_authenticated")
            return {}

        try:
            service = self._get_docs_service()

            def get_doc():
                return service.documents().get(documentId=document_id).execute()

            doc = await self._run_in_executor(get_doc)

            # Extract text content
            content = self._extract_doc_text(doc.get("body", {}).get("content", []))

            return {
                "id": document_id,
                "title": doc.get("title", ""),
                "content": content,
            }

        except Exception as e:
            logger.error(
                "workspace_client.get_document_failed",
                document_id=document_id,
                error=str(e)
            )
            return {}

    def _extract_doc_text(self, content: list) -> str:
        """Extract text from Google Docs content elements."""
        text_parts = []

        for element in content:
            if "paragraph" in element:
                for elem in element["paragraph"].get("elements", []):
                    if "textRun" in elem:
                        text_parts.append(elem["textRun"].get("content", ""))

        return "".join(text_parts)

    async def close(self) -> None:
        """Close client and cleanup resources."""
        self._gmail = None
        self._keep = None
        self._tasks = None
        self._drive = None
        self._docs = None
        self._credentials = None
        self._initialized = False

        logger.info("workspace_client.closed")
