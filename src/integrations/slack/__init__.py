"""
Slack Integration for Neurohumogenistic Agent

Provides bidirectional Slack connectivity for the Genesis Conductor platform:
- Receives directives via Slack messages
- Posts real-time telemetry updates (thermodynamic state, directive processing)
- Sends compliance alerts (PSF violations, ARR floor breaches)
- Publishes Yennefer hourly sync reports

Usage:
    slack = SlackNotifier(webhook_url=os.getenv("SLACK_WEBHOOK_URL"))
    await slack.post_sync_report(report)
"""

from .notifier import SlackNotifier
from .event_bridge import SlackEventBridge
from .blocks import (
    build_directive_block,
    build_thermodynamic_block,
    build_compliance_block,
    build_sync_report_block,
)

__all__ = [
    "SlackNotifier",
    "SlackEventBridge",
    "build_directive_block",
    "build_thermodynamic_block",
    "build_compliance_block",
    "build_sync_report_block",
]
