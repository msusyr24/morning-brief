"""
Last night's basketball: every final NBA score plus any game involving a
Top-25 men's college team, from ESPN's public scoreboard JSON (no key needed).

"Last night" = the most recent US Eastern date whose games are all final, so a
run that starts while West Coast games are still on shows the previous slate.
"""

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from net import http_get

ET = ZoneInfo("America/New_York")
URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/{league}/scoreboard"


def _scoreboard(league, day, extra=""):
    url = URL.format(league=league) + f"?dates={day:%Y%m%d}&limit=400{extra}"
    resp, err = http_get(url, mode="direct_first", attempts=2, timeout=15, accept="application/json")
    if resp is None:
        raise RuntimeError(err)
    return resp.json().get("events", [])


def _parse(event):
    comp = event["competitions"][0]
    status = comp.get("status") or event.get("status") or {}
    stype = status.get("type", {})
    teams = []
    for c in comp.get("competitors", []):
        t = c.get("team", {})
        rank = (c.get("curatedRank") or {}).get("current", 99)
        leader = ""
        for group in c.get("leaders") or []:
            if group.get("name") == "points" and group.get("leaders"):
                top = group["leaders"][0]
                leader = f"{top.get('athlete', {}).get('shortName', '')} {top.get('displayValue', '')}".strip()
        teams.append({
            "abbr": t.get("abbreviation", "?"),
            "name": t.get("shortDisplayName") or t.get("displayName", "?"),
            "score": int(c.get("score") or 0),
            "home": c.get("homeAway") == "home",
            "winner": bool(c.get("winner")),
            "rank": rank if rank and rank <= 25 else None,
            "leader": leader,
        })
    teams.sort(key=lambda x: x["home"])  # away first
    return {
        "final": bool(stype.get("completed")),
        "detail": stype.get("shortDetail", ""),
        "teams": teams,
        "margin": abs(teams[0]["score"] - teams[1]["score"]) if len(teams) == 2 else 0,
        "ot": "OT" in stype.get("shortDetail", ""),
    }


def _latest_complete_slate(league, extra=""):
    """Most recent US-Eastern date with finished games. The brief runs at ~04:45
    in Romania (~21:45 ET), so the current night's late games are often still on:
    show the ones already final and count the rest."""
    today = datetime.now(timezone.utc).astimezone(ET).date()
    for back in range(0, 4):
        day = today - timedelta(days=back)
        games = [_parse(e) for e in _scoreboard(league, day, extra)]
        finals = [g for g in games if g["final"]]
        if finals:
            return day, finals, len(games) - len(finals)
    return None, [], 0


def get_hoops(health):
    out = {"nba": [], "ncaa": [], "nba_date": None, "ncaa_date": None, "nba_pending": 0, "ncaa_pending": 0}
    try:
        day, games, pending = _latest_complete_slate("nba")
        out["nba_date"], out["nba"], out["nba_pending"] = day, games, pending
        health["NBA scores"] = ("ok", f"{len(games)} games" if games else "no games")
    except Exception as e:
        health["NBA scores"] = ("fail", str(e)[:60])
    try:
        day, games, pending = _latest_complete_slate("mens-college-basketball", "&groups=50")
        ranked = [g for g in games if any(t["rank"] for t in g["teams"])]
        out["ncaa_pending"] = pending
        for g in ranked:
            w = next((t for t in g["teams"] if t["winner"]), None)
            l = next((t for t in g["teams"] if not t["winner"]), None)
            g["upset"] = bool(w and l and l["rank"] and (not w["rank"] or w["rank"] > l["rank"]))
        ranked.sort(key=lambda g: (not g["upset"], min(t["rank"] or 99 for t in g["teams"])))
        out["ncaa_date"], out["ncaa"] = day, ranked
        health["College scores"] = ("ok", f"{len(ranked)} ranked games" if ranked else "no ranked games")
    except Exception as e:
        health["College scores"] = ("fail", str(e)[:60])
    return out
