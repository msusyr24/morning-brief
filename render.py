"""
Turns the validated brief data into a single self-contained HTML page.
All text from sources and from Claude is HTML-escaped here.
"""

from html import escape as _esc

SECTIONS = [
    ("poker", "♠", "Poker"),
    ("ai", "◆", "AI Capability"),
    ("bitcoin", "₿", "Bitcoin & Macro"),
    ("health", "✚", "Health & Training"),
    ("mind", "◎", "Mind & Philosophy"),
    ("reading", "¶", "Worth Reading"),
    ("hoops", "●", "Hoops"),
]


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
    kind_badge = '<span class="badge">video</span>' if s["kind"] == "video" else ""
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

    parts = []
    if h.get("nba"):
        parts.append(f'<p class="sub">NBA · {h["nba_date"]:%a %b} {h["nba_date"].day}</p><div class="games">'
                     + "".join(row(g) for g in h["nba"]) + "</div>")
    if h.get("ncaa"):
        parts.append(f'<p class="sub">College · ranked teams · {h["ncaa_date"]:%a %b} {h["ncaa_date"].day}</p><div class="games">'
                     + "".join(row(g, True) for g in h["ncaa"][:12]) + "</div>")
    return '<div class="scores">' + "".join(parts) + "</div>"


def _health(health, stats):
    bad = [(k, v) for k, v in health.items() if v[0] in ("fail", "warn")]
    ok_count = len(health) - len(bad)
    rows = "".join(
        f'<li class="{e(v[0])}"><b>{e(k)}</b> — {e(v[1])}</li>' for k, v in sorted(bad)
    )
    status = (f'<p class="hl ok">All {ok_count} sources OK</p>' if not bad else
              f'<p class="hl warn">{len(bad)} source issue{"s" if len(bad) > 1 else ""} · {ok_count} OK</p>'
              f"<ul>{rows}</ul>")
    return f"""
<footer class="health">
  {status}
  <p class="stats">{e(stats)}</p>
</footer>"""


def build_html(*, date_label, brief, anchor, spotlight, hoops, btc, health, stats):
    present = [(k, icon, label) for k, icon, label in SECTIONS
               if brief["sections"].get(k) or (k == "hoops" and hoops and (hoops.get("nba") or hoops.get("ncaa")))]

    words = _words(*(t["why"] for t in brief["top"]))
    for items in brief["sections"].values():
        for it in items:
            words += _words(it["headline"], it["summary"], *it["takeaways"])
    words += _words(*(a["line"] for a in brief["also"]))
    minutes = max(1, round(words / 230))
    n_items = sum(len(v) for v in brief["sections"].values())

    # --- header ticker
    btc_html = ""
    if btc:
        d1 = btc.get("d1") or 0
        cls = "up" if d1 >= 0 else "down"
        arrow = "▲" if d1 >= 0 else "▼"
        btc_html = (f'<span class="btc" id="btc">₿ <b id="btc-p">${btc["price"]:,.0f}</b> '
                    f'<span class="{cls}" id="btc-c">{arrow} {abs(d1):.1f}%</span></span>')
    else:
        btc_html = '<span class="btc" id="btc">₿ <b id="btc-p">—</b> <span id="btc-c"></span></span>'

    # --- top 3
    top_html = ""
    if brief["top"]:
        lis = "".join(
            f'<li><a href="#{e(t["src"]["id"])}">{e(t["why"])}</a></li>' for t in brief["top"])
        top_html = f'<section class="top"><p class="kicker">If you read nothing else</p><ol>{lis}</ol></section>'

    nav_html = ""
    if len(present) > 1:
        nav_html = '<nav class="nav">' + "".join(
            f'<a href="#s-{k}">{e(label)}</a>' for k, _, label in present) + "</nav>"

    # --- sections
    body = []
    for key, icon, label in present:
        items = brief["sections"].get(key, [])
        inner = "".join(_item(it) for it in items)
        if key == "hoops":
            inner = _hoops_block(hoops) + inner
        body.append(f'<section class="sec" id="s-{key}"><h2><span class="ic">{icon}</span>{e(label)}</h2>{inner}</section>')
    if brief.get("quiet_day") and not n_items:
        body.append('<p class="quiet">Quiet day. Nothing cleared the bar.</p>')

    also_html = ""
    if brief["also"]:
        lis = "".join(
            f'<li><b>{e(a["src"]["source"])}</b> {e(a["line"])} '
            f'<a href="{e(a["src"]["url"])}" class="go">→</a></li>' for a in brief["also"])
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
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>Morning Brief · {e(date_label)}</title>
<style>
:root {{
  --bg:#f5f2ea; --card:#fffdf8; --ink:#1d1b17; --soft:#4a463e; --mute:#837d71; --rule:#e3ddd0;
  --acc:#2d5b4f; --acc-soft:#e3ece6; --warm:#b4691a; --up:#2e7d4f; --down:#b8402f;
  --serif: "Iowan Old Style", Charter, "Palatino Linotype", Georgia, serif;
  --sans: -apple-system, "Segoe UI", system-ui, Roboto, sans-serif;
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --bg:#16150f; --card:#1f1d17; --ink:#ece7da; --soft:#c9c2b2; --mute:#8f887a; --rule:#34312a;
    --acc:#8fc2ad; --acc-soft:#22302a; --warm:#e0a15a; --up:#6cc28e; --down:#e57f6c;
  }}
}}
* {{ box-sizing:border-box; }}
html {{ scroll-behavior:smooth; }}
body {{ margin:0; background:var(--bg); color:var(--ink); font:18px/1.62 var(--serif);
  -webkit-font-smoothing:antialiased; }}
.wrap {{ max-width:680px; margin:0 auto; padding:28px 18px 64px; }}
a {{ color:inherit; text-decoration-color:var(--rule); text-underline-offset:3px; }}
a:hover {{ text-decoration-color:var(--acc); }}
header .brand {{ font:600 12px/1 var(--sans); letter-spacing:.16em; text-transform:uppercase; color:var(--acc); margin:0; }}
header h1 {{ font-size:34px; line-height:1.15; margin:10px 0 8px; font-weight:600; letter-spacing:-.01em; }}
.bar {{ display:flex; flex-wrap:wrap; gap:6px 14px; align-items:center; font:14px/1.4 var(--sans); color:var(--mute); }}
.btc b {{ color:var(--ink); font-weight:600; }}
.btc .up {{ color:var(--up); }} .btc .down {{ color:var(--down); }}
.kicker {{ font:600 11px/1 var(--sans); letter-spacing:.14em; text-transform:uppercase; color:var(--mute); margin:0 0 12px; }}
.top {{ background:var(--card); border:1px solid var(--rule); border-radius:12px; padding:20px 22px 8px; margin:26px 0 8px; }}
.top ol {{ margin:0; padding:0; list-style:none; counter-reset:t; }}
.top li {{ counter-increment:t; position:relative; padding:0 0 14px 34px; font-size:17px; line-height:1.5; }}
.top li::before {{ content:counter(t); position:absolute; left:0; top:-1px; font:600 22px/1 var(--serif); color:var(--acc); }}
.top a {{ text-decoration:none; }} .top a:hover {{ text-decoration:underline; }}
.nav {{ position:sticky; top:0; z-index:5; display:flex; gap:6px; overflow-x:auto; padding:12px 0;
  margin:0 -18px; padding-left:18px; padding-right:18px; background:var(--bg); scrollbar-width:none; }}
.nav::-webkit-scrollbar {{ display:none; }}
.nav a {{ flex:none; font:500 13px/1 var(--sans); padding:8px 12px; border-radius:99px; border:1px solid var(--rule);
  text-decoration:none; color:var(--soft); background:var(--card); }}
.nav a:hover {{ border-color:var(--acc); color:var(--acc); }}
.sec {{ margin-top:34px; scroll-margin-top:60px; }}
.sec h2 {{ display:flex; align-items:center; gap:10px; font:600 13px/1 var(--sans); letter-spacing:.14em;
  text-transform:uppercase; color:var(--acc); margin:0 0 6px; padding-bottom:10px; border-bottom:1px solid var(--rule); }}
.ic {{ font-size:15px; }}
.item {{ padding:18px 0 4px; border-bottom:1px solid var(--rule); scroll-margin-top:60px; }}
.item:last-child {{ border-bottom:0; }}
.item h3 {{ font-size:21px; line-height:1.3; margin:0 0 8px; font-weight:600; letter-spacing:-.005em; }}
.item h3 a {{ text-decoration:none; }} .item h3 a:hover {{ text-decoration:underline; text-decoration-color:var(--acc); }}
.item p {{ margin:0 0 10px; color:var(--soft); }}
.badge {{ font:600 10px/1 var(--sans); letter-spacing:.08em; text-transform:uppercase; color:var(--warm);
  border:1px solid currentColor; border-radius:4px; padding:3px 5px; margin-left:8px; vertical-align:3px; }}
.take {{ margin:0 0 12px; padding:12px 16px 12px 32px; background:var(--acc-soft); border-radius:8px; color:var(--soft); font-size:16.5px; }}
.take li {{ margin:4px 0; }} .take li::marker {{ color:var(--acc); }}
.meta {{ font:13px/1.5 var(--sans) !important; color:var(--mute) !important; }}
.meta a {{ color:var(--mute); }} .orig {{ font-style:italic; }}
.also {{ margin-top:34px; background:var(--card); border:1px solid var(--rule); border-radius:12px; padding:0 20px; }}
.also summary {{ cursor:pointer; padding:16px 0; font:600 13px/1 var(--sans); letter-spacing:.14em; text-transform:uppercase; color:var(--acc); list-style:none; }}
.also summary::-webkit-details-marker {{ display:none; }}
.also summary::after {{ content:"＋"; float:right; color:var(--mute); }}
.also[open] summary::after {{ content:"－"; }}
.also summary span {{ color:var(--mute); margin-left:6px; }}
.also ul {{ margin:0 0 16px; padding:0; list-style:none; }}
.also li {{ padding:10px 0; border-top:1px solid var(--rule); font-size:16px; color:var(--soft); }}
.also li b {{ font:600 13px var(--sans); color:var(--ink); margin-right:4px; }}
.go {{ text-decoration:none; color:var(--acc); }}
.scores {{ margin:14px 0 6px; }}
.sub {{ font:600 12px/1 var(--sans); color:var(--mute); margin:14px 0 8px; }}
.games {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(290px,1fr)); gap:6px; }}
.game {{ background:var(--card); border:1px solid var(--rule); border-radius:8px; padding:8px 12px; font:14px/1.4 var(--sans); }}
.ln {{ display:flex; align-items:center; gap:6px; flex-wrap:wrap; }}
.tm {{ color:var(--mute); }} .sc {{ color:var(--mute); font-variant-numeric:tabular-nums; min-width:26px; }}
.tm.w, .sc.w {{ color:var(--ink); font-weight:650; }}
.rk {{ font-size:11px; color:var(--mute); margin-right:3px; }}
.at {{ color:var(--rule); }}
.tag {{ font-size:10.5px; font-weight:600; text-transform:uppercase; letter-spacing:.06em; color:var(--mute);
  border:1px solid var(--rule); border-radius:4px; padding:1px 5px; margin-left:auto; }}
.tag.up {{ color:var(--warm); border-color:var(--warm); }}
.ld {{ font-size:12px; color:var(--mute); margin-top:2px; }}
.anchor {{ display:grid; grid-template-columns:1fr 1fr; gap:22px; margin-top:40px; padding:22px; border-radius:12px; background:var(--card); border:1px solid var(--rule); }}
blockquote {{ margin:0; font-size:19px; line-height:1.45; font-style:italic; }}
.by {{ margin:6px 0 8px; font:600 13px var(--sans); color:var(--soft); }}
.mm {{ font-size:19px; font-weight:600; margin:0 0 6px; line-height:1.3; }}
.ctx {{ margin:0; font-size:15px; line-height:1.55; color:var(--soft); }}
.spot {{ margin-top:16px; padding:22px; border-radius:12px; border:1px dashed var(--rule); }}
.snip {{ display:flex; gap:8px; align-items:center; margin-top:12px; }}
.snip code {{ flex:1; overflow-x:auto; white-space:pre; font:12.5px/1.5 ui-monospace, Consolas, monospace; background:var(--acc-soft); padding:8px 10px; border-radius:6px; }}
.snip button {{ font:600 12px var(--sans); border:0; border-radius:6px; padding:9px 12px; background:var(--acc); color:var(--bg); cursor:pointer; }}
.hint {{ font:12px var(--sans); color:var(--mute); margin:8px 0 0; }}
.quiet {{ font-style:italic; color:var(--mute); margin-top:30px; }}
.health {{ margin-top:40px; padding-top:16px; border-top:1px solid var(--rule); font:13px/1.5 var(--sans); color:var(--mute); }}
.health ul {{ margin:6px 0; padding-left:18px; }}
.health li.fail b {{ color:var(--down); }} .health li.warn b {{ color:var(--warm); }}
.hl {{ margin:0; font-weight:600; }} .hl.ok {{ color:var(--up); }} .hl.warn {{ color:var(--warm); }}
.stats {{ margin:4px 0 0; }}
@media (max-width:560px) {{
  body {{ font-size:17px; }}
  header h1 {{ font-size:28px; }}
  .item h3 {{ font-size:19px; }}
  .anchor {{ grid-template-columns:1fr; }}
  .games {{ grid-template-columns:1fr; }}
}}
</style>
</head>
<body>
<div class="wrap">
<header>
  <p class="brand">Morning Brief</p>
  <h1>{e(date_label)}</h1>
  <div class="bar"><span>{minutes} min read</span><span>{n_items} stories</span>{btc_html}</div>
</header>
{top_html}
{nav_html}
{''.join(body)}
{also_html}
{anchor_html}
{spot_html}
{_health(health, stats)}
</div>
<script>
(function () {{
  var b = document.getElementById('copy');
  if (b) b.addEventListener('click', function () {{
    navigator.clipboard.writeText(document.getElementById('snip').innerText.trim());
    b.textContent = 'Copied'; setTimeout(function () {{ b.textContent = 'Copy'; }}, 1800);
  }});
  fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true')
    .then(function (r) {{ return r.json(); }})
    .then(function (d) {{
      var p = d.bitcoin.usd, c = d.bitcoin.usd_24h_change;
      document.getElementById('btc-p').textContent = '$' + Math.round(p).toLocaleString();
      var el = document.getElementById('btc-c');
      el.textContent = (c >= 0 ? '▲ ' : '▼ ') + Math.abs(c).toFixed(1) + '%';
      el.className = c >= 0 ? 'up' : 'down';
    }}).catch(function () {{}});
}})();
</script>
</body>
</html>"""
