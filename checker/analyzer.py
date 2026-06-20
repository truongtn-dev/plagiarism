from __future__ import annotations

import re
from collections import Counter

from checker.extractor import ExtractedParagraph, split_sentences
from checker.models import ParagraphResult, RiskLevel, ScanReport, SourceMatch
from checker.suggestions import build_suggestions
from checker.text_normalize import content_word_count, strip_citations
from checker.web_checker import (
    check_paragraph_against_web,
    check_sentence_matches,
    compare_texts,
    detect_internal_overlap,
)


def _risk_level(similarity: float, has_internal: bool) -> RiskLevel:
    if similarity >= 75 or (similarity >= 60 and has_internal):
        return RiskLevel.CRITICAL
    if similarity >= 55:
        return RiskLevel.HIGH
    if similarity >= 38:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def _word_count(text: str) -> int:
    return content_word_count(text)


def analyze_document(
    paragraphs: list[ExtractedParagraph],
    filename: str,
    scan_mode: str = "standard",
    progress_callback=None,
) -> ScanReport:
    mode_config = {
        "quick": {"max_results": 3, "delay": 0.15, "min_chars": 80},
        "standard": {"max_results": 5, "delay": 0.35, "min_chars": 60},
        "thorough": {"max_results": 8, "delay": 0.5, "min_chars": 40},
    }
    cfg = mode_config.get(scan_mode, mode_config["standard"])

    to_analyze = [p for p in paragraphs if not p.skip and len(strip_citations(p.text)) >= cfg["min_chars"]]
    all_texts = [strip_citations(p.text) for p in paragraphs if not p.skip]

    results: list[ParagraphResult] = []
    total_words = sum(_word_count(p.text) for p in paragraphs if not p.skip)
    total_chars = sum(len(p.text) for p in paragraphs if not p.skip)

    plagiarized_words = 0.0
    risk_summary = {level.value: 0 for level in RiskLevel}

    import time

    start = time.time()

    for i, para in enumerate(to_analyze):
        if progress_callback:
            progress_callback(i + 1, len(to_analyze), para.text[:80])

        web_matches = check_paragraph_against_web(
            strip_citations(para.text),
            max_results=cfg["max_results"],
            delay=cfg["delay"],
        )

        internal = detect_internal_overlap(all_texts, strip_citations(para.text))

        best_sim = 0.0
        top_match: SourceMatch | None = None
        if web_matches:
            best_sim = web_matches[0].similarity
            top_match = web_matches[0]

        sentence_hits = []
        if web_matches and best_sim >= 40:
            sentence_hits = check_sentence_matches(strip_citations(para.text), web_matches)

        if internal:
            best_sim = max(best_sim, 45.0)

        risk = _risk_level(best_sim, bool(internal))
        risk_summary[risk.value] += 1

        words = _word_count(para.text)
        weight = {"critical": 0.95, "high": 0.75, "medium": 0.45, "low": 0.12}[risk.value]
        plagiarized_words += words * (best_sim / 100.0) * weight

        suggestions = build_suggestions(
            para.text,
            web_matches,
            internal,
            sentence_hits,
            top_match.matched_text if top_match else "",
        )

        results.append(
            ParagraphResult(
                index=para.index,
                text=para.text,
                char_count=len(para.text),
                word_count=words,
                similarity=round(best_sim, 1),
                risk=risk,
                sources=web_matches,
                internal_duplicates=internal,
                suggestions=suggestions,
                section=para.section,
            )
        )

    skipped = [p for p in paragraphs if p.skip]
    for para in skipped:
        results.append(
            ParagraphResult(
                index=para.index,
                text=para.text,
                char_count=len(para.text),
                word_count=_word_count(para.text),
                similarity=0.0,
                risk=RiskLevel.LOW,
                section=para.section,
                suggestions=[f"Bỏ qua: {para.skip_reason}"],
            )
        )

    results.sort(key=lambda r: r.index)

    analyzed_words = sum(r.word_count for r in results if r.similarity > 0)
    if analyzed_words > 0:
        plagiarism_pct = min(100.0, (plagiarized_words / max(total_words, 1)) * 100)
    else:
        plagiarism_pct = 0.0

    plagiarism_pct = round(plagiarism_pct, 1)
    originality_pct = round(100.0 - plagiarism_pct, 1)

    duration = time.time() - start

    return ScanReport(
        filename=filename,
        total_paragraphs=len(paragraphs),
        analyzed_paragraphs=len(to_analyze),
        total_words=total_words,
        total_chars=total_chars,
        plagiarism_percent=plagiarism_pct,
        originality_percent=originality_pct,
        risk_summary=risk_summary,
        paragraphs=results,
        scan_mode=scan_mode,
        duration_seconds=round(duration, 1),
    )


def cross_check_paragraphs(paragraphs: list[ParagraphResult]) -> float:
    """Estimate self-similarity / repetition within the document."""
    texts = [p.text for p in paragraphs if p.word_count > 15]
    if len(texts) < 2:
        return 0.0

    dup_score = 0.0
    for i, a in enumerate(texts):
        for b in texts[i + 1 :]:
            from checker.web_checker import compare_texts

            sim, _ = compare_texts(a, b)
            if sim >= 50:
                dup_score += 0.5
    return min(100.0, dup_score)
