"""
IEEE Plagiarism Checker — Streamlit UI
Kiểm tra đạo văn toàn diện cho bài báo khoa học (.docx)
"""

from __future__ import annotations

import io
import json
import tempfile
from pathlib import Path

import streamlit as st

from checker.analyzer import analyze_document
from checker.export_docx import COPYRIGHT, export_report_docx
from checker.extractor import extract_paragraphs
from checker.fix_docx import generate_fixed_docx
from checker.models import RiskLevel

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IEEE Plagiarism Checker",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg: #0f1419;
    --surface: #1a2332;
    --surface2: #243044;
    --border: #2d3a4f;
    --text: #e8edf4;
    --muted: #8b9cb3;
    --accent: #3b82f6;
    --accent-glow: rgba(59, 130, 246, 0.25);
    --success: #22c55e;
    --warning: #f59e0b;
    --danger: #ef4444;
    --critical: #dc2626;
}

.stApp {
    background: linear-gradient(160deg, #0a0e14 0%, #0f1419 40%, #121820 100%);
    font-family: 'DM Sans', sans-serif;
    color: var(--text);
}

header[data-testid="stHeader"] { background: transparent; }

.main-header {
    text-align: center;
    padding: 2rem 0 1.5rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 2rem;
}
.main-header h1 {
    font-size: 2.2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #60a5fa, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.4rem;
}
.main-header p {
    color: var(--muted);
    font-size: 1.05rem;
}

.score-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.5rem;
    text-align: center;
    box-shadow: 0 4px 24px rgba(0,0,0,0.3);
    transition: transform 0.2s;
}
.score-card:hover { transform: translateY(-2px); }
.score-value {
    font-size: 3rem;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    line-height: 1;
}
.score-label {
    color: var(--muted);
    font-size: 0.9rem;
    margin-top: 0.5rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

.gauge-originality { color: var(--success); }
.gauge-plagiarism { color: var(--danger); }
.gauge-analyzed { color: var(--accent); }
.gauge-time { color: #a78bfa; }

.risk-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.risk-low { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
.risk-medium { background: rgba(245,158,11,0.15); color: #fbbf24; border: 1px solid rgba(245,158,11,0.3); }
.risk-high { background: rgba(239,68,68,0.15); color: #f87171; border: 1px solid rgba(239,68,68,0.3); }
.risk-critical { background: rgba(220,38,38,0.2); color: #fca5a5; border: 1px solid rgba(220,38,38,0.4); }

.para-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 4px solid var(--accent);
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
}
.para-card.risk-medium { border-left-color: var(--warning); }
.para-card.risk-high { border-left-color: var(--danger); }
.para-card.risk-critical { border-left-color: var(--critical); }
.para-card.risk-low { border-left-color: var(--success); }

.para-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
    align-items: center;
    margin-bottom: 0.75rem;
    font-size: 0.85rem;
    color: var(--muted);
}
.para-text {
    font-size: 0.95rem;
    line-height: 1.65;
    color: #c9d6e8;
    margin: 0.75rem 0;
    padding: 1rem;
    background: var(--surface2);
    border-radius: 8px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    max-height: 200px;
    overflow-y: auto;
}
.suggestion {
    background: rgba(59,130,246,0.08);
    border-left: 3px solid var(--accent);
    padding: 0.6rem 1rem;
    margin: 0.4rem 0;
    border-radius: 0 8px 8px 0;
    font-size: 0.88rem;
    line-height: 1.5;
}
.source-link {
    color: #60a5fa;
    font-size: 0.85rem;
    word-break: break-all;
}

div[data-testid="stSidebar"] {
    background: var(--surface);
    border-right: 1px solid var(--border);
}
.stButton > button {
    background: linear-gradient(135deg, #3b82f6, #6366f1);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 0.65rem 1.5rem;
    font-weight: 600;
    width: 100%;
    transition: box-shadow 0.2s;
}
.stButton > button:hover {
    box-shadow: 0 0 20px var(--accent-glow);
}

.stProgress > div > div {
    background: linear-gradient(90deg, #3b82f6, #8b5cf6);
}

.filter-pills { margin: 1rem 0; }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def risk_badge(risk: RiskLevel) -> str:
    cls = f"risk-{risk.value}"
    labels = {
        RiskLevel.LOW: "An toàn",
        RiskLevel.MEDIUM: "Theo dõi",
        RiskLevel.HIGH: "Cao",
        RiskLevel.CRITICAL: "Nghiêm trọng",
    }
    return f'<span class="risk-badge {cls}">{labels.get(risk, risk.value)}</span>'


def render_header():
    st.markdown(
        f"""
        <div class="main-header">
            <h1>🔍 IEEE Plagiarism Checker</h1>
            <p>Kiểm tra đạo văn toàn diện · So khớp web · Phát hiện trùng lặp · Gợi ý paraphrase cho bài IEEE</p>
            <p style="font-size:0.85rem;color:#64748b;margin-top:0.75rem;font-style:italic;">© {COPYRIGHT}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_score_cards(report):
    cols = st.columns(4)
    cards = [
        ("gauge-originality", f"{report.originality_percent}%", "Độ nguyên bản"),
        ("gauge-plagiarism", f"{report.plagiarism_percent}%", "Đạo văn ước tính"),
        ("gauge-analyzed", str(report.analyzed_paragraphs), "Đoạn đã quét"),
        ("gauge-time", f"{report.duration_seconds}s", "Thời gian quét"),
    ]
    for col, (css, val, label) in zip(cols, cards):
        with col:
            st.markdown(
                f"""
                <div class="score-card">
                    <div class="score-value {css}">{val}</div>
                    <div class="score-label">{label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_risk_summary(report):
    st.subheader("📊 Phân bố mức rủi ro")
    cols = st.columns(4)
    levels = [
        (RiskLevel.LOW, "An toàn", "#22c55e"),
        (RiskLevel.MEDIUM, "Theo dõi", "#f59e0b"),
        (RiskLevel.HIGH, "Cao", "#ef4444"),
        (RiskLevel.CRITICAL, "Nghiêm trọng", "#dc2626"),
    ]
    for col, (level, label, color) in zip(cols, levels):
        count = report.risk_summary.get(level.value, 0)
        with col:
            st.metric(label, count)


def render_paragraph(p: "ParagraphResult", show_all: bool = False):
    if p.similarity == 0 and p.risk == RiskLevel.LOW and not show_all:
        if "Bỏ qua" in (p.suggestions[0] if p.suggestions else ""):
            return

    risk_cls = f"risk-{p.risk.value}"
    sim_color = (
        "#22c55e"
        if p.similarity < 38
        else "#f59e0b"
        if p.similarity < 55
        else "#ef4444"
        if p.similarity < 75
        else "#dc2626"
    )

    with st.container():
        st.markdown(
            f"""
            <div class="para-card {risk_cls}">
                <div class="para-meta">
                    <strong>Đoạn #{p.index}</strong>
                    <span>· {p.section}</span>
                    <span>· {p.word_count} từ</span>
                    <span style="color:{sim_color}; font-weight:600;">{p.similarity}% trùng khớp</span>
                    {risk_badge(p.risk)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander(f"Xem chi tiết đoạn #{p.index} — {p.section}", expanded=p.risk in (RiskLevel.HIGH, RiskLevel.CRITICAL)):
            st.markdown(f'<div class="para-text">{p.text[:1200]}{"…" if len(p.text)>1200 else ""}</div>', unsafe_allow_html=True)

            if p.sources:
                st.markdown("**🔗 Nguồn trùng khớp tiềm ẩn:**")
                for src in p.sources[:3]:
                    st.markdown(
                        f"- **{src.title}** ({src.similarity}%)  \n"
                        f"  <span class='source-link'>{src.url or 'N/A'}</span>  \n"
                        f"  _{src.snippet[:200]}…_",
                        unsafe_allow_html=True,
                    )
                    if src.matched_text:
                        st.code(src.matched_text[:250], language=None)

            if p.internal_duplicates:
                st.warning("Trùng lặp nội bộ: " + "; ".join(p.internal_duplicates[:2]))

            if p.suggestions:
                st.markdown("**💡 Gợi ý sửa đổi:**")
                for s in p.suggestions:
                    st.markdown(f'<div class="suggestion">{s}</div>', unsafe_allow_html=True)


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


def main():
    render_header()

    with st.sidebar:
        st.header("⚙️ Cấu hình quét")
        default_path = Path(__file__).parent / "HTTL-NEW.docx"
        uploaded = st.file_uploader("Tải file .docx", type=["docx"])
        scan_mode = st.selectbox(
            "Chế độ quét",
            ["quick", "standard", "thorough"],
            index=1,
            format_func=lambda x: {
                "quick": "⚡ Nhanh (~2 phút)",
                "standard": "🔍 Chuẩn (~5 phút)",
                "thorough": "🔬 Kỹ lưỡng (~10 phút)",
            }[x],
        )
        min_risk = st.selectbox(
            "Lọc hiển thị",
            ["all", "medium+", "high+"],
            index=1,
            format_func=lambda x: {
                "all": "Tất cả đoạn",
                "medium+": "Theo dõi trở lên",
                "high+": "Chỉ rủi ro cao",
            }[x],
        )
        run_scan = st.button("🚀 Bắt đầu kiểm tra đạo văn", type="primary")
        auto_fix = st.button(
            "✏️ Tự động sửa đạo văn",
            help="Paraphrase nhẹ các đoạn rủi ro trung bình/cao. Giữ nguyên field citation Mendeley — không đụng [1],[2]…",
        )

        st.markdown("---")
        st.caption(
            "Tool so khớp với nguồn web công khai (DuckDuckGo). "
            "Kết quả mang tính tham khảo — nên dùng thêm Turnitin/iThenticate trước khi nộp IEEE."
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
        st.info(f"📄 Sử dụng file mặc định: **{default_path.name}** (tải file khác ở sidebar)")
    else:
        st.session_state.doc_path = None

    doc_path = st.session_state.doc_path

    if run_scan and doc_path:
        paragraphs = extract_paragraphs(doc_path)
        progress = st.progress(0, text="Đang khởi tạo quét...")
        status = st.empty()

        def on_progress(current, total, preview):
            pct = current / total
            progress.progress(pct, text=f"Đang quét đoạn {current}/{total}...")
            status.caption(f"▶ {preview}…")

        with st.spinner("Đang phân tích đạo văn — vui lòng chờ..."):
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
        st.success(f"✅ Hoàn tất! Quét {report.analyzed_paragraphs} đoạn trong {report.duration_seconds}s")

    if auto_fix and st.session_state.report and st.session_state.doc_path:
        with st.spinner("Đang paraphrase và giữ nguyên citation Mendeley..."):
            fixed_bytes, stats = generate_fixed_docx(
                st.session_state.doc_path,
                st.session_state.report,
                min_similarity=45.0,
            )
        st.session_state.fixed_docx = fixed_bytes
        st.session_state.fix_stats = stats
        failed = getattr(stats, "paragraphs_failed", 0)
        st.success(
            f"✅ Đã sửa **{stats.paragraphs_modified}** đoạn · "
            f"Giữ nguyên **{stats.paragraphs_unchanged}** đoạn · "
            f"Bỏ qua/lỗi **{stats.paragraphs_skipped + failed}** đoạn"
        )
        if failed:
            st.warning("Một số đoạn không sửa được để bảo vệ citation Mendeley — giữ nguyên bản gốc ở các đoạn đó.")
    elif auto_fix and not st.session_state.report:
        st.warning("Hãy chạy kiểm tra đạo văn trước khi tự động sửa.")

    report = st.session_state.report
    if report:
        render_score_cards(report)
        st.markdown("---")
        render_risk_summary(report)

        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            st.subheader("📋 Kết quả chi tiết theo đoạn")
        with col2:
            if st.session_state.fixed_docx:
                st.download_button(
                    "✅ Tải bài đã sửa (.docx)",
                    data=st.session_state.fixed_docx,
                    file_name=f"fixed_{Path(report.filename).stem}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    help="Văn bản màu đỏ = phần đã paraphrase; citation Mendeley giữ nguyên",
                    type="primary",
                )
            else:
                st.caption("Nhấn **Tự động sửa đạo văn** ở sidebar để tạo bản sửa")
        with col3:
            st.download_button(
                "📄 Tải báo cáo Word",
                data=export_report_docx(report, min_risk=min_risk),
                file_name=f"plagiarism_report_{Path(report.filename).stem}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                help="Xuất file .docx để đọc lỗi và gợi ý sửa song song với bài gốc",
            )
        with col4:
            st.download_button(
                "⬇️ JSON",
                data=export_report_json(report),
                file_name=f"plagiarism_report_{report.filename}.json",
                mime="application/json",
            )

        if st.session_state.fix_stats:
            fs = st.session_state.fix_stats
            st.info(
                f"📝 **Bản sửa tự động:** {fs.paragraphs_modified} đoạn đã paraphrase "
                f"(tô **đỏ** phần thay đổi). Citation Mendeley/IEEE `[n]` không bị thay đổi. "
                f"Đoạn đã sửa: {', '.join(f'#{i}' for i in fs.modified_indices[:20])}"
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
            st.success("🎉 Không phát hiện đoạn văn có rủi ro đáng kể ở mức lọc hiện tại.")
        else:
            for p in flagged:
                render_paragraph(p)

        with st.expander("ℹ️ Cách đọc kết quả"):
            st.markdown(
                """
                | Mức | Ý nghĩa | Hành động |
                |-----|---------|-----------|
                | **An toàn** (< 38%) | Thuật ngữ chung hoặc diễn đạt riêng | Giữ nguyên, đảm bảo citation |
                | **Theo dõi** (38–54%) | Cụm từ tương tự nguồn công khai | Paraphrase nhẹ, kiểm tra trích dẫn |
                | **Cao** (55–74%) | Khả năng copy ý lớn | Viết lại đoạn, thêm citation IEEE |
                | **Nghiêm trọng** (≥ 75%) | Trùng lặp mạnh với nguồn web | Bắt buộc paraphrase toàn bộ |

                **Công thức ước tính:** trọng số theo mức rủi ro × % trùng khớp với nguồn web / tổng số từ.
                """
            )
    elif not run_scan:
        st.markdown(
            """
            ### Bắt đầu
            1. File **HTTL-NEW.docx** sẽ được dùng mặc định nếu có trong thư mục.
            2. Chọn chế độ quét ở **sidebar** bên trái.
            3. Nhấn **Bắt đầu kiểm tra đạo văn**.

            Tool sẽ:
            - Trích xuất toàn bộ đoạn văn từ `.docx`
            - Tìm kiếm & so khớp với nguồn web công khai
            - Phát hiện trùng lặp nội bộ trong bài
            - Báo **% đạo văn ước tính** và gợi ý sửa từng đoạn
            - **Tự động sửa đạo văn**: paraphrase, giữ Mendeley, tô đỏ phần đã sửa
            """
        )


if __name__ == "__main__":
    main()
