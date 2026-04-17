"""
Channel Spotlight: suggests a YouTube channel adjacent to interests.
- Verifies the channel exists via handle lookup
- Auto-rotates after 3 days if not added
- Tracks history to avoid repeats
"""

import json
import os
import re
import requests
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

STATE_FILE = "suggestions_state.json"
MAX_DAYS_SHOWN = 3

client = Anthropic()


def load_state():
    if not os.path.exists(STATE_FILE):
        return {"current_suggestion": None, "shown_count": 0, "history": []}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def verify_channel_exists(channel_id):
    """Check a channel ID resolves to a real, active feed. Returns True/False."""
    if not channel_id or not channel_id.startswith("UC") or len(channel_id) != 24:
        return False
    feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    try:
        response = requests.get(feed_url, timeout=10)
        return response.status_code == 200 and "<entry>" in response.text
    except Exception:
        return False


def ask_claude_for_suggestion(current_channels, history, interests_text):
    """Ask Claude to suggest one adjacent channel, including its channel ID."""
    current_names = list(current_channels.keys())

    prompt = f"""I follow these YouTube channels and care about these topics:

CURRENT CHANNELS:
{chr(10).join(f"- {name}" for name in current_names)}

MY INTERESTS:
{interests_text}

PREVIOUSLY SUGGESTED (do NOT repeat):
{chr(10).join(f"- {name}" for name in history) if history else "(none yet)"}

Suggest ONE new YouTube channel that is:
- Adjacent to my interests but NOT already in my list or history
- Genuinely different in perspective — steelmans an angle I'm missing, OR covers a related topic I'm not getting
- Real and currently active (has published videos recently)
- A single person or podcast — not a news aggregator or generic topic channel

IMPORTANT: Include the channel's YouTube channel ID (the 24-character string that starts with "UC"). You know many of these from your training. If you're not sure of the exact ID, pick a different channel you ARE sure of.

Return your answer as a JSON object with this exact structure — no other text, no markdown code fences:

{{
  "channel_name": "Display name (e.g., 'Peter Attia')",
  "channel_id": "UCxxxxxxxxxxxxxxxxxxxxxx",
  "youtube_handle": "@theofficialhandle",
  "pitch": "2-3 sentences. Start with why this steelmans or expands what I'm currently consuming. Be specific about what they cover that my current channels don't. Mention the format (interview/solo/etc) and typical depth. No hype."
}}"""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        print(f"[suggestions] Failed to parse Claude response: {text[:200]}")
        return None


def get_suggestion(current_channels, interests_text, max_retries=3):
    """Main entry. Returns dict with suggestion data or None."""
    state = load_state()

    # If we have an active suggestion that's still in window, reuse it
    current = state.get("current_suggestion")
    if current and state.get("shown_count", 0) < MAX_DAYS_SHOWN:
        # Check if user added it since last run
        current_name = current.get("channel_name", "")
        if current_name in current_channels:
            # User added it! Celebrate, then rotate
            print(f"[suggestions] '{current_name}' was added — rotating.")
            state["current_suggestion"] = None
            state["shown_count"] = 0
        else:
            state["shown_count"] += 1
            save_state(state)
            days_left = MAX_DAYS_SHOWN - state["shown_count"] + 1
            current["days_left"] = days_left
            return current

    # Need a new suggestion
    print("[suggestions] Getting new suggestion from Claude...")
    for attempt in range(max_retries):
        suggestion = ask_claude_for_suggestion(
            current_channels,
            state.get("history", []),
            interests_text,
        )
        if not suggestion:
            continue

        channel_id = suggestion.get("channel_id", "")
        channel_name = suggestion.get("channel_name", "")

        if not verify_channel_exists(channel_id):
            print(f"[suggestions] Could not verify {channel_name} ({channel_id}), retrying...")
            # Add to history so we don't try the same again
            state.setdefault("history", []).append(channel_name)
            save_state(state)
            continue

        # Success — keep channel_id in place (already in suggestion dict)
        state["current_suggestion"] = suggestion
        state["shown_count"] = 1
        state.setdefault("history", []).append(suggestion.get("channel_name", ""))
        save_state(state)
        suggestion["days_left"] = MAX_DAYS_SHOWN
        return suggestion

    # All retries failed
    save_state(state)
    return None