"""Regenerate public/sitemap.xml and public/robots.txt from the HTML pages
actually present in public/ (the build output — see tools/build.py, which
calls this automatically as its last step).

Run standalone if needed: python3 tools/gen_sitemap.py
"""
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape

SITE = "https://n0g.at"
ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"


def last_modified(rel_to_public: Path) -> str | None:
    """Latest git commit date touching this file, as YYYY-MM-DD, or None.
    public/ is git-committed build output, so this reflects the last time
    the page's actual byte content changed (a no-op rebuild produces an
    identical file, so nothing new gets committed for it)."""
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", str(Path("public") / rel_to_public)],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
        return out or None
    except Exception:
        return None


def find_pages():
    return sorted(p.relative_to(PUBLIC) for p in PUBLIC.rglob("*.html"))


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
    # public/ is the whole served tree now — content/, templates/, and
    # tools/ never get deployed at all (see the site restructuring plan),
    # so there's nothing left that needs a Disallow line.
    return f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n"


def main():
    pages = find_pages()
    sitemap_path = PUBLIC / "sitemap.xml"
    robots_path = PUBLIC / "robots.txt"

    sitemap_path.write_text(build_sitemap(pages), encoding="utf-8")
    robots_path.write_text(build_robots(), encoding="utf-8")

    print(f"Wrote public/sitemap.xml with {len(pages)} URLs")
    print("Wrote public/robots.txt")


if __name__ == "__main__":
    main()
