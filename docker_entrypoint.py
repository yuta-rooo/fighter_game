from __future__ import annotations
import os
import subprocess
import sys

VALID_MODES = {"online", "cpu"}
VALID_DIFFICULTIES = {"easy", "normal", "hard"}

def main() -> None:
    mode = os.environ.get("GAME_MODE", "online").strip().lower()
    difficulty = os.environ.get("CPU_DIFFICULTY", "normal").strip().lower()
    internal_port = os.environ.get("INTERNAL_PORT", "5000").strip()

    if mode not in VALID_MODES:
        raise SystemExit(
            f"Invalid GAME_MODE={mode!r}. Use one of: {sorted(VALID_MODES)}"
        )

    if difficulty not in VALID_DIFFICULTIES:
        raise SystemExit(
            "Invalid CPU_DIFFICULTY="
            f"{difficulty!r}. Use one of: {sorted(VALID_DIFFICULTIES)}"
        )

    command = [
        sys.executable,
        "server.py",
        "--host",
        "0.0.0.0",
        "--port",
        internal_port,
    ]

    if mode == "cpu":
        command.extend(["--cpu", "--difficulty", difficulty])

    print("Starting server:", " ".join(command), flush=True)
    subprocess.run(command, check=True)

if __name__ == "__main__":
    main()
