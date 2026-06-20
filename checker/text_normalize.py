from __future__ import annotations

import re

# Inline IEEE / Mendeley numeric citations: [1], [2,3], [1]-[4], [1], [2]
CITATION_INLINE_RE = re.compile(
    r"\[\s*\d+(?:\s*[-–—]\s*\d+)?(?:\s*,\s*\d+)*\s*\]"
)
# Reference list entry at paragraph start
REFERENCE_ENTRY_RE = re.compile(r"^\s*\[\d+\]\s")
# Mendeley field leak in plain text
MENDELEY_LEAK_RE = re.compile(
    r"ADDIN CSL_CITATION\s*\{.*?\}\s*(\[\d+\])?",
    re.I | re.DOTALL,
)
# DOI / vol. patterns common in bibliography (low signal for body plagiarism)
BIB_BOILERPLATE_RE = re.compile(
    r"\b(doi\s*:\s*\S+|vol\.\s*\d+|no\.\s*\d+|pp\.\s*\d+[-–]\d+)\b",
    re.I,
)


def strip_citations(text: str) -> str:
    """
    Remove inline citations and bibliography noise for similarity comparison.
    Original meaning is preserved; only citation markers are stripped.
    """
    if not text:
        return ""
    t = MENDELEY_LEAK_RE.sub(" ", text)
    t = CITATION_INLINE_RE.sub(" ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def strip_for_comparison(text: str) -> str:
    """Aggressive normalize for plagiarism matching (no citations, no bib tokens)."""
    t = strip_citations(text)
    t = BIB_BOILERPLATE_RE.sub(" ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def content_word_count(text: str) -> int:
    """Word count excluding inline citation markers."""
    cleaned = strip_citations(text)
    return len(re.findall(r"\b\w+\b", cleaned))


def is_reference_paragraph(text: str, section: str) -> bool:
    if section == "References":
        return True
    if REFERENCE_ENTRY_RE.match(text):
        return True
    # Typical IEEE bibliography line: Author, "Title," Journal, vol. ...
    if re.match(r"^\[\d+\]", text.strip()):
        return True
    return False


def citation_density(text: str) -> float:
    """Share of chars that are citation markers (for diagnostics)."""
    if not text:
        return 0.0
    without = strip_citations(text)
    removed = len(text) - len(without)
    return removed / max(len(text), 1)
