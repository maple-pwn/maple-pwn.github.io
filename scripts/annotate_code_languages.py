from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def detect_language(lines: list[str]) -> str | None:
    text = "\n".join(lines).strip()
    if not text:
        return None

    if text.startswith(("flowchart", "sequenceDiagram", "graph ", "graph\n", "classDiagram", "erDiagram", "gantt", "journey")):
        return "mermaid"
    if any(line.strip().startswith(("[mcp_servers.", "theme:", "plugins:", "nav:", "site_name:", "docs_dir:")) for line in lines):
        return "yaml"
    if text.startswith(("{", "[")) and '"' in text and ":" in text:
        return "json"
    if any(line.strip().startswith(("# ~/.codex/config.toml", "[mcp_servers.", "[tool.", "[project]", "command = ", "args = [")) for line in lines):
        return "toml"
    if any(line.strip().startswith(("def ", "import ", "from ", "for ", "if ", "print(", "class ")) for line in lines) and ":" in text:
        return "python"
    if any(line.strip().startswith(("mov ", "jmp ", "push ", "pop ", "call ", "cmp ", "lea ", "xor ", "int ", "assume ", "code segment", ".data:", ".text:", "section .", "global ")) for line in lines):
        if any(".data:" in line or "db " in line or "align " in line for line in lines):
            return "asm"
        return "asm"
    if any(line.strip().startswith(("#include", "int ", "char ", "void ", "struct ", "typedef ", "FILE *", "return ")) for line in lines) and any("{" in line or ";" in line for line in lines):
        return "c"
    if any(line.strip().startswith(("curl ", "grep ", "docker ", "tree ", "sed ", "checksec ", "gdb ", "python ", "tshark ", "source ", "websocat ", "git ", "mkdocs ")) for line in lines):
        return "bash"
    if any(line.strip().startswith(("task_id:", "input:", "environment:", "tools:", "constraints:", "logging:", "success:")) for line in lines):
        return "yaml"
    if text.startswith(("web-initial-recon/", "task_id:", "---\nname:", "name: web-initial-recon")):
        return "yaml"
    if re.match(r"^[A-Za-z_][A-Za-z0-9_]*\s*:=\s*.+", lines[0].strip()):
        return "text"
    return None


def annotate_file(path: Path) -> bool:
    lines = path.read_text(encoding="utf-8").splitlines()
    changed = False
    i = 0
    while i < len(lines):
        if lines[i].strip() != "```":
            i += 1
            continue
        start = i
        i += 1
        block: list[str] = []
        while i < len(lines) and not lines[i].lstrip().startswith("```"):
            block.append(lines[i])
            i += 1
        lang = detect_language(block)
        if lang:
            indent = lines[start][: len(lines[start]) - len(lines[start].lstrip())]
            lines[start] = f"{indent}```{lang}"
            changed = True
        if i < len(lines):
            i += 1
    if changed:
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return changed


def main() -> None:
    changed = 0
    for md in DOCS.rglob("*.md"):
        if annotate_file(md):
            changed += 1
            print(md.relative_to(ROOT))
    print(f"changed={changed}")


if __name__ == "__main__":
    main()
