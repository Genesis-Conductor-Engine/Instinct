"""
Slack Notifier for Neurohumogenistic Agent

Sends rich formatted messages to Slack channels:
- Hourly Yennefer sync reports
- Real-time thermodynamic state alerts
- PSF compliance violations
- Directive processing milestones
"""

import asyncio
import os
from datetime import datetime
from typing import Any, Optional

import structlog

from .blocks import (
    build_compliance_block,
    build_directive_block,
    build_sync_report_block,
    build_thermodynamic_block,
)

logger = structlog.get_logger(__name__)


class SlackNotifier:
    """
    Sends notifications to Slack channels via Incoming Webhooks or the
    Slack Web API (Bot Token).

    Supports:
    - Webhook-based posting (simpler, no OAuth)
    - Bot Token API (full message threading and updates)
    """

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        bot_token: Optional[str] = None,
        default_channel: str = "#genesis-conductor",
        username: str = "Genesis Conductor",
        icon_emoji: str = ":zap:",
    ):
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        self.bot_token = bot_token or os.getenv("SLACK_BOT_TOKEN")
        self.default_channel = default_channel
        self.username = username
        self.icon_emoji = icon_emoji
        self._session = None

        if not self.webhook_url and not self.bot_token:
            logger.warning(
                "slack.no_credentials",
                hint="Set SLACK_WEBHOOK_URL or SLACK_BOT_TOKEN env var"
            )

    async def _get_session(self):
        """Get or create aiohttp session."""
        if not self._session:
            try:
                import aiohttp
                self._session = aiohttp.ClientSession()
            except ImportError:
                logger.warning("slack.aiohttp_not_installed", hint="pip install aiohttp")
        return self._session

    async def post(
        self,
        text: str,
        blocks: Optional[list] = None,
        channel: Optional[str] = None,
        thread_ts: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Post a message to Slack.

        Args:
            text: Fallback text (also shown in notifications)
            blocks: Optional Block Kit blocks for rich formatting
            channel: Channel override (default: self.default_channel)
            thread_ts: Thread timestamp for threaded replies

        Returns:
            API response dict or None if failed
        """
        payload = {
            "text": text,
            "username": self.username,
            "icon_emoji": self.icon_emoji,
        }

        if blocks:
            payload["blocks"] = blocks

        if thread_ts:
            payload["thread_ts"] = thread_ts

        # Use webhook URL if available (simpler)
        if self.webhook_url:
            return await self._post_webhook(payload)

        # Fall back to Bot Token API
        if self.bot_token:
            payload["channel"] = channel or self.default_channel
            return await self._post_api(payload)

        # Neither configured - log only
        logger.info(
            "slack.message_logged_only",
            text=text,
            reason="No credentials configured"
        )
        return None

    async def _post_webhook(self, payload: dict) -> Optional[dict]:
        """Post via incoming webhook."""
        session = await self._get_session()
        if not session:
            return None

        try:
            import aiohttp
            async with session.post(
                self.webhook_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    logger.info("slack.webhook_sent")
                    return {"ok": True}
                else:
                    text = await resp.text()
                    logger.error("slack.webhook_failed", status=resp.status, body=text)
                    return None

        except Exception as e:
            logger.error("slack.webhook_error", error=str(e))
            return None

    async def _post_api(self, payload: dict) -> Optional[dict]:
        """Post via Slack Web API."""
        session = await self._get_session()
        if not session:
            return None

        try:
            import aiohttp
            async with session.post(
                "https://slack.com/api/chat.postMessage",
                json=payload,
                headers={"Authorization": f"Bearer {self.bot_token}"},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                data = await resp.json()

                if data.get("ok"):
                    logger.info("slack.api_sent", channel=payload.get("channel"))
                    return data
                else:
                    logger.error("slack.api_failed", error=data.get("error"))
                    return None

        except Exception as e:
            logger.error("slack.api_error", error=str(e))
            return None

    async def post_sync_report(self, report: dict, channel: Optional[str] = None) -> None:
        """Post Yennefer hourly sync report."""
        blocks = build_sync_report_block(report)
        await self.post(
            text=f"Genesis Conductor Sync: {report.get('timestamp', datetime.utcnow().isoformat())}",
            blocks=blocks,
            channel=channel,
        )

        logger.info(
            "slack.sync_report_posted",
            directives=report.get("directives", {}).get("total_processed", 0)
        )

    async def post_thermodynamic_alert(
        self,
        state: dict,
        channel: Optional[str] = None,
    ) -> None:
        """Post thermodynamic state alert (cold snap, high power)."""
        blocks = build_thermodynamic_block(state)
        is_cold_snap = state.get("cold_snap_active", False)

        text = (
            "COLD SNAP ACTIVE: Genesis Conductor entering recovery mode"
            if is_cold_snap
            else f"Thermodynamic Update: {state.get('total_power_w', 0):.1f}W | η={state.get('efficiency_eta', 0):.2f}"
        )

        await self.post(text=text, blocks=blocks, channel=channel)

    async def post_compliance_alert(
        self,
        directive_id: str,
        violations: list[str],
        channel: Optional[str] = None,
    ) -> None:
        """Post PSF compliance violation alert."""
        blocks = build_compliance_block(directive_id, violations)
        await self.post(
            text=f"PSF Compliance Violation: {directive_id}",
            blocks=blocks,
            channel=channel,
        )

        logger.warning(
            "slack.compliance_alert_posted",
            directive_id=directive_id,
            violations=len(violations)
        )

    async def post_directive_update(
        self,
        directive: Any,
        result: dict,
        channel: Optional[str] = None,
    ) -> None:
        """Post directive processing update."""
        blocks = build_directive_block(directive, result)
        await self.post(
            text=f"Directive processed: {directive.directive_type.value} [{directive.priority}/10]",
            blocks=blocks,
            channel=channel,
        )

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None
