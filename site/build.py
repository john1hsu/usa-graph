#!/usr/bin/env python3
"""Build the static GitHub Pages site for this knowledge graph.

Reads articles/**/*.md (frontmatter + body), graph/index.json and
graph/learning-path.md, and writes a self-contained static site to _site/.
Theme and copy come from site/site.yaml. Never writes to articles/ or graph/.

    pip install pyyaml markdown
    python3 site/build.py            # -> _site/index.html
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path

import markdown
import yaml

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
OUT = ROOT / "_site"

CFG = yaml.safe_load((SITE / "site.yaml").read_text(encoding="utf-8"))
PREFIX = CFG["prefix"]  # e.g. "us"

# Human phrasing for predicates: (outgoing label, incoming label).
PRED = {
    "broader": ("Part of", "Includes"),
    "related": ("Related", "Related"),
    "requires": ("Background reading", "Read next"),
    "partOf": ("Part of", "Has part"),
    "hasPart": ("Has part", "Part of"),
    "instanceOf": ("Example of", "Examples"),
    "contrastsWith": ("Contrasts with", "Contrasts with"),
    "confusedWith": ("Often confused with", "Often confused with"),
    "locatedIn": ("Located in", "Contains"),
    "contains": ("Contains", "Located in"),
    "borders": ("Borders", "Borders"),
    "capitalOf": ("Capital of", "Capital"),
    "hasCapital": ("Capital", "Capital of"),
    "occurredDuring": ("During", "Happened during this period"),
    "periodOf": ("Happened during this period", "During"),
    "occurredIn": ("Took place in", "Site of"),
    "siteOf": ("Site of", "Took place in"),
    "ledTo": ("Led to", "Resulted from"),
    "resultedFrom": ("Resulted from", "Led to"),
    "establishedBy": ("Established by", "Established"),
    "establishes": ("Established", "Established by"),
    "enactedBy": ("Enacted by", "Enacted"),
    "enacted": ("Enacted", "Enacted by"),
    "signedBy": ("Signed by", "Signed"),
    "signed": ("Signed", "Signed by"),
    "amends": ("Amends", "Amended by"),
    "amendedBy": ("Amended by", "Amends"),
    "interprets": ("Interprets", "Interpreted in"),
    "interpretedIn": ("Interpreted in", "Interprets"),
    "overturns": ("Overturns", "Overturned by"),
    "overturnedBy": ("Overturned by", "Overturns"),
    "protects": ("Protects", "Protected by"),
    "protectedBy": ("Protected by", "Protects"),
    "heldOffice": ("Held office", "Held by"),
    "officeHolder": ("Held by", "Held office"),
    "memberOf": ("Member of", "Members"),
    "hasMember": ("Members", "Member of"),
    "foundedBy": ("Founded by", "Founded"),
    "founded": ("Founded", "Founded by"),
    "ledBy": ("Led by", "Led"),
    "led": ("Led", "Led by"),
    "participatedIn": ("Took part in", "Participants"),
    "participant": ("Participants", "Took part in"),
    "affected": ("Affected", "Affected by"),
    "affectedBy": ("Affected by", "Affected"),
    "originatedIn": ("Originated in", "Origin of"),
    "originOf": ("Origin of", "Originated in"),
    "symbolizes": ("Symbolizes", "Symbolized by"),
    "symbolizedBy": ("Symbolized by", "Symbolizes"),
    "commemorates": ("Commemorates", "Commemorated by"),
    "commemoratedBy": ("Commemorated by", "Commemorates"),
    "supportedBy": ("Supported by", "Supports"),
    "supports": ("Supports", "Supported by"),
    "challengedBy": ("Challenged by", "Challenges"),
    "challenges": ("Challenges", "Challenged by"),
    "introducedBy": ("Proposed by", "Proposed"),
    "introduced": ("Proposed", "Proposed by"),
    "introducedIn": ("First set out in", "Sets out"),
    "introduces": ("Sets out", "First set out in"),
    "authoredBy": ("Written by", "Wrote"),
    "authored": ("Wrote", "Written by"),
    "influencedBy": ("Influenced by", "Influenced"),
    "influenced": ("Influenced", "Influenced by"),
    "studiedIn": ("Studied in", "Studies"),
}
# Show these groups first, in this order; "Related" last.
PRED_ORDER = ["Part of", "Includes", "During", "Took place in", "Located in", "Background reading", "Read next", "Led to", "Resulted from"]

LEVELS = {"introductory": "Introductory", "intermediate": "Intermediate", "advanced": "Advanced"}


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def humanize(slug: str) -> str:
    s = slug.replace("-", " ").strip()
    return s[:1].upper() + s[1:]


def camel_words(s: str) -> str:
    w = re.sub(r"(?<!^)([A-Z])", r" \1", s).lower()
    return w[:1].upper() + w[1:]


def slug_of(node_id: str) -> str:
    return node_id.split(":", 1)[1]


def read_article(path: Path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        return None, text
    return yaml.safe_load(m.group(1)) or {}, m.group(2)


# ---------------------------------------------------------------- load
index = json.loads((ROOT / "graph" / "index.json").read_text(encoding="utf-8"))
nodes = {n["id"]: n for n in index}
fm_by_id, body_by_id = {}, {}
for n in index:
    fm, body = read_article(ROOT / n["file"])
    fm_by_id[n["id"]] = fm or {}
    body_by_id[n["id"]] = body

domains = defaultdict(list)
for n in index:
    domains[n["domain"]].append(n)
for d in domains.values():
    d.sort(key=lambda n: n["title"].lower())
domain_order = sorted(domains, key=lambda d: (-len(domains[d]), d))
domain_label = {d: CFG.get("domains", {}).get(d) or humanize(d) for d in domains}

# Outgoing and incoming edges (written-to-written and written-to-unwritten).
incoming = defaultdict(list)
for n in index:
    for e in n["edges"]:
        incoming[e["object"]].append((n["id"], e))

all_sources = {u for n in index for u in n.get("source_urls", [])}


def link_for(node_id: str, depth: int) -> str:
    up = "../" * depth
    if node_id in nodes:
        n = nodes[node_id]
        return f'<a href="{up}a/{slug_of(node_id)}.html">{esc(n["title"])}</a>'
    return f'<span class="unwritten" title="Not written yet">{esc(humanize(slug_of(node_id)))}</span>'


# ---------------------------------------------------------------- body rendering
MD = markdown.Markdown(extensions=["tables", "sane_lists", "smarty"])


def render_body(node_id: str, body: str) -> str:
    body = re.sub(r"^# .*\n", "", body.lstrip(), count=1)  # title is in the header
    body = re.split(r"^## Sources\s*$", body, flags=re.M)[0]
    # Footnote markers -> superscript links to the source list.
    def fn(m):
        sid = m.group(1)
        num = re.sub(r"\D", "", sid) or sid
        return f'<sup class="fn"><a href="#src-{sid}" aria-label="Source {num}">{num}</a></sup>'
    body = re.sub(r"\[\^([A-Za-z0-9_-]+)\]", fn, body)
    # "**Title** (`ct:slug`)" -> a link on the title (plain bold if not written yet).
    idpat = re.escape(PREFIX) + r":[a-z0-9-]+"
    def titled(m):
        title, nid = m.group(1), m.group(2)
        if nid in nodes:
            return f'<a class="idref" href="{slug_of(nid)}.html"><strong>{title}</strong></a>'
        return f"**{title}**"
    body = re.sub(r"\*\*([^*]+)\*\*\s?\(`(" + idpat + r")`\)", titled, body)
    body = re.sub(r"\s?\(`" + idpat + r"`(?:,\s*`" + idpat + r"`)*\)", "", body)
    def bare(m):
        nid = m.group(1)
        if nid in nodes:
            return f'<a class="idref" href="{slug_of(nid)}.html">{esc(nodes[nid]["title"])}</a>'
        return esc(humanize(slug_of(nid)))
    body = re.sub(r"`(" + idpat + r")`", bare, body)
    MD.reset()
    out = MD.convert(body)
    return out


# ---------------------------------------------------------------- page shell
FONTS = CFG["fonts_url"]
# Content hash of the site assets, so browsers never pair new pages with a cached old stylesheet.
ASSET_V = hashlib.sha256(b"".join(f.read_bytes() for f in sorted((SITE / "assets").iterdir())) + (SITE / "site.yaml").read_bytes()).hexdigest()[:10]


def page(title: str, body: str, depth: int, *, desc: str = "", extra_head: str = "", page_class: str = "") -> str:
    up = "../" * depth
    full = f"{title} | {CFG['title']}" if title != CFG["title"] else title
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full)}</title>
<meta name="description" content="{esc(desc or CFG['tagline'])}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{esc(FONTS)}">
<link rel="stylesheet" href="{up}assets/style.css?v={ASSET_V}">
<link rel="icon" href="{up}assets/icon.svg" type="image/svg+xml">
{extra_head}
</head>
<body class="{page_class}">
<a class="skip" href="#main">Skip to content</a>
<header class="masthead">
  <a class="wordmark" href="{up}index.html">{esc(CFG['title'])}</a>
  <nav aria-label="Site">
    <a href="{up}index.html#browse">Browse</a>
    <a href="{up}timeline.html">Timeline</a>
    <a href="{up}path.html">Learning path</a>
    <a href="{CFG['repo_url']}">Source on GitHub</a>
  </nav>
</header>
<main id="main">
{body}
</main>
<footer class="colophon">
  <p>{esc(CFG['footer'])} Built from <a href="{CFG['repo_url']}">{esc(CFG['repo'])}</a>; every claim links to the source it came from.</p>
</footer>
</body>
</html>
"""


# ---------------------------------------------------------------- article pages
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]


def nice_date(d) -> str:
    """1776-07-04 -> July 4, 1776; 1776-07 -> July 1776; -1000 -> 1000 BCE."""
    if not d:
        return ""
    d = str(d)
    neg = d.startswith("-")
    parts = d.lstrip("-").split("-")
    year = f"{int(parts[0])} BCE" if neg else str(int(parts[0]))
    if len(parts) == 3:
        return f"{MONTHS[int(parts[1]) - 1]} {int(parts[2])}, {year}"
    if len(parts) == 2:
        return f"{MONTHS[int(parts[1]) - 1]} {year}"
    return year


DATE_LABEL = {"Person": "Lived", "State": "Statehood", "Law": "Enacted", "CourtCase": "Decided", "Document": "Dated"}


def span(n: dict) -> str:
    st, en = n.get("start"), n.get("end")
    if not st:
        return ""
    return nice_date(st) + (f" – {nice_date(en)}" if en and en != st else "")


def facts(n: dict, fm: dict) -> str:
    rows = [
        ("Kind", camel_words(n["type"])),
        (DATE_LABEL.get(n["type"], "When"), span(n)),
        ("Level", LEVELS.get(n.get("level", ""), n.get("level", ""))),
        ("Evidence", CFG.get("evidence", {}).get(n.get("evidenceStatus", ""), n.get("evidenceStatus", ""))),
        ("Added", str(n.get("created", ""))),
    ]
    items = "".join(f"<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>" for k, v in rows if v)
    ev = esc(n.get("evidenceStatus", ""))
    return f'<dl class="facts" data-evidence="{ev}">{items}</dl>'


def study(fm: dict, n: dict) -> str:
    parts = []
    tl = n.get("timeline") or []
    if tl:
        li = "".join(f'<li><time datetime="{esc(e["date"])}">{esc(nice_date(e["date"]))}</time>'
                     f'<span>{esc(e["event"])}</span></li>' for e in tl)
        parts.append(f'<section class="block timeline"><h2>Timeline</h2><ol>{li}</ol></section>')
    mc = fm.get("misconception") or {}
    if mc:
        parts.append(f"""
<section class="block example">
  <h2>Myth and fact</h2>
  <div class="ex-pair">
    <figure class="ex-before"><figcaption>Myth</figcaption><blockquote>{esc(mc.get('myth', ''))}</blockquote></figure>
    <figure class="ex-after"><figcaption>Fact</figcaption><blockquote>{esc(mc.get('fact', ''))}</blockquote></figure>
  </div>
  <p class="ex-why"><strong>Why it matters.</strong> {esc(mc.get('why', ''))}</p>
</section>""")
    rv = fm.get("review") or []
    if rv:
        li = "".join(f"<li><details><summary>{esc(q.get('question', ''))}</summary><p>{esc(q.get('answer', ''))}</p>"
                     "</details></li>" for q in rv)
        parts.append(f'<section class="block review"><h2>Check your understanding</h2><ul>{li}</ul></section>')
    return "".join(parts)


def connections(node_id: str, depth: int) -> str:
    groups = defaultdict(list)
    seen = set()
    for e in nodes[node_id]["edges"]:
        p = e["predicate"].split(":", 1)[1]
        label = PRED.get(p, (camel_words(p), camel_words(p)))[0]
        key = (label, e["object"])
        if key not in seen:
            seen.add(key)
            groups[label].append(e["object"])
    for src, e in incoming.get(node_id, []):
        p = e["predicate"].split(":", 1)[1]
        label = PRED.get(p, (camel_words(p), camel_words(p)))[1]
        key = (label, src)
        if key not in seen:
            seen.add(key)
            groups[label].append(src)
    if not groups:
        return ""

    def order(label):
        if label in PRED_ORDER:
            return (0, PRED_ORDER.index(label))
        if label == "Related":
            return (2, 0)
        return (1, label)

    out = []
    for label in sorted(groups, key=order):
        targets = sorted(groups[label], key=lambda t: (t not in nodes, link_for(t, depth)))
        li = "".join(f"<li>{link_for(t, depth)}</li>" for t in targets)
        out.append(f"<div><h3>{esc(label)}</h3><ul>{li}</ul></div>")
    return f'<aside class="connections" aria-labelledby="conn-h"><h2 id="conn-h">Connections</h2>{"".join(out)}</aside>'


def sources(fm: dict) -> str:
    srcs = fm.get("sources") or []
    if not srcs:
        return ""
    li = []
    for s in srcs:
        sid = esc(s.get("id", ""))
        kind = esc(s.get("type", ""))
        li.append(
            f'<li id="src-{sid}"><a href="{esc(s.get("url", ""))}">{esc(s.get("title", ""))}</a>'
            f'<span class="src-pub">{esc(s.get("publisher", ""))}</span>'
            f'<span class="src-meta">{kind.capitalize()} source{", opened " + esc(s.get("accessed")) if s.get("accessed") else ""}</span></li>'
        )
    return f'<section class="block sources" aria-labelledby="src-h"><h2 id="src-h">Sources</h2><ol>{"".join(li)}</ol></section>'


def article_page(node_id: str) -> str:
    n, fm = nodes[node_id], fm_by_id[node_id]
    depth = 1
    aliases = fm.get("aliases") or n.get("aliases") or []
    alias_html = (
        f'<p class="aliases">Also called {", ".join(esc(a) for a in aliases)}</p>' if aliases else ""
    )
    crumb = f'<a href="../index.html#d-{esc(n["domain"])}">{esc(domain_label[n["domain"]])}</a>'
    body = f"""
<article class="entry">
  <header class="entry-head">
    <p class="crumb">{crumb}</p>
    <h1>{esc(n['title'])}</h1>
    {alias_html}
    <p class="lede">{esc(n.get('summary', ''))}</p>
    {facts(n, fm)}
  </header>
  <div class="entry-grid">
    <div class="prose">
      {render_body(node_id, body_by_id[node_id])}
      {study(fm, n)}
      {sources(fm)}
    </div>
    {connections(node_id, depth)}
  </div>
</article>"""
    return page(n["title"], body, depth, desc=n.get("summary", ""), page_class="p-entry")


# ---------------------------------------------------------------- learning path
def learning_path() -> str:
    path = ROOT / "graph" / "learning-path.md"
    stages = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^(\d+)\.\s+(.*)$", line)
            if not m:
                continue
            items = []
            for chunk in m.group(2).split("; "):
                lm = re.match(r"\[(.+?)\]\(\.\./articles/[^/]+/([^)]+)\.md\)\s*\((\w+)\)", chunk)
                um = re.match(r"`(" + re.escape(PREFIX) + r":[a-z0-9-]+)`\s*\(unwritten\)", chunk)
                if lm:
                    items.append((lm.group(1), lm.group(2), lm.group(3)))
                elif um:
                    items.append((humanize(slug_of(um.group(1))), None, "unwritten"))
            stages.append(items)
    blocks = []
    for i, items in enumerate(stages, 1):
        li = []
        for title, slug, lvl in items:
            if slug:
                li.append(f'<li data-level="{esc(lvl)}"><a href="a/{esc(slug)}.html">{esc(title)}</a></li>')
            else:
                li.append(f'<li class="unwritten" title="Not written yet">{esc(title)}</li>')
        blocks.append(
            f'<section class="stage"><h2><span class="stage-n">Stage {i}</span> {len(items)} topics</h2>'
            f'<ul>{"".join(li)}</ul></section>'
        )
    body = f"""
<div class="pathpage">
  <header class="page-head">
    <h1>Learning path</h1>
    <p class="lede">Topics ordered by what they build on. Everything in stage 1 stands on its own; each later stage assumes something from the stages before it. Dashed outlines mark intermediate topics; dotted, faded names are prerequisites that haven’t been written yet.</p>
  </header>
  {"".join(blocks) or "<p>The learning path appears once articles declare prerequisites.</p>"}
</div>"""
    return page("Learning path", body, 0, page_class="p-path")


# ---------------------------------------------------------------- timeline
def date_key(d: str):
    neg = d.startswith("-")
    parts = [int(x) for x in d.lstrip("-").split("-")] + [0, 0]
    return (-parts[0] if neg else parts[0], parts[1], parts[2])


def century(d: str) -> str:
    y = date_key(d)[0]
    if y <= 0:
        return "Before the common era"
    c = (y - 1) // 100 + 1
    suffix = "th" if 10 <= c % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(c % 10, "th")
    return f"{c}{suffix} century"


def timeline_page() -> str:
    rows = []
    for n in index:
        if n.get("start"):
            rows.append((date_key(n["start"]), 0, n["start"], span(n),
                         f'<a href="a/{esc(slug_of(n["id"]))}.html"><strong>{esc(n["title"])}</strong></a>'
                         f'<span class="kind">{esc(camel_words(n["type"]))}</span>', n["domain"]))
        for e in n.get("timeline") or []:
            rows.append((date_key(e["date"]), 1, e["date"], nice_date(e["date"]),
                         f'{esc(e["event"])} <span class="tl-dot" aria-hidden="true">·</span><a class="tl-from" href="a/{esc(slug_of(n["id"]))}.html">{esc(n["title"])}</a>',
                         n["domain"]))
    rows.sort(key=lambda r: (r[0], r[1], r[4]))
    blocks, current, items = [], None, []
    for key, kind, d, label, html_, dom in rows:
        c = century(d)
        if c != current and items:
            blocks.append(f'<section class="era"><h2>{esc(current)}</h2><ol>{"".join(items)}</ol></section>')
            items = []
        current = c
        items.append(f'<li class="{"tl-node" if kind == 0 else "tl-event"}" data-domain="{esc(dom)}">'
                     f'<time datetime="{esc(d)}">{esc(label)}</time><div>{html_}</div></li>')
    if items:
        blocks.append(f'<section class="era"><h2>{esc(current)}</h2><ol>{"".join(items)}</ol></section>')
    body = f"""
<div class="tlpage">
  <header class="page-head">
    <h1>Timeline</h1>
    <p class="lede">Every dated article in the graph, in order, with the key moments from each article’s own timeline in between. Bold entries are articles; the rest are moments within them.</p>
  </header>
  {"".join(blocks) or "<p>The timeline fills in as dated articles are added.</p>"}
</div>"""
    return page("Timeline", body, 0, page_class="p-timeline")


# ---------------------------------------------------------------- home
def home() -> str:
    search = [
        {"s": slug_of(n["id"]), "t": n["title"], "a": " ".join(n.get("aliases", [])), "m": n.get("summary", "")}
        for n in index
    ]

    sections = []
    for d in domain_order:
        li = "".join(
            f'<li data-s="{esc(slug_of(n["id"]))}"><a href="a/{esc(slug_of(n["id"]))}.html">{esc(n["title"])}</a>'
            f'<span class="kind">{esc(camel_words(n["type"]))}</span></li>'
            for n in domains[d]
        )
        sections.append(
            f'<section class="domain" id="d-{esc(d)}" data-domain="{esc(d)}">'
            f'<h3><span class="swatch" aria-hidden="true"></span>{esc(domain_label[d])} <span class="count">{len(domains[d])}</span></h3>'
            f"<ul>{li}</ul></section>"
        )

    latest = sorted(index, key=lambda n: (str(n.get("created", "")), n["title"]), reverse=True)[:6]
    latest_li = "".join(
        f'<li><a href="a/{esc(slug_of(n["id"]))}.html">{esc(n["title"])}</a><span>{esc(n.get("summary", ""))}</span></li>'
        for n in latest
    )

    data = json.dumps({"search": search}, ensure_ascii=False)
    data = data.replace("</", "<\\/")
    stat = (
        f"{len(index)} articles in {len(domains)} areas, connected by "
        f"{sum(len(n['edges']) for n in index)} links and backed by {len(all_sources)} cited sources."
    )
    body = f"""
<section class="hero">
  <div class="hero-copy">
    <h1>{CFG['headline']}</h1>
    <p class="lede">{esc(CFG['intro'])}</p>
    <p class="stat">{esc(stat)}</p>
  </div>
</section>

<section class="browse" id="browse" aria-labelledby="browse-h">
  <div class="browse-head">
    <h2 id="browse-h">Browse</h2>
    <label class="search">
      <span class="visually-hidden">Find an article</span>
      <input id="q" type="search" placeholder="Find an article, e.g. {esc(CFG['search_example'])}" autocomplete="off">
    </label>
  </div>
  <p id="nores" class="nores" hidden>No article matches that yet. Try a broader word, or check the learning path.</p>
  <div class="domains">{"".join(sections)}</div>
</section>

<section class="latest" aria-labelledby="latest-h">
  <h2 id="latest-h">Recently added</h2>
  <ul>{latest_li}</ul>
</section>

<script id="kg-data" type="application/json">{data}</script>
<script src="assets/home.js?v={ASSET_V}"></script>"""
    return page(CFG["title"], body, 0, page_class="p-home")


# ---------------------------------------------------------------- write
def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "a").mkdir(parents=True)
    (OUT / "assets").mkdir()
    for f in (SITE / "assets").iterdir():
        shutil.copy(f, OUT / "assets" / f.name)
    # Theme tokens from site.yaml, prepended to the shared stylesheet.
    t = CFG["theme"]
    def tokens(mode):
        return "".join(f"--{k}:{v};" for k, v in t[mode].items())
    theme_css = (
        f":root{{{tokens('light')}--font-body:{t['font_body']};--font-ui:{t['font_ui']};--font-display:{t['font_display']};}}\n"
        f"@media (prefers-color-scheme: dark){{:root:not([data-theme=light]){{{tokens('dark')}}}}}\n"
        f":root[data-theme=dark]{{{tokens('dark')}}}\n"
    )
    n = len(domain_order)
    for i, d in enumerate(domain_order):
        h = round((t.get("hue_start", 0) + i * 360 / n) % 360)
        theme_css += f'[data-domain="{d}"]{{--dc:hsl({h} 48% 42%)}}\n'
        theme_css += (f'@media (prefers-color-scheme: dark){{:root:not([data-theme=light]) [data-domain="{d}"]{{--dc:hsl({h} 55% 66%)}}}}\n'
                      f':root[data-theme=dark] [data-domain="{d}"]{{--dc:hsl({h} 55% 66%)}}\n')
    css = (OUT / "assets" / "style.css").read_text(encoding="utf-8")
    (OUT / "assets" / "style.css").write_text(theme_css + css, encoding="utf-8")

    (OUT / "index.html").write_text(home(), encoding="utf-8")
    (OUT / "path.html").write_text(learning_path(), encoding="utf-8")
    (OUT / "timeline.html").write_text(timeline_page(), encoding="utf-8")
    for nid in nodes:
        (OUT / "a" / f"{slug_of(nid)}.html").write_text(article_page(nid), encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    (OUT / "404.html").write_text(
        page("Not found", '<div class="page-head"><h1>That page isn’t here</h1>'
             '<p class="lede">It may have been renamed. <a href="index.html">Go to the full article list</a>.</p></div>', 0,
             extra_head=f'<base href="/{CFG["repo"].split("/")[1]}/">'),
        encoding="utf-8",
    )
    print(f"site: {len(nodes)} articles -> {OUT.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
