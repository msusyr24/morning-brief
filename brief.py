"""
Morning Brief — v0.3
Sources: Hacker News + YouTube channels
Adds: daily anchor (quote + mental model) and channel spotlight
"""

import os
import requests
import time
import re
from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree
from anthropic import Anthropic
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig
from quotes import pick_quote_for_today
from mental_models import pick_model_for_today
from suggestions import get_suggestion

load_dotenv()
client = Anthropic()

# --- Your interests ---
MY_INTERESTS = """
I care about:
- AI at the CAPABILITY level: what new things can AI actually DO? Novel end-user applications, surprising capabilities.
- Bitcoin, monetary policy, macroeconomics, Michael Saylor's perspective
- Health science with REAL DATA: carnivore / low-carb / conventional diet debates, metabolism, longevity, exercise science
- Evidence-based fitness: hypertrophy, programming, recovery
- Poker theory, especially GTO concepts and high-level strategy
- NBA and college basketball — games, storylines, analysis
- Thoughtful long-form ideas worth sitting with

I do NOT care about:
- AI infrastructure, inference layers, agent frameworks, model releases, dev tooling
- Political drama, culture war content, sensationalism
- Crypto speculation, altcoins, NFTs
- Startup funding gossip, corporate earnings, exec drama
- Programming language wars, framework discourse
"""

# --- YouTube channels to monitor ---
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
}

LOOKBACK_DAYS = 3
# --- Test mode: cheap runs during development ---
TEST_MODE = False  # Flip to False for real daily runs

if TEST_MODE:
    print("⚡ TEST_MODE ON — reduced sources, cheap tokens")


# ---------- Hacker News ----------
def fetch_hn_stories(n=30):
    print(f"[HN] Fetching top {n} stories...")
    top_ids = requests.get(
        "https://hacker-news.firebaseio.com/v0/topstories.json"
    ).json()[:n]
    stories = []
    for story_id in top_ids:
        story = requests.get(
            f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
        ).json()
        if story and story.get("title"):
            stories.append({
                "title": story.get("title", ""),
                "url": story.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                "score": story.get("score", 0),
                "comments_url": f"https://news.ycombinator.com/item?id={story_id}",
            })
    print(f"[HN]   Got {len(stories)} stories.")
    return stories

# ---------- Generic RSS fetcher ----------
import feedparser

RSS_SOURCES = {
    # Bitcoin & macro
    "Bitcoin Magazine": {
        "url": "https://bitcoinmagazine.com/.rss/full/",
        "category": "bitcoin",
    },
    "Lyn Alden": {
        "url": "https://www.lynalden.com/feed/",
        "category": "bitcoin",
    },
    "What Bitcoin Did": {
        "url": "https://www.whatbitcoindid.com/podcast?format=rss",
        "category": "bitcoin",
    },
    # AI capabilities from the source
    "Anthropic": {
        "url": "https://www.anthropic.com/news/rss.xml",
        "category": "ai",
    },
    "OpenAI": {
        "url": "https://openai.com/news/rss.xml",
        "category": "ai",
    },
    # Health / science / longevity
    "Peter Attia": {
        "url": "https://peterattiamd.com/feed/",
        "category": "health",
    },
    "Examine": {
        "url": "https://examine.com/rss/",
        "category": "health",
    },
    # Long-form ideas
    "Stratechery (free)": {
        "url": "https://stratechery.com/feed/",
        "category": "ideas",
    },
    "Marginal Revolution": {
        "url": "https://marginalrevolution.com/feed",
        "category": "ideas",
    },
}


def fetch_rss_source(name, config, days=3):
    """Fetch a single RSS feed. Returns items from the last N days."""
    try:
        feed = feedparser.parse(config["url"])
    except Exception as e:
        print(f"[RSS] {name}: error — {e}")
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    items = []
    for entry in feed.entries[:20]:  # Cap at 20 per feed to avoid overwhelming
        # Parse publish date (format varies across feeds)
        published = None
        for attr in ["published_parsed", "updated_parsed"]:
            pub_struct = entry.get(attr)
            if pub_struct:
                published = datetime(*pub_struct[:6], tzinfo=timezone.utc)
                break
        if not published or published < cutoff:
            continue

        # Some feeds give a summary, some give full content; grab what's there
        summary = entry.get("summary", "") or entry.get("description", "")
        # feedparser sometimes returns html — quick flattening
        summary = re.sub(r"<[^>]+>", "", summary)[:400]

        items.append({
            "source": name,
            "category": config["category"],
            "title": entry.get("title", ""),
            "url": entry.get("link", ""),
            "summary": summary,
            "published": published.isoformat(),
        })
    return items


def fetch_all_rss():
    """Pull recent items from all RSS sources in parallel."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    print(f"[RSS] Checking {len(RSS_SOURCES)} RSS sources...")
    all_items = []

    with ThreadPoolExecutor(max_workers=len(RSS_SOURCES)) as pool:
        futures = {
            pool.submit(fetch_rss_source, name, config): name
            for name, config in RSS_SOURCES.items()
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                items = future.result(timeout=15)
                if items:
                    print(f"[RSS]   {name}: {len(items)} item(s)")
                all_items.extend(items)
            except Exception as e:
                print(f"[RSS]   {name}: error — {type(e).__name__}")

    print(f"[RSS] Total items: {len(all_items)}")
    return all_items

# ---------- YouTube ----------
def fetch_recent_videos(channel_name, channel_id, days=LOOKBACK_DAYS):
    """Fetch videos published in the last N days from a channel's RSS feed."""
    feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    try:
        response = requests.get(feed_url, timeout=8)
        root = ElementTree.fromstring(response.content)
    except Exception as e:
        print(f"[YT] {channel_name}: feed error ({e})")
        return []

    ns = {"atom": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    videos = []

    for entry in root.findall("atom:entry", ns):
        published_str = entry.find("atom:published", ns).text
        published = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
        if published < cutoff:
            continue
        videos.append({
            "channel": channel_name,
            "title": entry.find("atom:title", ns).text,
            "video_id": entry.find("yt:videoId", ns).text,
            "url": entry.find("atom:link", ns).attrib["href"],
            "published": published_str,
        })
    return videos


_transcript_api = YouTubeTranscriptApi(
    proxy_config=WebshareProxyConfig(
        proxy_username=os.getenv("WEBSHARE_PROXY_USERNAME"),
        proxy_password=os.getenv("WEBSHARE_PROXY_PASSWORD"),
    )
)
LONG_FORM_CHANNELS = {"Joe Rogan", "Lex Fridman"}


def fetch_transcript(video_id, channel_name=None):
    """Try to pull a transcript. Returns None if unavailable."""
    import threading
    if TEST_MODE:
        max_chars = 3000
    else:
        max_chars = 60000 if channel_name in LONG_FORM_CHANNELS else 15000
    result = [None]
    error = [None]

    def _do_fetch():
        try:
            fetched = _transcript_api.fetch(video_id)
            text = " ".join([snippet.text for snippet in fetched.snippets])
            result[0] = text[:max_chars]
        except Exception as e:
            error[0] = type(e).__name__

    thread = threading.Thread(target=_do_fetch, daemon=True)
    thread.start()
    thread.join(timeout=30)

    if thread.is_alive():
        print(f"    [transcript] {video_id}: TIMEOUT (>30s)")
        return None
    if error[0]:
        print(f"    [transcript] {video_id}: {error[0]}")
        return None
    return result[0]


def fetch_all_youtube():
    """Pull recent videos from every channel in parallel, then add transcripts in parallel."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    print(f"[YT] Checking {len(YOUTUBE_CHANNELS)} channels for videos in last {LOOKBACK_DAYS} days...")
    all_videos = []

    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = {
            pool.submit(fetch_recent_videos, name, cid): name
            for name, cid in YOUTUBE_CHANNELS.items()
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                videos = future.result(timeout=20)
                if videos:
                    print(f"[YT]   {name}: {len(videos)} new video(s)")
                all_videos.extend(videos)
            except Exception as e:
                print(f"[YT]   {name}: error — {type(e).__name__}")

    print(f"[YT] Fetching transcripts for {len(all_videos)} videos in parallel...")

    completed = [0]
    total = len(all_videos)

    def _load_transcript(video):
        video["transcript"] = fetch_transcript(video["video_id"], video["channel"])
        completed[0] += 1
        print(f"[YT]   transcripts: {completed[0]}/{total}")
        return video

    with ThreadPoolExecutor(max_workers=5) as pool:
        list(pool.map(_load_transcript, all_videos))

    print(f"[YT] Total new videos: {len(all_videos)}")
    return all_videos


# ---------- Claude synthesis ----------
def build_brief(hn_stories, yt_videos, rss_items):
    print("[Claude] Generating brief...")

    hn_text = "\n".join([
        f"- [{s['score']} pts] {s['title']} — {s['url']}"
        for s in hn_stories
    ])

    # Group RSS items by category
    rss_by_category = {}
    for item in rss_items:
        rss_by_category.setdefault(item["category"], []).append(item)

    rss_text_parts = []
    for category, items in rss_by_category.items():
        rss_text_parts.append(f"\n### {category.upper()} ###")
        for item in items:
            block = f"- [{item['source']}] {item['title']} — {item['url']}"
            if item["summary"]:
                block += f"\n  Summary: {item['summary'][:300]}"
            rss_text_parts.append(block)
    rss_text = "\n".join(rss_text_parts) if rss_text_parts else "(No RSS items today.)"

    yt_text_parts = []
    for v in yt_videos:
        block = f"\n--- {v['channel']}: {v['title']} ({v['url']}) ---\n"
        if v["transcript"]:
            block += f"Transcript excerpt:\n{v['transcript']}\n"
        else:
            block += "(Transcript unavailable — title only)\n"
        yt_text_parts.append(block)
    yt_text = "\n".join(yt_text_parts) if yt_text_parts else "(No new videos today.)"

    prompt = f"""You are my morning brief curator. I care about these topics:

{MY_INTERESTS}

Below are today's inputs from four streams: Hacker News (tech/AI), RSS feeds (Bitcoin/macro, AI capability announcements, health, long-form ideas), and YouTube channels I follow. Produce a clean HTML brief.

=== HACKER NEWS ===
{hn_text}

=== RSS FEEDS ===
{rss_text}

=== YOUTUBE ===
{yt_text}

Output format: HTML fragments only, no <html> or <body> wrapper. Use these sections IN THIS ORDER, but SKIP any section with no worthwhile content (do not include empty sections):

<h2>🎥 From People I Follow</h2>

<p><strong>Worth your time:</strong></p>

Group by person. For each person whose content this period has real substance:
<div class="story">
  <h3>Channel Name</h3>
  <p>Lead with the substance: what did they actually argue, claim, or cover? Cite specific claims, studies, numbers, or points they made. Weave multiple videos from the same person together. 3-5 sentences.</p>
  <p class="meta">Videos: <a href="URL1">Title 1</a> · <a href="URL2">Title 2</a></p>
</div>

<p><strong>Also posted:</strong></p>
<ul>
For every OTHER person who posted videos with transcripts (that weren't included above), write one <li> per person in this format:
  <li><strong>Channel Name:</strong> One-sentence summary of what they posted. (<a href="URL">Title</a>)</li>
If they posted multiple, mention the one with most substance and note "+N more."
</ul>

<h2>₿ Bitcoin & Macro</h2>
Pull from BOTH the RSS "bitcoin" category AND any HN or YouTube items about Bitcoin/monetary policy/macroeconomics. For each item worth flagging:
<div class="story">
  <h3><a href="URL">Title</a></h3>
  <p>2-3 sentences on the substance. If this is a Saylor appearance, cite his core argument. If it's an essay or analysis, summarize the thesis — not the article structure.</p>
  <p class="meta">Source</p>
</div>

<h2>🧬 Health & Science</h2>
Pull from RSS "health" category AND related HN/YouTube items. Cite specific studies, mechanisms, or data. Skip listicle-style content.

<h2>💡 Worth Reading</h2>
For HN stories and RSS "ideas" items worth my time:
<div class="story">
  <h3><a href="URL">Title</a></h3>
  <p>2-3 sentences on substance and why it matters.</p>
  <p class="meta"><a href="COMMENTS_URL">Discussion</a> (if HN) or Source</p>
</div>

<h2>🤖 AI Capability Watch</h2>
Only include items from the RSS "ai" category OR HN items that are about NEW END-USER CAPABILITIES (not infrastructure, model releases for release's sake, or framework discourse). If nothing substantive: skip this section entirely.

Rules:
- Be ruthless. Skip padding. Skip political drama. Skip crypto altcoin talk.
- If a whole section has nothing worthwhile, skip the heading entirely
- For YouTube: summarize the IDEAS, not the video. "Chaffee argues that..." not "This video discusses..."
- No hype, no filler
- If the day has almost nothing, say so honestly with <p><em>Quiet day. Not much worth flagging.</em></p>
"""

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=6000,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


# ---------- HTML wrapper ----------
def build_html(brief_content):
    today = datetime.now().strftime("%A, %B %d, %Y")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Morning Brief — {today}</title>
<style>
  body {{
    font-family: Georgia, serif;
    max-width: 720px;
    margin: 40px auto;
    padding: 0 20px;
    line-height: 1.6;
    color: #222;
    background: #fafaf7;
  }}
  h1 {{ font-size: 2em; margin-bottom: 0; }}
  .date {{ color: #888; margin-top: 0; font-style: italic; }}
  h2 {{ margin-top: 2em; border-bottom: 1px solid #ddd; padding-bottom: 0.3em; }}
  h3 {{ margin-bottom: 0.3em; }}
  h3 a {{ color: #1a1a1a; text-decoration: none; }}
  h3 a:hover {{ text-decoration: underline; }}
  .story {{ margin-bottom: 1.8em; }}
  .meta {{ color: #888; font-size: 0.9em; margin-top: 0.3em; }}
  .meta a {{ color: #888; }}

  .btc-ticker {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #fff8e7;
    border: 1px solid #f0d890;
    padding: 10px 18px;
    border-radius: 6px;
    margin-bottom: 1.5em;
    font-family: -apple-system, 'Segoe UI', sans-serif;
  }}
  .btc-label {{ font-weight: bold; color: #8b6914; }}
  .btc-price {{ font-size: 1.3em; font-weight: bold; color: #222; }}
  .btc-change {{ font-size: 0.95em; font-weight: bold; }}
  .btc-up {{ color: #2d8a2d; }}
  .btc-down {{ color: #c23030; }}
  .btc-meta {{ color: #888; font-size: 0.85em; }}

  .anchor {{ background: #f0ede4; padding: 20px 25px; border-radius: 6px; margin-bottom: 2em; }}
  .anchor h2 {{ border-bottom: none; margin-top: 0; }}
  .anchor-block {{ margin: 1.2em 0; }}
  .quote {{ font-size: 1.15em; font-style: italic; margin: 0 0 0.3em 0; }}
  .author {{ color: #555; margin: 0 0 0.5em 0; font-weight: bold; }}
  .model-label {{ font-size: 0.85em; color: #888; text-transform: uppercase; letter-spacing: 0.05em; margin: 0; }}
  .model-name {{ font-size: 1.2em; font-weight: bold; margin: 0.2em 0 0.4em 0; }}
  .context {{ color: #444; font-size: 0.95em; margin: 0; }}

  .spotlight {{ background: #eef4f0; padding: 20px 25px; border-left: 4px solid #5a8a6b; border-radius: 6px; margin-bottom: 2em; }}
  .spotlight h2 {{ border-bottom: none; margin-top: 0; }}
  .spotlight-name {{ font-size: 1.25em; font-weight: bold; margin: 0 0 0.4em 0; }}
  .spotlight-pitch {{ color: #333; margin: 0 0 1em 0; }}
  .spotlight-instructions {{ font-size: 0.95em; color: #555; margin: 0 0 0.4em 0; }}
  .spotlight-snippet {{ background: #1e2a24; color: #d4e8d8; padding: 12px 15px; border-radius: 4px; font-family: 'Consolas', 'Monaco', monospace; font-size: 0.9em; overflow-x: auto; margin: 0.3em 0; }}
  .copy-btn {{ background: #5a8a6b; color: white; border: none; padding: 6px 14px; border-radius: 4px; cursor: pointer; font-size: 0.85em; margin-top: 0.3em; }}
  .copy-btn:hover {{ background: #4a7a5b; }}
  .spotlight-meta {{ color: #888; font-size: 0.85em; font-style: italic; margin: 0.8em 0 0 0; }}
</style>
</head>
<body>
<div class="btc-ticker">
  <span class="btc-label">₿ Bitcoin</span>
  <span class="btc-price" id="btc-price">Loading...</span>
  <span class="btc-change" id="btc-change"></span>
  <span class="btc-meta" id="btc-meta"></span>
</div>

<script>
(async () => {{
  try {{
    const res = await fetch('https://api.coingecko.com/api/v3/coins/bitcoin?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false');
    const data = await res.json();
    const price = data.market_data.current_price.usd;
    const change24 = data.market_data.price_change_percentage_24h;
    const change7d = data.market_data.price_change_percentage_7d;

    document.getElementById('btc-price').innerText = '$' + price.toLocaleString(undefined, {{maximumFractionDigits: 0}});

    const changeEl = document.getElementById('btc-change');
    const sign = change24 >= 0 ? '▲' : '▼';
    changeEl.innerText = `${{sign}} ${{Math.abs(change24).toFixed(2)}}% (24h)`;
    changeEl.className = 'btc-change ' + (change24 >= 0 ? 'btc-up' : 'btc-down');

    document.getElementById('btc-meta').innerText = `7d: ${{change7d >= 0 ? '+' : ''}}${{change7d.toFixed(1)}}%`;
  }} catch (err) {{
    document.getElementById('btc-price').innerText = 'Price unavailable';
  }}
}})();
</script>
<h1>Morning Brief</h1>
<p class="date">{today}</p>
{brief_content}
</body>
</html>"""


# ---------- Main ----------
if __name__ == "__main__":
    hn_stories = fetch_hn_stories(n=5 if TEST_MODE else 30)

    if TEST_MODE:
        # Only check 2 channels during testing
        test_channels = dict(list(YOUTUBE_CHANNELS.items())[:2])
        original_channels = YOUTUBE_CHANNELS
        YOUTUBE_CHANNELS.clear()
        YOUTUBE_CHANNELS.update(test_channels)
        yt_videos = fetch_all_youtube()
        YOUTUBE_CHANNELS.clear()
        YOUTUBE_CHANNELS.update(original_channels)

        # Skip RSS during testing to save tokens
        rss_items = []
    else:
        yt_videos = fetch_all_youtube()
        rss_items = fetch_all_rss()

    # Pick today's anchor content
    quote_text, quote_author, quote_context = pick_quote_for_today()
    model_name, model_domain, model_story = pick_model_for_today()

    # Get today's channel spotlight
    suggestion = get_suggestion(YOUTUBE_CHANNELS, MY_INTERESTS)

    # Save raw dump for debugging
    with open("raw_stories.txt", "w", encoding="utf-8") as f:
        f.write("=== HACKER NEWS ===\n")
        for i, s in enumerate(hn_stories, 1):
            f.write(f"{i}. [{s['score']} pts] {s['title']}\n   {s['url']}\n\n")
        f.write("\n=== RSS ===\n")
        for item in rss_items:
            f.write(f"[{item['category']}] {item['source']}: {item['title']}\n  {item['url']}\n\n")
        f.write("\n=== YOUTUBE ===\n")
        for v in yt_videos:
            f.write(f"{v['channel']}: {v['title']}\n  {v['url']}\n  Transcript: {'yes' if v['transcript'] else 'NO'}\n\n")

    brief = build_brief(hn_stories, yt_videos, rss_items)

    # Build the anchor block
    anchor_html = f"""
<div class="anchor">
  <h2>☀️ Today's Anchor</h2>
  <div class="anchor-block">
    <p class="quote">"{quote_text}"</p>
    <p class="author">— {quote_author}</p>
    <p class="context">{quote_context}</p>
  </div>
  <div class="anchor-block">
    <p class="model-label">Mental Model · {model_domain}</p>
    <p class="model-name">{model_name}</p>
    <p class="context">{model_story}</p>
  </div>
</div>
"""

    # Build the spotlight block
    spotlight_html = ""
    if suggestion:
        snippet = f'    "{suggestion["channel_name"]}": "{suggestion["channel_id"]}",'
        days_left = suggestion.get("days_left", 1)
        day_note = "showing for 1 more day" if days_left == 1 else f"showing for {days_left} more days"

        spotlight_html = f"""
<div class="spotlight">
  <h2>🧭 Channel Spotlight</h2>
  <p class="spotlight-name">{suggestion["channel_name"]}</p>
  <p class="spotlight-pitch">{suggestion["pitch"]}</p>
  <p class="spotlight-instructions">Interested? Copy the line below into <code>YOUTUBE_CHANNELS</code> in <code>brief.py</code> and save:</p>
  <pre class="spotlight-snippet" id="snippet">{snippet}</pre>
  <button class="copy-btn" onclick="navigator.clipboard.writeText(document.getElementById('snippet').innerText.trim()); this.innerText='✅ Copied'; setTimeout(()=>this.innerText='📋 Copy snippet', 2000);">📋 Copy snippet</button>
  <p class="spotlight-meta">{day_note}. If you don't add it, a new channel will be suggested.</p>
</div>
"""

    html = build_html(anchor_html + spotlight_html + brief)

    with open("brief.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("\nDone. Open brief.html.")
    print("See raw_stories.txt to compare raw input vs. curated output.")