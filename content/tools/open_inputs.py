#!/usr/bin/env python3
"""Open one explicitly selected production's inputs in Finder."""
import argparse
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def inputs_path(episode):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}_[a-z0-9][a-z0-9-]*", episode):
        raise ValueError("Use a production ID such as 2026-09-21_nagging-environment")
    production = ROOT / "productions" / episode
    if not production.is_dir() or not production.resolve().is_relative_to(ROOT):
        raise ValueError("Production not found inside this content workspace")
    inputs = production / "inputs"
    if inputs.is_symlink() and not inputs.exists():
        raise ValueError("Inputs link is broken; repair it before opening")
    if not inputs.resolve().is_relative_to(ROOT):
        raise ValueError("Inputs points outside this content workspace")
    if inputs.exists() and not inputs.is_dir():
        raise ValueError("Inputs is not a directory")
    return inputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("episode", help="Explicit production ID; no automatic latest selection")
    parser.add_argument("--print-only", action="store_true", help="Validate and print without creating or opening")
    args = parser.parse_args()
    try:
        inputs = inputs_path(args.episode)
    except ValueError as error:
        parser.error(str(error))
    if not args.print_only:
        inputs.mkdir(exist_ok=True)
        subprocess.run(["/usr/bin/open", str(inputs)], check=True)
    print(inputs)


if __name__ == "__main__":
    main()
