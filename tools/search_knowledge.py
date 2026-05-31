from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
KB_PATH = BASE_DIR / "knowledge" / "hardware_kb.md"


def _split_sections(markdown_text: str) -> list[str]:
    sections: list[str] = []
    current: list[str] = []

    for line in markdown_text.splitlines():
        if line.startswith("# ") and current:
            sections.append("\n".join(current).strip())
            current = [line]
        else:
            current.append(line)

    if current:
        sections.append("\n".join(current).strip())
    return [section for section in sections if section]


def _shorten(text: str, max_chars: int = 100) -> str:
    compact = " ".join(text.split())
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 1].rstrip() + "…"


def search_knowledge(keywords: list[str]) -> list[str]:
    if not KB_PATH.exists():
        raise FileNotFoundError(f"知识库文件不存在：{KB_PATH}")

    kb_text = KB_PATH.read_text(encoding="utf-8")
    sections = _split_sections(kb_text)
    normalized_keywords = [keyword.lower() for keyword in keywords if keyword]

    snippets: list[str] = []
    seen: set[str] = set()
    for section in sections:
        section_lower = section.lower()
        if any(keyword in section_lower for keyword in normalized_keywords):
            snippet = _shorten(section)
            if snippet not in seen:
                seen.add(snippet)
                snippets.append(snippet)

    return snippets
