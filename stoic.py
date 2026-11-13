"""
Daily Stoic passage: a real paragraph from a public-domain translation
(Project Gutenberg), plus a two-sentence modern reading applied to decisions
and the mental game. Texts are downloaded once and cached in stoic_cache/.

A model checks each candidate paragraph really is the author's own text (not
the translator's preface or notes) before it's used, and never rewrites it.
"""

import os
import random
import re
from datetime import date

from net import http_get

CACHE = "stoic_cache"
BOOKS = [
    {"slug": "marcus", "author": "Marcus Aurelius", "work": "Meditations",
     "translator": "George Long", "url": "https://www.gutenberg.org/cache/epub/2680/pg2680.txt"},
    {"slug": "epictetus", "author": "Epictetus", "work": "Enchiridion",
     "translator": None, "url": "https://www.gutenberg.org/cache/epub/45109/pg45109.txt"},
]

SCHEMA = {
    "type": "object",
    "properties": {
        "is_author_text": {"type": "boolean",
                           "description": "True only if the passage is the ancient author's own text, "
                                          "not a translator's preface, biography, footnote or index."},
        "theme": {"type": "string", "description": "2-5 word theme, e.g. 'What is in your control'"},
        "commentary": {"type": "string",
                       "description": "2-3 plain sentences: what it means in modern words, then how it "
                                      "applies to decisions under uncertainty, variance, tilt or daily discipline."},
    },
    "required": ["is_author_text", "theme", "commentary"],
}


def _text(book):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, book["slug"] + ".txt")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    resp, err = http_get(book["url"], mode="direct_first", attempts=2, timeout=30)
    if resp is None:
        print(f"[stoic] {book['work']}: {err}")
        return ""
    text = resp.content.decode("utf-8", errors="replace")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return text


def _candidates(text):
    start = re.search(r"\*\*\* ?START OF.*?\*\*\*", text)
    end = re.search(r"\*\*\* ?END OF", text)
    body = text[start.end() if start else 0: end.start() if end else len(text)]
    paras = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", body)]
    good = []
    for p in paras:
        if not 220 <= len(p) <= 1100:
            continue
        if re.search(r"gutenberg|translat|footnote|\[\d+\]|chapter|^[A-Z\s.]{12,}$", p, re.I):
            continue
        if sum(c.isalpha() for c in p) / len(p) < 0.75:
            continue
        good.append(p)
    n = len(good)
    return good[n // 10: n - n // 10] if n > 20 else good  # skip front/back matter


def pick_passage_for_today(today=None, tries=6):
    import llm  # local import: keeps this module importable without the API

    today = today or date.today()
    rng = random.Random(today.toordinal())
    first = today.toordinal() % len(BOOKS)
    for book in BOOKS[first:] + BOOKS[:first]:  # alternate authors; fall back to the other
        got = _pick_from(book, rng, tries)
        if got:
            return got
    return None


def _pick_from(book, rng, tries):
    import llm

    cands = _candidates(_text(book))
    for p in rng.sample(cands, min(tries, len(cands))):
        try:
            out = llm._call_tool(
                llm.TRIAGE_MODEL,
                f"You check and annotate a passage from {book['author']}'s {book['work']} for a morning brief. "
                "The reader plays and backs professional poker and cares about Stoicism applied to decisions. "
                "Plain text, no hype, no quotes from the passage.",
                f"Passage:\n\n{p}", "submit_passage", SCHEMA, max_tokens=800)
        except Exception as e:
            print(f"[stoic] annotation failed: {type(e).__name__}")
            return None
        if out.get("is_author_text") and out.get("commentary"):
            src = f"{book['author']}, {book['work']}" + (f" (tr. {book['translator']})" if book["translator"] else "")
            return {"text": p, "source": src, "theme": out.get("theme", "").strip(),
                    "commentary": out["commentary"].strip()}
    return None
