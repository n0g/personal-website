"""Regenerate sitemap.xml from the HTML pages actually present in the repo.

Run from anywhere: python3 tools/gen_sitemap.py
Re-run whenever a page is added or removed.
"""
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape

SITE = "https://n0g.at"
ROOT = Path(__file__).resolve().parent.parent

# Directories/files to skip entirely (not part of the public site).
SKIP_DIRS = {".venv", ".git", ".claude", "fonts", "static", "latex-sources", "tools"}


def last_modified(rel: Path) -> str | None:
    """Latest git commit date touching this file (rel, relative to ROOT), as YYYY-MM-DD, or None."""
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", str(rel)],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
        return out or None
    except Exception:
        return None


def find_pages():
    pages = []
    for path in sorted(ROOT.rglob("*.html")):
        rel = path.relative_to(ROOT)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        pages.append(rel)
    return pages


def url_for(rel: Path) -> str:
    if rel.name == "index.html" and len(rel.parts) == 1:
        return f"{SITE}/"
    return f"{SITE}/{rel.as_posix()}"


def priority_for(rel: Path) -> str:
    if rel.name == "index.html" and len(rel.parts) == 1:
        return "1.0"
    if rel.parts[0] == "publications":
        return "0.7"
    return "0.5"


def build_sitemap(pages):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for rel in pages:
        loc = escape(url_for(rel))
        lastmod = last_modified(rel)
        lines.append("  <url>")
        lines.append(f"    <loc>{loc}</loc>")
        if lastmod:
            lines.append(f"    <lastmod>{lastmod}</lastmod>")
        lines.append(f"    <priority>{priority_for(rel)}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def build_robots():
    # Deployment is a plain `git pull` on the server, so everything tracked
    # in the repo — including this tools/ directory — ends up publicly
    # servable. Nothing in tools/ is sensitive, but keep it out of search
    # results since it's not real site content.
    return (
        f"User-agent: *\n"
        f"Allow: /\n"
        f"Disallow: /tools/\n\n"
        f"Sitemap: {SITE}/sitemap.xml\n"
    )


def main():
    pages = find_pages()
    sitemap_path = ROOT / "sitemap.xml"
    robots_path = ROOT / "robots.txt"

    sitemap_path.write_text(build_sitemap(pages), encoding="utf-8")
    robots_path.write_text(build_robots(), encoding="utf-8")

    print(f"Wrote {sitemap_path.relative_to(ROOT)} with {len(pages)} URLs")
    print(f"Wrote {robots_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
