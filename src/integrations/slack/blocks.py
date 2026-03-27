"""
Slack Block Kit builders for Neurohumogenistic Agent messages.

Builds rich formatted messages using Slack's Block Kit:
- Sync report cards (thermodynamic state, directive counts, revenue)
- Compliance violation alerts (PSF, ARR floor)
- Directive processing summaries
- Thermodynamic state gauges
"""

from datetime import datetime
from typing import Any


def build_sync_report_block(report: dict) -> list:
    """Build Yennefer hourly sync report blocks."""
    timestamp = report.get("timestamp", datetime.utcnow().isoformat())

    # Extract metrics
    directives = report.get("directives", {})
    revenue = report.get("revenue", {})
    thermo = report.get("thermodynamic", {})
    cascade = report.get("cascade", {})
    system = report.get("system", {})

    total_processed = directives.get("total_processed", 0)
    pipeline_value = revenue.get("pipeline_value_usd", 0)
    monthly_target = revenue.get("monthly_target_usd", 70000)
    target_pct = min(100, pipeline_value / monthly_target * 100) if monthly_target else 0

    efficiency = thermo.get("thermodynamic.efficiency_eta", 1.0)
    power = thermo.get("thermodynamic.total_power_w", 0)
    cold_snap = thermo.get("thermodynamic.cold_snap", 0) == 1

    # Efficiency indicator
    eta_bar = "█" * int(efficiency * 10) + "░" * (10 - int(efficiency * 10))
    target_bar = "█" * int(target_pct / 10) + "░" * (10 - int(target_pct / 10))

    cold_snap_text = " | 🧊 COLD SNAP" if cold_snap else ""

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "⚡ Genesis Conductor · Yennefer Sync",
                "emoji": True,
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Neurohumogenistic Workspace Integration*\n`{timestamp}`{cold_snap_text}"
            }
        },
        {"type": "divider"},
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Directives Processed*\n`{total_processed}`"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Pending*\n`{directives.get('pending', 0)}`"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Pipeline Value*\n`${pipeline_value:,.0f}`"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Monthly Target*\n`{target_pct:.1f}%` {target_bar}"
                },
            ]
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*η_thermo Efficiency*\n`{efficiency:.2f}` {eta_bar}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Power Draw*\n`{power:.1f}W`"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Compliant Ops*\n`{revenue.get('compliant_opportunities', 0)}`"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Filtered*\n`{revenue.get('filtered_opportunities', 0)}`"
                },
            ]
        },
    ]

    # Directive breakdown by type
    by_type = directives.get("by_type", {})
    if by_type:
        type_lines = []
        type_labels = {
            "vector_1": "HIGH_LEVERAGE",
            "doe_phase_1": "DOE_MISSION",
            "active_foreground": "EXECUTION",
            "psf_verification": "PSF_COMPLIANCE",
            "cold_snap": "THERMO_GATE",
            "13_streams": "REVENUE_PIPE",
        }
        for dtype, count in by_type.items():
            label = type_labels.get(dtype, dtype)
            blocks_line = "▪" * min(count, 10)
            type_lines.append(f"`{label}` {blocks_line} {count}")

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Directive Distribution*\n" + "\n".join(type_lines)
            }
        })

    # Cascade stats
    if cascade:
        cascade_cost = cascade.get("total_cost_usd", 0)
        tier_usage = cascade.get("tier_usage", {})
        blocks.append({
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*FrugalGPT Cost*\n`${cascade_cost:.4f}`"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Tier Distribution*\nT1:{tier_usage.get(1,0)} T2:{tier_usage.get(2,0)} T3:{tier_usage.get(3,0)}"
                },
            ]
        })

    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"Running: {'✅' if system.get('running') else '❌'} | Cold Snap: {'🧊' if system.get('cold_snap_active') else '✅ Off'} | <https://prototypes.genesisconductor.io|Diamond Vault>"
            }
        ]
    })

    return blocks


def build_thermodynamic_block(state: dict) -> list:
    """Build thermodynamic state alert blocks."""
    power = state.get("total_power_w", 0)
    efficiency = state.get("efficiency_eta", 1.0)
    cold_snap = state.get("cold_snap_active", False)
    temperature = state.get("temperature_celsius", 25.0)

    emoji = "🧊" if cold_snap else ("🔥" if power > 200 else "⚡")
    status = "COLD SNAP RECOVERY" if cold_snap else ("HIGH LOAD" if power > 200 else "NOMINAL")

    efficiency_pct = efficiency * 100
    eta_bar = "█" * int(efficiency * 10) + "░" * (10 - int(efficiency * 10))

    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{emoji} Thermodynamic Kernel · {status}",
                "emoji": True,
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Power*\n`{power:.1f}W`"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*η_thermo*\n`{efficiency_pct:.1f}%` {eta_bar}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Temperature*\n`{temperature:.1f}°C`"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Cold Snap*\n`{'ACTIVE 🧊' if cold_snap else 'INACTIVE'}`"
                },
            ]
        },
        *([{
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":snowflake: *Cold Snap active* — High-compute operations throttled. Edge Agent background processing continues. Expected recovery in 5 minutes."
            }
        }] if cold_snap else [])
    ]


def build_compliance_block(directive_id: str, violations: list[str]) -> list:
    """Build PSF compliance violation alert blocks."""
    severity = "🚨" if len(violations) > 2 else "⚠️"

    violation_text = "\n".join(f"• {v}" for v in violations)

    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{severity} PSF Compliance Violation",
                "emoji": True,
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Directive:* `{directive_id}`\n*Violations ({len(violations)}):*\n{violation_text}"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Required:* $25k Year 1 ARR floor · Dual-staffing mandate · \"Deployment: Foundations\" terminology"
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Review SOW"},
                    "style": "danger",
                    "value": f"review_{directive_id}"
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Override"},
                    "value": f"override_{directive_id}"
                }
            ]
        }
    ]


def build_directive_block(directive: Any, result: dict) -> list:
    """Build directive processing summary block."""
    type_labels = {
        "vector_1": ("HIGH_LEVERAGE_PORTFOLIO", "🏆"),
        "doe_phase_1": ("DOE_MISSION_ALIGNED", "🔬"),
        "active_foreground": ("EXECUTION_QUEUE", "⚙️"),
        "psf_verification": ("PSF_COMPLIANCE", "✅"),
        "cold_snap": ("THERMODYNAMIC_GATE", "🧊"),
        "13_streams": ("REVENUE_PIPELINE", "💰"),
    }

    dtype_val = directive.directive_type.value
    label, emoji = type_labels.get(dtype_val, (dtype_val, "📋"))

    tier = result.get("tier_used", "?")
    tier_model = {1: "Haiku", 2: "Sonnet", 3: "Opus"}.get(tier, "?")

    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{emoji} *{label}* · Priority `{directive.priority}/10`\n`{directive.id}`"
            },
            "accessory": {
                "type": "mrkdwn",
                "text": f"Tier {tier} ({tier_model})"
            } if False else None  # Accessory must be a valid block element
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Source*\n`{directive.source}`"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Model Tier*\n`Tier {tier}` ({tier_model})"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Cost*\n`${result.get('cost_estimate_usd', 0):.6f}`"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Latency*\n`{result.get('latency_ms', 0):.1f}ms`"
                },
            ]
        },
    ]
