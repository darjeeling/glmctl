#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "rich>=13.0.0",
#     "schedule>=1.2.0",
# ]
# ///
"""
Claude Idle Monitor with TUI
Monitors Claude activity files and runs claude command when idle at top of each hour.
"""

import argparse
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import schedule
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


class ClaudeIdleMonitor:
    def __init__(
        self,
        directory: str,
        prompt: str,
        check_interval: int = 10,
        idle_threshold: int = 20,
    ):
        self.directory = Path(directory).resolve()
        self.prompt = prompt
        self.check_interval = check_interval  # minutes
        self.idle_threshold = idle_threshold  # minutes

        self.last_activity_time: Optional[datetime] = None
        self.last_check_time: Optional[datetime] = None
        self.execution_logs: list[str] = []
        self.max_logs = 5
        self.running = True

        # File paths to monitor
        self.history_file = Path.home() / ".claude" / "history.jsonl"
        self.projects_dir = Path.home() / ".claude" / "projects"

    def get_latest_modification_time(self) -> Optional[datetime]:
        """Get the most recent modification time from all monitored files."""
        latest_time = None

        # Check history.jsonl
        if self.history_file.exists():
            mtime = datetime.fromtimestamp(self.history_file.stat().st_mtime)
            if latest_time is None or mtime > latest_time:
                latest_time = mtime

        # Check all .jsonl files in projects directory
        if self.projects_dir.exists():
            for jsonl_file in self.projects_dir.rglob("*.jsonl"):
                mtime = datetime.fromtimestamp(jsonl_file.stat().st_mtime)
                if latest_time is None or mtime > latest_time:
                    latest_time = mtime

        return latest_time

    def is_idle(self) -> bool:
        """Check if Claude has been idle for longer than threshold."""
        if self.last_activity_time is None:
            return False

        idle_duration = datetime.now() - self.last_activity_time
        return idle_duration >= timedelta(minutes=self.idle_threshold)

    def get_idle_duration(self) -> Optional[timedelta]:
        """Get current idle duration."""
        if self.last_activity_time is None:
            return None
        return datetime.now() - self.last_activity_time

    def get_next_hour(self) -> datetime:
        """Get the next top of the hour."""
        now = datetime.now()
        next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        return next_hour

    def check_and_update_activity(self):
        """Check for activity and update last activity time."""
        self.last_check_time = datetime.now()
        latest_time = self.get_latest_modification_time()

        if latest_time:
            self.last_activity_time = latest_time

    def run_claude(self):
        """Execute claude command if idle."""
        if not self.is_idle():
            return

        now = datetime.now()
        if now.minute != 0:  # Only run at top of the hour
            return

        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] Executing claude in {self.directory}"
        self.add_log(log_msg)

        try:
            subprocess.run(
                ["claude", "-p", self.prompt],
                cwd=self.directory,
                capture_output=False,
                timeout=None,
            )
            self.add_log(f"[{timestamp}] Execution completed")
        except Exception as e:
            # Silently ignore errors as per requirements
            pass

    def add_log(self, message: str):
        """Add a log message (keep last N messages)."""
        self.execution_logs.append(message)
        if len(self.execution_logs) > self.max_logs:
            self.execution_logs.pop(0)

    def generate_display(self) -> Layout:
        """Generate the TUI display."""
        layout = Layout()

        # Create status table
        status_table = Table.grid(padding=(0, 2))
        status_table.add_column(style="cyan", justify="right")
        status_table.add_column(style="white")

        # Current time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status_table.add_row("Current Time:", current_time)

        # Last activity
        if self.last_activity_time:
            last_activity = self.last_activity_time.strftime("%Y-%m-%d %H:%M:%S")
            status_table.add_row("Last Activity:", last_activity)
        else:
            status_table.add_row("Last Activity:", "Checking...")

        # Idle status
        idle_duration = self.get_idle_duration()
        if idle_duration:
            minutes = int(idle_duration.total_seconds() / 60)
            if self.is_idle():
                idle_text = Text(f"IDLE ({minutes} minutes)", style="bold red")
            else:
                idle_text = Text(f"Active ({minutes} minutes since last activity)", style="bold green")
            status_table.add_row("Status:", idle_text)
        else:
            status_table.add_row("Status:", "Initializing...")

        # Last check
        if self.last_check_time:
            last_check = self.last_check_time.strftime("%H:%M:%S")
            status_table.add_row("Last Check:", last_check)

        # Next check
        next_check = (datetime.now() + timedelta(minutes=self.check_interval)).strftime("%H:%M:%S")
        status_table.add_row("Next Check:", next_check)

        # Next execution (if idle)
        if self.is_idle():
            next_hour = self.get_next_hour().strftime("%H:%M:%S")
            status_table.add_row("Next Execution:", Text(next_hour, style="bold yellow"))

        # Configuration
        status_table.add_row("", "")
        status_table.add_row("Check Interval:", f"{self.check_interval} minutes")
        status_table.add_row("Idle Threshold:", f"{self.idle_threshold} minutes")
        status_table.add_row("Target Directory:", str(self.directory))
        status_table.add_row("Prompt:", self.prompt[:50] + "..." if len(self.prompt) > 50 else self.prompt)

        # Create logs panel
        logs_text = "\n".join(self.execution_logs) if self.execution_logs else "No executions yet"

        # Combine into layout
        layout.split_column(
            Layout(Panel(status_table, title="Claude Idle Monitor", border_style="blue")),
            Layout(Panel(logs_text, title="Execution Log", border_style="green")),
        )

        return layout

    def start(self):
        """Start the monitoring loop with TUI."""
        # Initial check
        self.check_and_update_activity()

        # Schedule tasks
        schedule.every(self.check_interval).minutes.do(self.check_and_update_activity)
        schedule.every().hour.at(":00").do(self.run_claude)

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
        description="Monitor Claude activity and run commands when idle at top of each hour"
    )
    parser.add_argument(
        "-d", "--directory",
        required=True,
        help="Directory where claude command will be executed"
    )
    parser.add_argument(
        "-p", "--prompt",
        required=True,
        help="Prompt to pass to claude command"
    )
    parser.add_argument(
        "--check-interval",
        type=int,
        default=10,
        help="Check interval in minutes (default: 10)"
    )
    parser.add_argument(
        "--idle-threshold",
        type=int,
        default=20,
        help="Idle threshold in minutes (default: 20)"
    )

    args = parser.parse_args()

    # Validate directory
    target_dir = Path(args.directory).resolve()
    if not target_dir.exists():
        console.print(f"[red]Error: Directory does not exist: {target_dir}[/red]")
        sys.exit(1)

    # Create and start monitor
    monitor = ClaudeIdleMonitor(
        directory=str(target_dir),
        prompt=args.prompt,
        check_interval=args.check_interval,
        idle_threshold=args.idle_threshold,
    )

    console.print(f"[green]Starting Claude Idle Monitor...[/green]")
    console.print(f"[cyan]Monitoring: ~/.claude/history.jsonl and ~/.claude/projects/**/*.jsonl[/cyan]")
    console.print(f"[cyan]Target directory: {target_dir}[/cyan]")
    console.print()

    time.sleep(2)  # Brief pause before starting TUI
    monitor.start()


if __name__ == "__main__":
    main()
