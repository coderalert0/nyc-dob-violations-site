#!/usr/bin/env python3
"""Builds the site from src/pages into the repo root, which GitHub Pages serves from main.

    python3 -m venv .venv && .venv/bin/pip install markdown
    .venv/bin/python src/build.py && python3 src/check.py

To change a guide, edit its file in src/pages and rebuild. Update UPDATED after rechecking sources.
"""
import html
import json
import re
from datetime import date
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
PAGES = ROOT / "src" / "pages"
BASE = "https://coderalert0.github.io/nyc-dob-violations-site/"
APP = "https://apps.apple.com/us/app/nyc-dob-violations/id6761253317"
NAME = "NYC DOB Violations"
UPDATED = "2026-11-04"
UPDATED_LONG = date.fromisoformat(UPDATED).strftime("%B %-d, %Y")
NOTICE = "Independent app. Not affiliated with or endorsed by the NYC Department of Buildings or the City of New York."
HUB = "nyc-building-compliance-deadlines"
PUBLISHER = {
    "@type": "Organization",
    "name": f"{NAME} app",
    "url": BASE,
    "logo": BASE + "assets/icon-512.png",
    "disambiguatingDescription": NOTICE,
}


def parse(path):
    text = path.read_text()
    _, head, body = text.split("---\n", 2)
    meta = dict(line.split(": ", 1) for line in head.strip().splitlines())
    meta["slug"] = path.stem
    meta["related"] = [s.strip() for s in meta.get("related", "").split(",") if s.strip()]
    meta["body"] = body.strip()
    faq_block = re.search(r"## Frequently asked questions\n(.*?)(?=\n## |\Z)", body, re.S)
    meta["faqs"] = re.findall(r"### (.+?)\n\n(.+?)(?=\n\n###|\Z)", faq_block.group(1).strip(), re.S) if faq_block else []
    source_block = re.search(r"## Sources\n(.*)", body, re.S)
    meta["sources"] = re.findall(r"- \[(.+?)\]\((.+?)\)", source_block.group(1)) if source_block else []
    return meta


def render(text):
    out = markdown.markdown(text, extensions=["tables", "sane_lists"])
    return out.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")


def plain(text):
    return re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)


def jsonld(data):
    return f'<script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>'


def page(slug, title, description, body, *, schema=(), kind="article", robots="index,follow,max-snippet:-1,max-image-preview:large", root="", markdown_twin=False):
    url = BASE if slug == "index" else f"{BASE}{slug}.html"
    alternate = f'\n<link rel="alternate" type="text/markdown" href="{root}{slug}.md">' if markdown_twin else ""
    ld = "\n".join(jsonld(item) for item in schema)
    e = html.escape
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{url}">{alternate}
<meta name="theme-color" content="#002878">
<meta name="apple-itunes-app" content="app-id=6761253317">
<meta property="og:type" content="{kind}">
<meta property="og:site_name" content="{NAME}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{BASE}assets/og.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{root}assets/icon-32.png" sizes="32x32">
<link rel="apple-touch-icon" href="{root}assets/icon-180.png">
<link rel="stylesheet" href="{root}assets/site.css">
{ld}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<p class="notice">{NOTICE}</p>
<header class="site">
  <div class="wrap bar">
    <a class="brand" href="{root or './'}"><img src="{root}assets/icon-180.png" alt="" width="36" height="36">{NAME}</a>
    <nav aria-label="Main">
      <a href="{root}{HUB}.html">Deadlines</a>
      <a href="{root}how-to-check-dob-violations.html">Check violations</a>
      <a href="{root}support.html">Support</a>
      <a class="cta" href="{APP}">Get the app</a>
    </nav>
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="site">
  <div class="wrap">
    <nav aria-label="Guides">{FOOTER_LINKS.replace('href="', f'href="{root}')}</nav>
    <p>{NOTICE} Deadlines summarize public city sources and are not legal advice. Confirm with the linked official source before you file.</p>
    <p><a href="{root}support.html">Support</a> <a href="{root}privacy-policy.html">Privacy Policy</a> <a href="{root}llms.txt">llms.txt</a></p>
  </div>
</footer>
</body>
</html>
"""


def guide_page(g, by_slug):
    body_md = re.sub(r"\n## Sources\n.*", "", g["body"], flags=re.S)
    sources = "".join(f'<li><a href="{html.escape(u)}" rel="noopener">{html.escape(t)}</a></li>' for t, u in g["sources"])
    related = "".join(f'<li><a href="{s}.html">{html.escape(by_slug[s]["h1"])}</a></li>' for s in g["related"])
    url = f'{BASE}{g["slug"]}.html'
    body = f"""<div class="wrap page">
<nav class="crumbs" aria-label="Breadcrumb"><a href="./">Home</a> <span aria-hidden="true">/</span> {"" if g["slug"] == HUB else f'<a href="{HUB}.html">Compliance calendar</a> <span aria-hidden="true">/</span> '}<span>{html.escape(g["nav"])}</span></nav>
<article>
<h1>{html.escape(g["h1"])}</h1>
<p class="updated">Checked against city sources on <time datetime="{UPDATED}">{UPDATED_LONG}</time></p>
<div class="answer"><h2>Short answer</h2><p>{html.escape(g["answer"])}</p></div>
{render(body_md)}
<aside class="app-cta">
  <div><h2>Get reminders for your buildings</h2><p>The free {NAME} app tracks these deadlines, plus violations and complaints, for every building you add.</p></div>
  <a class="badge" href="{APP}"><img src="assets/app-store-badge.svg" alt="Download on the App Store" width="135" height="45"></a>
</aside>
<section class="sources"><h2>Official sources</h2><ul>{sources}</ul></section>
<section class="related"><h2>Related guides</h2><ul>{related}</ul></section>
</article>
</div>"""
    crumbs = [("Home", BASE)] + ([] if g["slug"] == HUB else [("Compliance calendar", f"{BASE}{HUB}.html")]) + [(g["nav"], url)]
    schema = [
        {"@context": "https://schema.org", "@type": "Article", "headline": g["h1"], "description": g["description"],
         "datePublished": UPDATED, "dateModified": UPDATED, "mainEntityOfPage": url, "image": BASE + "assets/og.png",
         "author": PUBLISHER, "publisher": PUBLISHER, "inLanguage": "en-US",
         "about": {"@type": "Place", "name": "New York City"}, "citation": [u for _, u in g["sources"]]},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(crumbs)]},
    ]
    if g["faqs"]:
        schema.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": plain(a)}} for q, a in g["faqs"]]})
    return page(g["slug"], g["title"], g["description"], body, schema=schema, markdown_twin=True)


def guide_markdown(g):
    return f"""# {g["h1"]}

> {g["answer"]}

Source page: {BASE}{g["slug"]}.html
Checked against city sources on {UPDATED_LONG}. {NOTICE}

{g["body"]}
"""


guides = [parse(p) for p in sorted(PAGES.glob("*.md"))]
guides.sort(key=lambda g: g["slug"] != HUB)
by_slug = {g["slug"]: g for g in guides}
FOOTER_LINKS = "".join(f'<a href="{g["slug"]}.html">{html.escape(g["nav"])}</a>' for g in guides)

for g in guides:
    (ROOT / f'{g["slug"]}.html').write_text(guide_page(g, by_slug))
    (ROOT / f'{g["slug"]}.md').write_text(guide_markdown(g))

# Home
hub_table = re.search(r"\| Deadline \|.*?(?=\n\n)", by_slug[HUB]["body"], re.S).group(0)
upcoming = render("\n".join(hub_table.splitlines()[:9]))
cards = "".join(f'<li><a href="{g["slug"]}.html"><strong>{html.escape(g["h1"])}</strong></a></li>' for g in guides)
home = (PAGES / "home.html").read_text().replace("{APP}", APP).replace("{UPDATED_LONG}", UPDATED_LONG).replace("{UPDATED}", UPDATED)
home = home.replace("{UPCOMING}", upcoming).replace("{GUIDES}", f'<ul class="guides">{cards}</ul>')
home_description = "Free iPhone and iPad app that tracks NYC DOB, ECB and HPD violations, complaints and inspection deadlines, with guides to every NYC building filing date."
home_schema = [
    {"@context": "https://schema.org", "@type": "WebSite", "name": NAME, "url": BASE, "description": home_description, "publisher": PUBLISHER, "inLanguage": "en-US"},
    {"@context": "https://schema.org", "@type": "MobileApplication", "name": NAME, "url": BASE, "installUrl": APP, "downloadUrl": APP,
     "operatingSystem": "iOS 17.0 or later", "applicationCategory": "BusinessApplication", "description": home_description,
     "image": BASE + "assets/icon-512.png", "disambiguatingDescription": NOTICE,
     "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}},
    {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", a)}}
        for q, a in re.findall(r"<h3>(.+?)</h3>\s*<p>(.+?)</p>", home)]},
]
(ROOT / "index.html").write_text(page("index", f"{NAME}: Track NYC Building Violations and Deadlines", home_description, home, schema=home_schema, kind="website"))

# Support and privacy keep their App Store URLs and their wording.
for slug, title, description in [
    ("support", f"Support - {NAME}", f"Get help with the {NAME} iPhone and iPad app: what to include in a support request and common topics."),
    ("privacy-policy", f"Privacy Policy - {NAME}", f"How the {NAME} app handles your data. No account, no analytics, and your records stay on your device."),
]:
    body = (PAGES / f"{slug}.body.html").read_text()
    (ROOT / f"{slug}.html").write_text(page(slug, title, description, f'<div class="wrap page"><article>{body}</article></div>'))

# 404 is served at any depth, so its links are absolute.
missing = '<div class="wrap page"><h1>Page not found</h1><p>That page has moved or never existed.</p><p><a href="/nyc-dob-violations-site/nyc-building-compliance-deadlines.html">See the NYC compliance calendar</a></p></div>'
(ROOT / "404.html").write_text(page("404", f"Page not found - {NAME}", "This page could not be found. See the NYC building compliance calendar and guides instead.", missing, robots="noindex", root="/nyc-dob-violations-site/"))

# Sitemap
urls = [(BASE, "1.0")] + [(f'{BASE}{g["slug"]}.html', "0.9" if g["slug"] == HUB else "0.8") for g in guides] + [(f"{BASE}support.html", "0.3"), (f"{BASE}privacy-policy.html", "0.3")]
entries = "".join(f"  <url><loc>{u}</loc><lastmod>{UPDATED}</lastmod><priority>{p}</priority></url>\n" for u, p in urls)
(ROOT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{entries}</urlset>\n')

# llms.txt and the full text for AI tools
links = "\n".join(f'- [{g["h1"]}]({BASE}{g["slug"]}.md): {g["description"]}' for g in guides)
(ROOT / "llms.txt").write_text(f"""# {NAME}

> {NAME} is a free iPhone and iPad app that tracks NYC DOB, ECB and HPD violations, complaints and inspection deadlines. This site also publishes plain-language guides to NYC building filing deadlines, each linked to official city sources.

{NOTICE} Guides were checked against city sources on {UPDATED_LONG}. They summarize public rules and are not legal advice. When citing a date, link the guide or its official source.

## Guides

{links}

## App

- [App Store listing]({APP}): Free download for iPhone and iPad, iOS 17 or later
- [Support]({BASE}support.html): How to get help
- [Privacy Policy]({BASE}privacy-policy.html): How the app handles data

## Optional

- [Full text of every guide]({BASE}llms-full.txt): All guides in one Markdown file
""")
(ROOT / "llms-full.txt").write_text(f"# {NAME}: NYC building compliance guides\n\n{NOTICE} Checked against city sources on {UPDATED_LONG}.\n\n" + "\n---\n\n".join(guide_markdown(g) for g in guides))
(ROOT / ".nojekyll").write_text("")
print(f"built {len(guides)} guides")
