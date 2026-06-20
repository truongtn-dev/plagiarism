from __future__ import annotations

import re
import time
from difflib import SequenceMatcher

from ddgs import DDGS
from rapidfuzz import fuzz

from checker.models import SourceMatch


COMMON_PHRASES = {
    "business model canvas",
    "artificial intelligence",
    "entrepreneurship education",
    "experiential learning",
    "higher education",
    "innovation capability",
    "venture growth",
    "economic growth",
    "literature review",
    "research methodology",
    "statistical analysis",
    "machine learning",
    "deep learning",
    "open source",
    "peer review",
}


def _clean(text: str) -> str:
    text = re.sub(r"\[\d+\]", "", text)
    text = re.sub(r"[^\w\s'-]", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def _extract_search_query(text: str, max_len: int = 120) -> str:
    cleaned = re.sub(r"\[\d+\]", "", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    best = max(sentences, key=len) if sentences else cleaned
    if len(best) > max_len:
        words = best.split()
        chunk = []
        length = 0
        for w in words:
            if length + len(w) > max_len:
                break
            chunk.append(w)
            length += len(w) + 1
        best = " ".join(chunk)
    return best


def _search_web(query: str, max_results: int = 5) -> list[dict]:
    try:
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=max_results))
    except Exception:
        time.sleep(1.2)
        try:
            with DDGS() as ddgs:
                return list(ddgs.text(query, max_results=max_results))
        except Exception:
            return []


def _longest_common_substring(a: str, b: str, min_len: int = 25) -> str:
    sm = SequenceMatcher(None, a.lower(), b.lower())
    match = sm.find_longest_match(0, len(a), 0, len(b))
    if match.size >= min_len:
        return a[match.a : match.a + match.size]
    return ""


def compare_texts(source: str, target: str) -> tuple[float, str]:
    src = _clean(source)
    tgt = _clean(target)
    if not src or not tgt:
        return 0.0, ""

    token_score = fuzz.token_set_ratio(src, tgt)
    partial_score = fuzz.partial_ratio(src, tgt)
    ratio_score = fuzz.ratio(src[:2000], tgt[:2000])

    score = max(token_score, partial_score * 0.85, ratio_score * 0.9)
    matched = _longest_common_substring(source, target)
    return round(min(score, 100.0), 1), matched


def check_paragraph_against_web(
    text: str,
    max_results: int = 5,
    delay: float = 0.35,
) -> list[SourceMatch]:
    query = _extract_search_query(text)
    if len(query.split()) < 6:
        return []

    results = _search_web(query, max_results=max_results)
    time.sleep(delay)

    matches: list[SourceMatch] = []
    for item in results:
        body = item.get("body") or item.get("snippet") or ""
        title = item.get("title") or "Unknown source"
        url = item.get("href") or item.get("link") or ""
        if not body:
            continue

        sim, matched = compare_texts(text, body)
        if sim >= 28:
            matches.append(
                SourceMatch(
                    title=title[:200],
                    url=url,
                    snippet=body[:400],
                    similarity=sim,
                    matched_text=matched[:300],
                )
            )

    matches.sort(key=lambda m: m.similarity, reverse=True)
    return matches[:5]


def check_sentence_matches(text: str, sources: list[SourceMatch]) -> list[SourceMatch]:
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z\"'])", text)
    sentence_matches: list[SourceMatch] = []

    for sent in sentences:
        if len(sent.strip()) < 30:
            continue
        for src in sources:
            sim, matched = compare_texts(sent, src.snippet)
            if sim >= 55 and matched:
                sentence_matches.append(
                    SourceMatch(
                        title=src.title,
                        url=src.url,
                        snippet=sent[:300],
                        similarity=sim,
                        matched_text=matched[:200],
                    )
                )
    return sentence_matches


def detect_internal_overlap(paragraphs: list[str], current: str) -> list[str]:
    current_clean = _clean(current)
    overlaps: list[str] = []
    if len(current_clean) < 50:
        return overlaps

    for other in paragraphs:
        if other == current:
            continue
        other_clean = _clean(other)
        matched = _longest_common_substring(current, other, min_len=40)
        if matched and fuzz.partial_ratio(current_clean, other_clean) >= 70:
            overlaps.append(matched[:180])
    return overlaps[:3]
