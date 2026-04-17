"""
Morning Brief — v0.3
Sources: Hacker News + YouTube channels
Adds: daily anchor (quote + mental model) and channel spotlight
"""

import os
import requests
import time
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
}

LOOKBACK_DAYS = 3


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
def build_brief(hn_stories, yt_videos):
    print("[Claude] Generating brief...")

    hn_text = "\n".join([
        f"- [{s['score']} pts] {s['title']} — {s['url']}"
        for s in hn_stories
    ])

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

Below are today's inputs from Hacker News and from YouTube channels I follow. Produce a clean HTML brief.

=== HACKER NEWS ===
{hn_text}

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

Rules:
- If a video has "Transcript unavailable," still list it in "Also posted" but write: "⚠️ Title only, no transcript."
- Never invent or speculate on content. If you don't have the transcript, say so.

<h2>💡 Worth Reading</h2>
For each HN story worth my time:
<div class="story">
  <h3><a href="URL">Title</a></h3>
  <p>2-3 sentences on the substance and why it matters to me.</p>
  <p class="meta"><a href="COMMENTS_URL">Discussion</a></p>
</div>

Rules:
- Be ruthless. If something doesn't genuinely match my interests, cut it.
- For YouTube: summarize the IDEAS, not the video. "Chaffee argues that..." not "This video discusses..."
- No hype, no filler, no "in today's fast-paced world"
- If a whole section has nothing worthwhile, skip the heading entirely
- If the day has almost nothing, say so honestly with something like <p><em>Quiet day. Not much worth flagging.</em></p>
"""

    response = client.messages.create(
        model="claude-opus-4-5",
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
<h1>Morning Brief</h1>
<p class="date">{today}</p>
{brief_content}
</body>
</html>"""


# ---------- Main ----------
if __name__ == "__main__":
    hn_stories = fetch_hn_stories(n=30)
    yt_videos = fetch_all_youtube()

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
        f.write("\n=== YOUTUBE ===\n")
        for v in yt_videos:
            f.write(f"{v['channel']}: {v['title']}\n  {v['url']}\n  Transcript: {'yes' if v['transcript'] else 'NO'}\n\n")

    brief = build_brief(hn_stories, yt_videos)

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