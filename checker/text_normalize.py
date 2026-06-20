from __future__ import annotations

import re

# Inline IEEE / Mendeley numeric citations: [1], [2,3], [1]-[4], [1], [2]
CITATION_INLINE_RE = re.compile(
    r"\[\s*\d+(?:\s*[-–—]\s*\d+)?(?:\s*,\s*\d+)*\s*\]"
)
# Reference list entry at paragraph start: [1] Author...
REFERENCE_ENTRY_RE = re.compile(r"^\s*\[\d+\]\s")
# Mendeley field leak in plain text
MENDELEY_LEAK_RE = re.compile(
    r"ADDIN CSL_CITATION\s*\{.*?\}\s*(\[\d+\])?",
    re.I | re.DOTALL,
)
# DOI / vol. patterns common in bibliography
BIB_BOILERPLATE_RE = re.compile(
    r"\b(doi\s*:\s*\S+|vol\.\s*\d+|no\.\s*\d+|pp\.\s*\d+[-–]\d+)\b",
    re.I,
)

# IEEE author line: L. Raitskaya and E. Tikhonova, "Title," Journal...
IEEE_AUTHOR_LINE_RE = re.compile(
    r"^(\[\d+\]\s*)?"
    r"[A-Z]\.\s*[\w\-]+"
    r"(?:,\s*(?:and|&)\s+[A-Z]\.?\s*[\w\-]+|\s*,\s*et\s+al\.)*"
    r",\s*[\"\u201c\u2018]",
    re.I,
)

# Quoted article title followed by journal/conference marker
IEEE_TITLE_JOURNAL_RE = re.compile(
    r"[\"\u201c][^\"\u201d]+[\"\u201d],\s*[\w\s&\.]+,",
    re.I,
)

BIB_MARKER_COUNT_RE = re.compile(
    r"\b(vol\.\s*\d+|no\.\s*\d+|pp\.\s*\d+|doi\s*:\s*\S+|DOI\s*:\s*\S+|"
    r"Jan\.|Feb\.|Mar\.|Apr\.|May\.|Jun\.|Jul\.|Aug\.|Sep\.|Oct\.|Nov\.|Dec\.)\b",
    re.I,
)


def strip_citations(text: str) -> str:
    """Remove inline citations for similarity comparison."""
    if not text:
        return ""
    t = MENDELEY_LEAK_RE.sub(" ", text)
    t = CITATION_INLINE_RE.sub(" ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def strip_for_comparison(text: str) -> str:
    """Normalize for plagiarism matching (no citations, no bib tokens)."""
    t = strip_citations(text)
    t = BIB_BOILERPLATE_RE.sub(" ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def content_word_count(text: str) -> int:
    """Word count excluding inline citation markers."""
    cleaned = strip_citations(text)
    return len(re.findall(r"\b\w+\b", cleaned))


def is_ieee_bibliography_entry(text: str) -> bool:
    """
    Detect IEEE bibliography lines, with or without leading [n].
    Example: L. Raitskaya and E. Tikhonova, "Title," JLE, vol. 11, no. 2, pp. 5–19, doi: ...
    """
    t = text.strip()
    if not t or len(t) < 50:
        return False

    if REFERENCE_ENTRY_RE.match(t) or re.match(r"^\[\d+\]", t):
        return True

    markers = BIB_MARKER_COUNT_RE.findall(t)
    marker_count = len(markers)

    # Strong signal: author + quoted title + vol/pp/doi
    if IEEE_AUTHOR_LINE_RE.match(t) and marker_count >= 2:
        return True

    if IEEE_AUTHOR_LINE_RE.match(t) and IEEE_TITLE_JOURNAL_RE.search(t):
        return True

    # Author initials + doi + vol (common in user's refs)
    if re.match(r"^[A-Z]\.\s*[\w\-]+", t) and marker_count >= 2:
        if IEEE_TITLE_JOURNAL_RE.search(t) or "doi" in t.lower():
            return True

    # et al. bibliography
    if re.match(r"^(\[\d+\]\s*)?[A-Z]\.", t) and "et al." in t and marker_count >= 1:
        if IEEE_TITLE_JOURNAL_RE.search(t):
            return True

    return False


def is_reference_paragraph(text: str, section: str) -> bool:
    if section == "References":
        return True
    if is_ieee_bibliography_entry(text):
        return True
    return False


def citation_density(text: str) -> float:
    """Share of chars that are citation markers (for diagnostics)."""
    if not text:
        return 0.0
    without = strip_citations(text)
    removed = len(text) - len(without)
    return removed / max(len(text), 1)
