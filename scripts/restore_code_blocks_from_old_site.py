from __future__ import annotations

import subprocess
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OLD_SITE_COMMIT = "14b67a34d2112f8f3f4ca731a114e5989e14ac76"


def old_html_path(md: Path) -> str:
    rel = md.relative_to(DOCS).as_posix()
    if rel == "index.md":
        return "index.html"
    return rel[: -len("index.md")] + "index.html"


def git_show(path: str) -> str | None:
    result = subprocess.run(
        ["git", "show", f"{OLD_SITE_COMMIT}:{path}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        return None
    return result.stdout


def extract_old_blocks(md: Path) -> list[str] | None:
    html = git_show(old_html_path(md))
    if html is None:
        return None
    soup = BeautifulSoup(html, "lxml")
    return [pre.get_text("") for pre in soup.find_all("pre")]


def find_current_fences(lines: list[str]) -> list[tuple[int, int, str]]:
    fences: list[tuple[int, int, str]] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.lstrip().startswith("```"):
            indent = line[: len(line) - len(line.lstrip())]
            lang = line.lstrip()[3:].strip()
            start = i
            i += 1
            while i < len(lines) and not lines[i].lstrip().startswith("```"):
                i += 1
            if i < len(lines):
                fences.append((start, i, lang))
        i += 1
    return fences


def rebuild(lines: list[str], fences: list[tuple[int, int, str]], blocks: list[str]) -> list[str]:
    out: list[str] = []
    last = 0
    for (start, end, _lang), block in zip(fences, blocks):
        out.extend(lines[last : start + 1])
        indent = lines[start][: len(lines[start]) - len(lines[start].lstrip())]
        body = block.rstrip("\n").splitlines()
        out.extend((indent + line) if line else "" for line in body)
        out.append(lines[end])
        last = end + 1
    out.extend(lines[last:])
    return out


def main() -> None:
    changed = 0
    skipped = 0
    for md in DOCS.rglob("*.md"):
        old_blocks = extract_old_blocks(md)
        if old_blocks is None:
            continue

        text = md.read_text(encoding="utf-8")
        lines = text.splitlines()
        fences = find_current_fences(lines)

        fence_langs = [lang for *_rest, lang in fences]
        non_mermaid = [(s, e, lang) for (s, e, lang) in fences if lang != "mermaid"]
        if len(non_mermaid) != len(old_blocks):
            skipped += 1
            continue

        new_lines = rebuild(lines, non_mermaid, old_blocks)
        new_text = "\n".join(new_lines) + "\n"
        if new_text != text:
            md.write_text(new_text, encoding="utf-8")
            changed += 1
            print(md.relative_to(ROOT))

    print(f"changed={changed} skipped={skipped}")


if __name__ == "__main__":
    main()
