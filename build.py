#!/usr/bin/env python3
"""Build the league page.

    python build.py --out site/index.html

Credentials come from .env next to this file, or from the environment (which wins).
Output is one self-contained HTML file.
"""
import argparse
import os
import sys
import time
from pathlib import Path

import espn
import render

HERE = Path(__file__).resolve().parent


def load_dotenv(path=HERE / ".env"):
    """Minimal KEY=VALUE loader; the real environment wins over the file."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip("'\""))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(HERE / "index.html"), help="output HTML path")
    ap.add_argument("--week", type=int, help="NFL week (default: whatever ESPN says is current)")
    args = ap.parse_args()

    load_dotenv()
    lg = espn.fetch(week=args.week)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render.render(lg))
    print(f"{time.strftime('%Y-%m-%d %H:%M')} {lg.name} week {lg.week}: "
          f"{len(lg.teams)} teams, {len(lg.matchups)} matchups, {len(lg.moves)} moves -> {out}", file=sys.stderr)
    for w in lg.warnings:
        print(f"warning: {w}", file=sys.stderr)


if __name__ == "__main__":
    main()
