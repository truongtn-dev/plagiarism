from __future__ import annotations

import time

from checker.extractor import ExtractedParagraph
from checker.models import ParagraphResult, RiskLevel, ScanReport, SourceMatch
from checker.suggestions import build_suggestions
from checker.text_normalize import content_word_count, strip_citations
from checker.web_checker import (
    best_fuzzy_similarity,
    check_paragraph_against_web,
    check_sentence_matches,
    compare_texts,
    count_matching_words,
    coverage_percent,
    detect_internal_overlap,
)

IEEE_SIMILARITY_THRESHOLD = 30.0
IEEE_ESTIMATE_WEIGHT = 0.72


def _risk_level(coverage: float, fuzzy: float, has_internal: bool) -> RiskLevel:
    signal = max(coverage, fuzzy * 0.55)
    if signal >= 55 or (signal >= 42 and has_internal):
        return RiskLevel.CRITICAL
    if signal >= 35 or fuzzy >= 50:
        return RiskLevel.HIGH
    if signal >= 18 or fuzzy >= 32:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def _paragraph_coverage(body_text: str, web_matches: list[SourceMatch], internal: list[str]) -> float:
    best_cov = 0.0
    if web_matches:
        for match in web_matches[:5]:
            best_cov = max(best_cov, coverage_percent(body_text, match.snippet))

    for chunk in internal:
        best_cov = max(best_cov, coverage_percent(body_text, chunk))

    return round(best_cov, 1)


def _paragraph_fuzzy(body_text: str, web_matches: list[SourceMatch], internal: list[str]) -> float:
    snippets = [m.snippet for m in web_matches[:5]]
    fuzzy = best_fuzzy_similarity(body_text, snippets)
    for chunk in internal:
        fuzzy = max(fuzzy, compare_texts(body_text, chunk)[0])
    return round(fuzzy, 1)


def _ieee_compliance_note(ieee_estimate: float, coverage: float, flagged_high: int) -> str:
    if ieee_estimate >= IEEE_SIMILARITY_THRESHOLD:
        return (
            f"IEEE risk estimate ({ieee_estimate:.1f}%) exceeds the typical {IEEE_SIMILARITY_THRESHOLD:.0f}% "
            "threshold used by iThenticate/Turnitin for conference submissions. Revise flagged paragraphs "
            "before re-uploading to EDAS."
        )
    if flagged_high >= 3 or ieee_estimate >= 22:
        return (
            f"IEEE risk estimate is {ieee_estimate:.1f}% (web/academic sources). Even if web coverage is "
            f"only {coverage:.1f}%, iThenticate also checks IEEE Xplore and unpublished papers — "
            "request the official similarity report from the conference chair if available."
        )
    return (
        "Web coverage is a lower bound. IEEE/iThenticate uses a private academic database; "
        "always verify with the official conference similarity report before submission."
    )


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

    plagiarized_words = 0
    ieee_estimate_words = 0.0
    flagged_high = 0
    risk_summary = {level.value: 0 for level in RiskLevel}

    start = time.time()

    for i, para in enumerate(to_analyze):
        if progress_callback:
            progress_callback(i + 1, len(to_analyze), para.text[:80])

        web_matches = check_paragraph_against_web(
            strip_citations(para.text),
            max_results=cfg["max_results"],
            delay=cfg["delay"],
            section=para.section,
        )

        internal = detect_internal_overlap(all_texts, strip_citations(para.text))
        body_text = strip_citations(para.text)

        cov = _paragraph_coverage(body_text, web_matches, internal)
        fuzzy = _paragraph_fuzzy(body_text, web_matches, internal)
        display_sim = max(cov, round(fuzzy * 0.55, 1))
        top_match: SourceMatch | None = web_matches[0] if web_matches else None

        sentence_hits = []
        if web_matches and (cov >= 10 or fuzzy >= 28):
            sentence_hits = check_sentence_matches(body_text, web_matches)

        risk = _risk_level(cov, fuzzy, bool(internal))
        if risk in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            flagged_high += 1
        risk_summary[risk.value] += 1

        words = _word_count(para.text)
        matched_words = 0
        if web_matches:
            matched_words = max(
                count_matching_words(body_text, m.snippet) for m in web_matches[:5]
            )
        for chunk in internal:
            matched_words = max(matched_words, count_matching_words(body_text, chunk))
        plagiarized_words += matched_words

        if web_matches and fuzzy >= 25:
            ieee_estimate_words += words * (fuzzy / 100.0) * IEEE_ESTIMATE_WEIGHT
        elif internal:
            ieee_estimate_words += words * 0.12

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
                similarity=display_sim,
                risk=risk,
                sources=web_matches,
                internal_duplicates=internal,
                suggestions=suggestions,
                section=para.section,
                coverage_percent=cov,
                fuzzy_similarity=fuzzy,
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

    # Turnitin-style: matched word runs (>=8 words) / total document words (excluding skipped).
    if total_words > 0:
        plagiarism_pct = min(100.0, (plagiarized_words / total_words) * 100)
    else:
        plagiarism_pct = 0.0

    plagiarism_pct = round(plagiarism_pct, 1)
    originality_pct = round(100.0 - plagiarism_pct, 1)

    ieee_estimate = round(min(100.0, (ieee_estimate_words / max(total_words, 1)) * 100), 1)
    compliance_note = _ieee_compliance_note(ieee_estimate, plagiarism_pct, flagged_high)

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
        ieee_estimate_percent=ieee_estimate,
        ieee_compliance_note=compliance_note,
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
