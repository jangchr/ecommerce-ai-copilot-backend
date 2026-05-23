import argparse
import re
import shutil
from pathlib import Path


LATEST_DIR = Path("runs/latest")


def main():
    parser = argparse.ArgumentParser(description="Freeze runs/latest as a named regression baseline.")
    parser.add_argument("--name", default="l9_2", help="Baseline directory name under runs/baselines.")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.name):
        raise SystemExit("Baseline name may contain only letters, numbers, underscores, and hyphens.")

    baseline_dir = Path("runs/baselines") / args.name
    if not LATEST_DIR.exists():
        raise SystemExit("runs/latest does not exist. Run full regression first.")

    if baseline_dir.exists():
        print(f"{args.name} baseline already exists. Skip overwrite.")
        return

    baseline_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(LATEST_DIR, baseline_dir)
    print(f"{args.name} baseline frozen.")


if __name__ == "__main__":
    main()
