"""
Fetchers: Hacker News, RSS/Atom feeds, YouTube channels + transcripts, article text.

Every fetcher returns plain dicts and records what happened in a `health` dict,
so the brief can show which sources failed instead of silently getting thinner.
"""

import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from html import unescape
from xml.etree import ElementTree

import feedparser
import requests
from bs4 import BeautifulSoup

from net import http_get, normalize_url

BOOTSTRAP_HOURS = 36  # first run with an empty ledger: only very recent items


def _clean(html_text, limit):
    text = re.sub(r"<[^>]+>", " ", html_text or "")
    text = re.sub(r"\s+", " ", unescape(text)).strip()
    return text[:limit]


def _too_old(published, days, ledger, key):
    """True if an item should be skipped for age. On the very first run (empty
    ledger) only the last 36h is shown and older in-window items are recorded
    as seen, so the second run doesn't flood with weeks of backlog."""
    now = datetime.now(timezone.utc)
    if published < now - timedelta(days=days):
        return True
    if ledger.bootstrap and published < now - timedelta(hours=BOOTSTRAP_HOURS):
        ledger.mark(key)
        return True
    return False


# ---------------------------------------------------------------- Hacker News
def fetch_hn(n, ledger, health):
    base = "https://hacker-news.firebaseio.com/v0"
    try:
        ids = requests.get(f"{base}/topstories.json", timeout=15).json()[:n]
    except Exception as e:
        health["Hacker News"] = ("fail", type(e).__name__)
        return []

    def one(sid):
        try:
            return requests.get(f"{base}/item/{sid}.json", timeout=10).json()
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=10) as pool:
        raw = list(pool.map(one, ids))

    stories = []
    for s in raw:
        if not s or not s.get("title") or s.get("dead") or s.get("deleted"):
            continue
        key = f"hn:{s['id']}"
        if ledger.has(key):
            continue
        discuss = f"https://news.ycombinator.com/item?id={s['id']}"
        stories.append({
            "key": key,
            "kind": "hn",
            "source": "Hacker News",
            "title": s["title"],
            "url": s.get("url") or discuss,
            "discussion_url": discuss,
            "points": s.get("score", 0),
            "comments": s.get("descendants", 0),
            "snippet": _clean(s.get("text", ""), 500),
            "content": "",
        })
    health["Hacker News"] = ("ok", f"{len(stories)} new") if raw else ("fail", "no items")
    return stories


# ---------------------------------------------------------------- RSS
def fetch_feed(name, cfg, ledger, default_days):
    lookback = cfg.get("lookback_days", default_days)
    resp, err = http_get(
        cfg["url"], mode=cfg.get("mode", "direct_first"), timeout=25,
        accept="application/atom+xml, application/rss+xml, application/xml, text/xml, */*",
    )
    if resp is None:
        return [], ("fail", err)

    feed = feedparser.parse(resp.content)
    if not feed.entries:
        why = str(getattr(feed, "bozo_exception", "")) or "0 entries"
        return [], ("fail", f"unparseable feed ({why[:60]})")

    items = []
    for entry in feed.entries[:30]:
        pub = entry.get("published_parsed") or entry.get("updated_parsed")
        if not pub:
            continue
        published = datetime(*pub[:6], tzinfo=timezone.utc)
        url = entry.get("link", "")
        key = f"url:{normalize_url(url)}"
        if ledger.has(key) or _too_old(published, lookback, ledger, key):
            continue
        full = ""
        if entry.get("content"):
            full = entry["content"][0].get("value", "")
        summary = entry.get("summary", "") or entry.get("description", "")
        items.append({
            "key": key,
            "kind": "rss",
            "source": name,
            "topic_hint": cfg["category"],
            "title": _clean(entry.get("title", ""), 300),
            "url": url,
            "published": published.isoformat(),
            "snippet": _clean(summary or full, 600),
            "content": _clean(full or summary, 9000),
        })
        if len(items) >= cfg.get("max_items", 5):
            break
    return items, ("ok", f"{len(items)} new" if items else "nothing new")


def fetch_all_rss(sources, ledger, health, default_days=3):
    out = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {name: pool.submit(fetch_feed, name, cfg, ledger, default_days)
                   for name, cfg in sources.items()}
        for name, fut in futures.items():
            try:
                items, status = fut.result()
            except Exception as e:
                items, status = [], ("fail", type(e).__name__)
            health[name] = status
            if status[0] != "ok":
                print(f"[RSS] {name}: {status[1]}")
            out.extend(items)
    print(f"[RSS] {len(out)} new items from {len(sources)} feeds")
    return out


# ---------------------------------------------------------------- YouTube
_YT_NS = {"atom": "http://www.w3.org/2005/Atom",
          "yt": "http://www.youtube.com/xml/schemas/2015"}


def fetch_channel(name, channel_id, ledger, lookback_days, max_videos):
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    resp, err = http_get(url, mode="proxy_first", attempts=3, timeout=15,
                         accept="application/atom+xml, application/xml, */*", backoff=4)
    if resp is None:
        return [], ("fail", err)
    body = resp.content.lstrip()
    if not (body.startswith(b"<?xml") or body.startswith(b"<feed")):
        return [], ("fail", "non-XML response")
    try:
        root = ElementTree.fromstring(body)
    except Exception:
        return [], ("fail", "XML parse error")

    videos = []
    for entry in root.findall("atom:entry", _YT_NS):
        vid = entry.findtext("yt:videoId", default="", namespaces=_YT_NS)
        published = datetime.fromisoformat(
            entry.findtext("atom:published", default="1970-01-01T00:00:00+00:00",
                           namespaces=_YT_NS))
        if not vid or ledger.has(f"yt:{vid}") or _too_old(published, lookback_days, ledger, f"yt:{vid}"):
            continue
        link = entry.find("atom:link", _YT_NS).attrib.get("href", "")
        videos.append({
            "key": f"yt:{vid}",
            "kind": "video",
            "source": name,
            "video_id": vid,
            "title": entry.findtext("atom:title", default="", namespaces=_YT_NS),
            "url": f"https://www.youtube.com/watch?v={vid}",
            "is_short": "/shorts/" in link,
            "published": published.isoformat(),
            "snippet": "",
            "content": "",
        })
        if len(videos) >= max_videos:
            break
    n_entries = len(root.findall("atom:entry", _YT_NS))
    return videos, ("ok", f"{len(videos)} new" if videos else f"nothing new ({n_entries} in feed)")


def _transcript_api():
    from youtube_transcript_api import YouTubeTranscriptApi
    user = os.getenv("WEBSHARE_PROXY_USERNAME")
    if user:
        from youtube_transcript_api.proxies import WebshareProxyConfig
        return YouTubeTranscriptApi(proxy_config=WebshareProxyConfig(
            proxy_username=user,
            proxy_password=os.getenv("WEBSHARE_PROXY_PASSWORD"),
        ))
    return YouTubeTranscriptApi()


def fetch_transcript(api, video_id, max_chars, timeout=40):
    result, error = [None], [None]

    def run():
        try:
            fetched = api.fetch(video_id)
            result[0] = " ".join(s.text for s in fetched.snippets)[:max_chars]
        except Exception as e:
            error[0] = type(e).__name__

    t = threading.Thread(target=run, daemon=True)
    t.start()
    t.join(timeout)
    if t.is_alive():
        return None, "timeout"
    return result[0], error[0]


def fetch_all_youtube(channels, ledger, health, *, lookback_days=7, max_per_channel=3,
                      long_form=(), long_chars=60000, normal_chars=15000, short_chars=1500):
    videos = []
    with ThreadPoolExecutor(max_workers=4) as pool:  # >4 triggers YouTube throttling
        futures = {name: pool.submit(fetch_channel, name, cid, ledger,
                                     lookback_days, max_per_channel)
                   for name, cid in channels.items()}
        for name, fut in futures.items():
            try:
                vids, status = fut.result()
            except Exception as e:
                vids, status = [], ("fail", type(e).__name__)
            health[f"YT · {name}"] = status
            print(f"[YT] {name}: {status[1]}")
            videos.extend(vids)

    if not videos:
        return []

    api = _transcript_api()

    def cap(v):
        if v["is_short"]:
            return short_chars
        return long_chars if v["source"] in long_form else normal_chars

    def load(v):
        v["content"], v["_err"] = fetch_transcript(api, v["video_id"], cap(v))
        return v

    print(f"[YT] Fetching {len(videos)} transcripts...")
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(load, videos))

    failed = [v for v in videos if not v["content"]]
    if failed:
        print(f"[YT] Retrying {len(failed)} failed transcripts sequentially...")
        time.sleep(8)
        for v in failed:
            v["content"], v["_err"] = fetch_transcript(api, v["video_id"], cap(v))

    ok = [v for v in videos if v["content"]]
    missing = [v for v in videos if not v["content"]]
    for v in ok:
        v["snippet"] = v["content"][:900]
    health["YouTube transcripts"] = (
        "ok" if len(missing) <= max(2, len(videos) // 5) else "warn",
        f"{len(ok)}/{len(videos)} fetched"
        + (f" — will retry: {', '.join(sorted({v['source'] for v in missing}))}" if missing else ""),
    )
    print(f"[YT] {len(ok)} transcripts OK, {len(missing)} missing (retried next run)")
    return ok


# ---------------------------------------------------------------- article text
def extract_article(html_bytes, limit=7000):
    soup = BeautifulSoup(html_bytes, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "aside",
                     "form", "noscript", "svg", "figure"]):
        tag.decompose()
    root = soup.find("article") or soup.find("main") or soup.body or soup
    parts = [el.get_text(" ", strip=True) for el in root.find_all(["p", "li", "h2", "h3", "blockquote"])]
    text = "\n".join(p for p in parts if len(p) > 40)
    return re.sub(r"[ \t]+", " ", text)[:limit]


def enrich_with_articles(items, health):
    """Fetch full text for picked HN/RSS items whose feed didn't include it."""
    todo = [i for i in items if i["kind"] in ("hn", "rss") and len(i.get("content", "")) < 1500
            and not i["url"].lower().endswith(".pdf")]
    if not todo:
        return

    def one(item):
        resp, _ = http_get(item["url"], mode="direct_first", attempts=2, timeout=15,
                           accept="text/html,application/xhtml+xml,*/*")
        if resp is None or "html" not in resp.headers.get("Content-Type", "html"):
            return False
        text = extract_article(resp.content)
        if len(text) > len(item.get("content", "")):
            item["content"] = text
            return True
        return False

    with ThreadPoolExecutor(max_workers=6) as pool:
        got = sum(pool.map(one, todo))
    health["Article text"] = ("ok" if got >= len(todo) // 2 else "warn", f"{got}/{len(todo)} fetched")
    print(f"[Articles] Full text for {got}/{len(todo)} picks")


# ---------------------------------------------------------------- Bitcoin price
def fetch_btc():
    resp, _ = http_get(
        "https://api.coingecko.com/api/v3/coins/bitcoin?localization=false&tickers=false"
        "&market_data=true&community_data=false&developer_data=false",
        mode="direct_first", attempts=2, timeout=15, accept="application/json")
    if resp is None:
        return None
    try:
        md = resp.json()["market_data"]
        return {
            "price": md["current_price"]["usd"],
            "d1": md.get("price_change_percentage_24h"),
            "d7": md.get("price_change_percentage_7d"),
        }
    except Exception:
        return None
