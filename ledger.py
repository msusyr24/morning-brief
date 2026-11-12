"""
Seen-items ledger (seen.json).

Anything that has been put in front of the triage step is recorded here, so it
never shows up in a later brief. This replaces the old per-channel YouTube
watermark, which re-showed a channel's latest video every day it didn't upload.

Videos whose transcript failed are NOT recorded, so they get retried next run.
"""

import json
import os
from datetime import datetime, timedelta, timezone

LEDGER_FILE = "seen.json"
KEEP_DAYS = 120  # longer than any feed's lookback window


class Ledger:
    def __init__(self, path=LEDGER_FILE):
        self.path = path
        self.items = {}
        self.bootstrap = not os.path.exists(path)
        if not self.bootstrap:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.items = json.load(f).get("items", {})
            except Exception:
                self.items = {}

    def has(self, key):
        return key in self.items

    def mark(self, key):
        if key and key not in self.items:
            self.items[key] = datetime.now(timezone.utc).date().isoformat()

    def save(self):
        cutoff = (datetime.now(timezone.utc) - timedelta(days=KEEP_DAYS)).date().isoformat()
        self.items = {k: d for k, d in self.items.items() if d >= cutoff}
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump({"items": dict(sorted(self.items.items()))}, f, indent=0)
