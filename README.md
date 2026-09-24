# The Austin Powers Premiere

A public page for the league: this week's scoreboard, standings, power rankings, and
recent transactions. One self-contained HTML file, rebuilt on a schedule and served from
GitHub Pages, so anyone in the league can open the link on a phone with nothing to install.

## What's on it

- **Week scoreboard** — every matchup, live points, and a projected finish (points already
  banked, plus projections for anyone who hasn't kicked off), with each side's top scorer.
- **Standings** — W-L, PF, PA, weekly average, streak, and a bar per week of the season.
- **Power rankings** — season average and last three weeks, nudged by record. The number
  beside a team is how far it sits from its spot in the standings.
- **Transactions** — the last 15 moves, with FAAB bids where ESPN reports them.

## Run it

    python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
    cp .env.example .env        # fill in ESPN_S2 and SWID
    .venv/bin/python build.py --out site/index.html

`--week N` rebuilds a past week. Open `site/index.html` straight from disk; there are no
external assets.

## Credentials

The league is private, so ESPN needs a logged-in session. From a browser signed in to
espn.com: DevTools > Application > Cookies > espn.com, copy `espn_s2` and `SWID` (keep the
curly braces on SWID). They go in `.env` locally and in repo secrets for Actions.

The cookies expire every few months. When the build starts failing with "ESPN refused the
cookies", grab fresh ones.

## Publishing

`.github/workflows/publish.yml` builds the page and deploys it to Pages: Tuesday morning
after MNF, Thursday before kickoff, and every 15 minutes during Sunday and Monday game
windows. Repo secrets needed: `ESPN_S2` and `SWID` (the league id and season are defaults in `espn.py`). Enable Pages with source "GitHub Actions"
in repo settings first.

The page carries `noindex`, so it won't turn up in search. Anyone with the link can read it.

## Code

- `espn.py` — reads the league via [espn-api](https://github.com/cwendt94/espn-api) into
  plain dataclasses. No lineup logic, nothing team-specific.
- `render.py` — the HTML. Inline CSS, inline SVG sparklines and favicon.
- `build.py` — CLI that wires the two together.
