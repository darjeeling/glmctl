#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "rich>=13.0.0",
#     "schedule>=1.2.0",
#     "pydantic-ai-slim[anthropic]",
#     "python-dotenv",
# ]
# ///
"""
AI Idle Monitor with TUI
Monitors AI assistant activity files and executes actions when idle at top of each hour.
Supports both Claude and GLM systems.
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import schedule
from dotenv import dotenv_values
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


class BaseAIMonitor(ABC):
    """Base class for AI activity monitoring."""

    def __init__(
        self,
        name: str,
        directory: str,
        prompt: str,
        monitor_base_path: Path,
    ):
        self.name = name
        self.directory = Path(directory).resolve()
        self.prompt = prompt
        self.monitor_base_path = monitor_base_path
        self.check_interval = 0.5  # minutes (30 seconds)
        self.idle_threshold = 10  # minutes

        self.last_activity_time: Optional[datetime] = None
        self.last_activity_file: Optional[str] = None
        self.last_activity_project_file: Optional[str] = None
        self.last_prompt: Optional[str] = None
        self.last_check_time: Optional[datetime] = None
        self.execution_logs: list[str] = []
        self.max_logs = 5

        # File paths to monitor
        self.history_file = monitor_base_path / "history.jsonl"
        self.projects_dir = monitor_base_path / "projects"

    def get_latest_modification_time(self) -> Optional[tuple[datetime, str, Optional[str]]]:
        """Get the most recent modification time and file paths.

        Returns:
            Tuple of (latest_time, latest_file, latest_project_file)
            - latest_time: Most recent modification time across all files
            - latest_file: Path to the most recently modified file (history or project)
            - latest_project_file: Path to the most recently modified project file (None if no project activity)
        """
        latest_time = None
        latest_file = None
        latest_project_time = None
        latest_project_file = None

        # Check history.jsonl
        if self.history_file.exists():
            mtime = datetime.fromtimestamp(self.history_file.stat().st_mtime)
            if latest_time is None or mtime > latest_time:
                latest_time = mtime
                latest_file = str(self.history_file)

        # Check all .jsonl files in projects directory
        if self.projects_dir.exists():
            for jsonl_file in self.projects_dir.rglob("*.jsonl"):
                mtime = datetime.fromtimestamp(jsonl_file.stat().st_mtime)

                # Track overall latest
                if latest_time is None or mtime > latest_time:
                    latest_time = mtime
                    latest_file = str(jsonl_file)

                # Track latest project file separately
                if latest_project_time is None or mtime > latest_project_time:
                    latest_project_time = mtime
                    latest_project_file = str(jsonl_file)

        if latest_time and latest_file:
            return (latest_time, latest_file, latest_project_file)
        return None

    def decode_project_id(self, project_id: str) -> str:
        """Decode project ID to actual file path.

        AI systems encode project paths like: -Users-dj-github-darjeeling-glmctl
        This decodes it back to: /Users/dj/github/darjeeling/glmctl
        """
        if project_id.startswith("-"):
            return "/" + project_id[1:].replace("-", "/")
        return project_id

    def get_last_prompt(self) -> Optional[str]:
        """Get the last prompt from history.jsonl file.

        Returns the 'display' field from the last line of history.jsonl.
        """
        try:
            if not self.history_file.exists():
                return None

            with open(self.history_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if not lines:
                    return None

                # Get last non-empty line
                for line in reversed(lines):
                    line = line.strip()
                    if line:
                        data = json.loads(line)
                        return data.get('display')

        except Exception:
            # Silently ignore errors
            pass

        return None

    def is_idle(self) -> bool:
        """Check if AI has been idle for longer than threshold."""
        if self.last_activity_time is None:
            return False

        idle_duration = datetime.now() - self.last_activity_time
        return idle_duration >= timedelta(minutes=self.idle_threshold)

    def get_idle_duration(self) -> Optional[timedelta]:
        """Get current idle duration."""
        if self.last_activity_time is None:
            return None
        return datetime.now() - self.last_activity_time

    def check_and_update_activity(self):
        """Check for activity and update last activity time."""
        self.last_check_time = datetime.now()
        result = self.get_latest_modification_time()

        if result:
            self.last_activity_time, self.last_activity_file, self.last_activity_project_file = result

        # Update last prompt from history.jsonl
        self.last_prompt = self.get_last_prompt()

    def add_log(self, message: str):
        """Add a log message (keep last N messages)."""
        self.execution_logs.append(f"[{self.name}] {message}")
        if len(self.execution_logs) > self.max_logs:
            self.execution_logs.pop(0)

    @abstractmethod
    def execute_when_idle(self):
        """Execute the action when system is idle.

        This method should be implemented by subclasses to define
        the specific action to take when the system is idle.
        """
        pass

    def run_if_idle(self):
        """Execute action if idle and at top of the hour."""
        if not self.is_idle():
            return

        now = datetime.now()
        if now.minute != 0:  # Only run at top of the hour
            return

        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] Executing in {self.directory}"
        self.add_log(log_msg)

        try:
            self.execute_when_idle()
        except Exception as e:
            self.add_log(f"[{timestamp}] Error: {type(e).__name__}: {str(e)[:100]}")


class ClaudeMonitor(BaseAIMonitor):
    """Monitor for Claude AI system."""

    def __init__(self, directory: str, prompt: str):
        super().__init__(
            name="Claude",
            directory=directory,
            prompt=prompt,
            monitor_base_path=Path.home() / ".claude",
        )

    def execute_when_idle(self):
        """Execute claude command."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            result = subprocess.run(
                ["claude", "-p", self.prompt],
                cwd=self.directory,
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode == 0:
                self.add_log(f"[{timestamp}] Execution completed successfully")
            else:
                self.add_log(f"[{timestamp}] Execution failed (returncode: {result.returncode})")
                if result.stderr:
                    # Log first 200 chars of stderr
                    stderr_msg = result.stderr[:200].replace('\n', ' ')
                    self.add_log(f"[{timestamp}] Error: {stderr_msg}")

        except subprocess.TimeoutExpired:
            self.add_log(f"[{timestamp}] Execution timed out (>300s)")
        except FileNotFoundError:
            self.add_log(f"[{timestamp}] Error: 'claude' command not found")
        except Exception as e:
            self.add_log(f"[{timestamp}] Error: {type(e).__name__}: {str(e)[:100]}")


class GLMMonitor(BaseAIMonitor):
    """Monitor for GLM AI system."""

    GLMENV_ENV = "~/.glmenv/env"

    def __init__(self, directory: str, prompt: str):
        super().__init__(
            name="GLM",
            directory=directory,
            prompt=prompt,
            monitor_base_path=Path.home() / ".glmenv" / "claude",
        )
        self.agent: Optional[Agent] = None
        self._initialize_agent()

    def _initialize_agent(self):
        """Initialize Pydantic AI agent with GLM configuration."""
        try:
            config = dotenv_values(Path(self.GLMENV_ENV).expanduser())

            if not config.get("ANTHROPIC_AUTH_TOKEN") or not config.get("ANTHROPIC_BASE_URL"):
                console.print(f"[yellow]Warning: GLM config incomplete in {self.GLMENV_ENV}[/yellow]")
                return

            model = AnthropicModel(
                "glm-4.5-air",
                provider=AnthropicProvider(
                    api_key=config["ANTHROPIC_AUTH_TOKEN"],
                    base_url=config["ANTHROPIC_BASE_URL"]
                )
            )
            self.agent = Agent(model)
        except Exception as e:
            console.print(f"[yellow]Warning: Failed to initialize GLM agent: {e}[/yellow]")
            self.agent = None

    def execute_when_idle(self):
        """Execute GLM API call."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if self.agent is None:
            self.add_log(f"[{timestamp}] Error: Agent not initialized")
            return

        try:
            # Execute the prompt via API
            result = self.agent.run_sync(self.prompt)

            # Log success with response preview
            response_preview = str(result.data)[:100]
            self.add_log(f"[{timestamp}] API call successful: {response_preview}...")

        except Exception as e:
            self.add_log(f"[{timestamp}] API call failed: {type(e).__name__}: {str(e)[:100]}")


class MultiMonitor:
    """Orchestrator for multiple AI monitors."""

    def __init__(
        self,
        claude_monitor: Optional[ClaudeMonitor] = None,
        glm_monitor: Optional[GLMMonitor] = None,
    ):
        self.claude_monitor = claude_monitor
        self.glm_monitor = glm_monitor
        self.running = True

    def get_active_monitors(self) -> list[BaseAIMonitor]:
        """Get list of active monitors."""
        monitors = []
        if self.claude_monitor:
            monitors.append(self.claude_monitor)
        if self.glm_monitor:
            monitors.append(self.glm_monitor)
        return monitors

    def check_all_activity(self):
        """Check activity for all monitors."""
        for monitor in self.get_active_monitors():
            monitor.check_and_update_activity()

    def run_all_if_idle(self):
        """Run all monitors if idle."""
        for monitor in self.get_active_monitors():
            monitor.run_if_idle()

    def generate_display(self) -> Layout:
        """Generate the TUI display for all monitors."""
        layout = Layout()
        monitors = self.get_active_monitors()

        if not monitors:
            return Layout(Panel("No monitors active", title="AI Idle Monitor"))

        # Create monitor panels
        monitor_panels = []
        for monitor in monitors:
            panel = self._create_monitor_panel(monitor)
            monitor_panels.append(Layout(panel))

        # Collect all logs
        all_logs = []
        for monitor in monitors:
            all_logs.extend(monitor.execution_logs)

        # Sort logs by timestamp (they start with [name] [timestamp])
        all_logs.sort()
        logs_text = "\n".join(all_logs[-10:]) if all_logs else "No executions yet"
        logs_panel = Layout(Panel(logs_text, title="Execution Log", border_style="green"))

        # Combine into layout
        if len(monitor_panels) == 1:
            layout.split_column(monitor_panels[0], logs_panel)
        else:
            monitors_layout = Layout()
            monitors_layout.split_row(*monitor_panels)
            layout.split_column(monitors_layout, logs_panel)

        return layout

    def _create_monitor_panel(self, monitor: BaseAIMonitor) -> Panel:
        """Create a panel for a single monitor."""
        table = Table.grid(padding=(0, 2))
        table.add_column(style="cyan", justify="right")
        table.add_column(style="white")

        # Current time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        table.add_row("Current Time:", current_time)

        # Last activity
        if monitor.last_activity_time:
            last_activity = monitor.last_activity_time.strftime("%Y-%m-%d %H:%M:%S")
            table.add_row("Last Activity:", last_activity)

            # Show last project (always show if available)
            if monitor.last_activity_project_file:
                project_path = Path(monitor.last_activity_project_file)
                try:
                    relative = project_path.relative_to(monitor.projects_dir)
                    project_id = relative.parts[0]
                    # Decode project ID to actual path
                    actual_path = monitor.decode_project_id(project_id)
                    table.add_row(
                        "Last Project:",
                        Text(actual_path, style="bold cyan")
                    )
                except ValueError:
                    pass

            # Show last prompt
            if monitor.last_prompt:
                # Truncate if too long
                prompt_display = monitor.last_prompt[:80] + "..." if len(monitor.last_prompt) > 80 else monitor.last_prompt
                table.add_row(
                    "Last Prompt:",
                    Text(prompt_display, style="dim white")
                )
        else:
            table.add_row("Last Activity:", "Checking...")

        # Idle status
        idle_duration = monitor.get_idle_duration()
        if idle_duration:
            minutes = int(idle_duration.total_seconds() / 60)
            if monitor.is_idle():
                idle_text = Text(f"IDLE ({minutes} minutes)", style="bold red")
            else:
                idle_text = Text(f"Active ({minutes} minutes since last activity)", style="bold green")
            table.add_row("Status:", idle_text)
        else:
            table.add_row("Status:", "Initializing...")

        # Next execution (if idle)
        if monitor.is_idle():
            next_hour = monitor.get_next_hour().strftime("%H:%M:%S")
            table.add_row("Next Execution:", Text(next_hour, style="bold yellow"))

        # Configuration
        table.add_row("", "")
        table.add_row("Target Directory:", str(monitor.directory))
        table.add_row("Prompt:", monitor.prompt[:40] + "..." if len(monitor.prompt) > 40 else monitor.prompt)

        return Panel(table, title=f"{monitor.name} Monitor", border_style="blue")

    def get_next_hour(self) -> datetime:
        """Get the next top of the hour."""
        now = datetime.now()
        next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        return next_hour

    def start(self):
        """Start the monitoring loop with TUI."""
        # Initial check
        self.check_all_activity()

        # Schedule tasks
        schedule.every(0.5).minutes.do(self.check_all_activity)
        schedule.every().hour.at(":00").do(self.run_all_if_idle)

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Run with live display
        with Live(self.generate_display(), refresh_per_second=1, console=console) as live:
            while self.running:
                schedule.run_pending()
                live.update(self.generate_display())
                time.sleep(1)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.running = False
        console.print("\n[yellow]Shutting down monitor...[/yellow]")
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description="Monitor AI activity and run commands when idle at top of each hour"
    )
    parser.add_argument(
        "-d", "--directory",
        default=None,
        help="Directory where commands will be executed (default: current directory)"
    )
    parser.add_argument(
        "--claude-prompt",
        default="analyze this project",
        help="Prompt to pass to Claude (default: 'analyze this project')"
    )
    parser.add_argument(
        "--glm-prompt",
        default="write haiku for me about today",
        help="Prompt to pass to GLM (default: 'analyze this project')"
    )
    parser.add_argument(
        "--claude-only",
        action="store_true",
        help="Monitor only Claude (default: monitor both)"
    )
    parser.add_argument(
        "--glm-only",
        action="store_true",
        help="Monitor only GLM (default: monitor both)"
    )

    args = parser.parse_args()

    # Validate mutual exclusivity
    if args.claude_only and args.glm_only:
        console.print("[red]Error: Cannot use --claude-only and --glm-only together[/red]")
        sys.exit(1)

    # Use current directory if not specified
    if args.directory is None:
        target_dir = Path.cwd()
    else:
        target_dir = Path(args.directory).resolve()
        if not target_dir.exists():
            console.print(f"[red]Error: Directory does not exist: {target_dir}[/red]")
            sys.exit(1)

    # Create monitors based on arguments
    claude_monitor = None
    glm_monitor = None

    if not args.glm_only:
        claude_monitor = ClaudeMonitor(
            directory=str(target_dir),
            prompt=args.claude_prompt,
        )

    if not args.claude_only:
        glm_monitor = GLMMonitor(
            directory=str(target_dir),
            prompt=args.glm_prompt,
        )

    # Create multi-monitor
    multi_monitor = MultiMonitor(
        claude_monitor=claude_monitor,
        glm_monitor=glm_monitor,
    )

    # Display startup info
    console.print("[green]Starting AI Idle Monitor...[/green]")
    if claude_monitor:
        console.print("[cyan]Monitoring Claude: ~/.claude/history.jsonl and ~/.claude/projects/**/*.jsonl[/cyan]")
    if glm_monitor:
        console.print("[cyan]Monitoring GLM: ~/.glmenv/claude/history.jsonl and ~/.glmenv/claude/projects/**/*.jsonl[/cyan]")
    console.print(f"[cyan]Target directory: {target_dir}[/cyan]")
    console.print()

    time.sleep(2)  # Brief pause before starting TUI
    multi_monitor.start()


if __name__ == "__main__":
    main()
