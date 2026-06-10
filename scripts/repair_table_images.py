from __future__ import annotations

import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

IMG_TOKEN = re.compile(
    r"(Pasted image \d{14}\.png|image-\d{8,}(?:-\d+)*?(?:-\d+)?(?:\.\w+)?|[A-Za-z0-9_.-]+\.(?:png|jpg|jpeg|svg|webp))"
)


def choose_image_root(md: Path) -> Path:
    rel = md.relative_to(DOCS)
    if rel.parts and rel.parts[0] == "pwn":
        return DOCS / "pwn" / "images"
    return DOCS / "images"


def find_best_match(token: str, image_root: Path) -> Path | None:
    token = token.strip()
    direct = image_root / token
    if direct.exists():
        return direct

    stem = Path(token).stem
    matches = sorted(image_root.glob(f"{stem}*"))
    if matches:
        matches.sort(key=lambda p: (len(p.name), p.name))
        return matches[0]
    return None


def to_relpath(md: Path, target: Path) -> str:
    return os.path.relpath(target, md.parent).replace("\\", "/")


def repair_cell(cell: str, md: Path, image_root: Path) -> str:
    if "![](" in cell or "<img" in cell:
        return cell.strip()
    match = IMG_TOKEN.search(cell)
    if not match:
        return cell.strip()

    target = find_best_match(match.group(1), image_root)
    if not target:
        return cell.strip()

    return f"![]({to_relpath(md, target)})"


def repair_tables(text: str, md: Path) -> str:
    image_root = choose_image_root(md)
    lines = text.splitlines()
    changed = False

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not (stripped.startswith("|") and stripped.endswith("|")):
            continue
        if re.fullmatch(r"\|\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?", stripped):
            continue

        cells = [c.strip() for c in stripped.strip("|").split("|")]
        new_cells = [repair_cell(c, md, image_root) for c in cells]
        if new_cells != cells:
            indent = line[: len(line) - len(line.lstrip())]
            lines[idx] = f"{indent}| " + " | ".join(new_cells) + " |"
            changed = True

    if not changed:
        return text
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def main() -> None:
    changed_files = 0
    for md in DOCS.rglob("*.md"):
        text = md.read_text(encoding="utf-8")
        updated = repair_tables(text, md)
        if updated != text:
            md.write_text(updated, encoding="utf-8")
            changed_files += 1
            print(md.relative_to(ROOT))

    print(f"changed_files={changed_files}")


if __name__ == "__main__":
    main()
