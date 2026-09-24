"""The page itself: scoreboard, standings, power rankings, transactions.

One self-contained HTML file, no external assets, so it works opened from disk or served
from Pages. Everything here is league-wide and public by design.
"""
import html
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo("America/Chicago")

FAVICON = (
    "data:image/svg+xml,"
    "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E"
    "%3Crect width='64' height='64' rx='12' fill='%231c1e21'/%3E"
    "%3Cellipse cx='32' cy='32' rx='22' ry='13' transform='rotate(-35 32 32)' fill='%238b4a24'"
    " stroke='%23f6f7f9' stroke-width='3'/%3E"
    "%3Cg stroke='%23f6f7f9' stroke-width='3' stroke-linecap='round'%3E"
    "%3Cpath d='M25 39 L39 25'/%3E"
    "%3Cpath d='M28 34 L32 38'/%3E%3Cpath d='M31 31 L35 35'/%3E%3Cpath d='M34 28 L38 32'/%3E"
    "%3C/g%3E%3C/svg%3E"
)

CSS = """
:root { --bg:#f6f7f9; --card:#fff; --ink:#1c1e21; --muted:#6b7280; --line:#e5e7eb; --good:#15803d; --bad:#b91c1c; --live:#2563eb; }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--ink); font:15px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif; }
header { padding:22px 20px 8px; }
header h1 { margin:0; font-size:22px; }
header .muted { color:var(--muted); font-size:13px; }
main { display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,440px),1fr)); gap:16px; padding:12px 20px 40px; }
.card { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:16px 18px; min-width:0; }
.card h2 { margin:0 0 2px; font-size:17px; }
.card .sub { color:var(--muted); font-size:13px; margin-bottom:12px; }
.wide { grid-column:1 / -1; }
.scroll { overflow-x:auto; }
table { width:100%; border-collapse:collapse; font-size:14px; }
th, td { text-align:left; padding:6px; border-bottom:1px solid var(--line); white-space:nowrap; }
td.team { white-space:normal; }
th { color:var(--muted); font-weight:500; font-size:12px; }
td.num, th.num { text-align:right; font-variant-numeric:tabular-nums; }
.games { display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr)); gap:10px; }
.game { border:1px solid var(--line); border-radius:8px; padding:10px 12px; }
.game .row { display:flex; justify-content:space-between; align-items:baseline; gap:10px; padding:3px 0; }
.game .row.lead { font-weight:600; }
.game .nm { min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.game .pts { font-variant-numeric:tabular-nums; font-size:18px; }
.game .meta { color:var(--muted); font-size:12px; margin-top:6px; white-space:normal; }
.game .proj { color:var(--muted); font-size:12px; font-weight:400; margin-left:6px; }
.rank { color:var(--muted); font-variant-numeric:tabular-nums; width:1.6em; }
.move { color:var(--muted); font-size:12px; }
svg.spark { width:70px; height:18px; display:block; }
.up { color:var(--good); } .down { color:var(--bad); }
footer { color:var(--muted); font-size:12px; padding:0 20px 28px; }
@media (max-width:480px) { main, header, footer { padding-left:12px; padding-right:12px; } .card { padding:14px; } }
"""


def esc(s):
    return html.escape(str(s), quote=True)


def spark(vals, avg):
    """Weekly team scores; grey below the team's own average, dark at or above."""
    vals = [v for v in vals if v is not None]
    if not vals:
        return ""
    top = max(vals + [1.0])
    W, H, n = 70, 18, len(vals)
    bw = max(2, min(7, (W - (n - 1) * 2) / n))
    bars, tips = [], []
    for i, v in enumerate(vals):
        h = max(1.5, v / top * (H - 1))
        fill = "var(--ink)" if v >= avg else "var(--muted)"
        bars.append(f'<rect x="{i * (bw + 2):.1f}" y="{H - h:.1f}" width="{bw:.1f}" height="{h:.1f}" fill="{fill}" opacity="0.85" rx="1"/>')
        tips.append(f"W{i + 1} {v:.1f}")
    return f'<svg class="spark" viewBox="0 0 {W} {H}"><title>{esc(", ".join(tips))}</title>{"".join(bars)}</svg>'


def scoreboard(lg):
    if not lg.matchups:
        return ""
    games = []
    for m in lg.matchups:
        rows = []
        lead = "home" if m.home_pts > m.away_pts else "away" if m.away_pts > m.home_pts else None
        for which in ("away", "home"):
            name = getattr(m, which)
            pts = getattr(m, f"{which}_pts")
            proj = getattr(m, f"{which}_proj")
            proj_s = f'<span class="proj">proj {proj:.0f}</span>' if proj else ""
            rows.append(f'<div class="row{" lead" if lead == which else ""}"><span class="nm">{esc(name)}</span>'
                        f'<span><span class="pts">{pts:.1f}</span>{proj_s}</span></div>')
        tops = [t for t in (m.away_top, m.home_top) if t]
        meta = f'<div class="meta">Top: {esc(", ".join(tops))}</div>' if tops else ""
        games.append(f'<div class="game">{"".join(rows)}{meta}</div>')
    return (f'<section class="card wide"><h2>Week {lg.week}</h2>'
            f'<div class="sub">Live points, with the projected finish beside them.</div>'
            f'<div class="games">{"".join(games)}</div></section>')


def standings(lg):
    rows = lg.standings()
    if not rows:
        return ""
    body = []
    for i, t in enumerate(rows, 1):
        owner = f'<span class="move">{esc(t.owner)}</span>' if t.owner else ""
        body.append(
            f'<tr><td class="rank">{i}</td><td class="team">{esc(t.name)} {owner}</td>'
            f'<td class="num">{esc(t.record)}</td>'
            f'<td class="num">{t.pf:.1f}</td><td class="num">{t.pa:.1f}</td>'
            f'<td class="num">{t.avg:.1f}</td><td>{esc(t.streak)}</td>'
            f'<td>{spark(t.scores, t.avg)}</td></tr>')
    return ('<section class="card"><h2>Standings</h2><div class="sub">Sorted by wins, then points for.</div>'
            '<div class="scroll"><table><thead><tr><th></th><th>Team</th><th class="num">W-L</th>'
            '<th class="num">PF</th><th class="num">PA</th><th class="num">Avg</th><th>Strk</th><th>By week</th>'
            f'</tr></thead><tbody>{"".join(body)}</tbody></table></div></section>')


def power(lg):
    """Season average, weighted toward the last three weeks, nudged by actual record."""
    rated = []
    for t in lg.teams:
        if not t.scores:
            continue
        games = t.wins + t.losses
        win_pct = t.wins / games if games else 0.5
        rated.append((0.55 * t.avg + 0.35 * t.recent + 10 * win_pct, t))
    if not rated:
        return ""
    rated.sort(key=lambda r: -r[0])
    place = {t.tid: i for i, t in enumerate(lg.standings(), 1)}
    body = []
    for i, (rating, t) in enumerate(rated, 1):
        delta = place.get(t.tid, i) - i          # ahead of (or behind) where the standings have them
        move = f'<span class="up">+{delta}</span>' if delta > 0 else f'<span class="down">{delta}</span>' if delta < 0 else ""
        body.append(f'<tr><td class="rank">{i}</td><td class="team">{esc(t.name)} {move}</td>'
                    f'<td class="num">{rating:.1f}</td><td class="num">{t.avg:.1f}</td>'
                    f'<td class="num">{t.recent:.1f}</td></tr>')
    return ('<section class="card"><h2>Power rankings</h2>'
            '<div class="sub">Season average and last three weeks, nudged by record. The number beside a team is the gap against the standings.</div>'
            '<div class="scroll"><table><thead><tr><th></th><th>Team</th><th class="num">Rating</th>'
            '<th class="num">Avg</th><th class="num">Last 3</th></tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div></section>')


def transactions(lg, limit=15):
    moves = sorted(lg.moves, key=lambda m: -(m.ts or 0))[:limit]
    if not moves:
        return ""
    rows = []
    for m in moves:
        when = datetime.fromtimestamp(m.ts, timezone.utc).astimezone(LOCAL_TZ).strftime("%a %-I:%M %p") if m.ts else ""
        bid = f" (${m.bid})" if m.bid else ""
        where = " ".join(x for x in (m.pos, m.pro_team) if x)
        rows.append(f'<tr><td class="team">{esc(m.team)}</td><td>{esc(m.action + bid)}</td>'
                    f'<td class="team">{esc(m.player)} <span class="move">{esc(where)}</span></td>'
                    f'<td class="move">{esc(when)}</td></tr>')
    return ('<section class="card"><h2>Transactions</h2><div class="sub">Most recent league moves.</div>'
            '<div class="scroll"><table><thead><tr><th>Team</th><th>Move</th><th>Player</th><th></th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div></section>')


def render(lg):
    now = datetime.now(LOCAL_TZ)
    cards = scoreboard(lg) + standings(lg) + power(lg) + transactions(lg)
    for w in lg.warnings:
        cards += f'<section class="card wide"><h2>Heads up</h2><div class="down">{esc(w)}</div></section>'
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="300"><title>{esc(lg.name)}</title>
<meta name="robots" content="noindex">
<link rel="icon" href="{FAVICON}"><style>{CSS}</style></head>
<body><header><h1>{esc(lg.name)}</h1>
<div class="muted">Week {lg.week} \u00b7 updated {now.strftime("%a %b %-d, %-I:%M %p")} Central \u00b7 refreshes every 5 min</div></header>
<main>{cards}</main>
<footer>Scores and projections from ESPN. Unofficial, put together for the league.</footer></body></html>"""
