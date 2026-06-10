from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LABELS = {
    "Tip": "tip",
    "Note": "note",
    "Important": "important",
    "Warning": "warning",
    "Caution": "warning",
    "Info": "info",
    "Hint": "tip",
    "Success": "success",
    "Failure": "failure",
    "Question": "question",
}


def rewrite_block(lines: list[str], start: int, marker: str, title: str, end: int) -> None:
    lines[start] = f'!!! {marker} "{title}"'
    i = start + 1
    while i <= end:
        if lines[i]:
            lines[i] = "    " + lines[i]
        i += 1


def fix_eda(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if line.strip() == "!!!Note":
            lines[i] = "!!! note"
        elif line.strip() == "> !!!Tip":
            lines[i] = ""
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def fix_compiler(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if line.startswith("!!! important "):
            title = line[len("!!! important ") :].strip()
            lines[i] = f'!!! important "{title}"'
            if i + 1 < len(lines) and lines[i + 1] and not lines[i + 1].startswith("    "):
                lines[i + 1] = "    " + lines[i + 1]
            if i + 2 < len(lines) and lines[i + 2] and not lines[i + 2].startswith("    "):
                lines[i + 2] = "    " + lines[i + 2]
            break
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def fix_mysys03(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if line.startswith("!!!note ") and "从用户态中断进入内核态" in line:
            end = i + 1
            while end < len(lines) and lines[end].strip() != "```":
                end += 1
            while end + 1 < len(lines) and lines[end + 1].strip() != "```":
                end += 1
            if end + 1 < len(lines):
                end += 1
            rewrite_block(lines, i, "note", "举个例子（从用户态中断进入内核态）", end)
        elif line.startswith("!!!note ") and "访问规则" in line:
            end = i + 1
            while end < len(lines) and not lines[end].startswith("但是这样存在一个问题"):
                end += 1
            rewrite_block(lines, i, "note", "三者的访问规则&&例子", end - 1)
        elif line.startswith("!!!note ") and "调用门的内部执行结构" in line:
            end = i + 1
            while end < len(lines) and not lines[end].startswith("**获取内核例程地址"):
                end += 1
            rewrite_block(lines, i, "note", "调用门的内部执行结构：点击查看更多", end - 1)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def fix_mysys06(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if line.startswith("!!!note ") and "死循环" in line:
            end = i + 1
            while end < len(lines) and not lines[end].startswith("### "):
                end += 1
            rewrite_block(lines, i, "note", "“死循环”的错觉与根目录的作用", end - 1)
            break
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def fix_plain_labels(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    i = 0

    while i < len(lines):
        stripped = lines[i].strip()
        kind = LABELS.get(stripped)
        if not kind:
            out.append(lines[i])
            i += 1
            continue

        out.append(f"!!! {kind}")
        i += 1

        while i < len(lines) and not lines[i].strip():
            i += 1

        while i < len(lines):
            current = lines[i]
            current_stripped = current.strip()
            if not current_stripped:
                out.append("")
                i += 1
                break
            if current_stripped in LABELS or current_stripped.startswith("!!!") or current_stripped.startswith("#"):
                break
            out.append("    " + current)
            i += 1

    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def main() -> None:
    for md in (ROOT / "docs").rglob("*.md"):
        fix_plain_labels(md)
    fix_eda(ROOT / "docs" / "study" / "eda" / "index.md")
    fix_compiler(ROOT / "docs" / "study" / "compiler" / "index.md")
    fix_mysys03(ROOT / "docs" / "mysys" / "03" / "index.md")
    fix_mysys06(ROOT / "docs" / "mysys" / "06" / "index.md")


if __name__ == "__main__":
    main()
