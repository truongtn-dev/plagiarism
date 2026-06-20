from __future__ import annotations

import re
from dataclasses import dataclass

from docx import Document


@dataclass
class ExtractedParagraph:
    index: int
    text: str
    section: str
    skip: bool
    skip_reason: str = ""


SECTION_PATTERNS = [
    (re.compile(r"^abstract", re.I), "Abstract"),
    (re.compile(r"^index terms", re.I), "Index Terms"),
    (re.compile(r"^keywords", re.I), "Index Terms"),
    (re.compile(r"^introduction$", re.I), "Introduction"),
    (re.compile(r"^references$", re.I), "References"),
    (re.compile(r"^acknowledgment", re.I), "Acknowledgments"),
    (re.compile(r"^conclusion", re.I), "Conclusion"),
    (re.compile(r"^methodology", re.I), "Methodology"),
    (re.compile(r"^literature review", re.I), "Literature Review"),
    (re.compile(r"^results", re.I), "Results"),
    (re.compile(r"^discussion", re.I), "Discussion"),
    (re.compile(r"^figure \d", re.I), "Figures"),
    (re.compile(r"^table \d", re.I), "Tables"),
    (re.compile(r"^\d+\.?\s+[A-Z]", re.I), "Section"),
]

EMAIL_RE = re.compile(r"[\w.-]+@[\w.-]+\.\w+")
CITATION_ONLY_RE = re.compile(r"^\[\d+\](\s*\[\d+\])*$")


def _detect_section(text: str, current: str) -> str:
    stripped = text.strip()
    for pattern, name in SECTION_PATTERNS:
        if pattern.match(stripped):
            return name
    if re.match(r"^[IVXLC]+\.\s+[A-Z]", stripped):
        return "Section"
    if re.match(r"^\d+(\.\d+)*\.?\s+[A-Z]", stripped) and len(stripped) < 80:
        return stripped.split(".", 1)[-1].strip()[:60] or "Section"
    return current


from checker.text_normalize import is_reference_paragraph


def _should_skip(text: str, section: str) -> tuple[bool, str]:
    stripped = text.strip()
    if section == "References":
        return True, "References section (bibliography — excluded from plagiarism check)"
    if is_reference_paragraph(stripped, section):
        return True, "Bibliography entry (excluded from plagiarism check)"
    if len(stripped) < 40:
        return True, "Quá ngắn (< 40 ký tự)"
    if EMAIL_RE.search(stripped):
        return True, "Thông tin tác giả / email"
    if CITATION_ONLY_RE.match(stripped):
        return True, "Chỉ chứa trích dẫn số"
    if re.match(r"^\[\d+\]\s", stripped):
        return True, "Bibliography entry (excluded from plagiarism check)"
    if re.fullmatch(r"[\w\s,.-]+", stripped) and "@" in stripped and len(stripped) < 120:
        return True, "Khối thông tin tác giả"
    if stripped.count("\n") >= 2 and len(stripped) < 150:
        lines = [ln.strip() for ln in stripped.splitlines() if ln.strip()]
        if len(lines) >= 3 and all(len(ln) < 60 for ln in lines):
            return True, "Metadata tác giả / đơn vị"
    return False, ""


def extract_paragraphs(path: str) -> list[ExtractedParagraph]:
    doc = Document(path)
    current_section = "Header"
    results: list[ExtractedParagraph] = []

    for idx, para in enumerate(doc.paragraphs):
        text = para.text.strip()
        if not text:
            continue
        current_section = _detect_section(text, current_section)
        skip, reason = _should_skip(text, current_section)
        results.append(
            ExtractedParagraph(
                index=idx + 1,
                text=text,
                section=current_section,
                skip=skip,
                skip_reason=reason,
            )
        )
    return results


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\"'])", text)
    return [p.strip() for p in parts if len(p.strip()) > 20]
