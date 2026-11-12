"""
Morning Brief — v1.0

Pipeline:
  1. Collect   Hacker News, RSS feeds, YouTube (+ transcripts), basketball scores, BTC price
  2. Dedup     seen.json ledger: nothing appears in two briefs
  3. Triage    fast model scores every item 0-10 against MY_INTERESTS
  4. Enrich    full article text for the picks
  5. Write     stronger model writes the brief as structured data; code validates it
  6. Render    brief.html, plus raw_stories.txt (every candidate with its score)

Edit MY_INTERESTS, YOUTUBE_CHANNELS and RSS_SOURCES below. Everything else is plumbing.
Set BRIEF_TEST=1 for a cheap run with a few sources.
"""

import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

import llm  # noqa: E402
from hoops import get_hoops  # noqa: E402
from ledger import Ledger  # noqa: E402
from mental_models import pick_model_for_today  # noqa: E402
from quotes import pick_quote_for_today  # noqa: E402
from render import build_html  # noqa: E402
from sources import (enrich_with_articles, fetch_all_rss, fetch_all_youtube,  # noqa: E402
                     fetch_btc, fetch_hn)
from suggestions import get_suggestion  # noqa: E402

# ============================================================== YOUR SETTINGS
MY_INTERESTS = """
I care about:
- AI/ML at the CAPABILITY level: what new things can AI actually DO? Real end-user applications, novel uses, surprising capabilities, model releases with major upgrades/changes for average person.
- Bitcoin, monetary policy, macroeconomics, Michael Saylor's perspective
- Health science with REAL DATA: diet debates (especially carnivore/low-carb vs. conventional), exercise science, longevity research, metabolism
- Evidence-based fitness and training (hypertrophy, programming, recovery)
- Poker theory and high-level strategy content (GTO Wizard, GTO Lab, Jared Alderman)
- NBA and college basketball — games, storylines, analysis
- Philosophy and Stoicism: Marcus Aurelius, Seneca, Epictetus, and modern interpreters; ethics, dealing with adversity, what makes a good life
- Mental strength and the inner game: discipline, emotional regulation, decision-making under pressure, resilience, handling failure
- Mental models and frameworks for thinking clearly (Munger, Kahneman, first principles, inversion, etc.)
- Thoughtful long-form essays and ideas worth sitting with

I do NOT care about:
- AI infrastructure, inference layers, agent frameworks, dev tooling — too low-level for me
- "Open source Qwen-X-B beats benchmark Y" — unless it enables a meaningfully new thing I can do
- Political drama, culture war content, sensationalized headlines
- Crypto speculation, altcoins, NFTs
- Startup funding gossip without product substance
- Big Tech earnings, exec drama, corporate politics
- JavaScript framework discourse, programming language wars
- Generic self-help / hustle-culture content — "10 habits of successful people" style
"""

YOUTUBE_CHANNELS = {
    "GTO Wizard": "UCXSg1srGpJ67HuPTMm4w72g",
    "Ken Berry MD": "UCIma2WOQs1Mz2AuOt6wRSUw",
    "Anthony Chaffee MD": "UCzoRyR_nlesKZuOlEjWRXQQ",
    "Paul Saladino MD": "UCgBg0LcHfnJDPmFTTf677Pw",
    "Joe Rogan": "UCzQUP1qoWDoEbmsQxvdjxgQ",
    "Nick Norwitz": "UCLTZUJSEulehPtF_ytFiU_A",
    "GTO Lab": "UCOgptC4EkqVqOW7rNo5L7JA",
    "Jared Alderman": "UCnf7tCbgJu2RM3fbsJrximw",
    "Thomas DeLauer": "UC70SrI3VkT1MXALRtf0pcHg",
    "Lex Fridman": "UCSHZKyawb77ixDdsGog4iWA",
    "Dr. Sten Ekberg": "UCIe2pR6PE0dae9BunJ38F7w",
    "Renaissance Periodization": "UCfQgsKhHjSyRLOp9mnffqVg",
    "Peter Attia": "UC8kGsMa0LygSX9nkBcBH1Sg",
    "ModernWisdom": "UCIaH-gZIVC432YRjNVvnyCA",
    "Andrew Huberman": "UC2D2CMWXMOVWx7giW1n3LIg",
    "ThinkingPoker": "UC_qsy__bQgZlPTfrnOMVgHg",
    "Ben Felix": "UCDXTQ8nWmx_EhZ2v-kp7QxA",
    "Mind The Game": "UC6L_LBqoKZXFa4WxHox5iCw",
}
LONG_FORM_CHANNELS = {"Joe Rogan", "Lex Fridman"}  # longer transcript excerpts

# category = where triage leans for this source. lookback_days can be long:
# the seen-ledger guarantees an item is only ever shown once.
RSS_SOURCES = {
    # Bitcoin & macro
    "Bitcoin Magazine": {"url": "https://bitcoinmagazine.com/.rss/full/", "category": "bitcoin", "max_items": 8},
    "The Pomp Letter": {"url": "https://pomp.substack.com/feed", "category": "bitcoin", "max_items": 5},
    "Lyn Alden": {"url": "https://www.lynalden.com/feed/", "category": "bitcoin", "max_items": 3, "lookback_days": 60},
    # AI capability
    "Anthropic News": {"url": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml",
                       "category": "ai", "max_items": 5, "lookback_days": 14},
    "OpenAI Blog": {"url": "https://openai.com/blog/rss.xml", "category": "ai", "max_items": 5},
    "Simon Willison": {"url": "https://simonwillison.net/atom/everything/", "category": "ai", "max_items": 8},
    # Poker
    "GTO Wizard Blog": {"url": "https://blog.gtowizard.com/rss/", "category": "poker", "max_items": 3, "lookback_days": 14},
    # Health / training
    "Peter Attia": {"url": "https://peterattiamd.com/feed/", "category": "health", "max_items": 5},
    "Stronger by Science": {"url": "https://www.strongerbyscience.com/feed/", "category": "health", "max_items": 3, "lookback_days": 90},
    # Mind & philosophy
    "Farnam Street": {"url": "https://fs.blog/feed/", "category": "mind", "max_items": 3, "lookback_days": 14},
    "Figs in Winter (Pigliucci)": {"url": "https://figsinwintertime.substack.com/feed", "category": "mind", "max_items": 3, "lookback_days": 14},
    "Donald Robertson": {"url": "https://donaldrobertson.substack.com/feed", "category": "mind", "max_items": 3, "lookback_days": 14},
    # Ideas
    "Stratechery": {"url": "https://stratechery.com/feed/", "category": "reading", "max_items": 5},
    "Astral Codex Ten": {"url": "https://www.astralcodexten.com/feed", "category": "reading", "max_items": 3, "lookback_days": 7},
    "Marginal Revolution": {"url": "https://marginalrevolution.com/feed", "category": "reading", "max_items": 6},
    "Paul Graham": {"url": "https://program247365.github.io/paulgraham-rss/rss.xml", "category": "reading", "max_items": 3, "lookback_days": 90},
    "Collaborative Fund (Morgan Housel)": {"url": "https://collabfund.substack.com/feed", "category": "reading", "max_items": 3, "lookback_days": 30},
}

HN_STORIES = 40
YT_LOOKBACK_DAYS = 7
MAIN_SCORE = 6    # triage score that always earns a full read
MIN_MAIN = 10     # on slow days, fill up to this many full reads with 5s
MAX_MAIN = 16     # cap on full-text items sent to the writer
LIGHT_SCORE = 4   # ...for a one-line mention

TEST_MODE = os.getenv("BRIEF_TEST") == "1"


# ============================================================== pipeline
def gha(level, msg):
    """Print, and surface as an annotation in the GitHub Actions run summary."""
    print(f"[{level.upper()}] {msg}")
    if os.getenv("GITHUB_ACTIONS"):
        print(f"::{level}::{msg}")


def collect(ledger, health):
    channels = dict(list(YOUTUBE_CHANNELS.items())[:2]) if TEST_MODE else YOUTUBE_CHANNELS
    feeds = dict(list(RSS_SOURCES.items())[:3]) if TEST_MODE else RSS_SOURCES
    hn = fetch_hn(8 if TEST_MODE else HN_STORIES, ledger, health)
    rss = fetch_all_rss(feeds, ledger, health)
    yt = fetch_all_youtube(
        channels, ledger, health, lookback_days=YT_LOOKBACK_DAYS,
        long_form=LONG_FORM_CHANNELS, normal_chars=3000 if TEST_MODE else 15000,
        long_chars=3000 if TEST_MODE else 60000)
    items = yt + rss + hn
    for i, it in enumerate(items):
        it["id"] = f"{it['kind'][0]}{i}"
    return items, len(hn), len(rss), len(yt)


def quality_gate(n_hn, n_rss, n_yt):
    if n_hn + n_rss + n_yt == 0:
        gha("error", "No content collected from any source — keeping yesterday's brief.")
        sys.exit(1)
    if n_hn == 0:
        gha("warning", "Hacker News returned nothing.")
    if n_rss < 3:
        gha("warning", f"Only {n_rss} new RSS items — feeds may be failing.")
    if n_yt == 0:
        gha("warning", "No new YouTube transcripts.")


def write_raw_dump(items, scores):
    with open("raw_stories.txt", "w", encoding="utf-8") as f:
        f.write(f"Generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC\n")
        f.write("score  section   source / title\n" + "-" * 70 + "\n")
        for it in sorted(items, key=lambda x: -scores.get(x["id"], (-1, ""))[0]):
            s, sec = scores.get(it["id"], (-1, "?"))
            f.write(f"{s:>4}   {sec:<8}  [{it['kind']}] {it['source']}: {it['title']}\n"
                    f"{'':17}{it['url']}\n")


def main():
    started = datetime.now(timezone.utc)
    if os.getenv("GITHUB_ACTIONS"):
        for var in ("ANTHROPIC_API_KEY", "WEBSHARE_PROXY_USERNAME", "WEBSHARE_PROXY_PASSWORD"):
            if not os.getenv(var):
                gha("error", f"{var} is not set in the workflow secrets")
                sys.exit(1)
    if TEST_MODE:
        print("⚡ TEST MODE — few sources, short transcripts")

    ledger = Ledger()
    if ledger.bootstrap:
        print("[ledger] No seen.json yet — first run only looks at the last 36 hours")
    health = {}

    items, n_hn, n_rss, n_yt = collect(ledger, health)
    quality_gate(n_hn, n_rss, n_yt)
    hoops = get_hoops(health)
    btc = fetch_btc()
    if btc is None:
        health["Bitcoin price"] = ("warn", "CoinGecko unavailable")

    # --- triage
    print(f"[Claude] Triage of {len(items)} items with {llm.TRIAGE_MODEL}...")
    scores = {}
    for start in range(0, len(items), 80):  # batches keep each call small
        scores.update(llm.triage(items[start:start + 80], MY_INTERESTS))
    for it in items:
        s, sec = scores.get(it["id"], (0, "skip"))
        it["score"], it["section"] = s, sec
    write_raw_dump(items, scores)

    ranked = sorted((i for i in items if i["section"] != "skip"), key=lambda x: -x["score"])
    main_items = [i for i in ranked if i["score"] >= MAIN_SCORE][:MAX_MAIN]
    if len(main_items) < MIN_MAIN:
        main_items += [i for i in ranked if i["score"] == MAIN_SCORE - 1][:MIN_MAIN - len(main_items)]
    picked = {i["id"] for i in main_items}
    light_items = [i for i in ranked if i["score"] >= LIGHT_SCORE and i["id"] not in picked][:14]
    print(f"[Claude] {len(main_items)} main picks, {len(light_items)} light picks")

    enrich_with_articles(main_items, health)

    # --- write
    print(f"[Claude] Writing with {llm.WRITER_MODEL}...")
    by_id = {i["id"]: i for i in items}
    if main_items or light_items:
        draft = llm.write(main_items, light_items, MY_INTERESTS)
        brief = llm.validate(draft, by_id)
    else:
        brief = {"top": [], "sections": {}, "also": [], "quiet_day": True}

    # --- extras
    q_text, q_author, q_ctx = pick_quote_for_today()
    m_name, m_domain, m_story = pick_model_for_today()
    anchor = {"quote": q_text, "author": q_author, "quote_context": q_ctx,
              "model_name": m_name, "model_domain": m_domain, "model_story": m_story}
    try:
        spotlight = None if TEST_MODE else get_suggestion(YOUTUBE_CHANNELS, MY_INTERESTS)
    except Exception as e:
        spotlight = None
        health["Channel spotlight"] = ("warn", type(e).__name__)

    # Only now is the run a success: record everything triaged as seen.
    for it in items:
        ledger.mark(it["key"])
    ledger.save()

    took = (datetime.now(timezone.utc) - started).seconds
    stats = (f"{len(items)} new items scanned · {len(main_items)} read in full · "
             f"{llm.usage['input'] // 1000}k in / {llm.usage['output'] // 1000}k out tokens · {took // 60}m{took % 60:02d}s")
    today = datetime.now()
    html = build_html(
        date_label=f"{today:%A, %B} {today.day}",
        brief=brief, anchor=anchor, spotlight=spotlight, hoops=hoops,
        btc=btc, health=health, stats=stats,
    )
    with open("brief.html", "w", encoding="utf-8") as f:
        f.write(html)

    for name, (status, detail) in sorted(health.items()):
        if status == "fail":
            gha("warning", f"{name}: {detail}")
    print(f"\nDone in {took}s. Open brief.html · raw_stories.txt shows every item with its score.")


if __name__ == "__main__":
    main()
