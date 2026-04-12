from __future__ import annotations

import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urljoin, urlparse

from bs4 import BeautifulSoup, NavigableString, Tag
from markdownify import markdownify as to_markdown
import yaml


ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
SITEMAP_PATH = DOCS_DIR / "sitemap.xml"
HOME_HTML = DOCS_DIR / "index.html"
OUTPUT_MKDOCS = ROOT / "mkdocs.yml"
SOURCE_REF = "origin/gh-pages"

SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def git_show(path: str) -> str:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={ROOT.as_posix()}", "show", f"{SOURCE_REF}:{path}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout


def collect_page_locations() -> list[str]:
    if not SITEMAP_PATH.exists():
        try:
            xml = git_show("sitemap.xml")
        except RuntimeError:
            xml = None

        if xml:
            root = ET.fromstring(xml)
            locations: list[str] = []
            for loc in root.findall("sm:url/sm:loc", SITEMAP_NS):
                parsed = urlparse((loc.text or "").strip())
                locations.append(parsed.path.lstrip("/"))
            return locations

        locations: list[str] = []
        for path in sorted(DOCS_DIR.rglob("index.md")):
            relative = path.relative_to(DOCS_DIR).as_posix()
            if relative == "index.md":
                locations.append("")
            else:
                locations.append(relative[: -len("index.md")])
        return locations

    tree = ET.parse(SITEMAP_PATH)
    root = tree.getroot()
    locations: list[str] = []
    for loc in root.findall("sm:url/sm:loc", SITEMAP_NS):
        parsed = urlparse((loc.text or "").strip())
        locations.append(parsed.path.lstrip("/"))
    return locations


def location_to_html(location: str) -> Path:
    location = unquote(location)
    if not location:
        return DOCS_DIR / "index.html"
    return DOCS_DIR / location / "index.html"


def location_to_markdown(location: str) -> Path:
    location = unquote(location)
    if not location:
        return DOCS_DIR / "index.md"
    return DOCS_DIR / location / "index.md"


def direct_children(node: Tag, name: str) -> list[Tag]:
    return [child for child in node.children if isinstance(child, Tag) and child.name == name]


def direct_child(node: Tag, name: str, css_class: str | None = None) -> Tag | None:
    for child in node.children:
        if not isinstance(child, Tag) or child.name != name:
            continue
        if css_class and css_class not in child.get("class", []):
            continue
        return child
    return None


def first_direct_nav_list(node: Tag) -> Tag | None:
    nav = direct_child(node, "nav")
    if not nav:
        return None
    for child in nav.children:
        if isinstance(child, Tag) and child.name == "ul" and "md-nav__list" in child.get("class", []):
            return child
    return None


def href_to_nav_path(href: str | None, base_path: str) -> str | None:
    if not href:
        return None
    parsed = urlparse(href)
    if parsed.scheme or parsed.netloc:
        return None
    if href.startswith("#"):
        return None

    resolved = urljoin(base_path, href)
    path = urlparse(resolved).path.strip()
    if not path:
        return "index.md"
    path = path.lstrip("/")
    path = unquote(path)

    if path.endswith("/"):
        path = f"{path}index.md"
    elif path.endswith("/index.html"):
        path = f"{path[:-10]}index.md"
    elif path == "index.html":
        path = "index.md"
    elif path.endswith(".html"):
        return path

    return path


def parse_nav_list(ul: Tag, base_path: str) -> list[Any]:
    items: list[Any] = []

    for li in direct_children(ul, "li"):
        link = direct_child(li, "a", "md-nav__link")
        label = direct_child(li, "label", "md-nav__link")
        nested_list = first_direct_nav_list(li)

        title_source = link or label
        if not title_source:
            continue

        title = title_source.get_text(" ", strip=True)
        if not title:
            continue

        if nested_list is not None:
            children = parse_nav_list(nested_list, base_path)
            if children:
                items.append({title: children})
            continue

        nav_path = href_to_nav_path(link.get("href") if link else None, base_path)
        if nav_path:
            items.append({title: nav_path})

    return items


def parse_navigation() -> list[Any]:
    nav_source_path = "404.html"
    try:
        nav_source_html = git_show(nav_source_path)
    except RuntimeError:
        nav_source_path = "index.html"
        nav_source_html = HOME_HTML.read_text(encoding="utf-8")

    soup = BeautifulSoup(nav_source_html, "lxml")
    primary_nav = soup.select_one("div.md-sidebar--primary nav.md-nav")
    if not primary_nav:
        raise RuntimeError("Primary navigation not found in home page")

    nav_list = primary_nav.select_one("ul.md-nav__list")
    if not nav_list:
        raise RuntimeError("Primary navigation list not found in home page")

    base_path = "/" + nav_source_path
    return [{"首页": "index.md"}] + parse_nav_list(nav_list, base_path)


def make_placeholder(kind: str, bucket: dict[str, str], content: str) -> str:
    token = f"@@{kind}_{len(bucket)}@@"
    bucket[token] = content
    return token


def code_block_text(block: Tag) -> str:
    code = block.find("code")
    if code:
        return code.get_text("\n", strip=False).rstrip("\n")
    return block.get_text("\n", strip=False).rstrip("\n")


def preprocess_article(article: Tag) -> tuple[str, dict[str, str]]:
    placeholders: dict[str, str] = {}

    comments_heading = article.select_one("#__comments")
    if comments_heading:
        wrapper = comments_heading.find_parent("div")
        if wrapper:
            wrapper.decompose()

    for script in article.find_all("script"):
        script.decompose()

    for math_block in article.select("div.arithmatex"):
        raw = math_block.get_text("", strip=True)
        inner = raw
        if raw.startswith("\\[") and raw.endswith("\\]"):
            inner = raw[2:-2]
        token = make_placeholder("BLOCK_MATH", placeholders, f"\n$$\n{inner.strip()}\n$$\n")
        math_block.replace_with(NavigableString(token))

    for math_inline in article.select("span.arithmatex"):
        raw = math_inline.get_text("", strip=True)
        inner = raw
        if raw.startswith("\\(") and raw.endswith("\\)"):
            inner = raw[2:-2]
        token = make_placeholder("INLINE_MATH", placeholders, f"${inner.strip()}$")
        math_inline.replace_with(NavigableString(token))

    for html_block in article.select("div.github-heatmap"):
        token = make_placeholder("RAW_HTML", placeholders, f"\n{str(html_block)}\n")
        html_block.replace_with(NavigableString(token))

    for highlight in article.select("div.highlight"):
        code = code_block_text(highlight)
        token = make_placeholder("CODE", placeholders, f"\n```\n{code}\n```\n")
        highlight.replace_with(NavigableString(token))

    for pre in article.find_all("pre"):
        if pre.find_parent("div", class_="highlight"):
            continue
        code = code_block_text(pre)
        token = make_placeholder("CODE", placeholders, f"\n```\n{code}\n```\n")
        pre.replace_with(NavigableString(token))

    html = "".join(str(child) for child in article.contents)
    return html, placeholders


def cleanup_markdown(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n(```)", r"\n\n\1", text)
    text = re.sub(r"(```)\n(?=[^\n])", r"\1\n\n", text)
    text = re.sub(r"\n(#{1,6}\s)", r"\n\n\1", text)
    text = re.sub(r"\n(- |\d+\. )", r"\n\1", text)
    return text.strip() + "\n"


def convert_page(location: str) -> None:
    html_path = location_to_html(location)
    markdown_path = location_to_markdown(location)
    source_path = unquote(location)
    if not source_path:
        source_path = "index.html"
    else:
        source_path = f"{source_path}index.html"

    try:
        source_html = git_show(source_path)
    except RuntimeError:
        if not html_path.exists():
            raise FileNotFoundError(f"Missing HTML page for {location or '/'}: {html_path}")
        source_html = html_path.read_text(encoding="utf-8")

    soup = BeautifulSoup(source_html, "lxml")
    article = soup.select_one("article.md-content__inner")
    if not article:
        raise RuntimeError(f"Article content not found in {html_path}")

    html, placeholders = preprocess_article(article)
    markdown = to_markdown(
        html,
        heading_style="ATX",
        bullets="-",
        strip=["script"],
    )

    for token, content in placeholders.items():
        markdown = markdown.replace(token, content)
        markdown = markdown.replace(token.replace("_", "\\_"), content)

    markdown = cleanup_markdown(markdown)
    markdown_path.write_text(markdown, encoding="utf-8")
    if html_path.exists():
        html_path.unlink()


def write_mkdocs_config(nav: list[Any]) -> None:
    config = {
        "site_name": "Maple's blog",
        "site_url": "https://maple-pwn.github.io/",
        "docs_dir": "docs",
        "site_dir": "site",
        "use_directory_urls": True,
        "strict": False,
        "theme": {
            "name": "material",
            "language": "zh",
            "logo": "images/logo.svg",
            "favicon": "images/logo.svg",
            "custom_dir": "overrides",
            "features": [
                "content.code.copy",
                "content.code.select",
                "content.code.annotate",
                "navigation.titles",
                "navigation.tabs",
                "navigation.indexes",
                "navigation.top",
            ],
            "palette": [
                {
                    "media": "(prefers-color-scheme: light)",
                    "scheme": "default",
                    "primary": "indigo",
                    "accent": "indigo",
                    "toggle": {"icon": "material/weather-sunny", "name": "切换到深色模式"},
                },
                {
                    "media": "(prefers-color-scheme: dark)",
                    "scheme": "slate",
                    "primary": "indigo",
                    "accent": "indigo",
                    "toggle": {"icon": "material/weather-night", "name": "切换到浅色模式"},
                },
            ],
        },
        "markdown_extensions": [
            "tables",
            "attr_list",
            "md_in_html",
            {
                "pymdownx.arithmatex": {
                    "generic": True,
                }
            },
        ],
        "extra_css": [
            "resources/css/extra.css",
            "resources/css/tittle.css",
            "resources/css/read-metrics.css",
            "resources/css/leftsidebar.css",
            "https://static.zeoseven.com/zsft/292/main/result.css",
        ],
        "extra_javascript": [
            "resources/js/mathjax-config.js",
            "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js",
            "resources/js/read-metrics.js",
            "resources/js/sidebar-resize.js",
        ],
        "plugins": [],
        "nav": nav,
    }

    OUTPUT_MKDOCS.write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def prune_generated_outputs() -> None:
    for relative in ["assets", "search"]:
        target = DOCS_DIR / relative
        if target.exists():
            shutil.rmtree(target)

    for relative in ["sitemap.xml", "sitemap.xml.gz"]:
        target = DOCS_DIR / relative
        if target.exists():
            target.unlink()


def main() -> None:
    locations = collect_page_locations()
    nav = parse_navigation()

    for location in locations:
        convert_page(location)

    write_mkdocs_config(nav)
    prune_generated_outputs()

    print(json.dumps({"pages_recovered": len(locations), "nav_items": len(nav)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
