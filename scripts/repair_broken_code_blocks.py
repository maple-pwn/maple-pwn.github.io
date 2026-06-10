from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

OPERATORS = {
    "=",
    "==",
    "!=",
    "<=",
    ">=",
    "<",
    ">",
    "+",
    "-",
    "*",
    "/",
    "%",
    "&&",
    "||",
    "|",
    ":=",
    "=>",
    "->",
}
CLOSERS = {",", ";", ":", ")", "]", "}", "."}
OPENERS = {"(", "[", "{", "."}


def is_fence(line: str) -> bool:
    return line.lstrip().startswith("```")


def classify_block(block_lines: list[str]) -> bool:
    nonempty = [line for line in block_lines if line.strip()]
    blank_count = len(block_lines) - len(nonempty)
    if len(nonempty) < 2 or blank_count < 2:
        return False
    short_ratio = sum(1 for line in nonempty if len(line.strip()) <= 18) / len(nonempty)
    return short_ratio >= 0.75


def append_token(current: str, token: str) -> str:
    stripped = token.strip()
    if not current:
        return stripped
    if stripped in CLOSERS:
        return current + stripped
    if current.endswith(tuple(OPENERS)) or current.endswith(("'", '"', "`")):
        return current + stripped
    if stripped in OPENERS:
        return current + stripped
    if stripped in OPERATORS:
        return current.rstrip() + f" {stripped}"
    if current.endswith(tuple(OPERATORS)):
        return current + f" {stripped}"
    return current + f" {stripped}"


def should_newline(prev: str, nxt: str, gap: int) -> bool:
    prev_s = prev.strip()
    nxt_s = nxt.strip()
    if gap >= 2:
        return True
    if prev_s.endswith(":") and prev_s not in {":"}:
        return True
    if gap == 0:
        if nxt_s in CLOSERS or nxt_s in OPENERS or nxt_s in OPERATORS:
            return False
        if prev_s in OPENERS or prev_s in OPERATORS:
            return False
        if prev_s.endswith(tuple(OPENERS)):
            return False
        return True
    return False


def rebuild_block(block_lines: list[str]) -> list[str]:
    entries: list[tuple[str, int]] = []
    i = 0
    while i < len(block_lines):
        line = block_lines[i]
        if not line.strip():
            i += 1
            continue
        j = i + 1
        gap = 0
        while j < len(block_lines) and not block_lines[j].strip():
            gap += 1
            j += 1
        entries.append((line.strip(), gap))
        i = j

    if not entries:
        return block_lines

    rebuilt: list[str] = []
    current = entries[0][0]
    for idx in range(1, len(entries)):
        prev_token, gap = entries[idx - 1]
        token, _ = entries[idx]
        if should_newline(prev_token, token, gap):
            rebuilt.append(current.rstrip())
            current = token
        else:
            current = append_token(current, token)
    rebuilt.append(current.rstrip())
    return rebuilt


def repair_file(path: Path) -> bool:
    lines = path.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    changed = False
    i = 0

    while i < len(lines):
        line = lines[i]
        out.append(line)
        if not is_fence(line):
            i += 1
            continue

        indent = re.match(r"^\s*", line).group(0)
        i += 1
        block: list[str] = []
        while i < len(lines) and not is_fence(lines[i]):
            block.append(lines[i])
            i += 1

        if classify_block(block):
            rebuilt = rebuild_block(block)
            out.extend(indent + line if line else "" for line in rebuilt)
            changed = True
        else:
            out.extend(block)

        if i < len(lines):
            out.append(lines[i])
            i += 1

    if changed:
        path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return changed


def main() -> None:
    changed_files = 0
    for md in DOCS.rglob("*.md"):
        if repair_file(md):
            changed_files += 1
            print(md.relative_to(ROOT))
    print(f"changed_files={changed_files}")


if __name__ == "__main__":
    main()
