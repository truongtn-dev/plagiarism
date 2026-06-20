"""Global theme CSS and layout helpers."""

from __future__ import annotations

from ui.icons import icon_label, svg_icon

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
    --bg: #f4f6fb;
    --bg-elevated: #ffffff;
    --surface: #ffffff;
    --surface-muted: #f8fafc;
    --border: #e2e8f0;
    --border-strong: #cbd5e1;
    --text: #0f172a;
    --text-secondary: #475569;
    --text-muted: #64748b;
    --accent: #4f46e5;
    --accent-hover: #4338ca;
    --accent-soft: #eef2ff;
    --accent-glow: rgba(79, 70, 229, 0.15);
    --success: #059669;
    --success-soft: #ecfdf5;
    --warning: #d97706;
    --warning-soft: #fffbeb;
    --danger: #dc2626;
    --danger-soft: #fef2f2;
    --critical: #b91c1c;
    --radius: 14px;
    --radius-sm: 10px;
    --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.05);
    --shadow: 0 4px 24px rgba(15, 23, 42, 0.06);
    --shadow-lg: 0 12px 40px rgba(15, 23, 42, 0.08);
}

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.stApp {
    background: var(--bg);
    color: var(--text);
}

.block-container {
    padding-top: 2rem;
    max-width: 1180px;
}

header[data-testid="stHeader"] {
    background: rgba(255,255,255,0.85);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border);
}

#MainMenu, footer, header[data-testid="stHeader"] a { visibility: hidden; height: 0; }

/* ── Hero ── */
.hero {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 2.5rem 1.5rem 2rem;
    margin-bottom: 2rem;
    background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
    border: 1px solid var(--border);
    border-radius: calc(var(--radius) + 4px);
    box-shadow: var(--shadow);
}
.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.35rem 0.85rem;
    background: var(--accent-soft);
    color: var(--accent);
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    margin-bottom: 1rem;
}
.hero h1 {
    font-size: clamp(1.75rem, 4vw, 2.35rem);
    font-weight: 700;
    letter-spacing: -0.03em;
    color: var(--text);
    margin: 0 0 0.75rem;
    line-height: 1.2;
}
.hero-sub {
    color: var(--text-secondary);
    font-size: 1.05rem;
    max-width: 640px;
    line-height: 1.6;
    margin: 0;
}
.hero-copy {
    margin-top: 1.25rem;
    font-size: 0.8rem;
    color: var(--text-muted);
}

/* ── Icons ── */
.ico { display: inline-block; vertical-align: middle; flex-shrink: 0; }
.icon-label {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 600;
    color: var(--text);
}
.section-title {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    font-size: 1.15rem;
    font-weight: 600;
    letter-spacing: -0.02em;
    color: var(--text);
    margin: 0 0 1rem;
}
.section-title .ico-wrap {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    border-radius: var(--radius-sm);
    background: var(--accent-soft);
    color: var(--accent);
}

/* ── Score cards ── */
.score-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.35rem 1rem;
    text-align: left;
    box-shadow: var(--shadow-sm);
    transition: box-shadow 0.2s, transform 0.2s;
    height: 100%;
}
.score-card:hover {
    box-shadow: var(--shadow);
    transform: translateY(-1px);
}
.score-card-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.75rem;
}
.score-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    border-radius: var(--radius-sm);
}
.score-value {
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    line-height: 1;
    font-variant-numeric: tabular-nums;
}
.score-label {
    color: var(--text-muted);
    font-size: 0.8rem;
    font-weight: 500;
    margin-top: 0.35rem;
}
.gauge-originality { color: var(--success); }
.gauge-plagiarism { color: var(--danger); }
.gauge-analyzed { color: var(--accent); }
.gauge-time { color: #7c3aed; }
.score-icon.icon-success { background: var(--success-soft); color: var(--success); }
.score-icon.icon-danger { background: var(--danger-soft); color: var(--danger); }
.score-icon.icon-accent { background: var(--accent-soft); color: var(--accent); }
.score-icon.icon-purple { background: #f5f3ff; color: #7c3aed; }

/* ── Risk badges ── */
.risk-badge {
    display: inline-flex;
    align-items: center;
    padding: 0.2rem 0.65rem;
    border-radius: 999px;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.03em;
    text-transform: uppercase;
}
.risk-low { background: var(--success-soft); color: var(--success); border: 1px solid #a7f3d0; }
.risk-medium { background: var(--warning-soft); color: var(--warning); border: 1px solid #fde68a; }
.risk-high { background: var(--danger-soft); color: var(--danger); border: 1px solid #fecaca; }
.risk-critical { background: #fef2f2; color: var(--critical); border: 1px solid #fca5a5; }

/* ── Paragraph cards ── */
.para-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: var(--radius);
    padding: 1rem 1.25rem;
    margin-bottom: 0.75rem;
    box-shadow: var(--shadow-sm);
}
.para-card.risk-medium { border-left-color: var(--warning); }
.para-card.risk-high { border-left-color: var(--danger); }
.para-card.risk-critical { border-left-color: var(--critical); }
.para-card.risk-low { border-left-color: var(--success); }
.para-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 0.65rem;
    align-items: center;
    font-size: 0.82rem;
    color: var(--text-muted);
}
.para-meta strong { color: var(--text); font-weight: 600; }
.para-text {
    line-height: 1.65;
    color: var(--text-secondary);
    margin: 0.75rem 0 0;
    padding: 1rem;
    background: var(--surface-muted);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.8rem;
    max-height: 220px;
    overflow-y: auto;
}
.suggestion {
    background: var(--accent-soft);
    border-left: 3px solid var(--accent);
    padding: 0.65rem 1rem;
    margin: 0.45rem 0;
    border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
    font-size: 0.875rem;
    line-height: 1.55;
    color: var(--text-secondary);
}
.source-link { color: var(--accent); font-size: 0.85rem; word-break: break-all; }

/* ── Sidebar ── */
div[data-testid="stSidebar"] {
    background: var(--surface);
    border-right: 1px solid var(--border);
}
div[data-testid="stSidebar"] .block-container { padding-top: 1.5rem; }
.sidebar-brand {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.5rem 0 1.25rem;
    margin-bottom: 0.5rem;
    border-bottom: 1px solid var(--border);
}
.sidebar-brand-icon {
    width: 40px; height: 40px;
    display: flex; align-items: center; justify-content: center;
    background: var(--accent);
    color: #fff;
    border-radius: var(--radius-sm);
}
.sidebar-brand-text {
    font-weight: 700;
    font-size: 0.95rem;
    letter-spacing: -0.02em;
    color: var(--text);
    line-height: 1.3;
}
.sidebar-brand-sub { font-size: 0.72rem; color: var(--text-muted); font-weight: 500; }

/* ── Streamlit widgets ── */
.stButton > button {
    background: var(--accent) !important;
    color: #fff !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    padding: 0.6rem 1.25rem !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    box-shadow: var(--shadow-sm) !important;
    transition: background 0.15s, box-shadow 0.15s !important;
}
.stButton > button:hover {
    background: var(--accent-hover) !important;
    box-shadow: 0 4px 14px var(--accent-glow) !important;
}
.stButton > button[kind="secondary"] {
    background: var(--surface) !important;
    color: var(--text) !important;
    border: 1px solid var(--border-strong) !important;
}
.stDownloadButton > button {
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
}
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, var(--accent), #7c3aed) !important;
}
div[data-testid="stMetric"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem 1.1rem;
    box-shadow: var(--shadow-sm);
}
div[data-testid="stMetric"] label {
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    color: var(--text-muted) !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-weight: 700 !important;
    letter-spacing: -0.02em;
}

/* ── Getting started ── */
.steps-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 1rem;
    margin-top: 1.5rem;
}
.step-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.25rem;
    box-shadow: var(--shadow-sm);
}
.step-num {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px; height: 28px;
    background: var(--accent-soft);
    color: var(--accent);
    border-radius: 8px;
    font-size: 0.8rem;
    font-weight: 700;
    margin-bottom: 0.75rem;
}
.step-card h4 {
    margin: 0 0 0.4rem;
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--text);
}
.step-card p {
    margin: 0;
    font-size: 0.875rem;
    color: var(--text-muted);
    line-height: 1.5;
}
</style>
"""


def section_heading(icon_name: str, title: str) -> str:
    return (
        f'<div class="section-title">'
        f'<span class="ico-wrap">{svg_icon(icon_name, 18)}</span>'
        f"<span>{title}</span></div>"
    )


def hero_html(subtitle: str, copyright: str) -> str:
    return f"""
    <div class="hero">
        <div class="hero-badge">{icon_label("shield", "Academic Integrity Tool", 14)}</div>
        <h1>IEEE Plagiarism Checker</h1>
        <p class="hero-sub">{subtitle}</p>
        <p class="hero-copy">&copy; {copyright}</p>
    </div>
    """


def sidebar_brand_html() -> str:
    return f"""
    <div class="sidebar-brand">
        <div class="sidebar-brand-icon">{svg_icon("logo", 22, "ico")}</div>
        <div>
            <div class="sidebar-brand-text">Plagiarism Checker</div>
            <div class="sidebar-brand-sub">IEEE · Mendeley safe</div>
        </div>
    </div>
    """
