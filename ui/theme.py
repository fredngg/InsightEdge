"""
Global theme — InsightEdge dark navy palette.
Call inject_theme() at the top of every page.
"""
import streamlit as st

BG         = "#050a14"
CARD       = "#111827"
BORDER     = "#1e293b"
ACCENT     = "#00d4aa"
ACCENT_80  = "#00b894"
TEXT       = "#f8fafc"
MUTED      = "#94a3b8"
INPUT_BG   = "#ffffff"
INPUT_TEXT = "#0f172a"

_CSS = f"""
<style>
/* ── Page background ────────────────────────────────────────── */
.stApp {{
    background-color: {BG};
}}
[data-testid="stHeader"] {{
    background-color: rgba(5, 10, 20, 0.8);
    backdrop-filter: blur(10px);
}}

/* ── Sidebar ─────────────────────────────────────────────────── */
[data-testid="stSidebar"] {{
    background-color: {CARD} !important;
    border-right: 1px solid {BORDER};
}}

/* ── Typography ─────────────────────────────────────────────── */
h1, h2, h3, h4, h5, h6 {{
    color: {TEXT} !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
}}
/* Body text — slightly dimmed so bold labels stand out */
p, span, label {{
    color: #94a3b8;
}}
.stMarkdown p {{
    color: #94a3b8;
    line-height: 1.7;
}}
/* Bold labels in teal — strong contrast against body text */
b, strong, .stMarkdown strong {{
    color: {ACCENT} !important;
    font-weight: 700;
}}

/* ── Block container top padding ────────────────────────────── */
.block-container {{
    padding-top: 3.5rem !important;
}}

/* ── Input Fields (White Surface) ───────────────────────────── */
.stTextInput input, .stTextArea textarea, .stNumberInput input,
.stSelectbox [data-baseweb="select"] {{
    background-color: {INPUT_BG} !important;
    color: {INPUT_TEXT} !important;
    border-radius: 8px !important;
    border: 1px solid {BORDER} !important;
    padding: 12px !important;
}}
.stTextInput input:focus, .stTextArea textarea:focus, .stNumberInput input:focus {{
    border-color: {ACCENT} !important;
    box-shadow: 0 0 0 2px rgba(0,212,170,0.25) !important;
}}

/* ── Widget labels ───────────────────────────────────────────── */
[data-testid="stWidgetLabel"] p {{
    color: {TEXT} !important;
    font-size: 0.75rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    font-weight: 600 !important;
    margin-bottom: 8px !important;
}}
.stCaption, .stCaption > p, small {{
    color: {MUTED} !important;
}}

/* ── Buttons ─────────────────────────────────────────────────── */
div.stButton > button {{
    border-radius: 8px !important;
    padding: 10px 24px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease;
}}
div.stButton > button[kind="primary"] {{
    background-color: {ACCENT} !important;
    color: #ffffff !important;
    border: none !important;
    font-weight: 700 !important;
}}
div.stButton > button[kind="primary"] p,
div.stButton > button[kind="primary"] span {{
    color: #ffffff !important;
    font-weight: 700 !important;
}}
div.stButton > button[kind="primary"]:hover {{
    background-color: {ACCENT_80} !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 212, 170, 0.3);
}}
div.stButton > button[kind="secondary"] {{
    background-color: transparent !important;
    color: {ACCENT} !important;
    border: 1px solid {ACCENT} !important;
}}
div.stButton > button[kind="tertiary"] {{
    background: none !important;
    border: none !important;
    padding: 0 !important;
    color: {ACCENT} !important;
    font-weight: 600 !important;
    text-decoration: underline;
    cursor: pointer;
    min-height: unset !important;
}}
div.stButton > button[kind="tertiary"]:hover {{
    color: {ACCENT_80} !important;
}}

/* ── Cards & Expanders ───────────────────────────────────────── */
.streamlit-expanderHeader {{
    background-color: {CARD} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 10px !important;
    padding: 12px 16px !important;
    color: {TEXT} !important;
    font-weight: 600 !important;
}}
.streamlit-expanderHeader:hover {{
    background-color: #1a2638 !important;
}}
.streamlit-expanderHeader[aria-expanded="true"] {{
    border-radius: 10px 10px 0 0 !important;
    border-bottom-color: {ACCENT} !important;
}}
.streamlit-expanderContent {{
    background-color: {CARD} !important;
    border: 1px solid {BORDER} !important;
    border-top: none !important;
    border-radius: 0 0 10px 10px !important;
    padding: 1rem !important;
}}

/* ── Tabs ────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {{
    gap: 24px;
    background-color: transparent;
    border-bottom: 1px solid {BORDER} !important;
}}
.stTabs [data-baseweb="tab-highlight"] {{
    background-color: transparent !important;
}}
.stTabs [data-baseweb="tab-border"] {{
    background-color: transparent !important;
    display: none !important;
}}
.stTabs [data-baseweb="tab"] {{
    color: {MUTED} !important;
    font-weight: 500 !important;
    padding: 10px 4px !important;
    font-size: 0.875rem !important;
}}
.stTabs [aria-selected="true"] {{
    color: {ACCENT} !important;
    border-bottom: 2px solid {ACCENT} !important;
}}
.stTabs [data-baseweb="tab-panel"] {{
    padding-top: 1rem;
}}

/* ── Radio / Checkbox ────────────────────────────────────────── */
.stRadio > label, .stCheckbox > label {{ color: {TEXT} !important; }}

/* ── Progress bar ────────────────────────────────────────────── */
.stProgress > div > div > div > div {{ background-color: {ACCENT} !important; }}

/* ── Alerts ──────────────────────────────────────────────────── */
.stAlert {{ border-radius: 8px !important; }}
.stInfo  {{ background-color: #0d1f38 !important; border-left-color: {ACCENT} !important; }}

/* ── File Uploader ───────────────────────────────────────────── */
[data-testid="stFileUploader"] > section {{
    background-color: {INPUT_BG} !important;
    border: 2px dashed {ACCENT} !important;
    border-radius: 12px !important;
}}
[data-testid="stFileUploader"] * {{
    color: {INPUT_TEXT} !important;
}}

/* ── Dividers ────────────────────────────────────────────────── */
hr {{ border-color: {BORDER} !important; margin: 0.75rem 0 !important; }}

/* ── Spinner ─────────────────────────────────────────────────── */
.stSpinner > div {{ border-top-color: {ACCENT} !important; }}

/* ── File uploader ───────────────────────────────────────────── */
[data-testid="stFileUploader"] section {{
    background-color: #2d3748 !important;
    border: 1px solid {BORDER} !important;
    border-radius: 8px !important;
}}
[data-testid="stFileUploader"] section button {{
    background-color: #4a5568 !important;
    color: #ffffff !important;
    border: 1px solid #718096 !important;
    border-radius: 6px !important;
}}
[data-testid="stFileUploader"] section small,
[data-testid="stFileUploader"] section span,
[data-testid="stFileUploader"] section p {{
    color: #e2e8f0 !important;
}}
</style>
"""


def inject_theme():
    st.markdown(_CSS, unsafe_allow_html=True)
