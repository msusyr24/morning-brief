"""
Networking helpers shared by every fetcher.

http_get() tries a direct connection first and falls back to the Webshare
rotating proxy (or the reverse, for hosts that block GitHub runner IPs).
Every call has a timeout, so no single slow host can hang the run.
"""

import os
import re
import time

import requests

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


def proxy_config():
    """Requests-style proxies dict for Webshare, or None when no creds are set."""
    user = os.getenv("WEBSHARE_PROXY_USERNAME")
    pw = os.getenv("WEBSHARE_PROXY_PASSWORD")
    if not (user and pw):
        return None
    url = f"http://{user}-rotate:{pw}@p.webshare.io:80"
    return {"http": url, "https": url}


def http_get(url, *, mode="direct_first", attempts=3, timeout=20,
             accept="*/*", backoff=2.0, max_bytes=3_000_000):
    """
    GET a URL with retries. Returns (response_or_None, error_string_or_None).

    mode:
      "direct_first" - try direct, then switch to the proxy for the remaining attempts
      "proxy_first"  - try the proxy, then direct (hosts that block runner IPs, e.g. YouTube)
      "direct"       - never use the proxy
    """
    proxies = proxy_config()
    headers = dict(BROWSER_HEADERS, Accept=accept)

    if mode == "direct" or proxies is None:
        plan = [None] * attempts
    elif mode == "proxy_first":
        plan = [proxies] * (attempts - 1) + [None]
    else:
        plan = [None] + [proxies] * (attempts - 1)

    last_error = None
    for i, px in enumerate(plan):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout,
                                proxies=px, stream=True)
            body = resp.raw.read(max_bytes, decode_content=True)
            resp._content = body  # make .content / .text / .json() work after streaming
            resp._content_consumed = True
            resp.close()
            if resp.status_code == 200:
                return resp, None
            last_error = f"HTTP {resp.status_code}"
            if resp.status_code == 404 and px is None and mode == "direct":
                break  # a real 404, retrying won't help
        except Exception as e:
            last_error = type(e).__name__
        if i < len(plan) - 1:
            time.sleep(backoff * (i + 1))
    return None, last_error


_TRACKING_PARAMS = re.compile(r"([?&])(utm_[a-z]+|ref|source|mc_cid|mc_eid)=[^&#]*", re.I)


def normalize_url(url):
    """Strip tracking params and trailing slashes so the same link always matches."""
    if not url:
        return ""
    u = _TRACKING_PARAMS.sub(r"\1", url.strip())
    u = re.sub(r"[?&]+(#|$)", r"\1", u)
    u = u.replace("?&", "?")
    u = re.sub(r"^http://", "https://", u)
    u = re.sub(r"://www\.", "://", u)
    return u.rstrip("/")
