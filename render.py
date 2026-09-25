"""The page itself: scoreboard, standings, power rankings, transactions.

One HTML file. Fonts load from Google when there's a network; the page falls back to the
system stack and works fine opened straight from disk.

The scoreboard is the point. Each matchup is one bar split at the live score, with a mark
where the projection has it finishing, so "am I winning, and will I still be winning" reads
in a glance.
"""
import html
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo("America/Chicago")

FONTS = "https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..800&display=swap"

FAVICON = (
    "data:image/svg+xml,"
    "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E"
    "%3Crect width='64' height='64' rx='14' fill='%2317181C'/%3E"
    "%3Crect x='8' y='27' width='20' height='10' rx='5' fill='%23C22740'/%3E"
    "%3Crect x='36' y='27' width='20' height='10' rx='5' fill='%231C6A86'/%3E"
    "%3Crect x='30' y='19' width='4' height='26' rx='2' fill='%23ECEDE5'/%3E"
    "%3C/svg%3E"
)

CSS = """
:root {
  --paper:#ECEDE5; --card:#FFF; --ink:#17181C; --muted:#6E7168; --line:#DCDDD3;
  --red:#C22740; --blue:#1C6A86; --band:#17181C; --bandink:#ECEDE5; --sunk:#E3E4DA;
  --shadow:0 1px 0 rgba(23,24,28,.04), 0 2px 10px rgba(23,24,28,.05);
}
@media (prefers-color-scheme:dark) {
  :root {
    --paper:#15181A; --card:#1D2124; --ink:#E9EAE4; --muted:#969C96; --line:#2C3236;
    --red:#F0566E; --blue:#63BBD4; --band:#0E1012; --bandink:#ECEDE5; --sunk:#171B1E;
    --shadow:none;
  }
}
* { box-sizing:border-box; }
html { -webkit-text-size-adjust:100%; }
body {
  margin:0; background:var(--paper); color:var(--ink);
  font:400 15px/1.5 Archivo,-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
  font-variant-numeric:tabular-nums;
}

/* marquee */
.marquee { background:var(--band); color:var(--bandink); padding:24px 20px 20px; border-bottom:3px solid var(--red); }
.marquee .inner { max-width:1180px; margin:0 auto; }
.marquee h1 {
  margin:0; font-size:clamp(29px,6.4vw,54px); line-height:.92; font-weight:800;
  font-stretch:125%; font-variation-settings:"wdth" 118,"wght" 800;
  text-transform:uppercase; letter-spacing:-.015em;
}
.status { margin-top:14px; display:flex; flex-wrap:wrap; align-items:center; gap:6px 12px;
  font-size:12px; font-weight:600; letter-spacing:.13em; text-transform:uppercase; color:#A6A8A0; }
.status span + span::before { content:"/"; margin-right:12px; opacity:.45; }
.status .now + span::before { opacity:.45; }
.status .now { color:var(--bandink); display:inline-flex; align-items:center; gap:7px; }
.dot { width:8px; height:8px; border-radius:50%; background:var(--red); animation:pulse 2s ease-in-out infinite; }
@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:.3; } }

main { max-width:1180px; margin:0 auto; padding:22px 20px 40px; display:grid; gap:20px; }
.cols { display:grid; grid-template-columns:1fr; gap:20px; }
.col { display:grid; gap:20px; align-content:start; }
@media (min-width:900px) { .cols { grid-template-columns:minmax(0,1.08fr) minmax(0,1fr); } }

section { animation:rise .45s cubic-bezier(.2,.7,.3,1) both; }
@keyframes rise { from { opacity:0; transform:translateY(10px); } to { opacity:1; transform:none; } }
@media (prefers-reduced-motion:reduce) {
  section { animation:none; }
  .dot { animation:none; }
}

h2 { margin:0; font-size:12px; font-weight:700; letter-spacing:.16em; text-transform:uppercase;
  font-variation-settings:"wdth" 112,"wght" 700; }
.head { display:flex; align-items:baseline; gap:12px; margin-bottom:12px; }
.head .rule { flex:1; height:1px; background:var(--line); }
.head .note { font-size:12px; color:var(--muted); }
.sub { color:var(--muted); font-size:13px; margin:-6px 0 14px; max-width:60ch; }

.card { background:var(--card); border:1px solid var(--line); border-radius:12px; box-shadow:var(--shadow); }

/* scoreboard */
.games { display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,340px),1fr)); gap:12px; }
.game { padding:14px 16px 16px; }
.game .row { display:flex; justify-content:space-between; align-items:baseline; gap:12px; }
.game .nm { font-weight:500; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.game .row.ahead .nm { font-weight:700; }
.game .pts { font-size:21px; font-weight:700; font-variation-settings:"wdth" 108,"wght" 700; white-space:nowrap; }
.game .row.ahead .pts { color:var(--ink); }
.game .row .pts { color:var(--muted); }
.game .row.ahead.away .pts { color:var(--red); }
.game .row.ahead.home .pts { color:var(--blue); }
.game .best { display:flex; justify-content:space-between; gap:12px; font-size:12px; color:var(--muted); margin-top:2px; }

/* the margin bar: center is a tie, the fill runs toward whoever leads */
.bar { position:relative; height:12px; border-radius:6px; background:var(--sunk); margin:12px 0 6px; }
.bar i { position:absolute; top:0; bottom:0; }
.bar i.away { background:var(--red); border-radius:6px 0 0 6px; }
.bar i.home { background:var(--blue); border-radius:0 6px 6px 0; }
.bar .mid { position:absolute; left:50%; top:-4px; bottom:-4px; width:2px; background:var(--ink); opacity:.28; transform:translateX(-1px); }
.bar .tick { position:absolute; top:-4px; bottom:-4px; width:2px; background:var(--ink); border-radius:1px; transform:translateX(-1px); opacity:.55; }
.game.pre .bar i { opacity:.5; }
.game.pre .bar .tick { display:none; }
.verdict { font-size:12px; font-weight:600; letter-spacing:.02em; margin-bottom:10px; }
.verdict.away { color:var(--red); } .verdict.home { color:var(--blue); }
.verdict.tied { color:var(--muted); }

/* tables */
.scroll { overflow-x:auto; }
table { width:100%; border-collapse:collapse; font-size:14px; }
th, td { text-align:left; padding:9px 10px; border-bottom:1px solid var(--line); white-space:nowrap; }
tbody tr:last-child td { border-bottom:0; }
th { color:var(--muted); font-size:11px; font-weight:700; letter-spacing:.1em; text-transform:uppercase; }
td.num, th.num { text-align:right; }
td.team { white-space:normal; min-width:11ch; }
.rank { color:var(--muted); width:2.2em; font-size:13px; }
.who { font-weight:600; }
.owner, .meta { color:var(--muted); font-size:12px; font-weight:400; }
tr.top td { background:color-mix(in srgb, var(--blue) 7%, transparent); }
.up { color:var(--blue); font-size:12px; font-weight:700; }
.down { color:var(--red); font-size:12px; font-weight:700; }
svg.spark { width:86px; height:20px; display:block; }

/* moves */
.moves { display:grid; gap:0; }
.move { display:grid; grid-template-columns:auto 1fr auto; align-items:baseline; gap:10px;
  padding:9px 16px; border-bottom:1px solid var(--line); font-size:14px; }
.move:last-child { border-bottom:0; }
.act { min-width:8.4em; text-align:center; font-size:11px; font-weight:700; letter-spacing:.08em; text-transform:uppercase;
  padding:2px 7px; border-radius:4px; border:1px solid var(--line); color:var(--muted); }
.act.add { color:var(--blue); border-color:color-mix(in srgb, var(--blue) 35%, transparent); }
.act.drop { color:var(--red); border-color:color-mix(in srgb, var(--red) 35%, transparent); }

.notice { padding:14px 16px; font-size:14px; border-left:3px solid var(--red); }
footer { max-width:1180px; margin:0 auto; padding:0 20px 34px; color:var(--muted); font-size:12px; }
a { color:inherit; }
:focus-visible { outline:2px solid var(--blue); outline-offset:2px; border-radius:3px; }
@media (max-width:560px) {
  main, footer, .marquee { padding-left:14px; padding-right:14px; }
  .game { padding:13px 14px 14px; }
  th, td { padding:8px 8px; }
  .byweek { display:none; }
  .move { grid-template-columns:auto 1fr; }
  .move .when { grid-column:2; }
}
"""


def esc(s):
    return html.escape(str(s), quote=True)


def head(title, note=""):
    n = f'<span class="note">{esc(note)}</span>' if note else ""
    return f'<div class="head"><h2>{esc(title)}</h2><span class="rule"></span>{n}</div>'


SEASON_WEEKS = 14   # regular season; the track fills in as the year goes


def spark(vals, avg, weeks=SEASON_WEEKS):
    """Points per week against a full-season track. At or above the team's own average is ink."""
    vals = [v for v in vals if v is not None][:weeks]
    if not vals:
        return ""
    top = max(vals + [1.0])
    W, H = 86, 20
    slot = W / weeks
    bw = slot - 1.6
    bars, tips = [], []
    for i in range(weeks):
        x = i * slot
        if i < len(vals):
            v = vals[i]
            h = max(2, v / top * (H - 2))
            fill = "var(--ink)" if v >= avg else "var(--line)"
            bars.append(f'<rect x="{x:.1f}" y="{H - h:.1f}" width="{bw:.1f}" height="{h:.1f}" fill="{fill}" rx="1"/>')
            tips.append(f"W{i + 1} {v:.1f}")
        else:
            bars.append(f'<rect x="{x:.1f}" y="{H - 1.5:.1f}" width="{bw:.1f}" height="1.5" fill="var(--line)" opacity=".55" rx=".75"/>')
    label = f"Points by week: {', '.join(tips)}"
    return (f'<svg class="spark" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(label)}">'
            f'<title>{esc(label)}</title>{"".join(bars)}</svg>')


MARGIN_CAP = 35.0   # a 35 point win fills the bar; anything past that is already a blowout


def matchup(m):
    """One game as a margin bar. Center is a tie, the fill runs toward whoever leads,
    and the mark is where the projection has the margin finishing."""
    live = (m.home_pts + m.away_pts) > 0
    lead = m.home_pts - m.away_pts if live else m.home_proj - m.away_proj
    plead = m.home_proj - m.away_proj

    def reach(margin):
        return min(abs(margin) / MARGIN_CAP, 1.0) * 50

    side = "home" if lead > 0 else "away" if lead < 0 else "tied"
    fill = ""
    if side == "home":
        fill = f'<i class="home" style="left:50%;width:{reach(lead):.1f}%"></i>'
    elif side == "away":
        fill = f'<i class="away" style="right:50%;width:{reach(lead):.1f}%"></i>'
    tick = 50 + reach(plead) * (1 if plead > 0 else -1)
    bar = (f'<div class="bar" role="img" aria-label="{esc(verdict_text(m, live, lead, side))}">'
           f'{fill}<span class="mid"></span><span class="tick" style="left:{tick:.1f}%"></span></div>')

    rows = []
    for which in ("away", "home"):
        pts, proj = getattr(m, f"{which}_pts"), getattr(m, f"{which}_proj")
        ahead = " ahead" if live and side == which else ""
        top = getattr(m, f"{which}_top")
        rows.append(
            f'<div class="row {which}{ahead}"><span class="nm">{esc(getattr(m, which))}</span>'
            f'<span class="pts">{pts:.1f}</span></div>'
            f'<div class="best"><span>{esc(top)}</span><span>proj {proj:.0f}</span></div>')

    return (f'<div class="card game{"" if live else " pre"}">{rows[0]}{bar}'
            f'<div class="verdict {side}">{esc(verdict_text(m, live, lead, side))}</div>{rows[1]}</div>')


def verdict_text(m, live, lead, side):
    """The answer in plain words, because that is what anyone opening this page wants."""
    if side == "tied":
        return "Tied"
    name = m.home if side == "home" else m.away
    if live:
        return f"{name} by {abs(lead):.1f}"
    return f"Projected: {name} by {abs(lead):.0f}"


def scoreboard(lg):
    if not lg.matchups:
        return ""
    live = any((m.home_pts + m.away_pts) > 0 for m in lg.matchups)
    note = "Bar is live points. The mark is the projected finish." if live else "Bars are projections. Nobody has played yet."
    return (f'<section style="animation-delay:.02s">{head(f"Week {lg.week}", note)}'
            f'<div class="games">{"".join(matchup(m) for m in lg.matchups)}</div></section>')


def standings(lg):
    rows = lg.standings()
    if not rows:
        return ""
    body = []
    for i, t in enumerate(rows, 1):
        owner = f'<div class="owner">{esc(t.owner)}</div>' if t.owner else ""
        body.append(
            f'<tr{" class=top" if i == 1 else ""}><td class="rank">{i}</td>'
            f'<td class="team"><span class="who">{esc(t.name)}</span>{owner}</td>'
            f'<td class="num">{esc(t.record)}</td><td class="num">{t.pf:.0f}</td>'
            f'<td class="num">{t.pa:.0f}</td><td class="num">{t.avg:.1f}</td>'
            f'<td class="byweek">{spark(t.scores, t.avg)}</td></tr>')
    return ('<section style="animation-delay:.08s">' + head("Standings", "wins, then points for") +
            '<div class="card scroll"><table><thead><tr><th></th><th>Team</th><th class="num">W-L</th>'
            '<th class="num">PF</th><th class="num">PA</th><th class="num">Avg</th><th class="byweek">By week</th>'
            f'</tr></thead><tbody>{"".join(body)}</tbody></table></div></section>')


def power(lg):
    """Season average, weighted toward the last three weeks, nudged by record."""
    rated = []
    for t in lg.teams:
        if not t.scores:
            continue
        games = t.wins + t.losses
        rated.append((0.55 * t.avg + 0.35 * t.recent + 10 * (t.wins / games if games else .5), t))
    if not rated:
        return ""
    rated.sort(key=lambda r: -r[0])
    place = {t.tid: i for i, t in enumerate(lg.standings(), 1)}
    body = []
    for i, (rating, t) in enumerate(rated, 1):
        d = place.get(t.tid, i) - i
        move = f'<span class="up">&#9650;{d}</span>' if d > 0 else f'<span class="down">&#9660;{abs(d)}</span>' if d < 0 else ""
        body.append(f'<tr{" class=top" if i == 1 else ""}><td class="rank">{i}</td>'
                    f'<td class="team"><span class="who">{esc(t.name)}</span> {move}</td>'
                    f'<td class="num">{rating:.1f}</td><td class="num">{t.avg:.1f}</td>'
                    f'<td class="num">{t.recent:.1f}</td></tr>')
    return ('<section style="animation-delay:.14s">' + head("Power") +
            '<div class="sub">Season average and the last three weeks, nudged by record. '
            'The arrow is how far a team sits from its spot in the standings.</div>'
            '<div class="card scroll"><table><thead><tr><th></th><th>Team</th><th class="num">Rating</th>'
            '<th class="num">Avg</th><th class="num">Last 3</th></tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div></section>')


def moves(lg, limit=14):
    recent = sorted(lg.moves, key=lambda m: -(m.ts or 0))[:limit]
    if not recent:
        return ""
    rows = []
    for m in recent:
        when = datetime.fromtimestamp(m.ts, timezone.utc).astimezone(LOCAL_TZ).strftime("%a %-I:%M %p") if m.ts else ""
        kind = "drop" if m.action == "drop" else "add"
        label = m.action + (f" ${m.bid}" if m.bid else "")
        where = " ".join(x for x in (m.pos, m.pro_team) if x)
        rows.append(f'<div class="move"><span class="act {kind}">{esc(label)}</span>'
                    f'<span><span class="who">{esc(m.player)}</span> <span class="meta">{esc(where)}</span>'
                    f'<div class="meta">{esc(m.team)}</div></span>'
                    f'<span class="meta when">{esc(when)}</span></div>')
    return ('<section style="animation-delay:.2s">' + head("Moves", f"last {len(recent)}") +
            f'<div class="card moves">{"".join(rows)}</div></section>')


def status_line(lg, now):
    bits = []
    if lg.live_games:
        word = "game" if lg.live_games == 1 else "games"
        bits.append(f'<span class="now"><span class="dot"></span>{lg.live_games} NFL {word} under way</span>')
    elif lg.next_kickoff:
        ko = lg.next_kickoff.astimezone(LOCAL_TZ)
        bits.append(f'<span class="now">Next kickoff {esc(ko.strftime("%a %-I:%M %p"))}</span>')
    bits.append(f'<span>Week {lg.week}</span>')
    bits.append(f'<span>{len(lg.teams)} teams</span>')
    bits.append(f'<span>Updated {esc(now.strftime("%-I:%M %p"))} Central</span>')
    return f'<div class="status">{"".join(bits)}</div>'


def render(lg):
    now = datetime.now(LOCAL_TZ)
    cards = (scoreboard(lg) +
             f'<div class="cols"><div class="col">{standings(lg)}</div>'
             f'<div class="col">{power(lg)}{moves(lg)}</div></div>')
    for w in lg.warnings:
        cards += f'<section>{head("Heads up")}<div class="card notice">{esc(w)}</div></section>'
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="300"><meta name="robots" content="noindex">
<meta name="theme-color" content="#17181C">
<title>{esc(lg.name)}</title>
<link rel="icon" href="{FAVICON}">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<style>{CSS}</style></head>
<body>
<header class="marquee"><div class="inner"><h1>{esc(lg.name)}</h1>{status_line(lg, now)}</div></header>
<main>{cards}</main>
<footer>Scores and projections from ESPN. Refreshes every five minutes. Unofficial, put together for the league.</footer>
</body></html>"""
