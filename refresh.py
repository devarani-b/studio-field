#!/usr/bin/env python3
"""
Studio Field — daily refresh.
Fetches the newest UX articles from RSS feeds, updates the Today section
inside index.html, and writes an email preview to email-body.html.
"""
import json, re, sys, html as htmllib
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError
from xml.etree import ElementTree as ET

FEEDS = [
    ("Nielsen Norman Group", "https://www.nngroup.com/feed/rss/"),
    ("Smashing Magazine",    "https://www.smashingmagazine.com/feed/"),
]

# UX-relevant keywords — used to filter Smashing's mixed feed
UX_KEYWORDS = [
    "ux", "user experience", "usability", "user research", "design system",
    "interaction", "accessibility", "ai", "chatbot", "agentic", "figma",
    "prototype", "product design", "research", "cognitive", "user interface",
    "microcopy", "user testing", "personas", "journey", "heuristic",
]

def fetch(url, timeout=20):
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 StudioField/1.0"})
    with urlopen(req, timeout=timeout) as r:
        return r.read()

def parse_date(s):
    """Parse RFC-822 or ISO dates from RSS/Atom into UTC datetime."""
    if not s: return None
    s = s.strip()
    # RFC 822: 'Thu, 17 Jul 2026 10:00:00 +0000'
    for fmt in ("%a, %d %b %Y %H:%M:%S %z",
                "%a, %d %b %Y %H:%M:%S %Z",
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%d"):
        try:
            d = datetime.strptime(s, fmt)
            if d.tzinfo is None: d = d.replace(tzinfo=timezone.utc)
            return d
        except ValueError:
            continue
    return None

def strip_html(s):
    if not s: return ""
    s = re.sub(r"<[^>]+>", " ", s)
    s = htmllib.unescape(s)
    return re.sub(r"\s+", " ", s).strip()

def is_ux(item):
    text = (item["title"] + " " + item["body"]).lower()
    return any(k in text for k in UX_KEYWORDS)

def parse_feed(url, src):
    """Return a list of item dicts from an RSS or Atom feed."""
    try:
        raw = fetch(url)
    except (URLError, TimeoutError, Exception) as e:
        print(f"  ! could not fetch {src}: {e}", file=sys.stderr)
        return []
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        print(f"  ! bad XML from {src}: {e}", file=sys.stderr)
        return []

    items = []
    # RSS 2.0
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        link  = (it.findtext("link")  or "").strip()
        date  = parse_date(it.findtext("pubDate") or "")
        desc  = strip_html(it.findtext("description") or "")
        if title and link:
            items.append({"src": src, "title": title, "url": link,
                          "date": date, "body": desc[:500]})
    # Atom
    ns = "{http://www.w3.org/2005/Atom}"
    for it in root.iter(ns + "entry"):
        title = (it.findtext(ns + "title") or "").strip()
        link_el = it.find(ns + "link")
        link = link_el.get("href") if link_el is not None else ""
        date  = parse_date(it.findtext(ns + "updated") or it.findtext(ns + "published") or "")
        summary = strip_html(it.findtext(ns + "summary") or "")
        if title and link:
            items.append({"src": src, "title": title, "url": link,
                          "date": date, "body": summary[:500]})
    return items

def pick_todays_picks():
    """Grab freshest UX items across feeds; return top 2 by date."""
    all_items = []
    for src, url in FEEDS:
        print(f"  fetching {src} …")
        for it in parse_feed(url, src):
            if is_ux(it) and it["date"]:
                all_items.append(it)
    all_items.sort(key=lambda x: x["date"], reverse=True)
    return all_items[:2]

# ─────────────── infer topic + concise takeaways ───────────────
def infer_topic(text):
    t = text.lower()
    if "chatbot" in t or "agent" in t or "llm" in t or "genai" in t or "ai " in t: return "AI/Agentic"
    if "design system" in t or "component" in t or "token" in t: return "Design systems"
    if "research" in t or "usability" in t or "interview" in t or "user testing" in t: return "Research"
    if "career" in t or "leader" in t or "team" in t or "hiring" in t: return "Leadership"
    if "accessibility" in t or "wcag" in t: return "Accessibility"
    return "UX"

def make_takeaways(title, body):
    """Two short takeaways derived from the summary; falls back gracefully."""
    sents = re.split(r"(?<=[.!?])\s+", body.strip())
    good = [s for s in sents if 30 < len(s) < 180][:2]
    if not good:
        good = [title]
    return good

# ─────────────── update index.html ───────────────
def update_index(picks):
    """Rewrite EDITIONS[0] inside index.html with today's picks."""
    html = open("index.html", encoding="utf-8").read()
    idx = html.find("const DATA = {")
    if idx < 0: raise SystemExit("Cannot find DATA block in index.html")
    start = idx + len("const DATA = ")
    ed_pos = html.find("\nconst EDITIONS=DATA", start)
    end = html.rfind("};", start, ed_pos) + 1
    data = json.loads(html[start:end])

    today = datetime.now(timezone.utc).strftime("%B %-d, %Y")
    label = f"Auto-refresh {today}"

    articles = []
    for p in picks:
        articles.append({
            "topic": infer_topic(p["title"] + " " + p["body"]),
            "src":   p["src"],
            "title": p["title"],
            "by":    p["src"],
            "date":  p["date"].strftime("%Y-%m-%d"),
            "body":  p["body"] or "(Summary not available in feed — click through to read.)",
            "takeaways": make_takeaways(p["title"], p["body"]),
            "url":   p["url"],
        })

    # Replace the newest edition (or insert new)
    if data["EDITIONS"] and data["EDITIONS"][0].get("label", "").startswith("Auto-refresh"):
        data["EDITIONS"][0] = {"label": label, "articles": articles}
    else:
        data["EDITIONS"].insert(0, {"label": label, "articles": articles})

    new_str = "const DATA = " + json.dumps(data, ensure_ascii=False) + ";"
    html = html[:idx] + new_str + html[end + 1:]

    # Bump the refresh stamp
    stamp = datetime.now(timezone.utc).strftime("%B %-d, %Y")
    html = re.sub(r"Content refreshed [A-Z][a-z]+ \d+, \d{4}",
                  f"Content refreshed {stamp}", html)

    open("index.html", "w", encoding="utf-8").write(html)
    return articles

# ─────────────── email body ───────────────
def write_email(articles, site_url):
    esc = htmllib.escape
    cards = ""
    for a in articles:
        cards += f"""
        <div style="border:1px solid #e5e5e5;border-radius:12px;padding:16px 18px;margin:0 0 14px;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif">
          <div style="font-size:11px;color:#8a8a8a;text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px">{esc(a['src'])} · {esc(a['date'])}</div>
          <div style="font-weight:600;font-size:17px;line-height:1.25;margin:0 0 8px;color:#1a1a1a">{esc(a['title'])}</div>
          <p style="font-size:14px;line-height:1.5;color:#3a3a3a;margin:0 0 12px">{esc(a['body'][:280])}{'…' if len(a['body']) > 280 else ''}</p>
          <a href="{esc(a['url'])}" style="display:inline-block;background:#1a1a1a;color:#fff;text-decoration:none;padding:8px 14px;border-radius:8px;font-size:13px;font-weight:500">Read on {esc(a['src'])} →</a>
        </div>"""
    site_line = f'<a href="{esc(site_url)}" style="color:#E8633A;font-weight:600;text-decoration:none">Open Studio Field →</a>' if site_url else ""
    return f"""<!doctype html><html><body style="background:#fafafa;padding:24px 12px;margin:0">
      <div style="max-width:560px;margin:0 auto;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif">
        <div style="font-family:'Plus Jakarta Sans',-apple-system,sans-serif;font-weight:600;font-size:26px;letter-spacing:-.02em;margin:0 0 4px;color:#1a1a1a">Good morning, Devarani.</div>
        <div style="color:#8a8a8a;font-size:13px;margin:0 0 20px">Two fresh reads picked for you today.</div>
        {cards}
        <div style="text-align:center;margin:20px 0 8px">{site_line}</div>
        <div style="color:#bcbcbc;font-size:11px;text-align:center;margin-top:16px">Auto-refresh · Studio Field</div>
      </div></body></html>"""

# ─────────────── main ───────────────
if __name__ == "__main__":
    import os
    site_url = os.environ.get("SITE_URL", "")

    print("Studio Field — daily refresh")
    picks = pick_todays_picks()
    if len(picks) < 2:
        print("  ! fewer than 2 picks found — leaving index.html untouched")
        sys.exit(0)

    print(f"  picked: {picks[0]['title'][:60]}…")
    print(f"  picked: {picks[1]['title'][:60]}…")

    articles = update_index(picks)
    open("email-body.html", "w", encoding="utf-8").write(write_email(articles, site_url))
    print("✓ index.html updated, email-body.html written")
