from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
STREAMLIT_APP = PROJECT_ROOT / "frontend" / "streamlit_app.py"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Launch the Emotion Music Recommender application."
    )
    parser.add_argument(
        "mode",
        nargs="?",
        default="flask",
        choices=("flask", "streamlit"),
        help="App mode to run. Defaults to flask.",
    )
    return parser


def run_flask() -> int:
    try:
        from app.main import start_app
    except ImportError as exc:
        print(
            "Unable to start the Flask app because a dependency is missing.\n"
            f"Import error: {exc}\n"
            "Install the project requirements in a supported Python 3.13 "
            "virtual environment and try again.",
            file=sys.stderr,
        )
        return 1

    if not callable(start_app):
        print(
            "app.main.start_app is not callable. Check app/main.py.",
            file=sys.stderr,
        )
        return 1

    start_app()
    return 0


def run_streamlit() -> int:
    if not STREAMLIT_APP.exists():
        print(
            f"Streamlit app not found at {STREAMLIT_APP}.",
            file=sys.stderr,
        )
        return 1

    command = [sys.executable, "-m", "streamlit", "run", str(STREAMLIT_APP)]
    completed = subprocess.run(command, cwd=PROJECT_ROOT)
    return completed.returncode


def main() -> int:
    args = build_parser().parse_args()

    if args.mode == "streamlit":
        return run_streamlit()

    return run_flask()


if __name__ == "__main__":
    raise SystemExit(main())
