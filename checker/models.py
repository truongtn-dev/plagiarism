from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SourceMatch:
    title: str
    url: str
    snippet: str
    similarity: float
    matched_text: str = ""


@dataclass
class ParagraphResult:
    index: int
    text: str
    char_count: int
    word_count: int
    similarity: float
    risk: RiskLevel
    sources: list[SourceMatch] = field(default_factory=list)
    internal_duplicates: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    section: str = ""
    coverage_percent: float = 0.0
    fuzzy_similarity: float = 0.0


@dataclass
class ScanReport:
    filename: str
    total_paragraphs: int
    analyzed_paragraphs: int
    total_words: int
    total_chars: int
    plagiarism_percent: float
    originality_percent: float
    risk_summary: dict[str, int]
    paragraphs: list[ParagraphResult] = field(default_factory=list)
    scan_mode: str = "standard"
    duration_seconds: float = 0.0
    ieee_estimate_percent: float = 0.0
    ieee_compliance_note: str = ""
