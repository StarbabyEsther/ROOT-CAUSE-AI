"""RootCause AI — premium, three-page Streamlit demonstration.

Uses the existing workflow.py and scenario_registry.py in the team repository.
No demonstration login credentials are requested or stored.
"""

import base64
import difflib
import html
import json
import os
import threading
from decimal import Decimal, InvalidOperation
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# Keep the existing team backend intact.
from workflow import run_workflow

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"

st.set_page_config(
    page_title="RootCause AI | Financial Software Reliability",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

load_dotenv(ROOT / ".env")
# Streamlit Cloud credentials must be set privately via the app's Secrets settings.
# Pass them to child processes launched by workflow.py.
try:
    for name in ("NEBIUS_API_KEY", "NEBIUS_MODEL", "CONTREE_PROJECT_ID"):
        if name in st.secrets:
            os.environ[name] = str(st.secrets[name])
except (FileNotFoundError, KeyError):
    pass

SCENARIOS = {
    "duplicate_transaction": {
        "title": "Duplicate transactions",
        "subtitle": "Find repeated charges and incorrect totals.",
        "tag": "TRANSACTION INTEGRITY",
        "number": "01",
        "tests": 6,
        "sample": "A payment of $200 is counted twice.",
        "original": "transactions.py",
        "repaired": "verification_bundle/transactions.py",
    },
    "incorrect_refund": {
        "title": "Incorrect refunds",
        "subtitle": "Correct refund sign and accounting errors.",
        "tag": "REFUND RECONCILIATION",
        "number": "02",
        "tests": 7,
        "sample": "A refund is added instead of deducted.",
        "original": "refund_processor.py",
        "repaired": "refund_verification_bundle/refund_processor.py",
    },
    "monetary_precision": {
        "title": "Monetary precision",
        "subtitle": "Detect floating-point drift in financial calculations.",
        "tag": "NUMERICAL ACCURACY",
        "number": "03",
        "tests": 5,
        "sample": "0.10 + 0.20 differs from the exact decimal total.",
        "original": "precision_processor.py",
        "repaired": "precision_verification_bundle/precision_processor.py",
    },
}

if "rc_page" not in st.session_state:
    st.session_state.rc_page = "Welcome"
if "rc_scenario" not in st.session_state:
    st.session_state.rc_scenario = "duplicate_transaction"
if "rc_night" not in st.session_state:
    st.session_state.rc_night = False


@st.cache_resource
def run_lock():
    """Serialize in-process runs that write to the existing shared report paths."""
    return threading.Lock()


def change_page(page):
    st.session_state.rc_page = page
    st.rerun()


def picture_data_uri(filename):
    path = ASSETS / filename
    if not path.is_file():
        return ""
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def show_html(markup):
    # st.html avoids Markdown treating indented HTML as a literal code block.
    st.html(markup)


def esc(text):
    return html.escape(str(text), quote=True)


def money(value, precision=False):
    try:
        val = Decimal(str(value))
        if precision:
            return "$" + format(val, "f")
        return f"${val:,.2f}"
    except (InvalidOperation, TypeError, ValueError):
        return "Not available"


def safe_report(outcome):
    """Capture a sanitized, downloadable summary without secrets or verbose logs."""
    return {
        "product": "RootCause AI",
        "demo_data": "synthetic",
        "scenario_id": outcome["scenario_id"],
        "verified": outcome["verified"],
        "financial": outcome.get("financial", {}),
        "verification": outcome.get("verification", {}),
        "patch": outcome.get("patch", {}),
        "note": "Verified only against this scenario's regression tests, not all possible inputs.",
    }


def scrub_logs(logs):
    value = str(logs or "")
    for secret in (os.getenv("NEBIUS_API_KEY", ""), os.getenv("CONTREE_TOKEN", "")):
        if secret and len(secret) >= 8:
            value = value.replace(secret, "[REDACTED]")
    return value


# Apply a site-wide theme to Streamlit and all custom HTML cards.
# Changes are held in st.session_state for the current browser session.
_THEME_PALETTES = {'day': {'bg': '#F7F9FD', 'card': '#FFFFFF', 'soft': '#EBF3FF', 'text': '#14283F', 'heading': '#122D4B', 'muted': '#62758B', 'faint': '#788DA1', 'line': '#DEE7F0', 'accent': '#2258E8', 'accent-2': '#264BD1', 'button-text': '#FFFFFF', 'teal': '#149EAA', 'teal-halo': '#D8F5F1', 'brand-bg': '#102B4F', 'panel': '#122C4A', 'shadow': 'rgba(18,43,73,.15)', 'active-shadow': '#C7D9FF', 'code': '#EFF4FA'}, 'night': {'bg': '#071424', 'card': '#11243A', 'soft': '#162F49', 'text': '#E7F1FC', 'heading': '#F1F7FF', 'muted': '#B0C5DA', 'faint': '#9BAFC5', 'line': '#2B4560', 'accent': '#77B7FF', 'accent-2': '#64DCD7', 'button-text': '#051B34', 'teal': '#58E2D5', 'teal-halo': '#17484E', 'brand-bg': '#1A3557', 'panel': '#172E4A', 'shadow': 'rgba(0,0,0,.35)', 'active-shadow': '#244E83', 'code': '#0B1A2D'}}
_active_palette = _THEME_PALETTES["night" if st.session_state.rc_night else "day"]
_THEME_CSS = '\n/* RootCause AI: application-wide theme tokens and two matching color palettes. */\n:root, .stApp {\n    __THEME_VARS__\n    color-scheme: __COLOR_SCHEME__;\n}\n@import url(\'https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap\');\nhtml, body, [class*="css"], .stApp { font-family: \'DM Sans\', sans-serif !important; }\n.stApp { background:var(--rc-bg) !important; color:var(--rc-text) !important; }\n/* Move application navigation below the Streamlit system header rather than under it. */\n[data-testid="stHeader"] { background:transparent !important; height:0 !important; min-height:0 !important; box-shadow:none !important; }\n[data-testid="stToolbar"], [data-testid="stDecoration"] { display:none !important; }\n.block-container { max-width:1290px; padding-top:3.05rem !important; padding-bottom:3.2rem !important; }\nh1,h2,h3,h4 { font-family:\'Manrope\',sans-serif !important; color:var(--rc-heading) !important; letter-spacing:-.035em; }\n.stMarkdown p, .stCaption, [data-testid="stCaptionContainer"] { color:var(--rc-muted) !important; }\nlabel, [data-testid="stToggle"] label, .stToggle label, .stTabs button { color:var(--rc-text) !important; }\n[data-testid="stToggle"] { padding-top:5px; }\nbutton[kind="primary"] { background:linear-gradient(110deg,var(--rc-accent),var(--rc-accent-2)) !important; color:var(--rc-button-text) !important; border-radius:12px !important; border:none !important; font-weight:700 !important; padding:.62rem 1.2rem !important; min-height:47px; box-shadow:0 10px 23px var(--rc-shadow); }\nbutton[kind="primary"]:hover { filter:brightness(1.09); color:var(--rc-button-text) !important; }\nbutton[kind="secondary"] { background:var(--rc-card) !important; border:1px solid var(--rc-line) !important; color:var(--rc-text) !important; border-radius:11px !important; font-weight:650 !important; min-height:43px; }\nbutton[kind="secondary"]:hover { background:var(--rc-soft) !important; color:var(--rc-accent) !important; border-color:var(--rc-accent) !important; }\n[data-testid="stSelectbox"] div[data-baseweb="select"] > div { background:var(--rc-card) !important; color:var(--rc-text) !important; border-color:var(--rc-line) !important; border-radius:12px; }\n[data-testid="stMetric"] { background:var(--rc-card); border:1px solid var(--rc-line); border-radius:16px; padding:14px 18px; }\n[data-testid="stMetricValue"] { font-family:\'Manrope\',sans-serif; color:var(--rc-heading) !important; font-weight:800; }\n[data-testid="stMetricLabel"] { color:var(--rc-muted) !important; }\n[data-testid="stTabs"] button { font-weight:700; color:var(--rc-muted) !important; }\n[data-testid="stTabs"] button[aria-selected="true"] { color:var(--rc-accent) !important; }\n[data-testid="stAlert"] { border-radius:14px; }\n[data-testid="stExpander"] { background:var(--rc-card); border-radius:13px; border:1px solid var(--rc-line); }\n[data-testid="stExpander"] * { color:var(--rc-text); }\n[data-testid="stCodeBlock"] pre { background:var(--rc-code) !important; }\n[data-testid="stCodeBlock"] code { color:var(--rc-text); }\n.rc-brand { display:flex; gap:12px; align-items:center; padding:5px 0 4px; }\n.rc-mark { width:39px; height:39px; flex-shrink:0; display:flex; align-items:center; justify-content:center; background:var(--rc-brand-bg); color:#62e7db; border-radius:12px; font-size:24px; font-weight:800; box-shadow:0 6px 17px var(--rc-shadow); }\n.rc-brandname { font-family:Manrope,sans-serif; font-weight:800; font-size:21px; letter-spacing:-.045em; color:var(--rc-heading); line-height:1.05; }\n.rc-brandname span { color:var(--rc-accent); }\n.rc-brandmeta { font-size:9px; letter-spacing:.16em; color:var(--rc-faint); font-weight:800; margin-top:3px; }\n.rc-hero-left { padding-top:37px; padding-bottom:18px; }\n.rc-kicker { display:inline-flex; align-items:center; gap:8px; border:1px solid var(--rc-line); background:var(--rc-soft); padding:8px 13px; border-radius:999px; color:var(--rc-accent); font-size:11px; letter-spacing:.08em; font-weight:800; text-transform:uppercase; }\n.rc-dot { height:7px;width:7px; border-radius:50%; background:var(--rc-teal); display:inline-block; box-shadow:0 0 0 4px var(--rc-teal-halo); }\n.rc-bigtitle { font-family:Manrope,sans-serif; letter-spacing:-.055em; font-size:clamp(38px,4.5vw,65px); font-weight:800; color:var(--rc-heading); line-height:1.13; margin:24px 0 20px; }\n.rc-bigtitle strong { color:var(--rc-accent); font-weight:800; }\n.rc-summary { color:var(--rc-muted); font-size:17px; line-height:1.86; max-width:585px; margin:0 0 21px; }\n.rc-trustline { padding:14px 0; display:flex; gap:17px; flex-wrap:wrap; color:var(--rc-muted); font-size:12px; font-weight:700; }\n.rc-trustline span:before { content:\'✓\'; color:var(--rc-teal); font-weight:900; margin-right:6px; }\n.rc-photo-card { position:relative; border-radius:25px; overflow:hidden; height:435px; border:1px solid var(--rc-line); box-shadow:0 25px 60px var(--rc-shadow); background:linear-gradient(125deg,#092b52,#0f6d92); }\n.rc-photo-card img { width:100%; height:100%; object-fit:cover; object-position:center; display:block; }\n.rc-photo-card:after { position:absolute; inset:0;content:\'\';background:linear-gradient(180deg,rgba(1,20,39,.02),rgba(3,19,42,.12) 44%,rgba(3,17,33,.91));pointer-events:none; }\n.rc-photo-label { position:absolute; z-index:2; bottom:22px; left:24px; right:24px; color:#fff; }\n.rc-photo-label small { display:block; font-size:11px; font-weight:800; letter-spacing:.12em; color:#72f6f0; margin-bottom:7px; }\n.rc-photo-label strong { display:block; font-size:24px; font-family:Manrope,sans-serif; letter-spacing:-.04em; line-height:1.28; }\n.rc-photo-label p { color:#c4deee; font-size:12px; margin:7px 0 0; }\n.rc-image-caption { color:var(--rc-faint); font-size:11px; margin-top:9px; }\n.rc-section { padding-top:34px; }\n.rc-eyebrow { color:var(--rc-accent); font-size:11px; text-transform:uppercase; font-weight:800; letter-spacing:.13em; margin-bottom:9px; }\n.rc-heading { font-family:Manrope,sans-serif; font-size:clamp(24px,2.4vw,34px); letter-spacing:-.048em; font-weight:800; color:var(--rc-heading); line-height:1.2; margin-bottom:9px; }\n.rc-subheading { color:var(--rc-muted); font-size:14px; line-height:1.7; max-width:720px; margin-bottom:20px; }\n.rc-stats { margin:25px 0 8px; display:grid; grid-template-columns:repeat(3,1fr); gap:13px; }\n.rc-stat { background:var(--rc-card); padding:19px 21px; border:1px solid var(--rc-line); border-radius:16px; }\n.rc-stat-val { font-family:Manrope,sans-serif; color:var(--rc-heading); font-size:30px; font-weight:800; letter-spacing:-.05em; }\n.rc-stat-val span { color:var(--rc-teal); }\n.rc-stat-label { color:var(--rc-muted); font-weight:600; font-size:12px; margin-top:3px; }\n.rc-feature-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:14px; }\n.rc-feature { border:1px solid var(--rc-line); border-radius:19px; padding:22px 22px 23px; background:var(--rc-card); min-height:200px; }\n.rc-feature-no { display:flex; align-items:center; justify-content:center; background:var(--rc-soft); color:var(--rc-accent); width:37px; height:37px; border-radius:11px; font-weight:800; font-size:13px; }\n.rc-feature strong { display:block; font-family:Manrope,sans-serif; font-size:17px; letter-spacing:-.035em; margin:15px 0 8px; color:var(--rc-heading); }\n.rc-feature p { font-size:13px; color:var(--rc-muted); line-height:1.68; margin:0; }\n.rc-workstrip { background:var(--rc-panel); color:#fff; padding:28px 30px; margin:32px 0 14px; border-radius:20px; display:flex; align-items:center; justify-content:space-between; gap:18px; }\n.rc-workstrip strong {font-family:Manrope,sans-serif;font-size:22px;letter-spacing:-.04em;}\n.rc-workstrip p {font-size:13px;color:#c4d5e5;line-height:1.7;margin:8px 0 0;max-width:770px;}\n.rc-pill { border:1px solid #386580; background:#1d4665; color:#93f0df; border-radius:99px; padding:9px 12px; font-size:11px; white-space:nowrap; font-weight:800; }\n.rc-footer { border-top:1px solid var(--rc-line); padding:22px 0; margin-top:45px;display:flex;gap:10px;justify-content:space-between;flex-wrap:wrap; font-size:12px; color:var(--rc-muted); }\n.rc-pageintro {background:var(--rc-panel); color:#fff; border-radius:22px; padding:35px 38px; margin:14px 0 24px; background-image:radial-gradient(circle at 90% 1%,rgba(74,167,207,.23) 0%,transparent 39%);}\n.rc-pageintro .rc-eyebrow {color:#87eee5;} .rc-pageintro h1{color:#fff !important; font-size:37px; letter-spacing:-.045em; margin:5px 0 9px;} .rc-pageintro p{color:#c0d2e3;font-size:14px;line-height:1.7;max-width:800px;margin:0;}\n.rc-case { min-height:170px; border:1px solid var(--rc-line); border-radius:18px; background:var(--rc-card); padding:20px; margin-bottom:8px; }\n.rc-case.active {border-color:var(--rc-accent); box-shadow:0 3px 0 var(--rc-active-shadow); background:var(--rc-soft);}\n.rc-case .rc-case-id {font-weight:800; font-size:11px;color:var(--rc-accent);letter-spacing:.1em;margin-bottom:13px;}\n.rc-case h3 { font-family:Manrope,sans-serif; color:var(--rc-heading); margin:0 0 8px;font-size:16px;letter-spacing:-.035em;}\n.rc-case p { font-size:12px;color:var(--rc-muted);line-height:1.6;margin:0;min-height:55px; }\n.rc-surface {background:var(--rc-card);border:1px solid var(--rc-line);border-radius:17px;padding:22px 24px; margin:17px 0;}\n.rc-surface .rc-surface-head { font-size:15px; font-family:Manrope,sans-serif;font-weight:800;color:var(--rc-heading);}\n.rc-tag {display:inline-block;border-radius:99px;background:var(--rc-soft);color:var(--rc-accent);padding:7px 11px;font-size:11px;font-weight:800;letter-spacing:.07em;}\n.rc-note {color:var(--rc-muted);font-size:12px;line-height:1.8;}\n.rc-how-image {height:350px;border-radius:20px;object-fit:cover;width:100%;}\n@media (max-width:900px) {\n    .rc-bigtitle { font-size:41px; }\n    .rc-photo-card { height:340px; }\n    .rc-stats,.rc-feature-grid {grid-template-columns:1fr;}\n    .rc-pageintro {padding:24px;}\n    .rc-workstrip {display:block;}\n    .rc-pill {display:inline-block;margin-top:15px;}\n    .block-container {padding-top:2.5rem !important;}\n}\n'
_theme_vars = "\n    ".join(
    f"--rc-{name}: {value};" for name, value in _active_palette.items()
)
show_html("<style>" + _THEME_CSS.replace("__THEME_VARS__", _theme_vars).replace(
    "__COLOR_SCHEME__", "dark" if st.session_state.rc_night else "light"
) + "</style>")

# ------------------------------ Global navigation ------------------------------
nav = st.columns([3.0, 1.05, 1.15, 1.55, 1.25], gap="small")
with nav[0]:
    show_html("""<div class='rc-brand'><div class='rc-mark'>◈</div><div><div class='rc-brandname'>RootCause <span>AI</span></div><div class='rc-brandmeta'>FINANCIAL SOFTWARE RELIABILITY</div></div></div>""")
with nav[1]:
    if st.button("Welcome", key="nav_welcome", use_container_width=True):
        change_page("Welcome")
with nav[2]:
    if st.button("How it works", key="nav_how", use_container_width=True):
        change_page("How it works")
with nav[3]:
    if st.button("Open the Lab  →", type="primary", key="nav_lab", use_container_width=True):
        change_page("Investigation Lab")
with nav[4]:
    st.toggle("Night mode", key="rc_night", help="Switch between day and night appearance")


# ------------------------------ Welcome page ------------------------------
if st.session_state.rc_page == "Welcome":
    st.write("")
    hero_col, image_col = st.columns([1.1, .96], gap="large")
    with hero_col:
        show_html("""
<div class="rc-hero-left">
  <span class="rc-kicker"><i class="rc-dot"></i> AI-powered financial software debugging</span>
  <div class="rc-bigtitle">Financial errors, <strong>resolved with intelligence.</strong></div>
  <div class="rc-summary">Meet RootCause AI — a financial software debugging assistant that detects calculation problems, generates targeted code repairs with NVIDIA Nemotron, and independently validates each candidate fix inside Nebius Sandboxes.</div>
  <div class="rc-trustline"><span>Real AI repair workflow</span><span>Isolated verification</span><span>Synthetic demo data</span></div>
</div>
""")
        c1, c2 = st.columns([1.2, 1])
        with c1:
            if st.button("Launch interactive demo  →", type="primary", key="welcome_launch", use_container_width=True):
                change_page("Investigation Lab")
        with c2:
            if st.button("Explore how it works", key="welcome_how", use_container_width=True):
                change_page("How it works")
        st.caption("Guest demonstration — no signup or password required.")
    with image_col:
        img = picture_data_uri("rca_hero.jpg")
        photo = f'<img alt="Blue analytics monitors in a financial technology workspace" src="{img}">' if img else ""
        show_html(f"""
<div class='rc-photo-card'>{photo}<div class='rc-photo-label'><small>THE INTELLIGENT REPAIR ENGINE</small><strong>From discrepancy to verified code.</strong><p>Investigate · Generate · Validate</p></div></div>
""")

    show_html("""
<div class='rc-stats'>
  <div class='rc-stat'><div class='rc-stat-val'>03 <span>scenarios</span></div><div class='rc-stat-label'>Demonstrated financial defect types</div></div>
  <div class='rc-stat'><div class='rc-stat-val'>18/18</div><div class='rc-stat-label'>Regression tests passed in prior local runs</div></div>
  <div class='rc-stat'><div class='rc-stat-val'>AI <span>+ sandbox</span></div><div class='rc-stat-label'>Nemotron generation with Nebius verification</div></div>
</div>
<div class='rc-section'><div class='rc-eyebrow'>A better way to debug</div><div class='rc-heading'>How RootCause AI works</div><div class='rc-subheading'>An intelligent investigation pipeline — from identifying an incorrect financial total to validating a candidate repair against independent regression tests.</div></div>
<div class='rc-feature-grid'>
 <div class='rc-feature'><div class='rc-feature-no'>01</div><strong>Detect the discrepancy</strong><p>Investigate duplicate payments, refund sign errors, and monetary precision issues using controlled financial scenarios.</p></div>
 <div class='rc-feature'><div class='rc-feature-no'>02</div><strong>Generate a targeted fix</strong><p>NVIDIA Nemotron analyzes the faulty function and proposes an executable Python code correction.</p></div>
 <div class='rc-feature'><div class='rc-feature-no'>03</div><strong>Verify independently</strong><p>Run the original and candidate code in Nebius Sandboxes against scenario-specific protected regression tests.</p></div>
</div>
<div class='rc-workstrip'><div><strong>Ready to see autonomous debugging in action?</strong><p>Step into the demo workspace. Choose a financial scenario and inspect the AI-generated fix, test evidence, and code changes.</p></div><div class='rc-pill'>LIVE INVESTIGATION EXPERIENCE</div></div>
""")
    if st.button("Enter the Investigation Lab  →", type="primary", key="welcome_bottom_launch"):
        change_page("Investigation Lab")


# ------------------------------ How it works page ------------------------------
elif st.session_state.rc_page == "How it works":
    show_html("""
<div class='rc-pageintro'><div class='rc-eyebrow'>Behind the platform</div><h1>How RootCause AI works</h1><p>A transparent, three-stage workflow connecting financial analysis, NVIDIA Nemotron-assisted code repairs, and independent Nebius Sandbox regression testing.</p></div>
""")
    left, right = st.columns([1.1, .8], gap="large")
    with left:
        show_html("""
<div class='rc-section' style='padding-top:4px'><div class='rc-eyebrow'>The workflow</div><div class='rc-heading'>AI assistance with verification built in.</div><div class='rc-subheading'>RootCause AI doesn't mark a repair as successful just because an AI model suggested it. A candidate must pass the selected scenario's tests in an isolated execution environment.</div></div>
<div class='rc-feature' style='min-height:0;margin-bottom:12px'><div class='rc-feature-no'>01</div><strong>Understand the failure</strong><p>Examine synthetic transaction records, calculate a reference total, and report the actual discrepancy and suspected issue.</p></div>
<div class='rc-feature' style='min-height:0;margin-bottom:12px'><div class='rc-feature-no'>02</div><strong>Propose a repair</strong><p>Nemotron explains the suspected root cause and writes a function-level patch. Structural checks restrict the repair's scope.</p></div>
<div class='rc-feature' style='min-height:0'><div class='rc-feature-no'>03</div><strong>Test the repair independently</strong><p>Nebius Sandboxes execute baseline and candidate code against protected tests. Passing those tests produces a limited <code>verified_fixed</code> verdict.</p></div>
""")
    with right:
        workspace_img = picture_data_uri("rca_workspace.jpg")
        if workspace_img:
            show_html(f"<img class='rc-how-image' alt='Software development and analytics workstation' src='{workspace_img}'>")
        show_html("""
<div class='rc-surface'><div class='rc-surface-head'>Built with</div><div class='rc-trustline' style='margin-top:8px'><span>Python</span><span>NVIDIA Nemotron</span><span>Nebius Sandboxes</span><span>Streamlit</span></div><p class='rc-note'>All demo transactions are synthetic. Repairs are verified only for the supplied test cases; the application does not automatically patch production systems.</p></div>
""")
        if st.button("Try a live investigation  →", type="primary", key="how_launch", use_container_width=True):
            change_page("Investigation Lab")


# ------------------------------ Investigation lab ------------------------------
else:
    show_html("""
<div class='rc-pageintro'><div class='rc-eyebrow'>Interactive demonstration · Guest access</div><h1>Investigation Lab</h1><p>Choose a financial defect. Watch RootCause AI investigate the root cause, propose a code-level fix, and verify the candidate repair in Nebius Sandboxes.</p></div>
<div class='rc-section' style='padding-top:0'><div class='rc-eyebrow'>Select a case study</div><div class='rc-heading'>Three financial bugs. One intelligent workflow.</div><div class='rc-subheading'>All cases use synthetic sample transactions and a fixed set of regression tests.</div></div>
""")
    case_cols = st.columns(3, gap="medium")
    for col, (scenario_id, meta) in zip(case_cols, SCENARIOS.items()):
        with col:
            active = " active" if st.session_state.rc_scenario == scenario_id else ""
            show_html(f"""
<div class='rc-case{active}'><div class='rc-case-id'>{meta['number']} / {meta['tag']}</div><h3>{meta['title']}</h3><p>{meta['subtitle']}</p><span class='rc-tag'>{meta['tests']} protected tests</span></div>
""")
            if st.button(
                "Selected ✓" if active else "Select this scenario",
                key=f"case_{scenario_id}",
                use_container_width=True,
                disabled=bool(active),
            ):
                st.session_state.rc_scenario = scenario_id
                st.rerun()

    chosen = st.session_state.rc_scenario
    scenario = SCENARIOS[chosen]
    show_html(f"""
<div class='rc-surface'><div class='rc-surface-head'>{esc(scenario['title'])}</div><p style='color:var(--rc-muted);margin-top:8px;font-size:13px'>Example failure: {esc(scenario['sample'])}</p><div class='rc-trustline'><span>{scenario['tests']} regression tests</span><span>Original code preserved</span><span>Sandbox-verified candidate</span></div></div>
""")
    _, run_col = st.columns([1.7, 1.1])
    with run_col:
        clicked = st.button("Analyze & Repair selected case  →", type="primary", key="run_case", use_container_width=True)

    if clicked:
        lock = run_lock()
        if not lock.acquire(blocking=False):
            st.warning("Another investigation is currently running on this server. Please try again after it finishes.")
        else:
            try:
                with st.spinner("Investigating the discrepancy, generating the repair and checking it in Nebius Sandbox..."):
                    response = run_workflow(chosen)
                    original_path = ROOT / scenario["original"]
                    repaired_path = ROOT / scenario["repaired"]
                    original_code = original_path.read_text(encoding="utf-8") if original_path.is_file() else ""
                    repaired_code = repaired_path.read_text(encoding="utf-8") if repaired_path.is_file() else ""
                    comparison = "".join(difflib.unified_diff(
                        original_code.splitlines(keepends=True),
                        repaired_code.splitlines(keepends=True),
                        fromfile=f"original/{scenario['original']}",
                        tofile=f"candidate/{scenario['original']}",
                    )) if original_code and repaired_code else ""
                verification = response.get("verification") or {}
                passed = verification.get("final_passed", -1)
                failed = verification.get("final_failed", -1)
                # Require the correct test count, not merely a successful process exit.
                verified = bool(response.get("verified")) and (
                    verification.get("verdict") == "verified_fixed"
                    and passed == scenario["tests"]
                    and failed == 0
                )
                st.session_state.rc_result = {
                    "scenario_id": chosen,
                    "verified": verified,
                    "financial": response.get("financial") or {},
                    "verification": verification,
                    "patch": response.get("patch") or {},
                    "logs": scrub_logs(response.get("logs")),
                    "diff": comparison if verified else "",
                }
            except Exception as error:
                st.session_state.rc_result = {
                    "scenario_id": chosen,
                    "verified": False,
                    "financial": {}, "verification": {}, "patch": {},
                    "diff": "", "logs": f"Workflow failed: {type(error).__name__}: {error}",
                }
            finally:
                lock.release()

    outcome = st.session_state.get("rc_result")
    if outcome and outcome.get("scenario_id") == chosen:
        st.write("")
        show_html("<div class='rc-section' style='padding-top:3px'><div class='rc-eyebrow'>Investigation report</div><div class='rc-heading'>Analysis and verification</div></div>")
        if outcome["verified"]:
            st.success(f"Candidate repair VERIFIED: all {scenario['tests']} protected regression tests passed in Nebius Sandbox.")
        else:
            st.error("No verified repair obtained for this run. See the execution logs below for diagnostic details.")
        financial = outcome["financial"]
        verification = outcome["verification"]
        patch = outcome["patch"]
        is_precision = chosen == "monetary_precision"
        if financial:
            a, b, c = st.columns(3)
            a.metric("Financial discrepancy", money(financial.get("discrepancy"), precision=is_precision))
            b.metric("Actual calculated total", money(financial.get("actual_total"), precision=is_precision))
            c.metric("Expected total", money(financial.get("expected_total"), precision=is_precision))
            if is_precision:
                st.caption("Precision values are shown at their original decimal representation; currency rounding to 2 decimals can hide tiny errors.")
        investigation_tab, repair_tab, verification_tab = st.tabs([
            "01 · Diagnosis", "02 · AI-generated repair", "03 · Sandbox evidence"
        ])
        with investigation_tab:
            st.subheader("Financial diagnosis")
            st.write("**Scenario:**", scenario["title"])
            st.write("**Investigator assessment:**", financial.get("issue_type", "Not available"))
            if is_precision:
                st.info("This case targets floating-point drift; the independent precision tests establish whether the defect is fixed.")
            st.write("**Affected transactions:**")
            st.code(json.dumps(financial.get("affected_transactions", []), indent=2, default=str), language="json")
        with repair_tab:
            st.subheader("NVIDIA Nemotron repair")
            if patch:
                st.write("**Root cause:**", patch.get("root_cause", "Not provided"))
                st.write("**Explanation:**", patch.get("explanation", "Not provided"))
                st.code(str(patch.get("proposed_code", "")), language="python")
            else:
                st.info("No patch was returned for this run.")
            if outcome["diff"]:
                with st.expander("View code differences — original vs candidate", expanded=True):
                    st.code(outcome["diff"], language="diff")
        with verification_tab:
            st.subheader("Independent sandbox verification")
            x, y, z = st.columns(3)
            x.metric("Baseline tests failed", verification.get("baseline_failed", "—"))
            y.metric("Candidate tests passed", verification.get("final_passed", "—"))
            z.metric("Candidate tests failed", verification.get("final_failed", "—"))
            st.write("**Verdict:**", verification.get("verdict", "Not available"))
            if "elapsed_seconds" in verification:
                st.write("**Sandbox verification time:**", str(verification["elapsed_seconds"]) + " s")
            if "attempts" in verification:
                st.write("**AI patch attempts:**", verification["attempts"])
            with st.expander("View execution logs", expanded=not outcome["verified"]):
                st.code(outcome["logs"][-18000:] or "No logs were captured.", language="text")
        st.download_button(
            "Download investigation report (JSON)",
            data=json.dumps(safe_report(outcome), indent=2, default=str),
            file_name=f"rootcause_{chosen}_report.json",
            mime="application/json",
            key=f"download_{chosen}",
        )
        st.caption("This demo only verifies candidate repairs against its scenario-specific regression tests. It does not deploy fixes into production systems.")

show_html("""
<div class='rc-footer'><div><strong>RootCause AI</strong> · Autonomous Financial Software Debugging</div><div>Powered by NVIDIA Nemotron + Nebius Sandboxes · Synthetic demonstration data</div></div>
""")
