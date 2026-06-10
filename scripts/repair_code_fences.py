from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def fix_mysys03(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        window = lines[i + 1 : i + 12]
        if line == "    ```" and "    ```mermaid" in window:
            i += 1
            continue
        back_window = lines[max(0, i - 12) : i]
        if line == "    ```" and any("classDef step6" in prev for prev in back_window):
            i += 1
            continue
        if line == "```" and out and out[-1] == "" and len(out) >= 2 and out[-2] == "    ```":
            i += 1
            continue
        out.append(line)
        i += 1
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def fix_mysys06(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    removed_open = False
    removed_close = False
    i = 0
    while i < len(lines):
        line = lines[i]
        if not removed_open and line == "    ```":
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and lines[j].startswith("    ") and not lines[j].startswith("    ```"):
                removed_open = True
                i += 1
                continue
        if removed_open and not removed_close and line == "    ```":
            removed_close = True
            i += 1
            continue
        out.append(line)
        i += 1
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def main() -> None:
    fix_mysys03(ROOT / "docs" / "mysys" / "03" / "index.md")
    fix_mysys06(ROOT / "docs" / "mysys" / "06" / "index.md")


if __name__ == "__main__":
    main()
