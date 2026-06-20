"""
IEEE Plagiarism Checker — Streamlit UI
Kiểm tra đạo văn toàn diện cho bài báo khoa học (.docx)
"""

from __future__ import annotations

import html
import json
import tempfile
from pathlib import Path

import streamlit as st

from checker.analyzer import analyze_document
from checker.export_docx import COPYRIGHT, export_report_docx
from checker.extractor import extract_paragraphs
from checker.fix_docx import generate_fixed_docx
from checker.models import RiskLevel
from ui.icons import icon_label, svg_icon
from ui.theme import CUSTOM_CSS, hero_html, section_heading, sidebar_brand_html

_ICON = Path(__file__).parent / "assets" / "icon.svg"

st.set_page_config(
    page_title="IEEE Plagiarism Checker",
    page_icon=str(_ICON) if _ICON.exists() else None,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def risk_badge(risk: RiskLevel) -> str:
    cls = f"risk-{risk.value}"
    labels = {
        RiskLevel.LOW: "Safe",
        RiskLevel.MEDIUM: "Review",
        RiskLevel.HIGH: "High",
        RiskLevel.CRITICAL: "Critical",
    }
    return f'<span class="risk-badge {cls}">{labels.get(risk, risk.value)}</span>'


def render_header():
    st.markdown(
        hero_html(
            "Comprehensive plagiarism analysis for IEEE papers — web matching, "
            "duplicate detection, paraphrase suggestions, and Mendeley-safe auto-fix.",
            COPYRIGHT,
        ),
        unsafe_allow_html=True,
    )


def render_score_cards(report):
    cols = st.columns(4)
    cards = [
        ("shield", "icon-success", "gauge-originality", f"{report.originality_percent}%", "Originality"),
        ("percent", "icon-danger", "gauge-plagiarism", f"{report.plagiarism_percent}%", "Similarity (coverage)"),
        ("layers", "icon-accent", "gauge-analyzed", str(report.analyzed_paragraphs), "Paragraphs scanned"),
        ("clock", "icon-purple", "gauge-time", f"{report.duration_seconds}s", "Scan duration"),
    ]
    for col, (icon_name, icon_cls, val_cls, val, label) in zip(cols, cards):
        with col:
            st.markdown(
                f"""
                <div class="score-card">
                    <div class="score-card-top">
                        <div class="score-icon {icon_cls}">{svg_icon(icon_name, 20)}</div>
                    </div>
                    <div class="score-value {val_cls}">{val}</div>
                    <div class="score-label">{label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_risk_summary(report):
    st.markdown(section_heading("chart", "Risk distribution"), unsafe_allow_html=True)
    cols = st.columns(4)
    levels = [
        (RiskLevel.LOW, "Safe"),
        (RiskLevel.MEDIUM, "Review"),
        (RiskLevel.HIGH, "High"),
        (RiskLevel.CRITICAL, "Critical"),
    ]
    for col, (level, label) in zip(cols, levels):
        count = report.risk_summary.get(level.value, 0)
        with col:
            st.metric(label, count)


def render_paragraph(p: "ParagraphResult", show_all: bool = False):
    if p.similarity == 0 and p.risk == RiskLevel.LOW and not show_all:
        if "Bỏ qua" in (p.suggestions[0] if p.suggestions else ""):
            return

    risk_cls = f"risk-{p.risk.value}"
    sim_color = (
        "#059669"
        if p.similarity < 20
        else "#d97706"
        if p.similarity < 35
        else "#dc2626"
        if p.similarity < 60
        else "#b91c1c"
    )
    safe_text = html.escape(p.text[:1200]) + ("…" if len(p.text) > 1200 else "")

    st.markdown(
        f"""
        <div class="para-card {risk_cls}">
            <div class="para-meta">
                <strong>Paragraph #{p.index}</strong>
                <span>{html.escape(p.section)}</span>
                <span>{p.word_count} words</span>
                <span style="color:{sim_color}; font-weight:600;">{p.similarity}% match</span>
                {risk_badge(p.risk)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander(
        f"Details — Paragraph #{p.index} · {p.section}",
        expanded=p.risk in (RiskLevel.HIGH, RiskLevel.CRITICAL),
    ):
        st.markdown(f'<div class="para-text">{safe_text}</div>', unsafe_allow_html=True)

        if p.sources:
            st.markdown(
                f"**{icon_label('link', 'Potential matching sources', 16)}**",
                unsafe_allow_html=True,
            )
            for src in p.sources[:3]:
                st.markdown(
                    f"- **{html.escape(src.title)}** ({src.similarity}%)  \n"
                    f"  <span class='source-link'>{html.escape(src.url or 'N/A')}</span>  \n"
                    f"  _{html.escape(src.snippet[:200])}…_",
                    unsafe_allow_html=True,
                )
                if src.matched_text:
                    st.code(src.matched_text[:250], language=None)

        if p.internal_duplicates:
            st.warning("Internal duplication: " + "; ".join(p.internal_duplicates[:2]))

        if p.suggestions:
            st.markdown(
                f"**{icon_label('sparkles', 'Revision suggestions', 16)}**",
                unsafe_allow_html=True,
            )
            for s in p.suggestions:
                st.markdown(
                    f'<div class="suggestion">{html.escape(s)}</div>',
                    unsafe_allow_html=True,
                )


def export_report_json(report) -> bytes:
    data = {
        "filename": report.filename,
        "plagiarism_percent": report.plagiarism_percent,
        "originality_percent": report.originality_percent,
        "analyzed_paragraphs": report.analyzed_paragraphs,
        "duration_seconds": report.duration_seconds,
        "risk_summary": report.risk_summary,
        "paragraphs": [
            {
                "index": p.index,
                "section": p.section,
                "similarity": p.similarity,
                "risk": p.risk.value,
                "text_preview": p.text[:300],
                "suggestions": p.suggestions,
                "sources": [
                    {"title": s.title, "url": s.url, "similarity": s.similarity}
                    for s in p.sources
                ],
            }
            for p in report.paragraphs
            if p.similarity > 0
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")


def render_getting_started():
    st.markdown(section_heading("info", "Getting started"), unsafe_allow_html=True)
    st.markdown(
        """
        <div class="steps-grid">
            <div class="step-card">
                <div class="step-num">1</div>
                <h4>Upload document</h4>
                <p>Upload your <code>.docx</code> file in the sidebar, or use the default file if present.</p>
            </div>
            <div class="step-card">
                <div class="step-num">2</div>
                <h4>Configure scan</h4>
                <p>Choose scan depth and risk filter, then run the plagiarism analysis.</p>
            </div>
            <div class="step-card">
                <div class="step-num">3</div>
                <h4>Review & export</h4>
                <p>Download Word/JSON reports or auto-fix flagged sections while preserving Mendeley citations.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main():
    render_header()

    with st.sidebar:
        st.markdown(sidebar_brand_html(), unsafe_allow_html=True)
        st.markdown(
            f"**{icon_label('settings', 'Scan configuration', 16)}**",
            unsafe_allow_html=True,
        )
        default_path = Path(__file__).parent / "HTTL-NEW.docx"
        uploaded = st.file_uploader("Upload .docx file", type=["docx"])
        scan_mode = st.selectbox(
            "Scan mode",
            ["quick", "standard", "thorough"],
            index=1,
            format_func=lambda x: {
                "quick": "Quick (~2 min)",
                "standard": "Standard (~5 min)",
                "thorough": "Thorough (~10 min)",
            }[x],
        )
        min_risk = st.selectbox(
            "Display filter",
            ["all", "medium+", "high+"],
            index=1,
            format_func=lambda x: {
                "all": "All paragraphs",
                "medium+": "Review and above",
                "high+": "High risk only",
            }[x],
        )
        run_scan = st.button("Start plagiarism scan", type="primary")
        auto_fix = st.button(
            "Auto-fix plagiarism",
            help="Light paraphrase for medium/high-risk paragraphs. Mendeley citation fields [1], [2]… are preserved.",
        )

        st.markdown("---")
        st.caption(
          "Kiểm tra đạo văn toàn diện cho bài báo khoa học"
        )
        st.caption(f"© {COPYRIGHT}")

    if "report" not in st.session_state:
        st.session_state.report = None
    if "doc_path" not in st.session_state:
        st.session_state.doc_path = None
    if "fixed_docx" not in st.session_state:
        st.session_state.fixed_docx = None
    if "fix_stats" not in st.session_state:
        st.session_state.fix_stats = None

    if uploaded:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
        tmp.write(uploaded.read())
        tmp.close()
        doc_path = tmp.name
        filename = uploaded.name
        st.session_state.doc_path = doc_path
    elif default_path.exists():
        doc_path = str(default_path)
        filename = default_path.name
        st.session_state.doc_path = doc_path
        st.info(f"Using default file: **{default_path.name}** — upload another file in the sidebar.")
    else:
        st.session_state.doc_path = None

    doc_path = st.session_state.doc_path

    if run_scan and doc_path:
        paragraphs = extract_paragraphs(doc_path)
        progress = st.progress(0, text="Initializing scan…")
        status = st.empty()

        def on_progress(current, total, preview):
            pct = current / total
            progress.progress(pct, text=f"Scanning paragraph {current}/{total}…")
            status.caption(f"{preview[:72]}…")

        with st.spinner("Analyzing document — please wait…"):
            report = analyze_document(
                paragraphs,
                filename,
                scan_mode=scan_mode,
                progress_callback=on_progress,
            )
        st.session_state.report = report
        st.session_state.fixed_docx = None
        st.session_state.fix_stats = None
        progress.empty()
        status.empty()
        st.success(
            f"Scan complete — {report.analyzed_paragraphs} paragraphs analyzed in {report.duration_seconds}s."
        )

    if auto_fix and st.session_state.report and st.session_state.doc_path:
        with st.spinner("Paraphrasing while preserving Mendeley citations…"):
            fixed_bytes, stats = generate_fixed_docx(
                st.session_state.doc_path,
                st.session_state.report,
                min_similarity=45.0,
            )
        st.session_state.fixed_docx = fixed_bytes
        st.session_state.fix_stats = stats
        failed = getattr(stats, "paragraphs_failed", 0)
        st.success(
            f"Fixed **{stats.paragraphs_modified}** paragraphs · "
            f"Unchanged **{stats.paragraphs_unchanged}** · "
            f"Skipped/failed **{stats.paragraphs_skipped + failed}**"
        )
        if failed:
            st.warning(
                "Some paragraphs were skipped to protect Mendeley citations — original text kept."
            )
    elif auto_fix and not st.session_state.report:
        st.warning("Run a plagiarism scan before using auto-fix.")

    report = st.session_state.report
    if report:
        render_score_cards(report)
        st.markdown("---")
        render_risk_summary(report)

        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            st.markdown(section_heading("list", "Detailed results"), unsafe_allow_html=True)
        with col2:
            if st.session_state.fixed_docx:
                st.download_button(
                    "Download fixed .docx",
                    data=st.session_state.fixed_docx,
                    file_name=f"fixed_{Path(report.filename).stem}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    help="Red text = paraphrased sections; Mendeley citations unchanged",
                    type="primary",
                )
            else:
                st.caption("Use **Auto-fix plagiarism** in the sidebar to generate a revised document.")
        with col3:
            st.download_button(
                "Download report (.docx)",
                data=export_report_docx(report, min_risk=min_risk),
                file_name=f"plagiarism_report_{Path(report.filename).stem}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                help="Word report with errors and revision suggestions",
            )
        with col4:
            st.download_button(
                "Export JSON",
                data=export_report_json(report),
                file_name=f"plagiarism_report_{report.filename}.json",
                mime="application/json",
            )

        if st.session_state.fix_stats:
            fs = st.session_state.fix_stats
            st.info(
                f"**Auto-fixed document:** {fs.paragraphs_modified} paragraphs paraphrased "
                f"(changes highlighted in **red**). Mendeley/IEEE citations `[n]` preserved. "
                f"Modified: {', '.join(f'#{i}' for i in fs.modified_indices[:20])}"
                f"{'…' if len(fs.modified_indices) > 20 else ''}"
            )

        risk_order = {
            "high+": [RiskLevel.HIGH, RiskLevel.CRITICAL],
            "medium+": [RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL],
            "all": list(RiskLevel),
        }
        allowed = risk_order.get(min_risk, list(RiskLevel))

        flagged = [
            p
            for p in report.paragraphs
            if p.risk in allowed and (p.similarity > 0 or p.risk != RiskLevel.LOW)
        ]
        flagged.sort(key=lambda p: (-p.similarity, p.index))

        if not flagged:
            st.success("No paragraphs with significant risk at the current filter level.")
        else:
            for p in flagged:
                render_paragraph(p)

        with st.expander("How to read results"):
            st.markdown(
                """
                | Level | Meaning | Action |
                |-------|---------|--------|
                | **Safe** (< 20%) | Common terminology or original phrasing | Keep; verify citations |
                | **Review** (20–34%) | Similar phrases on public web | Light paraphrase; check citations |
                | **High** (35–59%) | Likely substantial overlap | Rewrite paragraph; add IEEE citation |
                | **Critical** (≥ 60%) | Strong match with web sources | Full paraphrase required |

                **How similarity % is calculated (Turnitin-style):** only contiguous runs of **8+ matching words** count toward the document score — not the whole paragraph × fuzzy match. References and bibliography are excluded.

                **Note:** This tool searches the public web via DuckDuckGo; Turnitin uses a proprietary paper database. Scores will not match exactly, but the method is now closer to Turnitin's coverage model.
                """
            )
    elif not run_scan:
        render_getting_started()


if __name__ == "__main__":
    main()
