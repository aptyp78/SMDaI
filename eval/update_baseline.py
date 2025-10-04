#!/usr/bin/env python3
import argparse
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "eval" / "metrics.json"
DST = ROOT / "eval" / "baseline.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Update baseline.json from metrics.json")
    parser.add_argument("--force", action="store_true", help="overwrite baseline without prompt")
    args = parser.parse_args()

    if not SRC.exists():
        sys.exit("metrics.json not found; run compute-baseline first.")
    if DST.exists() and not args.force:
        sys.exit("baseline.json exists; rerun with --force to overwrite.")

    shutil.copyfile(SRC, DST)
    print("baseline.json updated from metrics.json")


if __name__ == "__main__":
    main()
