"""
Morning Brief — v0.1
Pulls top Hacker News stories, summarizes with Claude, saves as HTML.
"""

import os
import requests
from datetime import datetime
from anthropic import Anthropic
from dotenv import load_dotenv

# Load the API key from .env
load_dotenv()
client = Anthropic()

# --- Your interests. Edit this freely. ---
MY_INTERESTS = """
I care about:
- AI/ML breakthroughs, new models, new capabilities, new tools
- New software or products that push the field forward
- Bitcoin, macroeconomics, Michael Saylor
- Health science: diet evidence, exercise science, longevity research
- Thoughtful long-form essays and ideas worth reading

I do NOT care about:
- Political drama, culture war content, sensationalized headlines
- Crypto speculation or altcoin pumps
- Startup funding gossip without substance
- Apple/Google/Microsoft corporate gossip unless it's about real capabilities
"""

# --- Step 1: Fetch Hacker News top stories ---
def fetch_hn_stories(n=30):
    """Grab top N stories from Hacker News."""
    print(f"Fetching top {n} Hacker News stories...")
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
    print(f"  Got {len(stories)} stories.")
    return stories

# --- Step 2: Have Claude filter and summarize ---
def filter_with_claude(stories):
    """Ask Claude to pick what matters and write a brief."""
    print("Asking Claude to filter and summarize...")

    stories_text = "\n".join([
        f"{i+1}. [{s['score']} pts] {s['title']} — {s['url']}"
        for i, s in enumerate(stories)
    ])

    prompt = f"""You are my personal morning brief curator. Below are today's top Hacker News stories. Your job: identify the ones genuinely worth my time based on my interests, skip the noise, and write a clean brief.

My interests:
{MY_INTERESTS}

Today's HN stories:
{stories_text}

Write the brief as HTML fragments (no <html>, <head>, or <body> tags — just content). Format:

<h2>Today's Signal</h2>
<p>One-sentence opening about today's theme if there is one, otherwise skip.</p>

For each story worth including (aim for 5-10, skip the rest):
<div class="story">
  <h3><a href="URL">Title</a></h3>
  <p>2-3 sentences on why this matters to me specifically. Not a summary of the article — your take on why I should or shouldn't click. Be direct, no hype.</p>
  <p class="meta"><a href="COMMENTS_URL">HN discussion</a> · {{score}} points</p>
</div>

Rules:
- If nothing is worth including, say so honestly. Don't pad.
- No sensationalism. No "you won't believe..." framing.
- If a story is technical and deep, say so. If it's a hot take, say so.
- Prioritize primary sources and substantive content over opinion pieces.
"""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.content[0].text

# --- Step 3: Wrap in a full HTML page ---
def build_html(brief_content):
    """Wrap the brief in a styled HTML page."""
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
</style>
</head>
<body>
<h1>Morning Brief</h1>
<p class="date">{today}</p>
{brief_content}
</body>
</html>"""

# --- Main ---
if __name__ == "__main__":
    stories = fetch_hn_stories(n=30)
    brief = filter_with_claude(stories)
    html = build_html(brief)

    output_path = "brief.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\nDone. Open {output_path} in a browser.")