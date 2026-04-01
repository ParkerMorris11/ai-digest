#!/usr/bin/env python3
"""macOS launchd scheduler for AI Digest.

Installs a launchd plist that runs main.py on weekdays at 8:00 AM.

Usage:
  python3 install_schedule.py            # install
  python3 install_schedule.py --uninstall
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


_LABEL       = "com.aidigest.daily"
_PLIST_PATH  = Path.home() / "Library" / "LaunchAgents" / f"{_LABEL}.plist"

_PLIST_TEMPLATE = """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{label}</string>

    <key>ProgramArguments</key>
    <array>
        <string>{python}</string>
        <string>{script}</string>
    </array>

    <key>StartCalendarInterval</key>
    <array>
        <!-- Monday -->
        <dict>
            <key>Weekday</key><integer>1</integer>
            <key>Hour</key><integer>8</integer>
            <key>Minute</key><integer>0</integer>
        </dict>
        <!-- Tuesday -->
        <dict>
            <key>Weekday</key><integer>2</integer>
            <key>Hour</key><integer>8</integer>
            <key>Minute</key><integer>0</integer>
        </dict>
        <!-- Wednesday -->
        <dict>
            <key>Weekday</key><integer>3</integer>
            <key>Hour</key><integer>8</integer>
            <key>Minute</key><integer>0</integer>
        </dict>
        <!-- Thursday -->
        <dict>
            <key>Weekday</key><integer>4</integer>
            <key>Hour</key><integer>8</integer>
            <key>Minute</key><integer>0</integer>
        </dict>
        <!-- Friday -->
        <dict>
            <key>Weekday</key><integer>5</integer>
            <key>Hour</key><integer>8</integer>
            <key>Minute</key><integer>0</integer>
        </dict>
    </array>

    <key>WorkingDirectory</key>
    <string>{working_dir}</string>

    <key>StandardOutPath</key>
    <string>{log_dir}/ai-digest.log</string>

    <key>StandardErrorPath</key>
    <string>{log_dir}/ai-digest-error.log</string>

    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
"""


def _launchctl(*args: str) -> bool:
    result = subprocess.run(["launchctl", *args], capture_output=True, text=True)
    if result.returncode != 0 and result.stderr:
        print(f"  launchctl warning: {result.stderr.strip()}")
    return result.returncode == 0


def install() -> int:
    if sys.platform != "darwin":
        print("Error: launchd scheduling is only supported on macOS.")
        return 1

    python      = sys.executable
    script      = str(Path(__file__).parent.resolve() / "main.py")
    working_dir = str(Path(__file__).parent.resolve())
    log_dir     = str(Path.home() / ".ai-digest" / "logs")

    Path(log_dir).mkdir(parents=True, exist_ok=True)
    _PLIST_PATH.parent.mkdir(parents=True, exist_ok=True)

    plist_content = _PLIST_TEMPLATE.format(
        label=_LABEL,
        python=python,
        script=script,
        working_dir=working_dir,
        log_dir=log_dir,
    )
    _PLIST_PATH.write_text(plist_content)
    print(f"Wrote plist to {_PLIST_PATH}")

    # Unload first in case an older version is registered.
    _launchctl("unload", str(_PLIST_PATH))
    if _launchctl("load", str(_PLIST_PATH)):
        print(f"Scheduled: AI Digest will run weekdays at 8:00 AM.")
        print(f"Logs: {log_dir}/ai-digest.log")
    else:
        print("Warning: launchctl load returned a non-zero exit code.")
        print("The plist was written — you can load it manually with:")
        print(f"  launchctl load {_PLIST_PATH}")

    return 0


def uninstall() -> int:
    if not _PLIST_PATH.exists():
        print("No scheduled job found.")
        return 0

    _launchctl("unload", str(_PLIST_PATH))
    _PLIST_PATH.unlink()
    print(f"Removed {_PLIST_PATH}")
    print("AI Digest schedule uninstalled.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Install or remove the AI Digest launchd schedule.")
    parser.add_argument("--uninstall", action="store_true", help="Remove the scheduled job")
    args = parser.parse_args()
    return uninstall() if args.uninstall else install()


if __name__ == "__main__":
    sys.exit(main())
