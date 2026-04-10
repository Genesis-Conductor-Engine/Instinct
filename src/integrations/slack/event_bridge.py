"""
Slack Event Bridge for Neurohumogenistic Agent

Receives inbound Slack events (slash commands, messages) and converts
them into WorkspaceDirectives for the EdgeAgent to process.

This enables Slack as an input surface alongside Google Workspace,
completing the neuro-symbolic convergence.

Supported commands:
  /genesis status    - Get current orchestrator status
  /genesis sync      - Trigger immediate Yennefer sync
  /genesis cold-snap - Toggle cold snap mode
  /genesis audit <text> - Run pareto audit on text
"""

import asyncio
import hashlib
import hmac
import os
import time
from typing import Any, Callable, Optional

import structlog

logger = structlog.get_logger(__name__)


class SlackEventBridge:
    """
    Slack Events API receiver that bridges Slack interactions to the
    Genesis Conductor EdgeAgent.

    Implements:
    - Slash command handler for /genesis
    - Event subscription for mentions
    - HMAC signature verification for request authenticity
    """

    def __init__(
        self,
        signing_secret: Optional[str] = None,
        orchestrator: Optional[Any] = None,
        notifier: Optional[Any] = None,
    ):
        self.signing_secret = signing_secret or os.getenv("SLACK_SIGNING_SECRET")
        self.orchestrator = orchestrator
        self.notifier = notifier

        self._command_handlers: dict[str, Callable] = {
            "status": self._handle_status,
            "sync": self._handle_sync,
            "cold-snap": self._handle_cold_snap,
            "audit": self._handle_audit,
        }

        logger.info("slack_bridge.initialized")

    def verify_signature(
        self,
        timestamp: str,
        body: str,
        signature: str,
    ) -> bool:
        """
        Verify Slack request signature using HMAC-SHA256.

        Prevents replay attacks with 5-minute timestamp window.
        Rejects unsigned requests by default for security.
        """
        if not self.signing_secret:
            # Only allow unsigned requests with explicit opt-in for local dev
            allow_insecure = os.getenv("ALLOW_INSECURE_SLACK_SIGNATURES", "").lower() == "true"
            if allow_insecure:
                logger.warning(
                    "slack_bridge.insecure_mode",
                    hint="ALLOW_INSECURE_SLACK_SIGNATURES=true - disable in production"
                )
                return True
            else:
                logger.error(
                    "slack_bridge.signature_verification_failed",
                    reason="SLACK_SIGNING_SECRET not configured"
                )
                return False

        # Check timestamp to prevent replay attacks
        if abs(time.time() - int(timestamp)) > 300:
            return False

        # Compute expected signature
        sig_basestring = f"v0:{timestamp}:{body}".encode()
        expected = "v0=" + hmac.new(
            self.signing_secret.encode(),
            sig_basestring,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected, signature)

    async def handle_slash_command(self, payload: dict) -> dict:
        """
        Handle /genesis slash commands.

        Returns immediate response for Slack (must be < 3 seconds),
        posts follow-up via response_url for longer operations.

        Args:
            payload: Slack slash command payload

        Returns:
            Immediate Slack response
        """
        command_text = payload.get("text", "").strip()
        response_url = payload.get("response_url", "")
        user_id = payload.get("user_id", "")
        channel_id = payload.get("channel_id", "")

        logger.info(
            "slack_bridge.slash_command",
            command=command_text,
            user=user_id,
            channel=channel_id,
        )

        # Parse subcommand
        parts = command_text.split(None, 1)
        subcommand = parts[0].lower() if parts else "status"
        args = parts[1] if len(parts) > 1 else ""

        handler = self._command_handlers.get(subcommand, self._handle_unknown)

        # Return immediate ACK, process async
        asyncio.create_task(
            self._process_command_async(handler, args, response_url, user_id)
        )

        return {
            "response_type": "ephemeral",
            "text": f"Processing `/genesis {subcommand}`...",
        }

    async def _process_command_async(
        self,
        handler: Callable,
        args: str,
        response_url: str,
        user_id: str,
    ) -> None:
        """Process command asynchronously and post result via response_url."""
        try:
            result = await handler(args, user_id)

            # Post to response_url
            if response_url and self.notifier:
                try:
                    import aiohttp
                    session = await self.notifier._get_session()
                    if session:
                        async with session.post(response_url, json=result) as resp:
                            if resp.status != 200:
                                logger.warning("slack_bridge.response_url_failed", status=resp.status)
                except Exception as e:
                    logger.error("slack_bridge.response_url_error", error=str(e))

        except Exception as e:
            logger.error("slack_bridge.command_error", error=str(e))

    async def _handle_status(self, args: str, user_id: str) -> dict:
        """Handle /genesis status command."""
        if not self.orchestrator:
            return {
                "response_type": "in_channel",
                "text": "Genesis Conductor is initializing...",
            }

        report = self.orchestrator.get_status_report()

        return {
            "response_type": "in_channel",
            "text": "Genesis Conductor Status",
            "blocks": _build_status_response(report, user_id),
        }

    async def _handle_sync(self, args: str, user_id: str) -> dict:
        """Handle /genesis sync command — triggers Yennefer sync."""
        if not self.orchestrator:
            return {"text": "Orchestrator not available"}

        report = await self.orchestrator.sync_yennefer()

        return {
            "response_type": "in_channel",
            "text": f"Yennefer sync complete: {report['directives']['total_processed']} directives processed",
            "blocks": _build_sync_response(report, user_id),
        }

    async def _handle_cold_snap(self, args: str, user_id: str) -> dict:
        """Handle /genesis cold-snap command — toggles Cold Snap mode."""
        if not self.orchestrator:
            return {"text": "Orchestrator not available"}

        kernel = self.orchestrator.thermodynamic_kernel
        current = kernel.get_state().is_cold_snap

        if current:
            kernel.exit_cold_snap()
            action = "exited"
        else:
            kernel.enter_cold_snap()
            action = "entered"

        return {
            "response_type": "in_channel",
            "text": f"Cold Snap {action} by <@{user_id}>",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{'🧊' if not current else '✅'} *Cold Snap {action}* by <@{user_id}>\n{'High-compute operations throttled.' if not current else 'Full processing capacity restored.'}"
                    }
                }
            ]
        }

    async def _handle_audit(self, args: str, user_id: str) -> dict:
        """Handle /genesis audit <text> — runs pareto audit."""
        if not args:
            return {"text": "Usage: /genesis audit <opportunity text>"}

        if not self.orchestrator:
            return {"text": "Orchestrator not available"}

        # Run pareto filter
        from src.agents.neurohumogenistic.edge_agent import DirectiveType, WorkspaceDirective

        directive = WorkspaceDirective(
            id=f"slack_audit_{int(time.time())}",
            source="slack",
            content=args,
            directive_type=DirectiveType.PSF_COMPLIANCE,
        )

        passed = self.orchestrator.pareto_filter.evaluate(directive)
        stats = self.orchestrator.pareto_filter.get_stats()

        return {
            "response_type": "ephemeral",
            "text": f"Pareto audit: {'PASS ✅' if passed else 'FAIL ❌'}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Pareto Audit Result*\n```{args[:200]}```\n\n{'✅ COMPLIANT' if passed else '❌ NON-COMPLIANT'}"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"Session stats: {stats['passed']}/{stats['total_evaluated']} passed ({stats['pass_rate'] * 100:.0f}% rate)"
                        }
                    ]
                }
            ]
        }

    async def _handle_unknown(self, args: str, user_id: str) -> dict:
        """Handle unknown subcommands."""
        return {
            "response_type": "ephemeral",
            "text": "Unknown command. Available: `status`, `sync`, `cold-snap`, `audit <text>`",
        }

    async def handle_event(self, event: dict) -> None:
        """
        Handle Slack Events API events (app_mention, message).

        Converts Slack messages into WorkspaceDirectives.
        """
        event_type = event.get("type")

        if event_type == "app_mention":
            await self._handle_mention(event)
        elif event_type == "message" and event.get("subtype") != "bot_message":
            await self._handle_dm(event)

    async def _handle_mention(self, event: dict) -> None:
        """Handle @genesis-conductor mentions."""
        text = event.get("text", "")
        user = event.get("user", "")
        channel = event.get("channel", "")

        # Strip bot mention
        import re
        clean_text = re.sub(r"<@[A-Z0-9]+>", "", text).strip()

        logger.info(
            "slack_bridge.mention",
            user=user,
            channel=channel,
            text=clean_text[:100]
        )

        # Convert to directive if orchestrator available
        if self.orchestrator and clean_text:
            from src.agents.neurohumogenistic.edge_agent import WorkspaceDirective

            directive = WorkspaceDirective(
                id=f"slack_{event.get('ts', int(time.time()))}",
                source="slack",
                content=clean_text,
                directive_type=self.orchestrator.edge_agent.classify_directive(
                    clean_text, "slack"
                ),
                metadata={"user": user, "channel": channel, "ts": event.get("ts")},
            )
            directive.priority = self.orchestrator.edge_agent.calculate_priority(directive)

            await self.orchestrator.edge_agent.dispatch_directive(directive)

    async def _handle_dm(self, event: dict) -> None:
        """Handle direct messages (future: conversational interface)."""
        pass


def _build_status_response(report: dict, user_id: str) -> list:
    """Build status response blocks."""
    system = report.get("system", {})
    directives = report.get("directives", {})
    revenue = report.get("revenue", {})

    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Genesis Conductor Status* (for <@{user_id}>)\n`{report.get('timestamp', '')}`"
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Status*\n{'🟢 Running' if system.get('running') else '🔴 Stopped'}"},
                {"type": "mrkdwn", "text": f"*Cold Snap*\n{'🧊 Active' if system.get('cold_snap_active') else '✅ Off'}"},
                {"type": "mrkdwn", "text": f"*Processed*\n`{directives.get('total_processed', 0)}`"},
                {"type": "mrkdwn", "text": f"*Pipeline*\n`${revenue.get('pipeline_value_usd', 0):,.0f}`"},
            ]
        }
    ]


def _build_sync_response(report: dict, user_id: str) -> list:
    """Build sync response blocks."""
    from .blocks import build_sync_report_block
    return build_sync_report_block(report)
