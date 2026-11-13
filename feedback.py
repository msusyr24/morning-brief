"""
Thumbs up / down feedback loop.

The page is static (GitHub Pages), so votes travel like this:
  1. Tapping 👍/👎 on an item stores the vote in the browser.
  2. "Send votes" opens a pre-filled GitHub issue titled "Brief feedback ...".
     You tap Submit. (Only issues opened by the repo owner are trusted.)
  3. The next run reads those issues, appends the votes to feedback.json,
     and closes the issues. Triage then sees a summary of your recent taste.
"""

import json
import os
import re
from collections import Counter
from datetime import datetime, timezone

import requests

FILE = "feedback.json"
REPO = os.getenv("GITHUB_REPOSITORY", "msusyr24/morning-brief")
KEEP = 500  # most recent votes kept
_LINE = re.compile(r"^\s*([+\-])\s*\|\s*(.+?)\s*\|\s*(.+?)\s*$")


def _load():
    if os.path.exists(FILE):
        with open(FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"votes": []}


def _save(data):
    data["votes"] = data["votes"][-KEEP:]
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)


def ingest(health):
    """Pull votes from open 'Brief feedback' issues into feedback.json."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return 0
    owner = REPO.split("/")[0].lower()
    h = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    try:
        r = requests.get(f"https://api.github.com/repos/{REPO}/issues",
                         params={"state": "open", "per_page": 50}, headers=h, timeout=15)
        r.raise_for_status()
        issues = r.json()
    except Exception as e:
        health["Feedback"] = ("warn", f"couldn't read issues ({type(e).__name__})")
        return 0

    data = _load()
    added = 0
    for iss in issues:
        if "pull_request" in iss or not iss.get("title", "").startswith("Brief feedback"):
            continue
        if (iss.get("user") or {}).get("login", "").lower() != owner:
            continue  # public repo: ignore votes from anyone but the owner
        day = (iss.get("created_at") or "")[:10]
        n = 0
        for line in (iss.get("body") or "").splitlines():
            m = _LINE.match(line)
            if m:
                data["votes"].append({"v": 1 if m.group(1) == "+" else -1,
                                      "source": m.group(2)[:120], "title": m.group(3)[:300], "date": day})
                n += 1
        added += n
        try:
            requests.post(iss["comments_url"], headers=h, timeout=15,
                          json={"body": f"Recorded {n} vote{'s' if n != 1 else ''}. Thanks!"})
            requests.patch(iss["url"], headers=h, timeout=15, json={"state": "closed"})
        except Exception:
            pass
    if added:
        _save(data)
    health["Feedback"] = ("ok", f"{added} new votes · {len(data['votes'])} total")
    print(f"[feedback] {added} new votes")
    return added


def taste_text():
    """A short block for the triage prompt describing what the reader liked/disliked."""
    votes = _load()["votes"]
    if not votes:
        return ""
    by_src = Counter()
    for v in votes:
        # "Michael Saylor · Some Podcast" -> credit the person, not the host channel
        by_src[v["source"].split(" · ")[0]] += v["v"]
    liked_src = [s for s, n in by_src.most_common() if n >= 2][:12]
    disliked_src = [s for s, n in sorted(by_src.items(), key=lambda x: x[1]) if n <= -2][:12]
    recent = votes[-80:]
    likes = [f"{v['source']}: {v['title']}" for v in reversed(recent) if v["v"] > 0][:25]
    dislikes = [f"{v['source']}: {v['title']}" for v in reversed(recent) if v["v"] < 0][:25]

    parts = ["\nThe reader's own thumbs-up/down votes on past briefs (most direct signal of taste; "
             "use them to calibrate, and weigh them above the generic list when they conflict):"]
    if liked_src:
        parts.append("- Sources they keep liking: " + ", ".join(liked_src))
    if disliked_src:
        parts.append("- Sources they keep disliking: " + ", ".join(disliked_src))
    if likes:
        parts.append("- Recently liked:\n" + "\n".join(f"    + {t}" for t in likes))
    if dislikes:
        parts.append("- Recently disliked:\n" + "\n".join(f"    - {t}" for t in dislikes))
    return "\n".join(parts) + "\n"
