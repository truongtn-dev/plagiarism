from __future__ import annotations

import re
from difflib import SequenceMatcher

from checker.models import SourceMatch


SYNONYM_HINTS = {
    "significantly": "considerably, substantially, markedly",
    "demonstrates": "shows, reveals, indicates",
    "examines": "investigates, explores, analyzes",
    "impact": "effect, influence, outcome",
    "rapid": "swift, fast-paced, accelerated",
    "transforming": "reshaping, changing, revolutionizing",
    "widely recognized": "commonly acknowledged, broadly accepted",
    "key driver": "primary catalyst, main engine",
    "play a central role": "serve as a cornerstone, act as a pivotal force",
    "despite its": "although its, even with its",
    "challenges": "difficulties, obstacles, hurdles",
    "emergence": "rise, advent, appearance",
    "empirically": "through data, via measurement, using evidence",
    "findings suggest": "results indicate, data imply, outcomes show",
    "in conclusion": "to summarize, overall, in sum",
}


def _find_repeated_phrases(text: str, min_len: int = 30) -> list[str]:
    from collections import Counter

    words = text.split()
    phrases: list[str] = []
    for n in range(5, 12):
        for i in range(len(words) - n):
            phrase = " ".join(words[i : i + n])
            if len(phrase) >= min_len:
                phrases.append(phrase.lower())
    counts = Counter(phrases)
    return [p for p, c in counts.items() if c > 1][:3]


def _suggest_paraphrase(original: str, matched: str) -> str:
    if not matched:
        return "Diễn đạt lại câu bằng cấu trúc chủ động/bị động khác và từ vựng đồng nghĩa."

    words = matched.lower().split()
    hints = []
    for w in words:
        if w in SYNONYM_HINTS:
            hints.append(f"Thay '{w}' → {SYNONYM_HINTS[w]}")
    if hints:
        return "; ".join(hints[:3])

    sm = SequenceMatcher(None, original.lower(), matched.lower())
    blocks = sm.get_matching_blocks()
    longest = max(blocks, key=lambda b: b.size, default=None)
    if longest and longest.size > 15:
        frag = original[longest.a : longest.a + longest.size]
        return (
            f"Đoạn trùng khớp: «{frag[:120]}…». "
            "Hãy chia nhỏ câu, đảo thứ tự mệnh đề, thay thuật ngữ bằng định nghĩa riêng của bạn."
        )
    return "Viết lại bằng giọng văn phân tích của riêng bạn; trích dẫn nguồn nếu dùng định nghĩa chuẩn."


def build_suggestions(
    text: str,
    web_matches: list[SourceMatch],
    internal_duplicates: list[str],
    sentence_hits: list[SourceMatch],
    matched_fragment: str,
) -> list[str]:
    suggestions: list[str] = []

    if not web_matches and not internal_duplicates:
        suggestions.append(
            "✓ No significant overlap with public web sources (citations [n] excluded from matching)."
        )
        return suggestions

    if web_matches:
        top = web_matches[0]
        if top.similarity >= 70:
            suggestions.append(
                f"⚠ Mức độ nghi ngờ cao ({top.similarity}%): nội dung gần với «{top.title[:80]}…». "
                "Cần paraphrase mạnh và thêm trích dẫn IEEE."
            )
        elif top.similarity >= 45:
            suggestions.append(
                f"⚡ Trùng lặp trung bình ({top.similarity}%) với «{top.title[:80]}…». "
                "Kiểm tra lại cách diễn đạt và bổ sung citation."
            )
        else:
            suggestions.append(
                f"ℹ Cụm từ tương tự ({top.similarity}%) — có thể là thuật ngữ chung ngành; "
                "xác nhận đã trích dẫn nếu là định nghĩa chuẩn."
            )

        if matched_fragment:
            suggestions.append(_suggest_paraphrase(text, matched_fragment))

        if top.url:
            suggestions.append(f"Nguồn tham khảo cần kiểm tra: {top.url}")

    for hit in sentence_hits[:2]:
        suggestions.append(
            f"Câu nghi ngờ ({hit.similarity}%): «{hit.snippet[:100]}…» → "
            + _suggest_paraphrase(hit.snippet, hit.matched_text)
        )

    for dup in internal_duplicates:
        suggestions.append(
            f"Trùng lặp nội bộ trong bài: «{dup[:100]}…» — gộp ý hoặc diễn đạt khác ở lần xuất hiện thứ hai."
        )

    citations = re.findall(r"\[\d+\]", text)
    if citations and web_matches and web_matches[0].similarity >= 50:
        suggestions.append(
            f"Đã có trích dẫn {', '.join(set(citations))} — đảm bảo citation khớp nguồn và không copy nguyên văn abstract nguồn."
        )
    elif web_matches and web_matches[0].similarity >= 55 and not citations:
        suggestions.append("Thiếu trích dẫn [n] cho đoạn có nội dung tương đồng — bổ sung theo chuẩn IEEE.")

    if re.search(r"business model canvas|osterwalder", text, re.I):
        suggestions.append(
            "Thuật ngữ BMC/Osterwalder là kiến thức nền — nên trích dẫn [5] và diễn giải bằng ngôn ngữ riêng, tránh copy mô tả từ Wikipedia/template."
        )

    return suggestions
