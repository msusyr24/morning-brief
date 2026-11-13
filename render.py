"""
Turns the validated brief data into a single self-contained HTML page.
All text from sources and from Claude is HTML-escaped here.
"""

from html import escape as _esc

# key, icon, label, accent (light), accent (dark)
SECTIONS = [
    ("poker",   "♠", "Poker",             "#2d5b4f", "#8fc2ad"),
    ("ai",      "◆", "AI Capability",     "#4a4f9c", "#a9adf0"),
    ("bitcoin", "₿", "Bitcoin & Macro",   "#b4691a", "#e7a865"),
    ("health",  "✚", "Health & Training", "#a33c3c", "#ec8f84"),
    ("mind",    "◎", "Mind & Philosophy", "#6b4b8a", "#c6a4e6"),
    ("romania", "◈", "Romania",           "#1f5f8b", "#86bde3"),
    ("reading", "¶", "Worth Reading",     "#5c5648", "#cfc6b2"),
    ("hoops",   "●", "Hoops",             "#c0531b", "#f0965f"),
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


def _item(it):
    s = it["src"]
    kind_badge = '<span class="badge">▶ video</span>' if s["kind"] == "video" else ""
    take = ""
    if it["takeaways"]:
        take = "<ul class=\"take\">" + "".join(f"<li>{e(t)}</li>" for t in it["takeaways"]) + "</ul>"
    return f"""
<article class="item" id="{e(s['id'])}">
  <h3><a href="{e(s['url'])}">{e(it['headline'])}</a>{kind_badge}</h3>
  <p>{e(it['summary'])}</p>{take}
  <p class="meta">{_meta(s)}</p>
</article>"""


def _hoops_block(h):
    if not h or not (h.get("nba") or h.get("ncaa")):
        return ""

    def row(g, college=False):
        a, b = g["teams"]

        def side(t):
            rank = f'<span class="rk">{t["rank"]}</span>' if t.get("rank") else ""
            cls = "w" if t["winner"] else ""
            return f'<span class="tm {cls}">{rank}{e(t["abbr"] if not college else t["name"])}</span><span class="sc {cls}">{t["score"]}</span>'

        tags = []
        if g.get("upset"):
            tags.append('<span class="tag up">upset</span>')
        if g.get("ot"):
            tags.append('<span class="tag">OT</span>')
        elif g["margin"] <= 3:
            tags.append('<span class="tag">close</span>')
        leaders = " · ".join(t["leader"] for t in (a, b) if t.get("leader"))
        lead_html = f'<div class="ld">{e(leaders)}</div>' if leaders and not college else ""
        return f'<div class="game"><div class="ln">{side(a)}<span class="at">@</span>{side(b)}{"".join(tags)}</div>{lead_html}</div>'

    def later(n):
        return f' · <span class="late">{n} still in progress</span>' if n else ""

    parts = []
    if h.get("nba"):
        parts.append(f'<p class="sub">NBA · {h["nba_date"]:%a %b} {h["nba_date"].day}{later(h.get("nba_pending"))}</p><div class="games">'
                     + "".join(row(g) for g in h["nba"]) + "</div>")
    if h.get("ncaa"):
        parts.append(f'<p class="sub">College · ranked teams · {h["ncaa_date"]:%a %b} {h["ncaa_date"].day}{later(h.get("ncaa_pending"))}</p><div class="games">'
                     + "".join(row(g, True) for g in h["ncaa"][:12]) + "</div>")
    return '<div class="scores">' + "".join(parts) + "</div>"


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


def build_html(*, date_label, greeting, brief, anchor, spotlight, hoops, btc, weather,
               health, stats, prev_url=None, base=""):
    present = [s for s in SECTIONS
               if brief["sections"].get(s[0]) or (s[0] == "hoops" and hoops and (hoops.get("nba") or hoops.get("ncaa")))]

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
        nav_html = '<nav class="nav">' + "".join(
            f'<a href="#s-{k}" style="--a:{la};--ad:{da}"><span>{icon}</span>{e(label)}</a>'
            for k, icon, label, la, da in present) + "</nav>"

    body = []
    for key, icon, label, la, da in present:
        items = brief["sections"].get(key, [])
        inner = "".join(_item(it) for it in items)
        if key == "hoops":
            inner = _hoops_block(hoops) + inner
        count = f'<span class="n">{len(items)}</span>' if items else ""
        body.append(f'<section class="sec" id="s-{key}" style="--a:{la};--ad:{da}">'
                    f'<h2><span class="ic">{icon}</span>{e(label)}{count}</h2>{inner}</section>')
    if not n_items:
        body.append('<p class="quiet">Quiet day. Nothing cleared the bar.</p>')

    also_html = ""
    if brief["also"]:
        lis = "".join(
            f'<li><a href="{e(a["src"]["url"])}"><b>{e(a["src"]["source"])}</b> {e(a["line"])}'
            f'<span class="go">→</span></a></li>' for a in brief["also"])
        also_html = (f'<details class="also"><summary>Also out today <span>{len(brief["also"])}</span></summary>'
                     f"<ul>{lis}</ul></details>")

    anchor_html = ""
    if anchor:
        anchor_html = f"""
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
<meta name="theme-color" content="#16150f" media="(prefers-color-scheme: dark)">
<meta name="apple-mobile-web-app-title" content="Brief">
<meta name="robots" content="noindex">
<link rel="icon" href="{base}icon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{base}apple-touch-icon.png">
<title>Morning Brief · {e(date_label)}</title>
<style>
:root {{
  --bg:#f5f2ea; --card:#fffdf8; --ink:#1d1b17; --soft:#47433b; --mute:#837d71; --rule:#e3ddd0;
  --acc:#2d5b4f; --acc-soft:#e6eee8; --warm:#b4691a; --up:#2e7d4f; --down:#b8402f;
  --serif: "Iowan Old Style", "Charter", "Palatino Linotype", Palatino, Georgia, serif;
  --sans: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, Roboto, sans-serif;
  --shadow: 0 1px 2px rgba(40,30,10,.04), 0 6px 24px -12px rgba(40,30,10,.18);
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --bg:#15140f; --card:#1e1c16; --ink:#ede8db; --soft:#cbc4b4; --mute:#8f887a; --rule:#33302a;
    --acc:#8fc2ad; --acc-soft:#202b26; --warm:#e0a15a; --up:#6cc28e; --down:#e57f6c;
    --shadow: 0 1px 2px rgba(0,0,0,.3), 0 8px 28px -14px rgba(0,0,0,.6);
  }}
  .sec, .nav a {{ --a: var(--ad) !important; }}
}}
* {{ box-sizing:border-box; }}
html {{ scroll-behavior:smooth; -webkit-text-size-adjust:100%; }}
body {{ margin:0; background:var(--bg); color:var(--ink); font:18px/1.64 var(--serif);
  -webkit-font-smoothing:antialiased; text-rendering:optimizeLegibility; }}
.wrap {{ max-width:700px; margin:0 auto; padding:max(28px, env(safe-area-inset-top)) 20px 72px; }}
a {{ color:inherit; text-decoration-color:var(--rule); text-underline-offset:3px; text-decoration-thickness:1px; }}
a:hover {{ text-decoration-color:currentColor; }}
.kicker {{ font:600 11px/1 var(--sans); letter-spacing:.14em; text-transform:uppercase; color:var(--mute); margin:0 0 10px; }}

header .brand {{ display:flex; align-items:center; gap:8px; font:600 12px/1 var(--sans); letter-spacing:.16em; text-transform:uppercase; color:var(--acc); margin:0; }}
header .brand::before {{ content:""; width:18px; height:18px; border-radius:50%;
  background:radial-gradient(circle at 50% 120%, var(--warm) 0 45%, transparent 46%), var(--acc-soft); box-shadow:inset 0 0 0 1px var(--rule); }}
header h1 {{ font-size:40px; line-height:1.1; margin:14px 0 6px; font-weight:600; letter-spacing:-.02em; }}
.greet {{ margin:0; color:var(--soft); font-size:17px; font-style:italic; }}
.bar {{ display:flex; flex-wrap:wrap; gap:4px 16px; margin-top:10px; font:13px/1.4 var(--sans); color:var(--mute); }}

.cards {{ display:grid; gap:12px; margin:24px 0 0; }}
.cards.n2 {{ grid-template-columns:1fr 1fr; }}
.card {{ background:var(--card); border:1px solid var(--rule); border-radius:14px; padding:16px 18px 14px; box-shadow:var(--shadow); position:relative; overflow:hidden; }}
.card .big {{ font:600 30px/1.1 var(--sans); letter-spacing:-.02em; font-variant-numeric:tabular-nums; display:flex; align-items:center; gap:8px; }}
.card .wi {{ font-size:26px; }}
.card .cap {{ margin:6px 0 0; font:13px/1.4 var(--sans); color:var(--mute); }}
.up {{ color:var(--up); }} .down {{ color:var(--down); }}
.spark {{ position:absolute; right:14px; top:14px; opacity:.95; }}
.spark .ln {{ fill:none; stroke-width:1.8; stroke-linejoin:round; stroke-linecap:round; }}
.spark.up .ln {{ stroke:var(--up); }} .spark.down .ln {{ stroke:var(--down); }}
.spark .fill {{ opacity:.12; }} .spark.up .fill {{ fill:var(--up); }} .spark.down .fill {{ fill:var(--down); }}
.spark.up .dot {{ fill:var(--up); }} .spark.down .dot {{ fill:var(--down); }}

.top {{ background:var(--card); border:1px solid var(--rule); border-radius:14px; padding:20px 22px 8px; margin:14px 0 6px; box-shadow:var(--shadow); }}
.top ol {{ margin:0; padding:0; list-style:none; counter-reset:t; }}
.top li {{ counter-increment:t; position:relative; padding:0 0 14px 36px; font-size:17.5px; line-height:1.5; }}
.top li::before {{ content:counter(t); position:absolute; left:0; top:-2px; font:600 24px/1 var(--serif); color:var(--warm); }}
.top a {{ text-decoration:none; }} .top a:hover {{ text-decoration:underline; text-decoration-color:var(--warm); }}

.nav {{ position:sticky; top:0; z-index:5; display:flex; gap:6px; overflow-x:auto; padding:12px 20px; margin:0 -20px;
  background:color-mix(in srgb, var(--bg) 88%, transparent); backdrop-filter:saturate(1.4) blur(10px); -webkit-backdrop-filter:saturate(1.4) blur(10px); scrollbar-width:none; }}
.nav::-webkit-scrollbar {{ display:none; }}
.nav a {{ flex:none; display:flex; align-items:center; gap:6px; font:500 13px/1 var(--sans); padding:8px 12px; border-radius:99px; border:1px solid var(--rule);
  text-decoration:none; color:var(--soft); background:var(--card); transition:border-color .15s, color .15s; }}
.nav a span {{ color:var(--a); }}
.nav a:hover {{ border-color:var(--a); color:var(--a); }}

.sec {{ margin-top:38px; scroll-margin-top:62px; }}
.sec h2 {{ display:flex; align-items:center; gap:10px; font:650 13px/1 var(--sans); letter-spacing:.14em;
  text-transform:uppercase; color:var(--a); margin:0 0 4px; padding-bottom:11px; border-bottom:2px solid var(--a); }}
.sec h2 .n {{ margin-left:auto; font-weight:500; color:var(--mute); letter-spacing:0; }}
.ic {{ font-size:15px; }}
.item {{ padding:20px 0 6px; border-bottom:1px solid var(--rule); scroll-margin-top:62px; }}
.item:last-child {{ border-bottom:0; }}
.item h3 {{ font-size:22px; line-height:1.28; margin:0 0 8px; font-weight:600; letter-spacing:-.01em; }}
.item h3 a {{ text-decoration:none; }} .item h3 a:hover {{ text-decoration:underline; text-decoration-color:var(--a); }}
.item p {{ margin:0 0 10px; color:var(--soft); }}
.item:target {{ background:linear-gradient(90deg, color-mix(in srgb, var(--a) 10%, transparent), transparent 70%); margin:0 -12px; padding-left:12px; padding-right:12px; border-radius:8px; }}
.badge {{ font:600 10px/1 var(--sans); letter-spacing:.06em; text-transform:uppercase; color:var(--a);
  border:1px solid currentColor; border-radius:4px; padding:3px 5px; margin-left:8px; vertical-align:4px; white-space:nowrap; opacity:.85; }}
.take {{ margin:2px 0 12px; padding:12px 16px 12px 32px; background:color-mix(in srgb, var(--a) 8%, var(--card)); border-radius:10px; color:var(--soft); font-size:16.5px; line-height:1.55; }}
.take li {{ margin:4px 0; }} .take li::marker {{ color:var(--a); }}
.meta {{ font:13px/1.5 var(--sans) !important; color:var(--mute) !important; }}
.meta a {{ color:var(--mute); }} .orig {{ font-style:italic; }}

.also {{ margin-top:38px; background:var(--card); border:1px solid var(--rule); border-radius:14px; padding:0 20px; box-shadow:var(--shadow); }}
.also summary {{ cursor:pointer; padding:17px 0; font:650 13px/1 var(--sans); letter-spacing:.14em; text-transform:uppercase; color:var(--acc); list-style:none; }}
.also summary::-webkit-details-marker {{ display:none; }}
.also summary::after {{ content:"＋"; float:right; color:var(--mute); }}
.also[open] summary::after {{ content:"－"; }}
.also summary span {{ color:var(--mute); margin-left:6px; }}
.also ul {{ margin:0 0 14px; padding:0; list-style:none; }}
.also li a {{ display:block; padding:11px 0; border-top:1px solid var(--rule); font-size:16px; line-height:1.5; color:var(--soft); text-decoration:none; }}
.also li a:hover {{ color:var(--ink); }}
.also li b {{ font:600 12.5px var(--sans); color:var(--ink); margin-right:6px; }}
.go {{ color:var(--acc); margin-left:6px; }}

.scores {{ margin:14px 0 6px; }}
.sub {{ font:600 12px/1 var(--sans); color:var(--mute); margin:16px 0 8px; }}
.late {{ font-weight:500; font-style:italic; }}
.games {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:6px; }}
.game {{ background:var(--card); border:1px solid var(--rule); border-radius:10px; padding:9px 12px; font:14px/1.4 var(--sans); }}
.ln {{ display:flex; align-items:center; gap:6px; flex-wrap:wrap; }}
.tm {{ color:var(--mute); }} .sc {{ color:var(--mute); font-variant-numeric:tabular-nums; min-width:26px; }}
.tm.w, .sc.w {{ color:var(--ink); font-weight:650; }}
.rk {{ font-size:11px; color:var(--mute); margin-right:3px; }}
.at {{ color:var(--rule); }}
.tag {{ font-size:10.5px; font-weight:600; text-transform:uppercase; letter-spacing:.06em; color:var(--mute);
  border:1px solid var(--rule); border-radius:4px; padding:1px 5px; margin-left:auto; }}
.tag.up {{ color:var(--warm); border-color:var(--warm); }}
.ld {{ font-size:12px; color:var(--mute); margin-top:2px; }}

.anchor {{ display:grid; grid-template-columns:1fr 1fr; gap:26px; margin-top:44px; padding:24px; border-radius:14px; background:var(--card); border:1px solid var(--rule); box-shadow:var(--shadow); }}
blockquote {{ margin:0; font-size:20px; line-height:1.45; font-style:italic; }}
blockquote::before {{ content:"“"; display:block; font:600 44px/0.6 var(--serif); color:var(--warm); margin:10px 0 4px; }}
.by {{ margin:8px 0 8px; font:600 13px var(--sans); color:var(--soft); }}
.mm {{ font-size:20px; font-weight:600; margin:0 0 6px; line-height:1.3; }}
.ctx {{ margin:0; font-size:15px; line-height:1.58; color:var(--soft); }}
.spot {{ margin-top:14px; padding:22px 24px; border-radius:14px; border:1px dashed var(--rule); }}
.snip {{ display:flex; gap:8px; align-items:center; margin-top:12px; }}
.snip code {{ flex:1; min-width:0; overflow-x:auto; white-space:pre; font:12.5px/1.5 ui-monospace, Consolas, monospace; background:var(--acc-soft); padding:8px 10px; border-radius:6px; }}
.snip button {{ font:600 12px var(--sans); border:0; border-radius:6px; padding:9px 12px; background:var(--acc); color:var(--bg); cursor:pointer; }}
.hint {{ font:12px var(--sans); color:var(--mute); margin:8px 0 0; }}
.quiet {{ font-style:italic; color:var(--mute); margin-top:30px; }}

.foot {{ margin-top:44px; padding-top:16px; border-top:1px solid var(--rule); font:13px/1.5 var(--sans); color:var(--mute); }}
.arch {{ display:flex; gap:18px; margin-bottom:12px; }}
.arch a {{ color:var(--acc); text-decoration:none; font-weight:600; }}
.foot details summary {{ cursor:pointer; list-style:none; }}
.foot details summary::-webkit-details-marker {{ display:none; }}
.foot ul {{ margin:6px 0; padding-left:18px; }}
.foot li.fail b {{ color:var(--down); }} .foot li.warn b {{ color:var(--warm); }}
.hl {{ margin:0; font-weight:600; }} .hl.ok {{ color:var(--up); }} .hl.warn {{ color:var(--warm); }}
.stats {{ margin:6px 0 0; }}
@media (max-width:560px) {{
  body {{ font-size:17px; }}
  header h1 {{ font-size:32px; }}
  .item h3 {{ font-size:19.5px; }}
  .anchor {{ grid-template-columns:1fr; gap:22px; }}
  .games {{ grid-template-columns:1fr; }}
  .card .big {{ font-size:25px; }}
  .spark {{ position:static; display:block; width:100%; height:30px; margin-top:8px; }}
}}
@media (max-width:380px) {{ .cards.n2 {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body>
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
<script>
(function () {{
  var b = document.getElementById('copy');
  if (b) b.addEventListener('click', function () {{
    navigator.clipboard.writeText(document.getElementById('snip').innerText.trim());
    b.textContent = 'Copied'; setTimeout(function () {{ b.textContent = 'Copy'; }}, 1800);
  }});
  var p = document.getElementById('btc-p');
  if (p) fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true')
    .then(function (r) {{ return r.json(); }})
    .then(function (d) {{
      var v = d.bitcoin.usd, c = d.bitcoin.usd_24h_change;
      p.textContent = '$' + Math.round(v).toLocaleString('en-US');
      document.getElementById('btc-c').innerHTML = '<span class="' + (c >= 0 ? 'up' : 'down') + '">' + (c >= 0 ? '▲ ' : '▼ ') + Math.abs(c).toFixed(1) + '%</span>';
    }}).catch(function () {{}});
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
