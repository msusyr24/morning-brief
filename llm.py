"""
Two-stage Claude pipeline.

1. triage()  — a fast model scores every candidate 0-10 against your interests
               and assigns a section. Cheap, sees only titles + snippets.
2. write()   — a stronger model writes the brief from the full text of the
               picks only. It returns structured data (not HTML), which the code
               validates: every item must point at a real source, nothing can
               appear twice, and links always come from the source data.
"""

import json
import os

from anthropic import Anthropic

TRIAGE_MODEL = os.getenv("BRIEF_TRIAGE_MODEL", "claude-haiku-5-5")
WRITER_MODEL = os.getenv("BRIEF_WRITER_MODEL", "claude-sonnet-5-5")

SECTION_KEYS = ["poker", "ai", "bitcoin", "health", "mind", "reading", "hoops"]

_client = None
usage = {"input": 0, "output": 0}


def client():
    global _client
    if _client is None:
        _client = Anthropic(max_retries=5, timeout=600)
    return _client


_forced_ok = {}  # model -> whether it accepts a forced tool_choice


def _call_tool(model, system, user, tool_name, schema, max_tokens):
    """Ask the model to answer by calling `tool_name`. Forces the tool where the
    model allows it; otherwise asks for it in the prompt and retries once."""
    tools = [{"name": tool_name, "description": "Submit the result.", "input_schema": schema}]
    system = system + f"\n\nReturn your answer by calling the {tool_name} tool exactly once."
    for attempt in range(2):
        kwargs = dict(model=model, max_tokens=max_tokens, system=system,
                      messages=[{"role": "user", "content": user}], tools=tools)
        if _forced_ok.get(model, True):
            kwargs["tool_choice"] = {"type": "tool", "name": tool_name}
        try:
            resp = client().messages.create(**kwargs)
        except Exception as e:
            if "tool_choice" in str(e) and _forced_ok.get(model, True):
                _forced_ok[model] = False
                print(f"[Claude] {model} doesn't allow forced tool use; asking instead")
                resp = client().messages.create(**{k: v for k, v in kwargs.items() if k != "tool_choice"})
            else:
                raise
        usage["input"] += resp.usage.input_tokens
        usage["output"] += resp.usage.output_tokens
        if resp.stop_reason == "max_tokens":
            print(f"[Claude] WARNING: {model} hit max_tokens; output may be cut short")
        for block in resp.content:
            if block.type == "tool_use" and block.name == tool_name:
                return block.input
        print(f"[Claude] {model} answered without calling {tool_name}; retrying")
    raise RuntimeError(f"{model} returned no tool call")


# ---------------------------------------------------------------- stage 1
TRIAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "scores": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "score": {"type": "integer", "minimum": 0, "maximum": 10},
                    "section": {"type": "string", "enum": SECTION_KEYS + ["skip"]},
                },
                "required": ["id", "score", "section"],
            },
        }
    },
    "required": ["scores"],
}

SECTION_GUIDE = """Sections:
- poker: poker strategy, theory, solver work, the poker industry
- ai: AI capability — what AI can newly DO (high bar, see interests)
- bitcoin: Bitcoin, monetary policy, macroeconomics, investing
- health: diet, metabolism, longevity, exercise science, training
- mind: Stoicism, philosophy, mental strength, decision-making, mental models
- reading: other genuinely interesting essays, science, ideas
- hoops: NBA and college basketball
- skip: not worth showing"""


def triage(candidates, interests):
    lines = []
    for c in candidates:
        extra = ""
        if c["kind"] == "hn":
            extra = f" [HN {c['points']} pts, {c['comments']} comments]"
        elif c["kind"] == "video" and c.get("is_short"):
            extra = " [YouTube SHORT]"
        snippet = (c.get("snippet") or "").replace("\n", " ")[:600]
        lines.append(f"{c['id']} | {c['source']}{extra} | {c['title']}\n    {snippet}")

    system = f"""You triage items for a personal morning brief. Score how much THIS reader would want each one (0-10) and pick its section.

{interests}

{SECTION_GUIDE}

Scoring:
- 9-10: squarely in their interests AND substantive (specific data, argument, technique, or a real launch)
- 7-8: clearly relevant with real substance — worth a paragraph
- 5-6: relevant, some substance — a short write-up or a one-liner
- 3-4: on-topic but thin, clickbait, or a rehash
- 0-2: off-topic, promotional, or on their "do not care" list
The reader hand-picked the YouTube channels and blogs, so a substantive episode or post on one of their topics is normally a 6-8, not a 5. Use the full range.
YouTube Shorts and clips rarely go above 5 unless they make a specific, novel claim.
Score every id exactly once."""

    result = _call_tool(TRIAGE_MODEL, system, "Items:\n\n" + "\n".join(lines),
                        "submit_scores", TRIAGE_SCHEMA, max_tokens=8000)
    out = {}
    for s in result.get("scores", []):
        if isinstance(s, dict) and s.get("id"):
            out[s["id"]] = (int(s.get("score", 0)), s.get("section", "skip"))
    return out


# ---------------------------------------------------------------- stage 2
WRITE_SCHEMA = {
    "type": "object",
    "properties": {
        "top": {
            "type": "array", "maxItems": 3,
            "description": "The 1-3 things most worth their attention today.",
            "items": {"type": "object", "properties": {
                "id": {"type": "string"},
                "why": {"type": "string", "description": "One short sentence: the point, not the topic."},
            }, "required": ["id", "why"]},
        },
        "items": {
            "type": "array",
            "items": {"type": "object", "properties": {
                "id": {"type": "string"},
                "section": {"type": "string", "enum": SECTION_KEYS},
                "headline": {"type": "string", "description": "Plain-language headline stating the core claim or news. Max ~12 words."},
                "summary": {"type": "string", "description": "2-4 sentences of substance."},
                "takeaways": {"type": "array", "maxItems": 4, "items": {"type": "string"},
                              "description": "Optional concrete tactics, numbers or claims. Omit if the summary covers it."},
            }, "required": ["id", "section", "headline", "summary"]},
        },
        "also": {
            "type": "array",
            "description": "Lighter items worth one line.",
            "items": {"type": "object", "properties": {
                "id": {"type": "string"},
                "line": {"type": "string", "description": "One sentence on what it says."},
            }, "required": ["id", "line"]},
        },
        "quiet_day": {"type": "boolean"},
    },
    "required": ["top", "items", "also"],
}


def write(main_items, light_items, interests):
    blocks = []
    for c in main_items:
        meta = f"{c['source']}"
        if c["kind"] == "video":
            meta += " (YouTube" + (" short)" if c.get("is_short") else ")")
        elif c["kind"] == "hn":
            meta += f" ({c['points']} pts)"
        body = c.get("content") or c.get("snippet") or "(title only)"
        blocks.append(f"<item id=\"{c['id']}\" suggested_section=\"{c['section']}\">\n"
                      f"Source: {meta}\nTitle: {c['title']}\n\n{body}\n</item>")
    light = [f"<light id=\"{c['id']}\">{c['source']}: {c['title']} — "
             f"{(c.get('snippet') or '')[:400]}</light>" for c in light_items]

    system = f"""You write a personal morning brief. Reader:

{interests}

{SECTION_GUIDE}

Editorial rules:
- Every item and every 'also' line must use an id from the input. Use each id AT MOST ONCE across items, also and top lists combined (top ids must also appear in items).
- Summarize the IDEAS: the specific claim, number, study, mechanism or technique. Never "X discusses Y" — say what X concluded about Y.
- Stick to what the source says. Don't add background facts from your own knowledge; if the source gives no specifics, say less.
- If the title is jargon or the product is obscure, the headline says what the thing IS.
- AI section: only new model families, new product categories from major labs, step-change capabilities, or surprising findings. 0-2 items on most days.
- Bitcoin section: only a real argument, data point or policy development. Skip price chatter.
- Give each <item> a full write-up if its text has real substance (a claim, number, mechanism, technique). Demote to a one-line 'also' only if the text is thin, promotional, or repeats another item. Drop it only if it's worthless. Aim for 6-14 full items on a normal day. Max 5 per section.
- 'also' is for <light> entries and demoted items worth one line. Skip the rest.
- Videos marked as shorts: one-line 'also' at most, unless they make a specific novel claim.
- Plain text only — no HTML or markdown. No hype words."""

    user = "Main candidates (full text):\n\n" + "\n\n".join(blocks)
    if light:
        user += "\n\nLighter candidates (one-liners at most):\n" + "\n".join(light)

    return _call_tool(WRITER_MODEL, system, user, "submit_brief", WRITE_SCHEMA, max_tokens=12000)


def validate(draft, by_id):
    """Drop unknown/duplicate ids and over-long sections; return a clean structure."""
    used = set()
    sections = {k: [] for k in SECTION_KEYS}
    for it in draft.get("items", []):
        iid = it.get("id")
        sec = it.get("section")
        if iid not in by_id or iid in used or sec not in sections or len(sections[sec]) >= 5:
            continue
        if not (it.get("headline") and it.get("summary")):
            continue
        used.add(iid)
        sections[sec].append({
            "src": by_id[iid],
            "headline": it["headline"].strip(),
            "summary": it["summary"].strip(),
            "takeaways": [t.strip() for t in it.get("takeaways") or [] if t and t.strip()][:4],
        })

    top = []
    for t in draft.get("top", []):
        if t.get("id") in used and t["id"] not in {x["src"]["id"] for x in top} and t.get("why"):
            top.append({"src": by_id[t["id"]], "why": t["why"].strip()})
    top = top[:3]

    also = []
    for a in draft.get("also", []):
        iid = a.get("id")
        if iid in by_id and iid not in used and a.get("line"):
            used.add(iid)
            also.append({"src": by_id[iid], "line": a["line"].strip()})

    dropped = len(draft.get("items", [])) + len(draft.get("also", [])) - len(used)
    if dropped:
        print(f"[validate] Dropped {dropped} invalid/duplicate entries from the draft")
    return {"top": top, "sections": sections, "also": also,
            "quiet_day": bool(draft.get("quiet_day")) and not used}
