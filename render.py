"""
Turns the validated brief data into a single self-contained HTML page.
All text from sources and from Claude is HTML-escaped here.
"""

import json
from html import escape as _esc

# key, icon, label, accent (light), accent (dark)
SECTIONS = [
    ("news",    "◉", "World & Markets",   "#38506b", "#a3b9d3"),
    ("poker",   "♠", "Poker",             "#2d5b4f", "#8fc2ad"),
    ("health",  "✚", "Health & Sleep",    "#a33c3c", "#ec8f84"),
    ("mind",    "◎", "Mind & Philosophy", "#6b4b8a", "#c6a4e6"),
    ("bitcoin", "₿", "Bitcoin & Macro",   "#b4691a", "#e7a865"),
    ("ai",      "◆", "AI Capability",     "#4a4f9c", "#a9adf0"),
    ("romania", "◈", "Romania",           "#1f5f8b", "#86bde3"),
    ("reading", "¶", "Worth Reading",     "#5c5648", "#cfc6b2"),
]

WMO = {  # Open-Meteo weather codes -> (icon, words)
    0: ("☀️", "Clear"), 1: ("🌤️", "Mostly clear"), 2: ("⛅", "Partly cloudy"), 3: ("☁️", "Overcast"),
    45: ("🌫️", "Fog"), 48: ("🌫️", "Freezing fog"),
    51: ("🌦️", "Light drizzle"), 53: ("🌦️", "Drizzle"), 55: ("🌧️", "Heavy drizzle"),
    56: ("🌧️", "Freezing drizzle"), 57: ("🌧️", "Freezing drizzle"),
    61: ("🌦️", "Light rain"), 63: ("🌧️", "Rain"), 65: ("🌧️", "Heavy rain"),
    66: ("🌧️", "Freezing rain"), 67: ("🌧️", "Freezing rain"),
    71: ("🌨️", "Light snow"), 73: ("🌨️", "Snow"), 75: ("❄️", "Heavy snow"), 77: ("🌨️", "Snow grains"),
    80: ("🌦️", "Showers"), 81: ("🌧️", "Showers"), 82: ("⛈️", "Heavy showers"),
    85: ("🌨️", "Snow showers"), 86: ("❄️", "Snow showers"),
    95: ("⛈️", "Thunderstorm"), 96: ("⛈️", "Thunderstorm, hail"), 99: ("⛈️", "Thunderstorm, hail"),
}


def e(x):
    return _esc(str(x if x is not None else ""), quote=True)


def _words(*texts):
    return sum(len(str(t).split()) for t in texts if t)


def _meta(src):
    bits = [e(src["source"])]
    if src["kind"] == "video":
        bits.append(f'<span class="orig">“{e(src["title"].strip(chr(34) + "“”"))}”</span>')
    elif src["kind"] == "hn":
        bits.append(f'<a href="{e(src["discussion_url"])}">{e(src["comments"])} comments</a>')
    return " · ".join(bits)


def _vote_attrs(src):
    return f'data-src="{e(src["source"])}" data-title="{e(src["title"])}"'


def _thumbs(src):
    return (f'<span class="vote" {_vote_attrs(src)}>'
            f'<button type="button" class="up" aria-label="More like this">👍</button>'
            f'<button type="button" class="dn" aria-label="Less like this">👎</button></span>')


def _item(it):
    s = it["src"]
    is_vid = s["kind"] == "video"
    thumb = ""
    if is_vid and s.get("video_id"):
        thumb = (f'<a class="thumb" href="{e(s["url"])}" aria-hidden="true" tabindex="-1">'
                 f'<img src="https://i.ytimg.com/vi/{e(s["video_id"])}/mqdefault.jpg" alt="" loading="lazy" '
                 f'width="320" height="180"><span class="play">▶</span></a>')
    take = ""
    if it["takeaways"]:
        take = "<ul class=\"take\">" + "".join(f"<li>{e(t)}</li>" for t in it["takeaways"]) + "</ul>"
    src_line = ("▶ " if is_vid else "") + e(s["source"])
    extra = ""
    if s["kind"] == "hn":
        extra = f' · <a href="{e(s["discussion_url"])}">{e(s["comments"])} comments</a>'
    orig = (f'<p class="orig">“{e(s["title"].strip(chr(34) + "“”"))}”</p>' if is_vid else "")
    return f"""
<article class="item" id="{e(s['id'])}">
  <p class="src">{src_line}{extra}</p>
  {thumb}<h3><a href="{e(s['url'])}">{e(it['headline'])}</a></h3>
  <p class="sum">{e(it['summary'])}</p>{take}{orig}
  <div class="row"><a class="open" href="{e(s['url'])}">{"Watch" if is_vid else "Read"} →</a>{_thumbs(s)}</div>
</article>"""


def _sparkline(values, w=132, h=36):
    if not values or len(values) < 2:
        return ""
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1
    pts = [(round(i * (w - 4) / (len(values) - 1) + 2, 1),
            round(h - 3 - (v - lo) * (h - 6) / span, 1)) for i, v in enumerate(values)]
    line = " ".join(f"{x},{y}" for x, y in pts)
    area = f"2,{h} " + line + f" {w - 2},{h}"
    up = values[-1] >= values[0]
    cls = "up" if up else "down"
    lx, ly = pts[-1]
    return (f'<svg class="spark {cls}" viewBox="0 0 {w} {h}" width="{w}" height="{h}" preserveAspectRatio="none" aria-hidden="true">'
            f'<polygon points="{area}" class="fill"/><polyline points="{line}" class="ln"/>'
            f'<circle cx="{lx}" cy="{ly}" r="2.6" class="dot"/></svg>')


def _pct(v):
    if v is None:
        return ""
    cls = "up" if v >= 0 else "down"
    return f'<span class="{cls}">{"▲" if v >= 0 else "▼"} {abs(v):.1f}%</span>'


def _cards(weather, btc):
    cards = []
    if weather:
        icon, words = WMO.get(weather.get("code"), ("🌡️", ""))
        rain = weather.get("precip_prob")
        rain_html = f" · {rain}% rain" if rain is not None and rain >= 20 else ""
        cards.append(f"""
  <div class="card wx">
    <p class="kicker">{e(weather.get('place') or 'Weather')}</p>
    <div class="big"><span class="wi">{icon}</span>{weather['temp']:.0f}°</div>
    <p class="cap">{e(words)} · H {weather['hi']:.0f}° L {weather['lo']:.0f}°{rain_html}</p>
  </div>""")
    if btc:
        cards.append(f"""
  <div class="card btc">
    <p class="kicker">Bitcoin</p>
    <div class="big" id="btc-p">${btc['price']:,.0f}</div>
    <p class="cap"><span id="btc-c">{_pct(btc.get('d1'))}</span> 24h · {_pct(btc.get('d7'))} 7d</p>
    {_sparkline(btc.get('spark') or [])}
  </div>""")
    return f'<section class="cards n{len(cards)}">{"".join(cards)}</section>' if cards else ""


def _health(health, stats, prev_url):
    bad = [(k, v) for k, v in health.items() if v[0] in ("fail", "warn")]
    ok_count = len(health) - len(bad)
    rows = "".join(
        f'<li class="{e(v[0])}"><b>{e(k)}</b> — {e(v[1])}</li>' for k, v in sorted(bad)
    )
    status = (f'<p class="hl ok">● All {ok_count} sources OK</p>' if not bad else
              f'<details><summary class="hl warn">● {len(bad)} source issue{"s" if len(bad) > 1 else ""} · {ok_count} OK</summary>'
              f"<ul>{rows}</ul></details>")
    prev = f'<a href="{e(prev_url)}">← Yesterday</a>' if prev_url else ""
    return f"""
<footer class="foot">
  <nav class="arch">{prev}<a href="archive/">All briefs</a></nav>
  {status}
  <p class="stats">{e(stats)}</p>
</footer>"""


def build_html(*, date_label, greeting, brief, anchor, spotlight, btc, weather,
               health, stats, prev_url=None, base="", feedback_repo="", day=""):
    present = [sec for sec in SECTIONS if brief["sections"].get(sec[0])]

    words = _words(*(t["why"] for t in brief["top"]))
    for items in brief["sections"].values():
        for it in items:
            words += _words(it["headline"], it["summary"], *it["takeaways"])
    words += _words(*(a["line"] for a in brief["also"]))
    minutes = max(1, round(words / 230))
    n_items = sum(len(v) for v in brief["sections"].values())

    top_html = ""
    if brief["top"]:
        lis = "".join(
            f'<li><a href="#{e(t["src"]["id"])}">{e(t["why"])}</a></li>' for t in brief["top"])
        top_html = f'<section class="top"><p class="kicker">If you read nothing else</p><ol>{lis}</ol></section>'

    nav_html = ""
    if len(present) > 1:
        nav_html = '<nav class="nav" aria-label="Sections">' + "".join(
            f'<a href="#s-{k}" style="--a:{la};--ad:{da}"><span>{icon}</span>{e(label)}'
            f'<em>{len(brief["sections"][k])}</em></a>'
            for k, icon, label, la, da in present) + "</nav>"

    body = []
    for key, icon, label, la, da in present:
        items = brief["sections"].get(key, [])
        inner = "".join(_item(it) for it in items)
        body.append(f'<section class="sec" id="s-{key}" style="--a:{la};--ad:{da}">'
                    f'<h2><span class="ic">{icon}</span>{e(label)}</h2>{inner}</section>')
    if not n_items:
        body.append('<p class="quiet">Quiet day. Nothing cleared the bar.</p>')

    also_html = ""
    if brief["also"]:
        lis = "".join(
            f'<li><a href="{e(a["src"]["url"])}"><b>{e(a["src"]["source"])}</b>{e(a["line"])}</a>'
            f'{_thumbs(a["src"])}</li>' for a in brief["also"])
        also_html = (f'<details class="also"><summary>Quick hits <span>{len(brief["also"])}</span></summary>'
                     f"<ul>{lis}</ul></details>")

    anchor_html = ""
    if anchor:
        psg = anchor.get("passage")
        psg_html = ""
        if psg:
            psg_html = f"""
<section class="passage">
  <p class="kicker">Daily Stoic reading{(" · " + e(psg["theme"])) if psg.get("theme") else ""}</p>
  <p class="ptext">{e(psg["text"])}</p>
  <p class="by">— {e(psg["source"])}</p>
  <p class="ctx">{e(psg["commentary"])}</p>
</section>"""
        anchor_html = f"""{psg_html}
<section class="anchor">
  <div>
    <p class="kicker">Quote</p>
    <blockquote>{e(anchor['quote'])}</blockquote>
    <p class="by">— {e(anchor['author'])}</p>
    <p class="ctx">{e(anchor['quote_context'])}</p>
  </div>
  <div>
    <p class="kicker">Mental model · {e(anchor['model_domain'])}</p>
    <p class="mm">{e(anchor['model_name'])}</p>
    <p class="ctx">{e(anchor['model_story'])}</p>
  </div>
</section>"""

    spot_html = ""
    if spotlight:
        snippet = f'    "{spotlight["channel_name"]}": "{spotlight["channel_id"]}",'
        days = spotlight.get("days_left", 1)
        spot_html = f"""
<section class="spot">
  <p class="kicker">Channel spotlight · {days} day{"s" if days != 1 else ""} left</p>
  <p class="mm"><a href="https://www.youtube.com/channel/{e(spotlight['channel_id'])}">{e(spotlight['channel_name'])}</a></p>
  <p class="ctx">{e(spotlight['pitch'])}</p>
  <div class="snip"><code id="snip">{e(snippet)}</code><button type="button" id="copy">Copy</button></div>
  <p class="hint">Paste into YOUTUBE_CHANNELS in brief.py to follow.</p>
</section>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#f5f2ea" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#15140f" media="(prefers-color-scheme: dark)">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="Brief">
<meta name="robots" content="noindex">
<link rel="icon" href="{base}icon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{base}apple-touch-icon.png">
<title>Morning Brief · {e(date_label)}</title>
<style>
:root {{
  --bg:#f5f2ea; --card:#fffdf8; --ink:#1d1b17; --soft:#47433b; --mute:#837d71; --rule:#e6e0d3;
  --acc:#2d5b4f; --acc-soft:#e6eee8; --warm:#b4691a; --up:#2e7d4f; --down:#b8402f;
  --serif: "Iowan Old Style", "Charter", "Palatino Linotype", Palatino, Georgia, serif;
  --sans: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", system-ui, Roboto, sans-serif;
  --shadow: 0 1px 2px rgba(40,30,10,.05), 0 8px 24px -14px rgba(40,30,10,.22);
  --r: 18px; --pad: 20px;
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --bg:#13120e; --card:#1c1a15; --ink:#efeadd; --soft:#cdc6b6; --mute:#8f887a; --rule:#2f2c26;
    --acc:#8fc2ad; --acc-soft:#1f2a25; --warm:#e0a15a; --up:#6cc28e; --down:#e57f6c;
    --shadow: 0 1px 2px rgba(0,0,0,.35), 0 10px 28px -16px rgba(0,0,0,.7);
  }}
  .sec, .nav a {{ --a: var(--ad) !important; }}
}}
* {{ box-sizing:border-box; -webkit-tap-highlight-color:transparent; }}
html {{ scroll-behavior:smooth; -webkit-text-size-adjust:100%; }}
body {{ margin:0; background:var(--bg); color:var(--ink); font:18px/1.62 var(--serif);
  -webkit-font-smoothing:antialiased; text-rendering:optimizeLegibility; overflow-x:hidden; }}
.wrap {{ max-width:680px; margin:0 auto;
  padding:max(30px, calc(env(safe-area-inset-top) + 14px)) max(var(--pad), env(safe-area-inset-right))
          calc(96px + env(safe-area-inset-bottom)) max(var(--pad), env(safe-area-inset-left)); }}
a {{ color:inherit; text-decoration-color:var(--rule); text-underline-offset:3px; text-decoration-thickness:1px; }}
.kicker {{ font:650 11px/1.2 var(--sans); letter-spacing:.13em; text-transform:uppercase; color:var(--mute); margin:0 0 10px; }}
.progress {{ position:fixed; inset:0 0 auto 0; height:3px; z-index:20; background:var(--warm); transform-origin:0 50%; transform:scaleX(0); }}

header .brand {{ display:flex; align-items:center; gap:8px; font:650 12px/1 var(--sans); letter-spacing:.16em; text-transform:uppercase; color:var(--acc); margin:0; }}
header .brand::before {{ content:""; width:18px; height:18px; border-radius:50%;
  background:radial-gradient(circle at 50% 120%, var(--warm) 0 45%, transparent 46%), var(--acc-soft); box-shadow:inset 0 0 0 1px var(--rule); }}
header h1 {{ font-size:42px; line-height:1.06; margin:14px 0 10px; font-weight:650; letter-spacing:-.025em; }}
.greet {{ margin:0; color:var(--soft); font-size:18px; line-height:1.5; font-style:italic; }}
.bar {{ display:flex; flex-wrap:wrap; gap:6px; margin-top:14px; }}
.bar span {{ font:600 12px/1 var(--sans); color:var(--soft); background:var(--card); border:1px solid var(--rule); border-radius:99px; padding:7px 11px; }}

.cards {{ display:grid; gap:10px; margin:22px 0 0; }}
.cards.n2 {{ grid-template-columns:1fr 1fr; }}
.card {{ background:var(--card); border:1px solid var(--rule); border-radius:var(--r); padding:15px 16px 13px; box-shadow:var(--shadow); position:relative; overflow:hidden; }}
.card .big {{ font:650 28px/1.1 var(--sans); letter-spacing:-.02em; font-variant-numeric:tabular-nums; display:flex; align-items:center; gap:8px; }}
.card .wi {{ font-size:24px; }}
.card .cap {{ margin:6px 0 0; font:12.5px/1.4 var(--sans); color:var(--mute); }}
.up {{ color:var(--up); }} .down {{ color:var(--down); }}
.spark {{ display:block; width:100%; height:30px; margin-top:8px; }}
.spark .ln {{ fill:none; stroke-width:1.8; stroke-linejoin:round; stroke-linecap:round; vector-effect:non-scaling-stroke; }}
.spark.up .ln {{ stroke:var(--up); }} .spark.down .ln {{ stroke:var(--down); }}
.spark .fill {{ opacity:.12; }} .spark.up .fill {{ fill:var(--up); }} .spark.down .fill {{ fill:var(--down); }}
.spark.up .dot {{ fill:var(--up); }} .spark.down .dot {{ fill:var(--down); }}

.top {{ background:var(--card); border:1px solid var(--rule); border-radius:var(--r); padding:20px 20px 6px; margin:12px 0 0; box-shadow:var(--shadow); }}
.top ol {{ margin:0; padding:0; list-style:none; counter-reset:t; }}
.top li {{ counter-increment:t; position:relative; padding:0 0 14px 34px; font-size:17.5px; line-height:1.48; }}
.top li::before {{ content:counter(t); position:absolute; left:0; top:-1px; font:650 23px/1 var(--serif); color:var(--warm); }}
.top a {{ text-decoration:none; }}

.nav {{ position:sticky; top:0; z-index:10; display:flex; gap:7px; overflow-x:auto; scroll-snap-type:x proximity; scroll-padding-inline:var(--pad);
  padding:calc(env(safe-area-inset-top) + 10px) var(--pad) 10px; margin:18px calc(-1 * var(--pad)) 0;
  background:color-mix(in srgb, var(--bg) 86%, transparent); backdrop-filter:saturate(1.5) blur(14px); -webkit-backdrop-filter:saturate(1.5) blur(14px);
  scrollbar-width:none; mask-image:linear-gradient(90deg, #000 88%, transparent); -webkit-mask-image:linear-gradient(90deg, #000 88%, transparent); }}
.nav::-webkit-scrollbar {{ display:none; }}
.nav a {{ flex:none; scroll-snap-align:start; display:flex; align-items:center; gap:6px; font:600 13.5px/1 var(--sans); padding:10px 13px; border-radius:99px; border:1px solid var(--rule);
  text-decoration:none; color:var(--soft); background:var(--card); }}
.nav a span {{ color:var(--a); }}
.nav a em {{ font-style:normal; font-weight:500; color:var(--mute); font-size:12px; }}
.nav a.on {{ border-color:var(--a); color:var(--a); background:color-mix(in srgb, var(--a) 9%, var(--card)); }}

.sec {{ margin-top:30px; scroll-margin-top:70px; }}
.sec h2 {{ display:flex; align-items:center; gap:9px; font:700 13px/1 var(--sans); letter-spacing:.13em;
  text-transform:uppercase; color:var(--a); margin:0 0 12px 4px; }}
.ic {{ font-size:15px; }}
.item {{ background:var(--card); border:1px solid var(--rule); border-radius:var(--r); padding:16px 18px 10px; margin-bottom:12px;
  box-shadow:var(--shadow); scroll-margin-top:70px; border-top:3px solid var(--a); }}
.item .src {{ font:650 12px/1.3 var(--sans); color:var(--a); margin:0 0 8px; letter-spacing:.01em; }}
.item .src a {{ color:var(--mute); font-weight:500; }}
.item h3 {{ font-size:21.5px; line-height:1.27; margin:0 0 9px; font-weight:650; letter-spacing:-.012em; }}
.item h3 a {{ text-decoration:none; }}
.item .sum {{ margin:0 0 10px; color:var(--soft); }}
.thumb {{ float:right; position:relative; width:112px; margin:2px 0 8px 14px; border-radius:10px; overflow:hidden; aspect-ratio:16/9; background:var(--rule); }}
.thumb img {{ width:100%; height:100%; object-fit:cover; display:block; }}
.thumb .play {{ position:absolute; inset:0; display:grid; place-items:center; color:#fff; font-size:15px; text-shadow:0 1px 6px rgba(0,0,0,.6); }}
.item:target {{ box-shadow:0 0 0 2px var(--a), var(--shadow); }}
.take {{ clear:both; margin:4px 0 12px; padding:12px 14px 12px 30px; background:color-mix(in srgb, var(--a) 7%, var(--card)); border-radius:12px; color:var(--soft); font-size:16px; line-height:1.52; }}
.take li {{ margin:4px 0; }} .take li::marker {{ color:var(--a); }}
.orig {{ clear:both; margin:0 0 6px; font:italic 13px/1.45 var(--sans); color:var(--mute); }}
.row {{ clear:both; display:flex; align-items:center; justify-content:space-between; gap:10px; border-top:1px solid var(--rule); margin:6px -4px 0; padding-top:6px; }}
.open {{ font:650 14px/1 var(--sans); color:var(--a); text-decoration:none; padding:10px 4px; }}

.vote {{ display:inline-flex; gap:4px; flex:none; }}
.vote button {{ width:40px; height:36px; border-radius:10px; border:1px solid transparent; background:transparent; font-size:17px; line-height:1;
  cursor:pointer; filter:grayscale(1); opacity:.5; transition:transform .12s, opacity .12s, filter .12s, background .12s; }}
.vote button:active {{ transform:scale(.9); }}
.vote button.on {{ filter:none; opacity:1; background:var(--acc-soft); border-color:var(--rule); }}

.also {{ margin-top:30px; background:var(--card); border:1px solid var(--rule); border-radius:var(--r); padding:0 16px 0 18px; box-shadow:var(--shadow); }}
.also summary {{ cursor:pointer; padding:18px 0; font:700 13px/1 var(--sans); letter-spacing:.13em; text-transform:uppercase; color:var(--acc); list-style:none; }}
.also summary::-webkit-details-marker {{ display:none; }}
.also summary::after {{ content:"＋"; float:right; color:var(--mute); }}
.also[open] summary::after {{ content:"－"; }}
.also summary span {{ color:var(--mute); margin-left:6px; }}
.also ul {{ margin:0 0 10px; padding:0; list-style:none; }}
.also li {{ display:flex; align-items:center; gap:6px; border-top:1px solid var(--rule); }}
.also li > a {{ flex:1; padding:12px 0; font-size:16px; line-height:1.48; color:var(--soft); text-decoration:none; }}
.also li b {{ display:block; font:650 12px/1.3 var(--sans); color:var(--ink); margin-bottom:2px; }}
.also .vote button {{ width:34px; }}

.passage {{ margin-top:36px; padding:24px 22px 22px; border-radius:var(--r); background:linear-gradient(160deg, color-mix(in srgb, #6b4b8a 10%, var(--card)), var(--card) 60%);
  border:1px solid var(--rule); box-shadow:var(--shadow); }}
.ptext {{ margin:0; font-size:19px; line-height:1.6; }}
.ptext::first-letter {{ float:left; font:650 52px/.86 var(--serif); margin:6px 8px 0 0; color:var(--warm); }}
.anchor {{ display:grid; grid-template-columns:1fr 1fr; gap:26px; margin-top:12px; padding:22px; border-radius:var(--r); background:var(--card); border:1px solid var(--rule); box-shadow:var(--shadow); }}
blockquote {{ margin:0; font-size:20px; line-height:1.45; font-style:italic; }}
blockquote::before {{ content:"“"; display:block; font:650 44px/0.6 var(--serif); color:var(--warm); margin:10px 0 4px; }}
.by {{ margin:10px 0 8px; font:650 13px var(--sans); color:var(--soft); }}
.mm {{ font-size:20px; font-weight:650; margin:0 0 6px; line-height:1.3; }}
.ctx {{ margin:0; font-size:15.5px; line-height:1.58; color:var(--soft); }}
.spot {{ margin-top:12px; padding:20px 22px; border-radius:var(--r); border:1px dashed var(--rule); }}
.snip {{ display:flex; gap:8px; align-items:center; margin-top:12px; }}
.snip code {{ flex:1; min-width:0; overflow-x:auto; white-space:pre; font:12.5px/1.5 ui-monospace, Consolas, monospace; background:var(--acc-soft); padding:9px 10px; border-radius:8px; }}
.snip button {{ font:650 13px var(--sans); border:0; border-radius:8px; padding:10px 14px; background:var(--acc); color:var(--bg); cursor:pointer; }}
.hint {{ font:12px var(--sans); color:var(--mute); margin:8px 0 0; }}
.quiet {{ font-style:italic; color:var(--mute); margin-top:30px; }}

.send {{ position:fixed; left:50%; bottom:calc(16px + env(safe-area-inset-bottom)); z-index:30; transform:translate(-50%, 140%);
  display:flex; align-items:center; gap:10px; padding:13px 20px; border-radius:99px; border:0; background:var(--ink); color:var(--bg);
  font:650 15px/1 var(--sans); box-shadow:0 10px 30px -8px rgba(0,0,0,.45); cursor:pointer; transition:transform .25s cubic-bezier(.2,.9,.3,1.2); white-space:nowrap; }}
.send.show {{ transform:translate(-50%, 0); }}
.send b {{ background:var(--warm); color:#fff; border-radius:99px; min-width:22px; padding:4px 7px; font-size:12px; text-align:center; }}

.foot {{ margin-top:40px; padding-top:16px; border-top:1px solid var(--rule); font:13px/1.5 var(--sans); color:var(--mute); }}
.arch {{ display:flex; gap:10px; margin-bottom:14px; }}
.arch a {{ color:var(--acc); text-decoration:none; font-weight:650; padding:10px 14px; border:1px solid var(--rule); border-radius:99px; background:var(--card); }}
.foot details summary {{ cursor:pointer; list-style:none; }}
.foot details summary::-webkit-details-marker {{ display:none; }}
.foot ul {{ margin:6px 0; padding-left:18px; }}
.foot li.fail b {{ color:var(--down); }} .foot li.warn b {{ color:var(--warm); }}
.hl {{ margin:0; font-weight:650; }} .hl.ok {{ color:var(--up); }} .hl.warn {{ color:var(--warm); }}
.stats {{ margin:6px 0 0; }}
@media (max-width:560px) {{
  :root {{ --pad:14px; --r:16px; }}
  body {{ font-size:17px; line-height:1.58; }}
  header h1 {{ font-size:36px; }}
  .greet {{ font-size:17px; }}
  .item {{ padding:15px 15px 8px; }}
  .item h3 {{ font-size:19.5px; }}
  .thumb {{ width:96px; margin-left:12px; }}
  .take {{ font-size:15.5px; }}
  .anchor {{ grid-template-columns:1fr; gap:22px; }}
  .card .big {{ font-size:24px; }}
  .ptext {{ font-size:18px; }}
}}
@media (max-width:360px) {{ .cards.n2 {{ grid-template-columns:1fr; }} }}
@media (prefers-reduced-motion:reduce) {{ html {{ scroll-behavior:auto; }} .send {{ transition:none; }} }}
</style>
</head>
<body>
<div class="progress" id="prog"></div>
<div class="wrap">
<header>
  <p class="brand">Morning Brief</p>
  <h1>{e(date_label)}</h1>
  <p class="greet">{e(greeting)}</p>
  <div class="bar"><span>{minutes} min read</span><span>{n_items} {"story" if n_items == 1 else "stories"}</span><span>{len(brief["also"])} quick hits</span></div>
</header>
{_cards(weather, btc)}
{top_html}
{nav_html}
{''.join(body)}
{also_html}
{anchor_html}
{spot_html}
{_health(health, stats, prev_url)}
</div>
<button type="button" class="send" id="send">Send feedback <b id="send-n">0</b></button>
<script>
(function () {{
  var REPO = {json.dumps(feedback_repo)}, DAY = {json.dumps(day)}, KEY = 'brief-votes';

  // copy button (channel spotlight)
  var b = document.getElementById('copy');
  if (b) b.addEventListener('click', function () {{
    navigator.clipboard.writeText(document.getElementById('snip').innerText.trim());
    b.textContent = 'Copied'; setTimeout(function () {{ b.textContent = 'Copy'; }}, 1800);
  }});

  // live BTC price
  var p = document.getElementById('btc-p');
  if (p) fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true')
    .then(function (r) {{ return r.json(); }})
    .then(function (d) {{
      var v = d.bitcoin.usd, c = d.bitcoin.usd_24h_change;
      p.textContent = '$' + Math.round(v).toLocaleString('en-US');
      document.getElementById('btc-c').innerHTML = '<span class="' + (c >= 0 ? 'up' : 'down') + '">' + (c >= 0 ? '▲ ' : '▼ ') + Math.abs(c).toFixed(1) + '%</span>';
    }}).catch(function () {{}});

  // reading progress + active section pill
  var prog = document.getElementById('prog'), pills = document.querySelectorAll('.nav a'), secs = document.querySelectorAll('.sec');
  function onScroll() {{
    var h = document.documentElement, max = h.scrollHeight - h.clientHeight;
    prog.style.transform = 'scaleX(' + (max > 0 ? h.scrollTop / max : 0) + ')';
    var cur = null;
    secs.forEach(function (s) {{ if (s.getBoundingClientRect().top < 120) cur = s.id; }});
    pills.forEach(function (a) {{
      var on = a.getAttribute('href') === '#' + cur;
      if (on && !a.classList.contains('on')) a.scrollIntoView({{inline: 'nearest', block: 'nearest'}});
      a.classList.toggle('on', on);
    }});
  }}
  window.addEventListener('scroll', onScroll, {{passive: true}}); onScroll();

  // thumbs up / down -> GitHub issue
  var votes = {{}};
  try {{ votes = JSON.parse(localStorage.getItem(KEY) || '{{}}'); }} catch (e) {{}}
  function save() {{ try {{ localStorage.setItem(KEY, JSON.stringify(votes)); }} catch (e) {{}} }}
  function id(el) {{ return el.dataset.src + '|' + el.dataset.title; }}
  var send = document.getElementById('send'), sendN = document.getElementById('send-n');
  function refresh() {{
    var n = Object.keys(votes).length;
    sendN.textContent = n; send.classList.toggle('show', n > 0 && !!REPO);
    document.querySelectorAll('.vote').forEach(function (el) {{
      var v = votes[id(el)];
      el.querySelector('.up').classList.toggle('on', !!v && v.v > 0);
      el.querySelector('.dn').classList.toggle('on', !!v && v.v < 0);
    }});
  }}
  document.querySelectorAll('.vote button').forEach(function (btn) {{
    btn.addEventListener('click', function (ev) {{
      ev.preventDefault();
      var el = btn.parentNode, k = id(el), v = btn.classList.contains('up') ? 1 : -1;
      if (votes[k] && votes[k].v === v) delete votes[k];
      else votes[k] = {{v: v, s: el.dataset.src, t: el.dataset.title}};
      if (navigator.vibrate) navigator.vibrate(8);
      save(); refresh();
    }});
  }});
  send.addEventListener('click', function () {{
    var lines = Object.keys(votes).map(function (k) {{
      var v = votes[k]; return (v.v > 0 ? '+' : '-') + ' | ' + v.s.replace(/\\|/g, '/') + ' | ' + v.t.replace(/\\|/g, '/');
    }});
    var url = 'https://github.com/' + REPO + '/issues/new?title=' + encodeURIComponent('Brief feedback ' + DAY) +
      '&body=' + encodeURIComponent(lines.join('\\n') + '\\n\\n(Tap Submit. The next brief learns from these.)');
    votes = {{}}; save(); refresh();
    window.open(url, '_blank');
  }});
  refresh();
}})();
</script>
</body>
</html>"""


def build_archive_index(entries):
    """entries: list of (date_iso, label, n_stories) newest first."""
    rows = "".join(
        f'<li><a href="{e(d)}.html"><span>{e(label)}</span><em>{n} stor{"y" if n == 1 else "ies"}</em></a></li>'
        for d, label, n in entries)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark"><meta name="robots" content="noindex">
<link rel="icon" href="../icon.svg" type="image/svg+xml"><title>Morning Brief · Archive</title>
<style>
:root {{ --bg:#f5f2ea; --card:#fffdf8; --ink:#1d1b17; --mute:#837d71; --rule:#e3ddd0; --acc:#2d5b4f; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#15140f; --card:#1e1c16; --ink:#ede8db; --mute:#8f887a; --rule:#33302a; --acc:#8fc2ad; }} }}
body {{ margin:0; background:var(--bg); color:var(--ink); font:17px/1.5 "Iowan Old Style", Charter, Georgia, serif; }}
.wrap {{ max-width:620px; margin:0 auto; padding:32px 20px 64px; }}
p.k {{ font:600 12px/1 -apple-system, "Segoe UI", sans-serif; letter-spacing:.16em; text-transform:uppercase; color:var(--acc); }}
h1 {{ font-size:34px; margin:10px 0 22px; }}
ul {{ list-style:none; padding:0; margin:0; background:var(--card); border:1px solid var(--rule); border-radius:14px; overflow:hidden; }}
li a {{ display:flex; justify-content:space-between; padding:14px 18px; border-top:1px solid var(--rule); text-decoration:none; color:inherit; }}
li:first-child a {{ border-top:0; }} li a:hover {{ background:var(--bg); }}
em {{ font:13px -apple-system, "Segoe UI", sans-serif; color:var(--mute); font-style:normal; }}
.back {{ display:inline-block; margin-top:20px; color:var(--acc); font:600 14px -apple-system, "Segoe UI", sans-serif; text-decoration:none; }}
</style></head><body><div class="wrap"><p class="k">Morning Brief</p><h1>Archive</h1><ul>{rows}</ul>
<a class="back" href="../">← Today's brief</a></div></body></html>"""
