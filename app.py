import streamlit as st
import pandas as pd
import numpy as np
import datetime
import random
import anthropic
import json
import re

st.set_page_config(
    page_title="Finoptions Intelligence Pro",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── GLOBAL CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

:root {
  --bg: #f5f6f8;
  --surface: #ffffff;
  --surface2: #f0f2f5;
  --border: #e2e5ea;
  --border2: #cdd1d8;
  --text: #111318;
  --muted: #6b7280;
  --muted2: #4b5563;
  --green: #16a34a;
  --green-bg: rgba(22,163,74,0.08);
  --green-border: rgba(22,163,74,0.22);
  --amber: #d97706;
  --amber-bg: rgba(217,119,6,0.08);
  --amber-border: rgba(217,119,6,0.22);
  --red: #dc2626;
  --red-bg: rgba(220,38,38,0.07);
  --red-border: rgba(220,38,38,0.20);
  --blue: #2563eb;
  --blue-bg: rgba(37,99,235,0.07);
  --blue-border: rgba(37,99,235,0.20);
  --purple: #7c3aed;
  --purple-bg: rgba(124,58,237,0.07);
  --accent: #16a34a;
}

html, body, [data-testid="stAppViewContainer"] {
  background: var(--bg) !important;
  color: var(--text) !important;
  font-family: 'DM Sans', sans-serif !important;
}

[data-testid="stHeader"] { background: var(--bg) !important; border-bottom: 1px solid var(--border) !important; }
[data-testid="stSidebar"] { background: var(--surface) !important; border-right: 1px solid var(--border) !important; }

.block-container { padding: 2rem 2.5rem !important; max-width: 1400px !important; }

h1, h2, h3 { font-family: 'DM Serif Display', serif !important; font-weight: 400 !important; color: var(--text) !important; }

/* ── TOP HEADER ── */
.top-header {
  display: flex; align-items: flex-start; justify-content: space-between;
  border-bottom: 1px solid var(--border); padding-bottom: 1.5rem; margin-bottom: 2rem;
}
.top-header-left .eyebrow {
  font-size: 11px; letter-spacing: .12em; text-transform: uppercase;
  color: var(--accent); font-family: 'DM Mono', monospace; margin-bottom: 6px;
}
.top-header-left h1 {
  font-size: 2rem !important; line-height: 1.15; margin: 0 !important; padding: 0 !important;
}
.top-header-left .subtitle { font-size: 13px; color: var(--muted); margin-top: 6px; }
.live-badge {
  display: inline-flex; align-items: center; gap: 6px;
  background: var(--green-bg); border: 1px solid var(--green-border);
  color: var(--green); font-size: 11px; font-family: 'DM Mono', monospace;
  padding: 5px 12px; border-radius: 20px; margin-top: 4px;
}
.live-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--green); animation: pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }

/* ── KPI CARDS ── */
.kpi-row { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 2rem; }
.kpi-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 12px; padding: 1.2rem 1.4rem; cursor: pointer;
  transition: border-color .2s, background .2s; position: relative; overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,.05);
}
.kpi-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
}
.kpi-card.green::before { background: var(--green); }
.kpi-card.amber::before { background: var(--amber); }
.kpi-card.red::before { background: var(--red); }
.kpi-card.blue::before { background: var(--blue); }
.kpi-card.purple::before { background: var(--purple); }
.kpi-card:hover { border-color: var(--border2); background: var(--surface2); box-shadow: 0 2px 8px rgba(0,0,0,.06); }
.kpi-label { font-size: 10px; letter-spacing: .1em; text-transform: uppercase; font-family: 'DM Mono', monospace; margin-bottom: 10px; }
.kpi-card.green .kpi-label { color: var(--green); }
.kpi-card.amber .kpi-label { color: var(--amber); }
.kpi-card.red .kpi-label { color: var(--red); }
.kpi-card.blue .kpi-label { color: var(--blue); }
.kpi-card.purple .kpi-label { color: var(--purple); }
.kpi-val { font-family: 'DM Serif Display', serif; font-size: 2rem; line-height: 1; color: var(--text); margin-bottom: 6px; }
.kpi-sub { font-size: 11px; color: var(--muted); }
.kpi-delta { font-size: 11px; font-family: 'DM Mono', monospace; margin-top: 8px; }
.kpi-card.green .kpi-delta { color: var(--green); }
.kpi-card.amber .kpi-delta { color: var(--amber); }
.kpi-card.red .kpi-delta { color: var(--red); }
.kpi-card.blue .kpi-delta { color: var(--blue); }
.kpi-card.purple .kpi-delta { color: var(--purple); }

/* ── AI INSIGHT PANEL ── */
.ai-panel {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem; position: relative;
  box-shadow: 0 1px 4px rgba(0,0,0,.05);
}
.ai-panel-header {
  display: flex; align-items: center; gap: 10px; margin-bottom: 1rem;
}
.ai-tag {
  font-size: 10px; letter-spacing: .1em; text-transform: uppercase;
  font-family: 'DM Mono', monospace; color: var(--purple);
  background: var(--purple-bg); border: 1px solid rgba(124,58,237,.2);
  padding: 3px 10px; border-radius: 20px;
}
.ai-model { font-size: 11px; color: var(--muted); font-family: 'DM Mono', monospace; }
.ai-body {
  font-size: 14px; line-height: 1.8; color: #374151;
  font-style: italic; border-left: 2px solid var(--purple); padding-left: 1.2rem;
}

/* ── SECTION HEADER ── */
.section-head {
  display: flex; align-items: baseline; gap: 12px;
  margin-bottom: 1rem; margin-top: 2rem;
}
.section-head h3 { font-size: 1.1rem !important; margin: 0 !important; }
.section-head .count {
  font-size: 11px; font-family: 'DM Mono', monospace;
  color: var(--muted); background: var(--surface2);
  border: 1px solid var(--border); padding: 2px 8px; border-radius: 20px;
}

/* ── CLIENT TABLE ── */
.client-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.client-table thead th {
  text-align: left; padding: 10px 14px; color: var(--muted);
  font-size: 10px; letter-spacing: .08em; text-transform: uppercase;
  font-family: 'DM Mono', monospace; border-bottom: 1px solid var(--border);
  font-weight: 400;
}
.client-table tbody tr {
  border-bottom: 1px solid var(--border); transition: background .12s; cursor: pointer;
}
.client-table tbody tr:hover { background: #f0f4ff; }
.client-table tbody td { padding: 11px 14px; color: var(--text); }
.client-name { font-weight: 500; }
.score-chip {
  font-family: 'DM Mono', monospace; font-size: 12px; font-weight: 500;
  padding: 3px 10px; border-radius: 20px; display: inline-block;
}
.chip-high { background: var(--green-bg); color: var(--green); border: 1px solid var(--green-border); }
.chip-medium { background: var(--amber-bg); color: var(--amber); border: 1px solid var(--amber-border); }
.chip-low { background: var(--red-bg); color: var(--red); border: 1px solid var(--red-border); }
.bar-wrap { display: inline-flex; align-items: center; gap: 8px; }
.mini-bar { height: 4px; border-radius: 2px; background: var(--border2); width: 56px; display: inline-block; position: relative; vertical-align: middle; overflow: hidden; }
.mini-fill { height: 100%; border-radius: 2px; position: absolute; left: 0; top: 0; }
.flag-pill {
  font-size: 10px; padding: 2px 7px; border-radius: 10px; margin-right: 3px;
  background: var(--surface2); color: var(--muted2); border: 1px solid var(--border);
  display: inline-block;
}

/* ── ACTION CARDS ── */
.action-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 12px; padding: 1.2rem 1.4rem; margin-bottom: 10px;
  display: flex; gap: 14px; align-items: flex-start;
}
.action-icon {
  width: 38px; height: 38px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 17px; flex-shrink: 0;
}
.action-icon.green { background: var(--green-bg); }
.action-icon.amber { background: var(--amber-bg); }
.action-icon.red { background: var(--red-bg); }
.action-icon.blue { background: var(--blue-bg); }
.action-body { flex: 1; }
.action-title { font-size: 13px; font-weight: 600; color: var(--text); margin-bottom: 4px; }
.action-desc { font-size: 12px; color: var(--muted2); line-height: 1.6; }
.action-tag {
  font-size: 10px; padding: 2px 8px; border-radius: 10px;
  font-family: 'DM Mono', monospace; margin-left: 8px; vertical-align: middle;
}

/* ── EVENT CARDS ── */
.event-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 2rem; }
.event-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 12px; padding: 1.2rem;
}
.event-card h4 { font-size: 13px; font-weight: 600; margin-bottom: 6px; }
.event-card p { font-size: 12px; color: var(--muted2); line-height: 1.6; margin-bottom: 10px; }
.event-meta { font-size: 11px; font-family: 'DM Mono', monospace; color: var(--muted); }

/* ── UPLOAD ZONE ── */
.upload-outer {
  max-width: 620px; margin: 4rem auto; text-align: center;
}
.upload-eyebrow {
  font-size: 11px; letter-spacing: .14em; text-transform: uppercase;
  font-family: 'DM Mono', monospace; color: var(--accent); margin-bottom: 1rem;
}
.upload-title { font-family: 'DM Serif Display', serif; font-size: 2.2rem; line-height: 1.2; margin-bottom: .75rem; color: var(--text); }
.upload-sub { font-size: 14px; color: var(--muted); margin-bottom: 2rem; }
.upload-box {
  border: 1.5px dashed var(--border2); border-radius: 16px;
  padding: 2.5rem; margin-bottom: 1.5rem; transition: border-color .2s;
  background: var(--surface); box-shadow: 0 1px 4px rgba(0,0,0,.06);
}

/* ── WA BUTTON ── */
.wa-btn {
  display: inline-flex; align-items: center; gap: 6px;
  background: rgba(37,211,102,.12); border: 1px solid rgba(37,211,102,.3);
  color: #25d366; font-size: 12px; font-weight: 500;
  padding: 5px 12px; border-radius: 8px; text-decoration: none;
  font-family: 'DM Mono', monospace;
}

/* ── STREAMLIT OVERRIDES ── */
.stButton > button {
  background: var(--surface) !important; border: 1px solid var(--border2) !important;
  color: var(--text) !important; font-family: 'DM Sans', sans-serif !important;
  font-size: 12px !important; font-weight: 500 !important;
  border-radius: 8px !important; padding: 6px 14px !important;
  box-shadow: 0 1px 2px rgba(0,0,0,.05) !important;
}
.stButton > button:hover { background: var(--surface2) !important; }
.stSelectbox > div > div { background: var(--surface) !important; border-color: var(--border) !important; color: var(--text) !important; border-radius: 8px !important; }
.stTextInput > div > div > input { background: var(--surface) !important; border-color: var(--border) !important; color: var(--text) !important; border-radius: 8px !important; }
div[data-testid="stFileUploader"] { background: var(--surface) !important; border: 1.5px dashed var(--border2) !important; border-radius: 12px !important; padding: 1rem !important; }
div[data-testid="stFileUploader"] label { color: var(--muted2) !important; font-size: 13px !important; }
.stAlert { background: var(--surface) !important; border-color: var(--border) !important; color: var(--muted2) !important; border-radius: 8px !important; }
.stSuccess { border-left: 3px solid var(--green) !important; }
.stInfo { border-left: 3px solid var(--blue) !important; }
.stWarning { border-left: 3px solid var(--amber) !important; }
div[data-testid="stMetric"] { background: transparent !important; }
[data-testid="stMarkdownContainer"] p { color: var(--muted2) !important; font-size: 13px !important; }
.stTabs [data-baseweb="tab-list"] { background: var(--surface2) !important; border-radius: 10px !important; padding: 4px !important; border: 1px solid var(--border) !important; }
.stTabs [data-baseweb="tab"] { color: var(--muted) !important; font-size: 13px !important; font-family: 'DM Sans' !important; border-radius: 8px !important; }
.stTabs [aria-selected="true"] { background: var(--surface) !important; color: var(--text) !important; box-shadow: 0 1px 3px rgba(0,0,0,.08) !important; }
hr { border-color: var(--border) !important; }
textarea { background: var(--surface) !important; border-color: var(--border) !important; color: var(--text) !important; border-radius: 8px !important; }
.stRadio label { color: var(--muted2) !important; font-size: 13px !important; }
</style>
""", unsafe_allow_html=True)

# ── HELPERS ────────────────────────────────────────────────────────────────

def fmt_inr(val):
    n = float(val or 0)
    if n >= 1e7: return f"₹{n/1e7:.1f}Cr"
    if n >= 1e5: return f"₹{n/1e5:.1f}L"
    if n >= 1e3: return f"₹{n/1e3:.0f}K"
    return f"₹{n:.0f}"

def num(v):
    try: return float(str(v).replace(",","").replace("₹","").strip())
    except: return 0.0

def months_ago(d):
    if not d or str(d).strip() == "": return 99
    try:
        dt = pd.to_datetime(d, dayfirst=True)
        return max(0, (datetime.datetime.now() - dt).days / 30)
    except: return 99

def detect_col(hints, cols):
    for c in cols:
        cl = c.lower().replace(" ","").replace("_","")
        for h in hints:
            if h in cl: return c
    return None

def score_client(row):
    p = num(row.get("portfolio", 0))
    sip = num(row.get("sip", 0))
    age = int(row.get("age") or 0)
    tenure_raw = row.get("tenure", "")
    try:
        yr = int(str(tenure_raw).strip())
        tenure_yrs = (2025 - yr) if yr > 1990 else yr
    except: tenure_yrs = 0
    ma = months_ago(row.get("lastContact", ""))
    nominee = str(row.get("nominee", "")).lower()
    goal = str(row.get("goal", "")).lower()

    s = 40
    if p > 8e6: s += 28
    elif p > 4e6: s += 20
    elif p > 1.5e6: s += 13
    elif p > 5e5: s += 7

    if sip > 20000: s += 18
    elif sip > 10000: s += 13
    elif sip > 3000: s += 8
    elif sip > 0: s += 4

    if ma < 1: s += 15
    elif ma < 3: s += 10
    elif ma < 6: s += 5
    elif ma > 12: s -= 18
    elif ma > 6: s -= 10

    if tenure_yrs > 15: s += 15
    elif tenure_yrs > 8: s += 10
    elif tenure_yrs > 3: s += 5

    if nominee == "no": s -= 8
    if "bond" in goal: s += 5
    if age > 55 and "lic" in goal: s += 5
    if sip == 0 and p > 5e5: s -= 5

    return max(0, min(100, round(s)))

def churn_risk(row):
    r = 0
    ma = months_ago(row.get("lastContact",""))
    sip = num(row.get("sip",0))
    nominee = str(row.get("nominee","")).lower()
    try:
        yr = int(str(row.get("tenure","2020")).strip())
        tenure_yrs = (2025 - yr) if yr > 1990 else yr
    except: tenure_yrs = 5

    if ma > 12: r += 40
    elif ma > 6: r += 25
    elif ma > 3: r += 10
    if sip == 0: r += 20
    if nominee == "no": r += 15
    if tenure_yrs < 2: r += 15
    return min(100, round(r))

def build_flags(row):
    f = []
    p = num(row.get("portfolio", 0))
    sip = num(row.get("sip", 0))
    ma = months_ago(row.get("lastContact",""))
    nominee = str(row.get("nominee","")).lower()
    if p > 5e6: f.append("HNI")
    if ma > 6: f.append("Inactive 6m+")
    if sip == 0 and p > 5e5: f.append("SIP gap")
    if nominee == "no": f.append("No nominee")
    if churn_risk(row) > 55: f.append("Churn risk")
    return f

FIELDS = [
    ("name",        ["name","client","naam","clientname"]),
    ("age",         ["age","umur","ayu"]),
    ("portfolio",   ["portfolio","aum","value","investment","amount","total"]),
    ("sip",         ["sip","monthly","sipamount"]),
    ("lastContact", ["last","date","meeting","contact","interaction","lastdate"]),
    ("goal",        ["product","goal","scheme","type"]),
    ("tenure",      ["since","tenure","year","startyear","clientsince"]),
    ("nominee",     ["nominee","nomination"]),
]

# ── AI INSIGHT ─────────────────────────────────────────────────────────────

def get_ai_insight(clients_df, summary):
    try:
        client_obj = anthropic.Anthropic()
        hni = summary["hni"]
        churn = summary["churn"]
        no_sip = summary["no_sip"]
        top = summary["top"]
        aum = summary["aum"]
        total = summary["total"]

        # Random perspective angle for variety
        angles = [
            "Focus on portfolio risk concentration and what the advisor must protect first.",
            "Focus on the single biggest revenue opportunity hiding in plain sight.",
            "Focus on client relationship health and which relationships are silently degrading.",
            "Focus on what the data reveals about the advisor's business trajectory in next 90 days.",
            "Focus on the surprising pattern in this portfolio that most advisors would miss.",
        ]
        angle = random.choice(angles)

        prompt = f"""You are a senior portfolio analyst with 20 years in Indian wealth management — IIM-trained, ex-HDFC Securities, now independent. You speak with precision, no fluff, no corporate jargon.

Portfolio snapshot you're analysing:
- Total clients: {total} | Total AUM: {fmt_inr(aum)}
- HNI clients (AUM >₹50L): {hni}
- Clients with churn probability >50%: {churn}
- Clients with no SIP despite having portfolio: {no_sip}
- Top-ranked client by ML score: {top.get('name','N/A')}, score {top.get('score',0)}/100, portfolio {fmt_inr(top.get('portfolio',0))}

Instruction: {angle}

Write a 4-sentence intelligence brief. Each sentence must be specific — cite actual numbers from the data above. Sound like you're briefing a colleague over coffee, not writing a report. No bullet points. No headers. No "I". No "it is important to note". Vary your sentence structure dramatically — mix short punchy observations with longer analytical ones. Start with something that surprises."""

        msg = client_obj.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=350,
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text.strip()
    except Exception as e:
        return f"Could not generate insight — check API connection. ({e})"

def get_action_insight(client_name, portfolio, sip, score, churn, flags, goal):
    try:
        client_obj = anthropic.Anthropic()
        prompt = f"""You are a senior financial advisor's trusted data science partner. A client profile just came up for action planning.

Client: {client_name}
Portfolio: {fmt_inr(portfolio)} | Monthly SIP: {fmt_inr(sip) if sip > 0 else "none"}
ML Score: {score}/100 | Churn Risk: {churn}%
Flags: {', '.join(flags) if flags else 'none'}
Product: {goal}

Write ONE sentence — a specific, human-sounding recommended action for this client. Sound like an experienced advisor, not a bot. Be specific. Do not use the client's name more than once. No fluff."""

        msg = client_obj.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=120,
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text.strip()
    except:
        return "Review portfolio and schedule a personalised call this week."

# ── UPLOAD SCREEN ──────────────────────────────────────────────────────────

def show_upload():
    st.markdown("""
    <div class="upload-outer">
      <div class="upload-eyebrow">◆ Finoptions Intelligence Pro</div>
      <div class="upload-title">Your clients,<br><em>intelligently ranked.</em></div>
      <div class="upload-sub">Upload any Excel or CSV — the engine maps your columns, scores every client with ML, and surfaces what your data is actually telling you.</div>
    </div>
    """, unsafe_allow_html=True)

    col_center = st.columns([1, 2, 1])[1]
    with col_center:
        uploaded = st.file_uploader("", type=["xlsx","xls","csv"], label_visibility="collapsed")
        st.markdown("<div style='text-align:center;margin-top:.5rem'><span style='font-size:12px;color:#7a8394'>Supports .xlsx · .xls · .csv · Any column format</span></div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Load sample dataset →", use_container_width=True):
            st.session_state.demo = True
            st.session_state.pop("ai_insight", None)
            st.session_state.pop("ai_insight_stale", None)
            st.rerun()

    return uploaded

# ── MAP COLUMNS SCREEN ─────────────────────────────────────────────────────

def show_mapping(df):
    cols = df.columns.tolist()
    st.markdown("### Map your columns")
    st.markdown("<p style='color:#7a8394;font-size:13px;margin-top:-8px'>Auto-detected where possible — adjust if needed.</p>", unsafe_allow_html=True)

    mapping = {}
    grid = st.columns(2)
    for i, (key, hints) in enumerate(FIELDS):
        best = detect_col(hints, cols)
        with grid[i % 2]:
            label_map = {
                "name":"Client name","age":"Age","portfolio":"Portfolio / AUM",
                "sip":"Monthly SIP","lastContact":"Last contact date",
                "goal":"Product / goal","tenure":"Client since (year)","nominee":"Nominee updated"
            }
            options = ["— skip —"] + cols
            default_idx = (cols.index(best) + 1) if best and best in cols else 0
            sel = st.selectbox(label_map[key], options, index=default_idx, key=f"map_{key}")
            mapping[key] = sel if sel != "— skip —" else None

    if st.button("Run intelligence engine →", use_container_width=False):
        st.session_state.mapping = mapping
        st.session_state.raw_df = df
        st.session_state.screen = "dashboard"
        st.session_state.pop("ai_insight", None)
        st.session_state.pop("ai_insight_stale", None)
        st.rerun()

# ── PROCESS DATA ───────────────────────────────────────────────────────────

def process(raw_df, mapping):
    clients = []
    default_fields = {
        "name": "", "age": "", "portfolio": "0", "sip": "0",
        "lastContact": "", "goal": "", "tenure": "2020", "nominee": ""
    }
    for _, row in raw_df.iterrows():
        c = dict(default_fields)
        for key, _ in FIELDS:
            col = mapping.get(key)
            if col and col in raw_df.columns and pd.notna(row[col]):
                c[key] = str(row[col]).strip()
        c["score"] = score_client(c)
        c["churn"] = churn_risk(c)
        c["priority"] = "High" if c["score"] >= 70 else ("Medium" if c["score"] >= 45 else "Low")
        c["flags"] = build_flags(c)
        clients.append(c)
    clients.sort(key=lambda x: x.get("score", 0), reverse=True)
    return clients

# ── DEMO DATA ──────────────────────────────────────────────────────────────

DEMO_CLIENTS = [
    {"name":"Ramesh Patel","age":"62","portfolio":"4800000","sip":"15000","lastContact":"2024-01-10","goal":"MF+LIC","tenure":"2010","nominee":"Yes"},
    {"name":"Sunita Shah","age":"45","portfolio":"1200000","sip":"8000","lastContact":"2023-09-20","goal":"MF","tenure":"2018","nominee":"No"},
    {"name":"Dinesh Mehta","age":"38","portfolio":"350000","sip":"5000","lastContact":"2024-02-28","goal":"SIP","tenure":"2022","nominee":"No"},
    {"name":"Kavita Joshi","age":"55","portfolio":"7200000","sip":"25000","lastContact":"2024-03-01","goal":"MF+Bonds+LIC","tenure":"2008","nominee":"Yes"},
    {"name":"Arun Trivedi","age":"48","portfolio":"900000","sip":"0","lastContact":"2023-06-15","goal":"LIC","tenure":"2015","nominee":"No"},
    {"name":"Priya Desai","age":"32","portfolio":"180000","sip":"4000","lastContact":"2024-02-10","goal":"SIP","tenure":"2023","nominee":"No"},
    {"name":"Hemant Rao","age":"67","portfolio":"9500000","sip":"0","lastContact":"2023-11-20","goal":"Bonds+LIC","tenure":"2005","nominee":"Yes"},
    {"name":"Nisha Gupta","age":"41","portfolio":"2100000","sip":"12000","lastContact":"2024-01-25","goal":"MF+LIC","tenure":"2016","nominee":"Yes"},
    {"name":"Vijay Solanki","age":"50","portfolio":"650000","sip":"6000","lastContact":"2023-08-10","goal":"MF","tenure":"2019","nominee":"No"},
    {"name":"Rekha Jain","age":"58","portfolio":"3400000","sip":"0","lastContact":"2023-12-05","goal":"LIC+Bonds","tenure":"2011","nominee":"Yes"},
    {"name":"Bhavesh Modi","age":"44","portfolio":"520000","sip":"7500","lastContact":"2024-03-10","goal":"MF","tenure":"2020","nominee":"No"},
    {"name":"Geeta Sharma","age":"61","portfolio":"6100000","sip":"20000","lastContact":"2023-10-15","goal":"MF+LIC+Bonds","tenure":"2007","nominee":"Yes"},
    {"name":"Kalpesh Vora","age":"36","portfolio":"210000","sip":"3000","lastContact":"2024-01-30","goal":"SIP","tenure":"2023","nominee":"No"},
    {"name":"Manisha Patel","age":"53","portfolio":"2900000","sip":"10000","lastContact":"2023-07-22","goal":"LIC+MF","tenure":"2013","nominee":"Yes"},
    {"name":"Suresh Agrawal","age":"70","portfolio":"12000000","sip":"0","lastContact":"2023-05-10","goal":"Bonds+LIC","tenure":"2002","nominee":"Yes"},
    {"name":"Hetal Trivedi","age":"39","portfolio":"430000","sip":"6000","lastContact":"2024-02-20","goal":"MF","tenure":"2021","nominee":"No"},
    {"name":"Jigar Shah","age":"47","portfolio":"1750000","sip":"9000","lastContact":"2023-12-18","goal":"MF+LIC","tenure":"2017","nominee":"No"},
    {"name":"Archana Desai","age":"56","portfolio":"4200000","sip":"0","lastContact":"2023-09-05","goal":"LIC+Bonds","tenure":"2009","nominee":"Yes"},
    {"name":"Nilesh Mehta","age":"33","portfolio":"95000","sip":"2000","lastContact":"2024-03-05","goal":"SIP","tenure":"2024","nominee":"No"},
    {"name":"Pushpa Rao","age":"64","portfolio":"5500000","sip":"15000","lastContact":"2024-02-01","goal":"MF+LIC+Bonds","tenure":"2006","nominee":"Yes"},
]

def prepare_demo():
    clients = []
    for c in DEMO_CLIENTS:
        c2 = dict(c)
        c2["score"] = score_client(c2)
        c2["churn"] = churn_risk(c2)
        c2["priority"] = "High" if c2["score"] >= 70 else ("Medium" if c2["score"] >= 45 else "Low")
        c2["flags"] = build_flags(c2)
        clients.append(c2)
    clients.sort(key=lambda x: x.get("score", 0), reverse=True)
    return clients

# ── DASHBOARD ──────────────────────────────────────────────────────────────

def show_dashboard(clients):
    total_aum = sum(num(c.get("portfolio", 0)) for c in clients)
    high = [c for c in clients if c.get("priority", "Low") == "High"]
    churn_risk_list = [c for c in clients if c.get("churn", 0) > 50]
    sip_gap = [c for c in clients if "SIP gap" in c.get("flags", [])]
    no_nom = [c for c in clients if "No nominee" in c.get("flags", [])]
    hni = [c for c in clients if "HNI" in c.get("flags", [])]
    top = clients[0] if clients else {}

    # ── HEADER ──
    st.markdown(f"""
    <div class="top-header">
      <div class="top-header-left">
        <div class="eyebrow">◆ Intelligence Engine · Active</div>
        <h1>Client Portfolio Intelligence</h1>
        <div class="subtitle">{len(clients)} clients · {fmt_inr(total_aum)} total AUM · ML scoring active</div>
      </div>
      <div>
        <div class="live-badge"><span class="live-dot"></span>Live · {datetime.datetime.now().strftime('%d %b %Y')}</div>
        <br>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI CARDS ──
    st.markdown(f"""
    <div class="kpi-row">
      <div class="kpi-card green">
        <div class="kpi-label">Total AUM</div>
        <div class="kpi-val">{fmt_inr(total_aum)}</div>
        <div class="kpi-sub">{len(clients)} clients tracked</div>
        <div class="kpi-delta">↑ Portfolio pipeline</div>
      </div>
      <div class="kpi-card blue">
        <div class="kpi-label">High Priority</div>
        <div class="kpi-val">{len(high)}</div>
        <div class="kpi-sub">ML score ≥ 70/100</div>
        <div class="kpi-delta">{round(len(high)/len(clients)*100) if clients else 0}% of base · convert now</div>
      </div>
      <div class="kpi-card red">
        <div class="kpi-label">Churn Risk</div>
        <div class="kpi-val">{len(churn_risk_list)}</div>
        <div class="kpi-sub">Probability &gt; 50%</div>
        <div class="kpi-delta">⚠ Urgent action needed</div>
      </div>
      <div class="kpi-card amber">
        <div class="kpi-label">SIP Gap</div>
        <div class="kpi-val">{len(sip_gap)}</div>
        <div class="kpi-sub">No SIP · have portfolio</div>
        <div class="kpi-delta">Revenue opportunity</div>
      </div>
      <div class="kpi-card purple">
        <div class="kpi-label">No Nominee</div>
        <div class="kpi-val">{len(no_nom)}</div>
        <div class="kpi-sub">Compliance exposure</div>
        <div class="kpi-delta">Regulatory follow-up</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── AI INSIGHT ──
    summary = {
        "hni": len(hni), "churn": len(churn_risk_list),
        "no_sip": len(sip_gap), "top": top,
        "aum": total_aum, "total": len(clients)
    }

    with st.spinner(""):
        if "ai_insight" not in st.session_state or st.session_state.get("ai_insight_stale"):
            insight = get_ai_insight(clients, summary)
            st.session_state.ai_insight = insight
            st.session_state.ai_insight_stale = False
        else:
            insight = st.session_state.ai_insight

    st.markdown(f"""
    <div class="ai-panel">
      <div class="ai-panel-header">
        <span class="ai-tag">AI Intelligence Brief</span>
        <span class="ai-model">claude-sonnet · fresh every session</span>
      </div>
      <div class="ai-body">{insight}</div>
    </div>
    """, unsafe_allow_html=True)

    col_r, _ = st.columns([1, 5])
    with col_r:
        if st.button("Refresh brief ↺"):
            st.session_state.ai_insight_stale = True
            st.rerun()

    # ── TABS ──
    tab1, tab2, tab3, tab4 = st.tabs(["Priority ranking", "Smart actions", "Event intelligence", "WhatsApp drafts"])

    # ─ TAB 1: CLIENT TABLE ─
    with tab1:
        filter_options = ["All clients", "High priority", "Medium", "Low", "Churn risk", "SIP gap", "No nominee"]
        filter_sel = st.selectbox("Filter", filter_options, label_visibility="collapsed")

        filtered = clients
        if filter_sel == "High priority": filtered = [c for c in clients if c.get("priority", "Low") == "High"]
        elif filter_sel == "Medium": filtered = [c for c in clients if c.get("priority", "Low") == "Medium"]
        elif filter_sel == "Low": filtered = [c for c in clients if c.get("priority", "Low") == "Low"]
        elif filter_sel == "Churn risk": filtered = [c for c in clients if c.get("churn", 0) > 50]
        elif filter_sel == "SIP gap": filtered = [c for c in clients if "SIP gap" in c.get("flags", [])]
        elif filter_sel == "No nominee": filtered = [c for c in clients if "No nominee" in c.get("flags", [])]

        st.markdown(f"<div style='font-size:12px;color:#7a8394;margin-bottom:.75rem'>Showing {len(filtered)} of {len(clients)} clients</div>", unsafe_allow_html=True)

        rows_html = ""
        for i, c in enumerate(filtered):
            chip_cls = "chip-high" if c.get("priority", "Low")=="High" else ("chip-medium" if c.get("priority", "Low")=="Medium" else "chip-low")
            fill_color = "#22c55e" if c.get("score", 0)>=70 else ("#f59e0b" if c.get("score", 0)>=45 else "#ef4444")
            churn_color = "#ef4444" if c.get("churn", 0)>60 else ("#f59e0b" if c.get("churn", 0)>30 else "#22c55e")
            flags_html = "".join(f'<span class="flag-pill">{f}</span>' for f in c.get("flags", [])[:2])
            rank_icon = "◆" if i == 0 else ("◇" if i == 1 else ("△" if i == 2 else f"#{i+1}"))
            rows_html += f"""<tr>
              <td style="color:#7a8394;font-family:'DM Mono',monospace;font-size:12px;width:44px">{rank_icon}</td>
              <td class="client-name">{c['name'] or '—'}</td>
              <td style="font-family:'DM Mono',monospace;font-size:12px">{fmt_inr(c['portfolio'])}</td>
              <td style="font-family:'DM Mono',monospace;font-size:12px">{fmt_inr(c['sip']) if num(c['sip'])>0 else '—'}</td>
              <td>
                <div class="bar-wrap">
                  <span style="font-family:'DM Mono',monospace;font-size:12px;min-width:28px">{c['score']}</span>
                  <span class="mini-bar"><span class="mini-fill" style="width:{c['score']}%;background:{fill_color}"></span></span>
                </div>
              </td>
              <td><span class="score-chip {chip_cls}">{c['priority']}</span></td>
              <td style="font-family:'DM Mono',monospace;font-size:11px;color:{churn_color}">{c['churn']}%</td>
              <td>{flags_html}</td>
            </tr>"""

        st.markdown(f"""
        <table class="client-table">
          <thead><tr>
            <th></th><th>Client</th><th>Portfolio</th><th>SIP/mo</th>
            <th>ML Score</th><th>Priority</th><th>Churn</th><th>Flags</th>
          </tr></thead>
          <tbody>{rows_html}</tbody>
        </table>
        """, unsafe_allow_html=True)

    # ─ TAB 2: SMART ACTIONS ─
    with tab2:
        top4 = clients[:4]
        inactive = [c for c in clients if "Inactive 6m+" in c.get("flags", [])][:2]
        sip_opp = [c for c in clients if "SIP gap" in c.get("flags", [])][:2]
        no_nom_list = [c for c in clients if "No nominee" in c.get("flags", [])][:2]

        actions = [
            {
                "icon": "◆", "cls": "green",
                "title": f"Immediate revenue — pitch {top4[0]['name'] if top4 else 'top client'} now",
                "desc": f"ML score {top4[0]['score'] if top4 else 0}/100. Portfolio {fmt_inr(top4[0]['portfolio'] if top4 else 0)} with strongest recency signals in your base. Recommend MF top-up or capital gain bond this week.",
                "tag": "High ROI", "tag_color": "#22c55e"
            },
            {
                "icon": "⚠", "cls": "red",
                "title": f"Churn prevention — {len(churn_risk_list)} clients at risk of leaving",
                "desc": f"{', '.join(c['name'] for c in churn_risk_list[:2])} haven't engaged in 6+ months. At this stage withdrawal probability rises 3× per month of inactivity. A personalised portfolio review call — not a sales call — is the right move.",
                "tag": "Urgent", "tag_color": "#ef4444"
            },
            {
                "icon": "↑", "cls": "amber",
                "title": f"SIP upgrade — {len(sip_gap)} HNI clients with zero SIP",
                "desc": f"{', '.join(c['name'] for c in sip_gap[:2])} hold significant portfolios with no systematic plan. A 10-minute compound growth projection demo converts over 60% of these cases historically.",
                "tag": "Growth", "tag_color": "#f59e0b"
            },
            {
                "icon": "◻", "cls": "blue",
                "title": f"Compliance sweep — {len(no_nom)} clients without nominee",
                "desc": f"Proactively fixing nominee gaps positions you as a responsible advisor, not just a product seller. This is a trust-building call with zero sales pressure — and it sticks.",
                "tag": "Compliance", "tag_color": "#3b82f6"
            },
        ]

        for a in actions:
            st.markdown(f"""
            <div class="action-card">
              <div class="action-icon {a['cls']}">{a['icon']}</div>
              <div class="action-body">
                <div class="action-title">
                  {a['title']}
                  <span class="action-tag" style="background:rgba(255,255,255,.05);color:{a['tag_color']};border:1px solid {a['tag_color']}33">{a['tag']}</span>
                </div>
                <div class="action-desc">{a['desc']}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

    # ─ TAB 3: EVENTS ─
    with tab3:
        hni_clients = [c for c in clients if "HNI" in c.get("flags", [])]
        senior_clients = [c for c in clients if int(c.get("age") or 0) >= 55]

        events = [
            {
                "title": "HNI portfolio conclave",
                "tag": "Revenue", "tag_color": "#22c55e",
                "desc": f"Private 1:1 review for {len(hni_clients)} HNI clients. Present capital gain bonds and new MF opportunities with personalised return projections.",
                "meta": f"{len(hni_clients)} clients · This quarter",
                "targets": [c.get("name", "—") for c in hni_clients[:3]]
            },
            {
                "title": "SIP accelerator drive",
                "tag": "Growth", "tag_color": "#f59e0b",
                "desc": f"Compound growth demo for {len(sip_gap)} clients with zero SIP. Show the ₹10L→₹40L projection in 15 years. One visual does the selling.",
                "meta": f"{len(sip_gap)} clients · Next month",
                "targets": [c.get("name", "—") for c in sip_gap[:3]]
            },
            {
                "title": "Senior estate planning camp",
                "tag": "Retention", "tag_color": "#a855f7",
                "desc": f"LIC maturity planning, estate structuring for {len(senior_clients)} clients aged 55+. Builds deep loyalty that survives market downturns.",
                "meta": f"{len(senior_clients)} clients · This quarter",
                "targets": [c.get("name", "—") for c in senior_clients[:3]]
            },
        ]

        cols = st.columns(3)
        for i, ev in enumerate(events):
            with cols[i]:
                targets_str = ", ".join(ev["targets"]) + ("..." if len(ev["targets"]) == 3 else "")
                st.markdown(f"""
                <div class="event-card">
                  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
                    <h4>{ev['title']}</h4>
                    <span class="score-chip" style="background:transparent;border:1px solid {ev['tag_color']}44;color:{ev['tag_color']};font-size:10px;padding:2px 8px">{ev['tag']}</span>
                  </div>
                  <p>{ev['desc']}</p>
                  <div class="event-meta">{ev['meta']}</div>
                  <div style="margin-top:8px;font-size:11px;color:#7a8394">Targets: {targets_str or '—'}</div>
                </div>
                """, unsafe_allow_html=True)

    # ─ TAB 4: WHATSAPP ─
    with tab4:
        client_names = [c.get("name", "—") for c in clients if c.get("name", "—")]
        selected_name = st.selectbox("Select client", client_names)
        sel_client = next((c for c in clients if c.get("name", "—") == selected_name), None)

        if sel_client:
            col_a, col_b = st.columns([1, 1])
            with col_a:
                st.markdown(f"""
                <div style="background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:1.2rem;margin-bottom:1rem">
                  <div style="font-size:10px;letter-spacing:.1em;text-transform:uppercase;font-family:'DM Mono',monospace;color:#7a8394;margin-bottom:10px">Client snapshot</div>
                  <div style="font-size:15px;font-weight:600;margin-bottom:8px">{sel_client['name']}</div>
                  <div style="font-size:12px;color:#9aa3b2;line-height:2">
                    Portfolio: <span style="color:#f0f1f3">{fmt_inr(sel_client['portfolio'])}</span><br>
                    SIP: <span style="color:#f0f1f3">{fmt_inr(sel_client['sip']) if num(sel_client['sip'])>0 else 'Not started'}</span><br>
                    ML Score: <span style="color:#f0f1f3">{sel_client['score']}/100</span><br>
                    Churn risk: <span style="color:{'#ef4444' if sel_client['churn']>50 else '#22c55e'}">{sel_client['churn']}%</span>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                msg_type = st.radio("Message type", ["Follow-up call request", "SIP upgrade proposal", "Portfolio review invite", "Nominee update request"], label_visibility="visible")

            with col_b:
                templates = {
                    "Follow-up call request": f"Dear {sel_client['name']},\n\nI've been reviewing your portfolio and there are a few important developments I'd like to walk you through personally. Your investment profile suggests this is a good time to revisit your strategy.\n\nCould we schedule a 20-minute call this week at your convenience?\n\nWarm regards,\nKartik Dadia | Aditya Finoptions",
                    "SIP upgrade proposal": f"Dear {sel_client['name']},\n\nBased on your current portfolio of {fmt_inr(sel_client['portfolio'])}, I've prepared a personalised SIP projection that could significantly accelerate your wealth creation over the next 10 years.\n\nThe numbers are compelling — I'd like to share them with you. Would 15 minutes work this week?\n\nWarm regards,\nKartik Dadia | Aditya Finoptions",
                    "Portfolio review invite": f"Dear {sel_client['name']},\n\nIt's time for your annual portfolio review. Given the current market conditions, I want to make sure your investments are positioned optimally for the next 12 months.\n\nI've already done the analysis — let's talk through it. When works best for you?\n\nWarm regards,\nKartik Dadia | Aditya Finoptions",
                    "Nominee update request": f"Dear {sel_client['name']},\n\nAs part of our annual compliance review, I noticed your nomination details may need updating. This is a critical document that protects your family's financial interests.\n\nIt takes under 10 minutes — may I assist you with this? I can come to you or we can do it over a call.\n\nWarm regards,\nKartik Dadia | Aditya Finoptions",
                }

                final_msg = templates[msg_type]
                edited = st.text_area("Edit before sending", final_msg, height=220)

                wa_msg = edited.replace("\n", "%0A").replace(" ", "%20")
                st.markdown(f'<a class="wa-btn" href="https://wa.me/?text={wa_msg}" target="_blank">Open in WhatsApp ↗</a>', unsafe_allow_html=True)

    # ── FOOTER ──
    st.markdown("<br><hr>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align:center;font-size:11px;color:#4a5060;font-family:DM Mono,monospace'>Finoptions Intelligence Pro · {len(clients)} clients · {fmt_inr(total_aum)} AUM · Built with ML + Claude AI</div>", unsafe_allow_html=True)

    if st.sidebar.button("Upload new file"):
        for k in ["clients","demo","screen","mapping","raw_df","ai_insight","ai_insight_stale"]:
            st.session_state.pop(k, None)
        st.rerun()

# ── MAIN ROUTER ────────────────────────────────────────────────────────────

def main():
    # Demo shortcut
    if st.session_state.get("demo") and "clients" not in st.session_state:
        st.session_state.clients = prepare_demo()
        st.session_state.screen = "dashboard"

    screen = st.session_state.get("screen", "upload")

    if screen == "dashboard" and "clients" in st.session_state:
        show_dashboard(st.session_state.clients)
        return

    if screen == "map" and "upload_df" in st.session_state:
        show_mapping(st.session_state.upload_df)
        return

    # Upload screen
    uploaded = show_upload()

    if uploaded:
        try:
            if uploaded.name.endswith(".csv"):
                df = pd.read_csv(uploaded)
            else:
                df = pd.read_excel(uploaded)
            st.session_state.upload_df = df
            st.session_state.screen = "map"
            st.rerun()
        except Exception as e:
            st.error(f"Could not read file: {e}")

if __name__ == "__main__":
    main()
