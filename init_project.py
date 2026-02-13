#!/usr/bin/env python3
"""
Project Initialization Script for Vision-MQTT-Servo-Tracking-System
Creates directory structure and starter files in the CURRENT directory.
"""

import sys
from pathlib import Path


def create_project_structure(base_path: Path):
    """Create the complete project directory and file structure."""

    project_files = [
        # PC Vision component
        "pc_vision/main.py",
        "pc_vision/vision.py",
        "pc_vision/mqtt_client.py",
        "pc_vision/requirements.txt",
        "pc_vision/config.py",

        # ESP8266 component
        "esp8266/main.py",
        "esp8266/servo.py",
        "esp8266/mqtt_client.py",
        "esp8266/boot.py",

        # Backend component
        "backend/server.py",
        "backend/mqtt_bridge.py",
        "backend/websocket_manager.py",
        "backend/requirements.txt",
        "backend/config.py",

        # Dashboard component
        "dashboard/index.html",
        "dashboard/script.js",
        "dashboard/style.css",

        # Root files
        ".gitignore",
        "README.md",
    ]

    print(f"\nCreating project structure in: {base_path.resolve()}\n")

    created_count = 0
    existing_count = 0

    for file_path in project_files:
        full_path = base_path / file_path

        try:
            # Create parent directories
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Create file if missing
            if not full_path.exists():
                full_path.touch()
                created_count += 1
                print(f"[+] Created: {file_path}")
            else:
                existing_count += 1
                print(f"[=] Exists:  {file_path}")

        except Exception as e:
            print(f"[!] Error creating {file_path}: {e}")

    print("\n--- Summary ---")
    print(f"Created files : {created_count}")
    print(f"Existing files: {existing_count}")
    print("Project initialization complete.\n")


if __name__ == "__main__":
    # Default → current directory
    base_dir = Path.cwd()

    # Optional: allow custom path
    if len(sys.argv) > 1:
        base_dir = Path(sys.argv[1])

    create_project_structure(base_dir)