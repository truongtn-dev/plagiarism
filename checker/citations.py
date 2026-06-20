from __future__ import annotations

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from docx.shared import RGBColor
from docx.text.paragraph import Paragraph
from docx.text.run import Run

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = "{%s}" % W_NS

PLACEHOLDER_RE = re.compile(r"\uE000(\d+)\uE001")
CITATION_LEAK_RE = re.compile(r"ADDIN CSL_CITATION|citationItems", re.I)


@dataclass
class TextPart:
    text: str
    runs: list = field(default_factory=list)


@dataclass
class FieldPart:
    elements: list = field(default_factory=list)
    display: str = ""


Part = TextPart | FieldPart


def _run_is_citation_field(run: Run) -> bool:
    el = run._element
    if el.find(f".//{W}instrText") is not None:
        return True
    if el.find(f".//{W}fldChar") is not None:
        return True
    return False


def segment_runs(paragraph: Paragraph) -> list[tuple[str, list[Run]]]:
    """Group consecutive runs into ('text', runs) or ('field', runs)."""
    segments: list[tuple[str, list[Run]]] = []
    buf: list[Run] = []
    buf_type: str | None = None

    for run in paragraph.runs:
        rtype = "field" if _run_is_citation_field(run) else "text"
        if buf_type is None:
            buf_type = rtype
            buf = [run]
        elif rtype == buf_type:
            buf.append(run)
        else:
            segments.append((buf_type, buf))
            buf_type = rtype
            buf = [run]
    if buf:
        segments.append((buf_type, buf))
    return segments


def extract_parts(paragraph: Paragraph) -> list[Part]:
    parts: list[Part] = []
    for seg_type, runs in segment_runs(paragraph):
        if seg_type == "text":
            parts.append(TextPart("".join(r.text or "" for r in runs), runs=list(runs)))
        else:
            parts.append(
                FieldPart(
                    elements=[r._element for r in runs],
                    display="".join(r.text or "" for r in runs),
                )
            )
    return parts


def parts_with_placeholders(parts: list[Part]) -> tuple[str, list[FieldPart]]:
    fields: list[FieldPart] = []
    chunks: list[str] = []
    field_idx = 0
    for part in parts:
        if isinstance(part, TextPart):
            chunks.append(part.text)
        else:
            token = f"\uE000{field_idx}\uE001"
            fields.append(part)
            chunks.append(token)
            field_idx += 1
    return "".join(chunks), fields


def _split_by_placeholders(text: str) -> list[tuple[str, int | None]]:
    segments: list[tuple[str, int | None]] = []
    pos = 0
    for m in PLACEHOLDER_RE.finditer(text):
        if m.start() > pos:
            segments.append((text[pos : m.start()], None))
        segments.append(("", int(m.group(1))))
        pos = m.end()
    if pos < len(text):
        segments.append((text[pos:], None))
    if not segments and text:
        segments.append((text, None))
    return segments


def _set_run_text(run: Run, text: str, red: bool = False):
    run.text = text
    if red:
        run.font.color.rgb = RGBColor(0xFF, 0x00, 0x00)


def _apply_text_to_runs(runs: list[Run], old: str, new: str, highlight: bool):
    if not runs:
        return
    if not new:
        for r in runs:
            _set_run_text(r, "")
        return

    if not highlight or old == new:
        _set_run_text(runs[0], new)
        for r in runs[1:]:
            _set_run_text(r, "")
        return

    sm = SequenceMatcher(None, old, new)
    combined = []
    for tag, _i1, _i2, j1, j2 in sm.get_opcodes():
        part = new[j1:j2]
        if part:
            combined.append((part, tag != "equal"))

    # Write chunk-by-chunk into available runs; overflow goes in last run
    if len(combined) <= len(runs):
        for i, (txt, is_red) in enumerate(combined):
            _set_run_text(runs[i], txt, red=is_red)
        for r in runs[len(combined) :]:
            _set_run_text(r, "")
    else:
        pos = 0
        for i, r in enumerate(runs):
            if i < len(runs) - 1 and pos < len(combined):
                txt, is_red = combined[pos]
                _set_run_text(r, txt, red=is_red)
                pos += 1
            elif i == len(runs) - 1:
                rest = "".join(t for t, _ in combined[pos:])
                any_red = any(red for _, red in combined[pos:])
                _set_run_text(r, rest, red=any_red)
            else:
                _set_run_text(r, "")


def apply_paraphrase_in_place(
    paragraph: Paragraph,
    new_plain: str,
    original_plain: str,
    highlight_changes: bool = True,
) -> bool:
    """
    Update only non-field runs; Mendeley field runs are never touched.
    Returns False if update would corrupt citations.
    """
    if CITATION_LEAK_RE.search(new_plain):
        return False

    segments = segment_runs(paragraph)
    orig_parts = _split_by_placeholders(original_plain)
    new_parts = _split_by_placeholders(new_plain)

    if len(orig_parts) != len(new_parts):
        return False
    if PLACEHOLDER_RE.findall(original_plain) != PLACEHOLDER_RE.findall(new_plain):
        return False

    text_seg_i = 0
    for (orig_text, o_field), (new_text, n_field) in zip(orig_parts, new_parts):
        if o_field is not None:
            continue
        while text_seg_i < len(segments) and segments[text_seg_i][0] != "text":
            text_seg_i += 1
        if text_seg_i >= len(segments):
            return False
        _, runs = segments[text_seg_i]
        _apply_text_to_runs(runs, orig_text, new_text, highlight_changes)
        text_seg_i += 1

    if CITATION_LEAK_RE.search(paragraph.text):
        return False
    return True


def rebuild_from_plain(
    paragraph: Paragraph,
    new_plain: str,
    fields: list[FieldPart],
    original_plain: str | None = None,
    highlight_changes: bool = True,
) -> bool:
    return apply_paraphrase_in_place(
        paragraph,
        new_plain,
        original_plain or "",
        highlight_changes,
    )
