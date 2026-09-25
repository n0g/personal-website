"""Build the site: content/*.yaml + templates/*.j2 -> public/.

Run: python3 tools/build.py   (needs jinja2 + pyyaml — see requirements.txt)

public/ is wiped and fully regenerated each run, so it never holds stale
output from a removed publication. public/ is what actually gets deployed
(see README note in the repo root / the site restructuring plan) — nothing
under content/, templates/, or tools/ is ever served.
"""
import itertools
import re
import shutil
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

SITE_URL = "https://n0g.at"

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
TEMPLATES = ROOT / "templates"
PAGES = ROOT / "pages"
PUBLIC = ROOT / "public"


def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def author_sort(name):
    """'First Middle Last' -> 'Last, First Middle' for citation_author tags."""
    parts = name.split()
    if len(parts) == 1:
        return parts[0]
    return f"{parts[-1]}, {' '.join(parts[:-1])}"


def citation_date(pub):
    year = pub["year"]
    month = pub.get("month")
    return f"{year}/{month:02d}" if month else str(year)


def pdf_url(pub, site_url):
    """Absolute citation_pdf_url: self-hosted PDFs get the public URL under
    /publications/; an already-absolute pdf_external URL (e.g. a paywalled
    dissertation hosted elsewhere) passes through unchanged."""
    if pub.get("pdf"):
        return f"{site_url}/publications/{pub['pdf']}"
    if pub.get("pdf_external"):
        return pub["pdf_external"]
    return None


def group_preserving_order(items, key):
    """Group `items` by `key(item)`, preserving first-occurrence order of
    both the groups and the items within each group — NOT sorted/alphabetical.
    (Python's itertools.groupby only groups *consecutive* runs; this handles
    a flat list where a group's members may need collecting from anywhere.)"""
    order = []
    buckets = {}
    for item in items:
        k = key(item)
        if k not in buckets:
            buckets[k] = []
            order.append(k)
        buckets[k].append(item)
    return [(k, buckets[k]) for k in order]


def main():
    # ---------- load content ----------
    site = load_yaml(CONTENT / "site.yaml")
    research_focus = load_yaml(CONTENT / "research_focus.yaml")
    awards = load_yaml(CONTENT / "awards.yaml")
    press = load_yaml(CONTENT / "press.yaml")

    pub_files = sorted((CONTENT / "publications").glob("*.yaml"))
    publications = [load_yaml(p) for p in pub_files]

    # newest year first; within a year, preserve the original list `order`
    publications.sort(key=lambda p: (-p["year"], p["order"]))
    publications_by_year = group_preserving_order(publications, key=lambda p: p["year"])
    # group_preserving_order gives first-occurrence order, which for a list
    # already sorted newest-year-first is already newest-first — no re-sort needed.

    press_by_group = group_preserving_order(press, key=lambda item: item["group"])

    # ---------- render ----------
    if PUBLIC.exists():
        shutil.rmtree(PUBLIC)
    PUBLIC.mkdir(parents=True)
    (PUBLIC / "publications").mkdir()

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES)),
        # Default (True): publication metadata (title, authors, badge, abstract,
        # bibtex, ...) is plain text ported from Python strings that were always
        # HTML-escaped at render time — autoescaping now does the same job.
        # A handful of site.yaml/research_focus.yaml/awards.yaml/press.yaml
        # fields were instead extracted directly FROM already-rendered HTML
        # (so they already contain entities like &amp; and/or raw tags like
        # <strong>) and are marked `| safe` at their specific use sites in the
        # templates to avoid double-escaping — autoescape stays on everywhere else.
        autoescape=True,
    )
    env.filters["author_sort"] = author_sort
    env.filters["pdf_url"] = pdf_url
    env.filters["citation_date"] = citation_date

    index_tpl = env.get_template("index.html.j2")
    (PUBLIC / "index.html").write_text(
        index_tpl.render(
            site=site,
            research_focus=research_focus,
            publications_by_year=publications_by_year,
            awards=awards,
            press_by_group=press_by_group,
        ),
        encoding="utf-8",
    )

    pub_tpl = env.get_template("publication.html.j2")
    for pub in publications:
        out = pub_tpl.render(pub=pub, site=site, site_url=SITE_URL)
        (PUBLIC / "publications" / f"{pub['slug']}.html").write_text(out, encoding="utf-8")
        if pub.get("pdf"):
            src = CONTENT / "publications" / "pdfs" / pub["pdf"]
            shutil.copy2(src, PUBLIC / "publications" / pub["pdf"])

    # ---------- copy static assets ----------
    shutil.copy2(TEMPLATES / "style.css", PUBLIC / "style.css")
    shutil.copy2(TEMPLATES / "copy.js", PUBLIC / "copy.js")

    for page in PAGES.glob("*.html"):
        shutil.copy2(page, PUBLIC / page.name)

    shutil.copytree(ROOT / "static", PUBLIC / "static")
    shutil.copytree(ROOT / "fonts", PUBLIC / "fonts")

    print(f"Built {PUBLIC} — {1 + len(publications) + len(list(PAGES.glob('*.html')))} HTML pages")

    # ---------- sitemap.xml / robots.txt ----------
    import gen_sitemap
    gen_sitemap.main()


if __name__ == "__main__":
    main()
