from __future__ import annotations

import hashlib
import mimetypes
import re
from pathlib import Path
from urllib.parse import urlparse

import requests


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
TARGET_DIR = DOCS / "images" / "external"
SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Referer": "https://maple-pwn.github.io/",
    }
)

MD_IMAGE = re.compile(r'!\[([^\]]*)\]\((https?://[^)\s]+)\)')
HTML_IMAGE = re.compile(r'((?:src|srcset)=["\'])(https?://[^"\']+)(["\'])', re.IGNORECASE)


def extension_for(url: str, content_type: str | None) -> str:
    path_ext = Path(urlparse(url).path).suffix.lower()
    if path_ext:
        return path_ext
    if content_type:
        guessed = mimetypes.guess_extension(content_type.split(";")[0].strip())
        if guessed:
            return guessed
    return ".bin"


def local_relpath(url: str, content_type: str | None) -> str:
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
    ext = extension_for(url, content_type)
    return f"images/external/{digest}{ext}"


def gather_urls() -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()

    for md in DOCS.rglob("*.md"):
        text = md.read_text(encoding="utf-8")
        for pattern in (MD_IMAGE, HTML_IMAGE):
            for match in pattern.finditer(text):
                url = match.group(2)
                if url not in seen:
                    seen.add(url)
                    urls.append(url)
    return urls


def download(url: str) -> tuple[str, bytes]:
    response = SESSION.get(url, timeout=30)
    response.raise_for_status()
    return response.headers.get("content-type", ""), response.content


def replace_refs(text: str, mapping: dict[str, str], depth: int) -> str:
    prefix = "../" * depth

    def md_repl(match: re.Match[str]) -> str:
        alt, url = match.groups()
        rel = prefix + mapping[url]
        return f"![{alt}]({rel})"

    def html_repl(match: re.Match[str]) -> str:
        start, url, end = match.groups()
        rel = prefix + mapping[url]
        return f"{start}{rel}{end}"

    text = MD_IMAGE.sub(md_repl, text)
    text = HTML_IMAGE.sub(html_repl, text)
    return text


def main() -> None:
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    mapping: dict[str, str] = {}
    failures: list[tuple[str, str]] = []
    for url in gather_urls():
        rel = local_relpath(url, None)
        path = DOCS / rel
        if path.exists():
            mapping[url] = rel
            print(f"cached {url} -> {rel}")
            continue
        try:
            content_type, data = download(url)
            rel = local_relpath(url, content_type)
            path = DOCS / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            mapping[url] = rel
            print(f"downloaded {url} -> {rel}")
        except Exception as exc:
            failures.append((url, str(exc)))
            print(f"failed {url} :: {exc}")

    for md in DOCS.rglob("*.md"):
        rel_parts = md.relative_to(DOCS).parts
        depth = max(len(rel_parts) - 1, 0)
        text = md.read_text(encoding="utf-8")
        updated = replace_refs(text, mapping, depth)
        if updated != text:
            md.write_text(updated, encoding="utf-8")
            print(f"updated {md.relative_to(ROOT)}")

    if failures:
        raise SystemExit("\n".join(f"{url} :: {err}" for url, err in failures))


if __name__ == "__main__":
    main()
