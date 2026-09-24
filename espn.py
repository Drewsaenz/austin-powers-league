"""ESPN fantasy football league reader.

One call, `fetch()`, turns a league into the plain data the page needs: standings,
this week's matchups with live and projected scores, and recent transactions.
Nothing team-specific: this is the whole league, the way everyone in it sees it.
"""
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

DEFAULT_LEAGUE_ID = 904472  # The Austin Powers Premiere; override with ESPN_LEAGUE_ID
TEAM_ALIASES = {"WSH": "WAS", "JAC": "JAX", "LA": "LAR", "OAK": "LV", "SD": "LAC"}
BENCH_SLOTS = {"BE", "Bench", "IR"}


def norm_team(abbr):
    return TEAM_ALIASES.get(abbr, abbr) if abbr else abbr


@dataclass
class TeamRow:
    tid: str
    name: str
    owner: str = ""
    record: str = ""
    wins: int = 0
    losses: int = 0
    pf: float = 0.0
    pa: float = 0.0
    scores: list = field(default_factory=list)   # points per completed week
    streak: str = ""

    @property
    def avg(self):
        return sum(self.scores) / len(self.scores) if self.scores else 0.0

    @property
    def recent(self):
        last = self.scores[-3:]
        return sum(last) / len(last) if last else 0.0


@dataclass
class Matchup:
    home: str
    away: str
    home_pts: float = 0.0
    away_pts: float = 0.0
    home_proj: float = 0.0
    away_proj: float = 0.0
    home_top: str = ""
    away_top: str = ""


@dataclass
class Move:
    ts: Optional[float]
    team: str
    action: str
    player: str
    pos: str = ""
    pro_team: str = ""
    bid: Optional[int] = None


@dataclass
class League:
    name: str
    season: int
    week: int
    teams: list = field(default_factory=list)
    matchups: list = field(default_factory=list)
    moves: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def standings(self):
        return sorted(self.teams, key=lambda t: (-t.wins, -t.pf))


def kickoffs(lg, week):
    """pro team -> kickoff datetime (UTC). Used to tell a game that has started from one that hasn't."""
    try:
        from espn_api.football.constant import PRO_TEAM_MAP
        sched = lg._get_pro_schedule(week)  # noqa: SLF001 (no public accessor)
    except Exception as e:  # noqa: BLE001
        print(f"warning: ESPN pro schedule failed: {e}", file=sys.stderr)
        return {}
    out = {}
    for tid, (_opp, ms) in sched.items():
        abbr = norm_team(PRO_TEAM_MAP.get(int(tid)))
        if abbr and ms:
            out[abbr] = datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)
    return out


def streak_of(team):
    """W3 / L2 from the team's outcome list."""
    outcomes = [o for o in (getattr(team, "outcomes", []) or []) if o and o != "U"]
    if not outcomes:
        return ""
    last, n = outcomes[-1], 0
    for o in reversed(outcomes):
        if o != last:
            break
        n += 1
    return f"{last[0].upper()}{n}"


def owner_of(team):
    owners = getattr(team, "owners", None) or []
    first = owners[0] if owners else {}
    if isinstance(first, dict):
        name = f"{first.get('firstName', '')} {first.get('lastName', '')}".strip()
        return name or first.get("displayName", "")
    return str(first or "")


def player_name(p):
    name = getattr(p, "name", "") or ""
    return f"{name} D/ST" if getattr(p, "position", "") == "D/ST" and "D/ST" not in name else name


def started(lineup):
    return [p for p in (lineup or []) if getattr(p, "slot_position", "") not in BENCH_SLOTS]


def side(team, lineup, kicks, now):
    """One half of a matchup: name, live points, projected finish, top scorer so far."""
    name = getattr(team, "team_name", None) or (f"team {team}" if team else "bye")
    players = started(lineup)
    pts = sum(float(getattr(p, "points", 0) or 0) for p in players)
    proj = 0.0
    for p in players:
        scored = float(getattr(p, "points", 0) or 0)
        ko = kicks.get(norm_team(getattr(p, "proTeam", "")))
        playing = bool(ko and now >= ko)
        # once a game is under way its points are the real number; before that, trust the projection
        proj += scored if playing else max(scored, float(getattr(p, "projected_points", 0) or 0))
    top = max(players, key=lambda p: float(getattr(p, "points", 0) or 0), default=None)
    top_s = ""
    if top is not None and float(getattr(top, "points", 0) or 0) > 0:
        top_s = f"{player_name(top)} {float(top.points):.1f}"
    return name, pts, proj, top_s


def fetch(week=None):
    """Read the league. ESPN_LEAGUE_ID, ESPN_SEASON, ESPN_S2 and SWID come from the environment."""
    from espn_api.football import League as ESPNLeague
    from espn_api.requests.espn_requests import ESPNAccessDenied

    league_id = int(os.environ.get("ESPN_LEAGUE_ID") or DEFAULT_LEAGUE_ID)
    season = int(os.environ.get("ESPN_SEASON") or datetime.now().year)
    s2, swid = os.environ.get("ESPN_S2"), os.environ.get("SWID")
    if not (s2 and swid):
        raise RuntimeError("ESPN_S2 and SWID are missing. See README, 'Credentials'.")
    try:
        lg = ESPNLeague(league_id=league_id, year=season, espn_s2=s2, swid=swid)
    except ESPNAccessDenied as e:
        raise RuntimeError(f"ESPN refused the cookies ({e}). Grab fresh espn_s2 and SWID from a logged-in tab.") from e

    week = week or lg.current_week
    out = League(name=lg.settings.name, season=season, week=week)

    for t in lg.teams:
        out.teams.append(TeamRow(
            tid=str(t.team_id), name=t.team_name, owner=owner_of(t),
            record=f"{t.wins}-{t.losses}" + (f"-{t.ties}" if t.ties else ""),
            wins=int(t.wins or 0), losses=int(t.losses or 0),
            pf=float(t.points_for or 0), pa=float(t.points_against or 0),
            scores=[float(x) for x in (t.scores or [])[:week] if x],
            streak=streak_of(t)))

    kicks = kickoffs(lg, week)
    now = datetime.now(timezone.utc)
    try:
        for b in lg.box_scores(week):
            h_name, h_pts, h_proj, h_top = side(b.home_team, b.home_lineup, kicks, now)
            a_name, a_pts, a_proj, a_top = side(b.away_team, b.away_lineup, kicks, now)
            out.matchups.append(Matchup(home=h_name, away=a_name, home_pts=h_pts, away_pts=a_pts,
                                        home_proj=h_proj, away_proj=a_proj, home_top=h_top, away_top=a_top))
    except Exception as e:  # noqa: BLE001
        out.warnings.append(f"No box scores for week {week}: {e}")

    try:
        for a in lg.recent_activity(size=30) or []:
            for team_obj, action, pl, bid in a.actions:
                if not hasattr(pl, "playerId"):
                    continue
                act = ("drop" if "DROPPED" in action else "waiver add" if "WAIVER" in action
                       else "trade" if "TRADED" in action else "add")
                out.moves.append(Move(ts=(a.date or 0) / 1000 or None,
                                      team=getattr(team_obj, "team_name", str(team_obj)),
                                      action=act, player=player_name(pl),
                                      pos=getattr(pl, "position", ""), pro_team=norm_team(getattr(pl, "proTeam", "")),
                                      bid=bid or None))
    except Exception as e:  # noqa: BLE001
        out.warnings.append(f"Transactions unavailable: {e}")

    return out
