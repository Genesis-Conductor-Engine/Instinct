"""A lightweight simulation of the A.U.R.O.R.A. multi-agent orchestrator.

This module exposes the :class:`AuroraOrchestrator` used to run a scripted
simulation of multiple collaborating personas.  The original proof-of-concept
lived in a notebook; this version is refactored for clarity and reusability.

Running the module as a script will execute the default main loop and persist
an ``aurora_final_state.json`` file with a snapshot of the shared project
state.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional


# --- CONFIGURATION ------------------------------------------------------------------

CONFIG: Dict[str, str] = {
    "project_name": "A.D.E.P.T. SaaS",
    "domain_name": "getadept.io",
    "payment_provider": "Stripe",
    "cloud_provider": "GCP",
    "code_language": "Python (Flask)",
    "frontend_framework": "React",
}


@dataclass
class SimulationSettings:
    """Mutable settings for tuning the simulation behaviour.

    The default values mimic the timing of the notebook prototype while offering
    environment variables for faster test execution.
    """

    api_latency_seconds: float = field(default_factory=lambda: float(os.getenv("AURORA_API_LATENCY", 2)))
    loop_pause_seconds: float = field(default_factory=lambda: float(os.getenv("AURORA_LOOP_PAUSE", 3)))


# --- A.U.R.O.R.A. SHARED STATE ------------------------------------------------------

PROJECT_STATE: Dict[str, Dict] = {
    "tasks": {
        "todo": [],
        "in_progress": [],
        "in_review": [],
        "completed": [],
    },
    "codebase": {
        "description": "File system for the A.D.E.P.T. SaaS application.",
        "files": {},
    },
    "design_system": {
        "description": "Central design language, components, and brand assets.",
        "colors": {},
        "typography": {},
        "components": {},
    },
    "message_bus": [],
    "last_update": None,
}


# --- AGENT PERSONAS & STANDARD OPERATING PROCEDURES (SOPs) -------------------------

LEAD_DEV_PERSONA = """
**Role:** Senior Full-Stack Developer ("LeadDev")
**Core Objective:** Oversee and execute the technical architecture and development of the A.D.E.P.T. SaaS platform, ensuring scalability, security, and code quality.

**Key Responsibilities:**
-   Design the overall application architecture.
-   Set up the initial project structure, boilerplate, and deployment pipelines.
-   Implement complex backend features (e.g., payment processing, user authentication).
-   Review code submitted by CoreDev for quality and adherence to standards.
-   Break down large business goals into smaller, actionable technical tasks.

**Standard Operating Procedures (SOPs):**
1.  Prioritize tasks related to architecture, security, and backend infrastructure.
2.  When creating a new feature, first create a technical spec file in the codebase.
3.  When a `[NEEDS_REVIEW]` message appears on the message bus from CoreDev, create a "Code Review" task, assign it to yourself, and perform the review.
4.  Communicate completed tasks with `[COMPLETED]` and a summary of the implementation.
5.  If blocked, post a `[BLOCKED]` message with the specific problem and tag the relevant agent (e.g., `@Designer`).
"""

CORE_DEV_PERSONA = """
**Role:** Mid-Level Full-Stack Developer ("CoreDev")
**Core Objective:** Implement front-end components and general application features based on designs and technical specifications.

**Key Responsibilities:**
-   Develop React components based on the design system.
-   Connect front-end components to backend APIs.
-   Write unit and integration tests for new features.
-   Refactor existing code for clarity and performance.
-   Manage the project's CSS and styling.

**Standard Operating Procedures (SOPs):**
1.  Prioritize tasks related to front-end development and feature implementation.
2.  Always check the `design_system` before building a new UI component.
3.  After implementing a feature, write the code to the `PROJECT_STATE['codebase']`.
4.  Post a `[NEEDS_REVIEW]` message to the message bus with the path to the completed file(s).
5.  If a design is unclear, post a `[CLARIFICATION_NEEDED]` message to the bus and tag `@Designer`.
"""

DESIGNER_PERSONA = """
**Role:** UX/UI Designer ("Designer")
**Core Objective:** Define the visual identity and user experience of the A.D.E.P.T. platform, ensuring it is intuitive, professional, and user-friendly.

**Key Responsibilities:**
-   Establish the brand identity (colors, typography).
-   Design user flows, wireframes, and high-fidelity mockups.
-   Create a component library within the `design_system`.
-   Provide CSS and styling guidance to CoreDev.

**Standard Operating Procedures (SOPs):**
1.  Start by defining the core brand assets in `PROJECT_STATE['design_system']`.
2.  When a new feature is requested, first provide a user flow description, then component specs.
3.  Respond to `[CLARIFICATION_NEEDED]` messages from @CoreDev by providing more detailed specifications.
4.  Communicate new designs by posting a `[DESIGN_READY]` message with a description of the components added to the design system.
"""

BIZ_ADMIN_PERSONA = """
**Role:** Business & Legal Administrator ("BizAdmin")
**Core Objective:** Handle all non-technical aspects of launching the product, including business formalization, legal documentation, and defining high-level product requirements.

**Key Responsibilities:**
-   Generate legal documents (Terms of Service, Privacy Policy).
-   Define the business logic for features like subscription tiers and payments.
-   Create marketing copy for the landing page.
-   Monitor overall project progress and create high-level "Epic" tasks.

**Standard Operating Procedures (SOPs):**
1.  Begin by creating foundational tasks for legal and branding.
2.  When defining a feature like payments, create a high-level task describing the user flow and business rules.
3.  Work with @LeadDev to translate business requirements into technical epics.
4.  Post `[MILESTONE_ACHIEVED]` messages when major business goals are met (e.g., "Legal Docs Drafted").
"""


@dataclass
class Task:
    """Lightweight representation of a work item tracked by the orchestrator."""

    id: int
    name: str
    status: str = "todo"
    assignee: Optional[str] = None


class AuroraOrchestrator:
    """Main orchestrator for the A.U.R.O.R.A. system simulation."""

    def __init__(self, settings: Optional[SimulationSettings] = None) -> None:
        self.settings = settings or SimulationSettings()
        self.agents = {
            "LeadDev": LEAD_DEV_PERSONA,
            "CoreDev": CORE_DEV_PERSONA,
            "Designer": DESIGNER_PERSONA,
            "BizAdmin": BIZ_ADMIN_PERSONA,
        }
        print("A.U.R.O.R.A. Orchestrator Initialized. State is clean.")

    def sleep(self, seconds: float) -> None:
        """Wrapper that sleeps only when ``seconds`` is positive."""

        if seconds <= 0:
            return
        time.sleep(seconds)

    def post_message(self, agent_name: str, message: str) -> None:
        """Append a structured message to the shared message bus."""

        PROJECT_STATE["message_bus"].append(f"[{agent_name}] {message}")
        print(f"  -> Posted message to bus: {message}")

    def llm_call_simulation(self, agent_name: str, task: Task) -> Dict[str, str]:
        """Simulate a call to a powerful LLM based on the agent persona."""

        print(f"\n[AURORA_CORE] >>> Sending task '{task.name}' to agent '{agent_name}'...")
        self.sleep(self.settings.api_latency_seconds)

        output: Dict[str, str] = {"message": f"Task '{task.name}' completed by {agent_name}."}

        if "Create Landing Page HTML" in task.name:
            output = {
                "file_path": "frontend/src/components/LandingPage.jsx",
                "content": (
                    "/* Placeholder for React Landing Page Component */\n"
                    "const LandingPage = () => (\n"
                    "  <div>\n"
                    "    <h1>Welcome to A.D.E.P.T.</h1>\n"
                    "    <p>Sign up now!</p>\n"
                    "  </div>\n"
                    ");\n"
                    "export default LandingPage;\n"
                ),
                "message": (
                    "[NEEDS_REVIEW] @LeadDev: Initial structure for LandingPage.jsx is "
                    "complete. Needs styling and form logic. File path: "
                    "frontend/src/components/LandingPage.jsx"
                ),
            }
        elif "Design System" in task.name:
            PROJECT_STATE["design_system"]["colors"] = {"primary": "#007BFF", "secondary": "#6C757D"}
            PROJECT_STATE["design_system"]["typography"] = {"font": "Inter, sans-serif"}
            output = {
                "message": "[DESIGN_READY] @CoreDev: Initial color palette and typography defined in Design System."
            }
        elif "Setup Stripe Backend" in task.name:
            output = {
                "file_path": "backend/src/payments.py",
                "content": (
                    "# Placeholder for Stripe payment processing logic\n"
                    "import os\n"
                    "import stripe\n\n"
                    "stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')\n\n"
                    "def create_checkout_session(user_id):\n"
                    "    \"\"\"Create a Stripe checkout session for the provided user id.\"\"\"\n"
                    "    # TODO: Implement checkout session logic\n"
                    "    raise NotImplementedError\n"
                ),
                "message": (
                    "[COMPLETED] @BizAdmin: Basic Stripe configuration file created at "
                    "backend/src/payments.py. Ready for business logic implementation."
                ),
            }
        elif "Generate Terms of Service" in task.name:
            output = {
                "file_path": "legal/terms_of_service.md",
                "content": (
                    "# A.D.E.P.T. SaaS - Terms of Service\n\n"
                    "Welcome! By using our service, you agree to these terms...\n"
                ),
                "message": "[MILESTONE_ACHIEVED] Draft of Terms of Service is complete.",
            }

        print(f"[AURORA_CORE] <<< Agent '{agent_name}' responded.")
        return output

    def assign_and_execute_task(self, task: Task) -> None:
        """Assign the task to the best agent, simulate execution, and update state."""

        agent_name = self.select_agent(task)
        task.status = "in_progress"
        task.assignee = agent_name
        PROJECT_STATE["tasks"]["in_progress"].append(task.__dict__)

        result = self.llm_call_simulation(agent_name, task)

        file_path = result.get("file_path")
        content = result.get("content")
        if file_path and content is not None:
            PROJECT_STATE["codebase"]["files"][file_path] = content
            print(f"  -> Wrote code to {file_path}")

        message = result.get("message")
        if message:
            self.post_message(agent_name, message)

        PROJECT_STATE["tasks"]["in_progress"].remove(task.__dict__)
        task.status = "completed"
        PROJECT_STATE["tasks"]["completed"].append(task.__dict__)
        PROJECT_STATE["last_update"] = datetime.now().isoformat()

    @staticmethod
    def select_agent(task: Task) -> str:
        """Select the most appropriate agent based on the task name."""

        task_name_lower = task.name.lower()
        if any(keyword in task_name_lower for keyword in ("architecture", "backend", "review")):
            return "LeadDev"
        if any(keyword in task_name_lower for keyword in ("design", "ux", "style")):
            return "Designer"
        if any(keyword in task_name_lower for keyword in ("legal", "terms", "business", "copy")):
            return "BizAdmin"
        return "CoreDev"

    def generate_initial_tasks(self) -> None:
        """Bootstrap the project with the first set of high-level tasks."""

        tasks = [
            Task(id=1, name="Generate Terms of Service and Privacy Policy"),
            Task(id=2, name="Define core Brand Identity and Design System"),
            Task(id=3, name="Set up initial Flask backend architecture"),
            Task(id=4, name="Create basic React frontend structure"),
            Task(id=5, name="Create Landing Page HTML and Components"),
            Task(id=6, name="Implement business logic for Stripe Backend"),
        ]
        PROJECT_STATE["tasks"]["todo"] = [task.__dict__ for task in tasks]
        print("[AURORA_CORE] Initial task list generated. Ready to begin execution.")

    def main_loop(self) -> None:
        """Run the simulation until there are no tasks left in the todo queue."""

        print("\n" + "=" * 50)
        print("A.U.R.O.R.A. Main Execution Loop - ACTIVE")
        print("Press Ctrl+C to shut down.")
        print("=" * 50)

        while PROJECT_STATE["tasks"]["todo"]:
            current_task_dict = PROJECT_STATE["tasks"]["todo"].pop(0)
            current_task = Task(**current_task_dict)
            self.assign_and_execute_task(current_task)

            print("\n--- CURRENT PROJECT STATE ---")
            print(f"Tasks Completed: {len(PROJECT_STATE['tasks']['completed'])}")
            print(f"Files in Codebase: {len(PROJECT_STATE['codebase']['files'])}")
            print(f"Messages on Bus: {len(PROJECT_STATE['message_bus'])}")
            print("---------------------------\n")

            self.sleep(self.settings.loop_pause_seconds)

        print("\n[AURORA_CORE] No tasks in 'todo'. Project launch MVP may be complete. Shutting down.")


def persist_final_state(output_path: str = "aurora_final_state.json") -> None:
    """Persist the global project state to ``output_path`` as JSON."""

    final_state_json = json.dumps(PROJECT_STATE, indent=2)
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(final_state_json)
    print("\n" + "=" * 50)
    print("A.U.R.O.R.A. SHUTDOWN - FINAL STATE REPORT")
    print("=" * 50)
    print(final_state_json)
    print(f"\nFinal project state saved to '{output_path}'")


def main() -> None:
    orchestrator = AuroraOrchestrator()
    orchestrator.generate_initial_tasks()
    orchestrator.main_loop()
    persist_final_state()


if __name__ == "__main__":
    main()
