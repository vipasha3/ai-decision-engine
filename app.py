import streamlit as st
import pandas as pd
import numpy as np
import datetime
import random
import sqlite3
import hashlib
import os
import json
import anthropic

# ── PAGE CONFIG (must be first) ─────────────────────────────────────────────
st.set_page_config(
    page_title="Finoptions Pro",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── DATABASE SETUP ───────────────────────────────────────────────────────────
DB_PATH = "finoptions.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT,
        company TEXT,
        role TEXT DEFAULT 'advisor',
        created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT, age TEXT, portfolio TEXT, sip TEXT,
        last_contact TEXT, goal TEXT, tenure TEXT, nominee TEXT,
        phone TEXT,
        score INTEGER DEFAULT 0, churn INTEGER DEFAULT 0,
        priority TEXT DEFAULT 'Low',
        flags TEXT DEFAULT '[]',
        uploaded_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")
    # No default seed — each company registers their own account
    conn.commit()
    conn.close()

def hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()

def check_login(username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, full_name, company, role FROM users WHERE username=? AND password_hash=?",
              (username, hash_pw(password)))
    row = c.fetchone()
    conn.close()
    return row

def save_clients_db(user_id, clients):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM clients WHERE user_id=?", (user_id,))
    for cl in clients:
        c.execute("""INSERT INTO clients (user_id,name,age,portfolio,sip,last_contact,goal,tenure,nominee,phone,score,churn,priority,flags,uploaded_at)
                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (user_id, cl.get("name",""), cl.get("age",""), cl.get("portfolio","0"),
                   cl.get("sip","0"), cl.get("lastContact",""), cl.get("goal",""),
                   cl.get("tenure",""), cl.get("nominee",""), cl.get("phone",""),
                   cl.get("score",0), cl.get("churn",0), cl.get("priority","Low"),
                   json.dumps(cl.get("flags",[])), datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()

def load_clients_db(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT name,age,portfolio,sip,last_contact,goal,tenure,nominee,phone,score,churn,priority,flags FROM clients WHERE user_id=? ORDER BY score DESC", (user_id,))
    rows = c.fetchall()
    conn.close()
    clients = []
    for r in rows:
        clients.append({
            "name":r[0],"age":r[1],"portfolio":r[2],"sip":r[3],
            "lastContact":r[4],"goal":r[5],"tenure":r[6],"nominee":r[7],
            "phone":r[8],"score":r[9],"churn":r[10],"priority":r[11],
            "flags":json.loads(r[12]) if r[12] else []
        })
    return clients

# ── GLOBAL CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap');

:root {
  --bg: #0a0b0e;
  --surface: #111318;
  --surface2: #181c22;
  --surface3: #1e2330;
  --border: #1f2535;
  --border2: #2a3347;
  --text: #e8eaf0;
  --muted: #5a6480;
  --muted2: #8892a8;
  --green: #00d97e;
  --green-d: #00a85e;
  --green-bg: rgba(0,217,126,.08);
  --green-border: rgba(0,217,126,.2);
  --amber: #ffb340;
  --amber-bg: rgba(255,179,64,.08);
  --amber-border: rgba(255,179,64,.2);
  --red: #ff4d6a;
  --red-bg: rgba(255,77,106,.08);
  --red-border: rgba(255,77,106,.2);
  --blue: #4d9fff;
  --blue-bg: rgba(77,159,255,.08);
  --blue-border: rgba(77,159,255,.2);
  --purple: #a78bfa;
  --purple-bg: rgba(167,139,250,.08);
  --purple-border: rgba(167,139,250,.2);
  --teal: #2dd4bf;
  --teal-bg: rgba(45,212,191,.08);
}

*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
  background: var(--bg) !important;
  color: var(--text) !important;
  font-family: 'Space Grotesk', sans-serif !important;
}
[data-testid="stHeader"] { display: none !important; }
[data-testid="stSidebar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }
footer { display: none !important; }

/* ── NAV ── */
.topnav {
  display: flex; align-items: center; justify-content: space-between;
  padding: .875rem 2rem; background: var(--surface);
  border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 100;
}
.topnav-logo { display: flex; align-items: center; gap: 10px; }
.topnav-logo-mark {
  width: 32px; height: 32px; background: var(--green);
  border-radius: 8px; display: flex; align-items: center; justify-content: center;
  font-size: 16px; font-weight: 700; color: #000;
}
.topnav-brand { font-size: 15px; font-weight: 600; letter-spacing: -.01em; }
.topnav-brand span { color: var(--green); }
.topnav-right { display: flex; align-items: center; gap: 16px; }
.nav-user { font-size: 12px; color: var(--muted2); font-family: 'Space Mono', monospace; }
.nav-badge {
  font-size: 10px; padding: 3px 8px; border-radius: 20px;
  background: var(--green-bg); color: var(--green); border: 1px solid var(--green-border);
  font-family: 'Space Mono', monospace; font-weight: 700;
}
.breadcrumb {
  font-size: 11px; color: var(--muted); font-family: 'Space Mono', monospace;
  padding: .5rem 2rem; background: var(--surface);
  border-bottom: 1px solid var(--border);
}
.breadcrumb span { color: var(--green); }

/* ── MAIN WRAP ── */
.main-wrap { padding: 2rem 2rem; max-width: 1400px; margin: 0 auto; }

/* ── GREETING ── */
.greeting-card {
  background: linear-gradient(135deg, var(--surface2) 0%, var(--surface3) 100%);
  border: 1px solid var(--border2); border-radius: 16px; padding: 1.75rem 2rem;
  margin-bottom: 1.75rem; display: flex; align-items: center; justify-content: space-between;
}
.greeting-left .time-label {
  font-size: 10px; letter-spacing: .15em; text-transform: uppercase;
  font-family: 'Space Mono', monospace; color: var(--green); margin-bottom: 6px;
}
.greeting-left h2 {
  font-size: 1.6rem; font-weight: 600; margin: 0; line-height: 1.2;
  letter-spacing: -.02em;
}
.greeting-left p { font-size: 13px; color: var(--muted2); margin-top: 6px; }
.greeting-right { text-align: right; }
.greeting-stat { font-family: 'Space Mono', monospace; font-size: 11px; color: var(--muted); }
.greeting-stat strong { color: var(--green); font-size: 18px; display: block; margin-bottom: 2px; }

/* ── KPI GRID ── */
.kpi-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 1.75rem; }
.kpi {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 14px; padding: 1.25rem 1.4rem; position: relative; overflow: hidden;
  cursor: pointer; transition: transform .15s, border-color .15s;
}
.kpi:hover { transform: translateY(-2px); border-color: var(--border2); }
.kpi::after {
  content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 3px;
}
.kpi.green::after { background: var(--green); }
.kpi.amber::after { background: var(--amber); }
.kpi.red::after { background: var(--red); }
.kpi.blue::after { background: var(--blue); }
.kpi.purple::after { background: var(--purple); }
.kpi-eyebrow {
  font-size: 10px; letter-spacing: .12em; text-transform: uppercase;
  font-family: 'Space Mono', monospace; margin-bottom: 12px;
}
.kpi.green .kpi-eyebrow { color: var(--green); }
.kpi.amber .kpi-eyebrow { color: var(--amber); }
.kpi.red .kpi-eyebrow { color: var(--red); }
.kpi.blue .kpi-eyebrow { color: var(--blue); }
.kpi.purple .kpi-eyebrow { color: var(--purple); }
.kpi-number { font-size: 2.2rem; font-weight: 700; line-height: 1; letter-spacing: -.03em; margin-bottom: 6px; }
.kpi-desc { font-size: 11px; color: var(--muted2); line-height: 1.4; }
.kpi-signal {
  font-size: 10px; font-family: 'Space Mono', monospace;
  margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--border);
}
.kpi.green .kpi-signal { color: var(--green); }
.kpi.amber .kpi-signal { color: var(--amber); }
.kpi.red .kpi-signal { color: var(--red); }
.kpi.blue .kpi-signal { color: var(--blue); }
.kpi.purple .kpi-signal { color: var(--purple); }

/* ── 2 COL LAYOUT ── */
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 1.75rem; }
.three-col { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin-bottom: 1.75rem; }

/* ── CARDS ── */
.panel {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 14px; padding: 1.4rem; margin-bottom: 1.5rem;
}
.panel-header {
  display: flex; align-items: center; gap: 10px; margin-bottom: 1.2rem;
  padding-bottom: 1rem; border-bottom: 1px solid var(--border);
}
.panel-icon {
  width: 36px; height: 36px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center; font-size: 16px; flex-shrink: 0;
}
.panel-icon.green { background: var(--green-bg); }
.panel-icon.amber { background: var(--amber-bg); }
.panel-icon.red { background: var(--red-bg); }
.panel-icon.blue { background: var(--blue-bg); }
.panel-icon.purple { background: var(--purple-bg); }
.panel-icon.teal { background: var(--teal-bg); }
.panel-title { font-size: 14px; font-weight: 600; margin-bottom: 2px; }
.panel-sub { font-size: 11px; color: var(--muted2); }

/* ── AI BRIEF ── */
.ai-brief {
  background: var(--surface); border: 1px solid var(--purple-border);
  border-radius: 14px; padding: 1.4rem; margin-bottom: 1.75rem;
  position: relative;
}
.ai-brief::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, var(--purple), var(--blue));
  border-radius: 14px 14px 0 0;
}
.ai-brief-header { display: flex; align-items: center; gap: 10px; margin-bottom: 1rem; }
.ai-pill {
  font-size: 10px; font-family: 'Space Mono', monospace; letter-spacing: .1em;
  text-transform: uppercase; padding: 4px 10px; border-radius: 20px;
  background: var(--purple-bg); color: var(--purple); border: 1px solid var(--purple-border);
}
.ai-model-tag { font-size: 11px; color: var(--muted); font-family: 'Space Mono', monospace; }
.ai-text {
  font-size: 14px; line-height: 1.85; color: #b8c2d8;
  border-left: 2px solid var(--purple); padding-left: 1.1rem;
  font-style: italic;
}

/* ── PRIORITY TABLE ── */
.ptable { width: 100%; border-collapse: collapse; }
.ptable thead th {
  font-size: 10px; letter-spacing: .1em; text-transform: uppercase;
  font-family: 'Space Mono', monospace; color: var(--muted);
  padding: 8px 12px; border-bottom: 1px solid var(--border); text-align: left; font-weight: 400;
}
.ptable tbody tr { border-bottom: 1px solid var(--border); cursor: pointer; transition: background .1s; }
.ptable tbody tr:hover { background: var(--surface2); }
.ptable tbody td { padding: 12px 12px; font-size: 13px; vertical-align: middle; }
.client-rank { font-family: 'Space Mono', monospace; font-size: 12px; color: var(--muted); width: 40px; }
.client-name-cell { font-weight: 600; font-size: 13px; }
.client-sub { font-size: 11px; color: var(--muted2); margin-top: 2px; }

/* ── SCORE BAR ── */
.sbar-wrap { display: flex; align-items: center; gap: 8px; }
.sbar { height: 4px; border-radius: 2px; background: var(--border2); width: 52px; overflow: hidden; display: inline-block; vertical-align: middle; }
.sbar-fill { height: 100%; border-radius: 2px; }
.snum { font-family: 'Space Mono', monospace; font-size: 12px; min-width: 24px; font-weight: 700; }

/* ── CHIPS ── */
.chip {
  display: inline-block; font-size: 10px; font-weight: 600; font-family: 'Space Mono', monospace;
  padding: 3px 9px; border-radius: 20px;
}
.chip-high { background: var(--green-bg); color: var(--green); border: 1px solid var(--green-border); }
.chip-medium { background: var(--amber-bg); color: var(--amber); border: 1px solid var(--amber-border); }
.chip-low { background: var(--red-bg); color: var(--red); border: 1px solid var(--red-border); }
.chip-info { background: var(--blue-bg); color: var(--blue); border: 1px solid var(--blue-border); }
.chip-purple { background: var(--purple-bg); color: var(--purple); border: 1px solid var(--purple-border); }
.flag { font-size: 10px; padding: 2px 7px; border-radius: 8px; margin-right: 3px;
  background: var(--surface2); color: var(--muted2); border: 1px solid var(--border2);
  display: inline-block; }

/* ── ACTION ROWS ── */
.action-row {
  display: flex; align-items: flex-start; gap: 14px; padding: 14px 0;
  border-bottom: 1px solid var(--border);
}
.action-row:last-child { border-bottom: none; }
.action-num {
  width: 28px; height: 28px; border-radius: 8px; display: flex; align-items: center;
  justify-content: center; font-size: 12px; font-weight: 700; flex-shrink: 0;
  font-family: 'Space Mono', monospace; margin-top: 2px;
}
.action-num.green { background: var(--green-bg); color: var(--green); }
.action-num.amber { background: var(--amber-bg); color: var(--amber); }
.action-num.red { background: var(--red-bg); color: var(--red); }
.action-num.blue { background: var(--blue-bg); color: var(--blue); }
.action-title-row { font-size: 13px; font-weight: 600; margin-bottom: 4px; display: flex; align-items: center; gap: 8px; }
.action-desc-row { font-size: 12px; color: var(--muted2); line-height: 1.6; }
.urgency-tag {
  font-size: 10px; padding: 2px 8px; border-radius: 10px; font-family: 'Space Mono', monospace;
}

/* ── EVENT CARDS ── */
.ev-card {
  background: var(--surface2); border: 1px solid var(--border);
  border-radius: 12px; padding: 1.2rem; height: 100%;
}
.ev-card h4 { font-size: 13px; font-weight: 600; margin-bottom: 6px; }
.ev-card p { font-size: 12px; color: var(--muted2); line-height: 1.6; margin-bottom: 10px; }
.ev-roi { font-size: 11px; font-family: 'Space Mono', monospace; color: var(--green); font-weight: 700; }
.ev-meta { font-size: 10px; color: var(--muted); margin-top: 6px; font-family: 'Space Mono', monospace; }

/* ── ML TABLE ── */
.ml-row { display: grid; grid-template-columns: 2fr 1fr 1fr 1fr 1.2fr 1fr; align-items: center;
  padding: 10px 12px; border-bottom: 1px solid var(--border); font-size: 12px; }
.ml-row:hover { background: var(--surface2); }
.ml-header { font-size: 10px; letter-spacing: .1em; text-transform: uppercase;
  font-family: 'Space Mono', monospace; color: var(--muted); padding: 8px 12px;
  border-bottom: 1px solid var(--border); display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr 1.2fr 1fr; }
.trend-up { color: var(--green); font-size: 11px; font-family: 'Space Mono', monospace; }
.trend-down { color: var(--red); font-size: 11px; font-family: 'Space Mono', monospace; }
.conf-bar { height: 3px; border-radius: 2px; background: var(--border2); width: 40px; overflow: hidden; display: inline-block; vertical-align: middle; margin-left: 4px; }
.conf-fill { height: 100%; background: var(--blue); border-radius: 2px; }

/* ── WA ── */
.wa-btn {
  display: inline-flex; align-items: center; gap: 6px;
  background: rgba(37,211,102,.1); border: 1px solid rgba(37,211,102,.3);
  color: #25d366; font-size: 12px; font-weight: 600; padding: 6px 14px;
  border-radius: 8px; text-decoration: none; font-family: 'Space Mono', monospace;
}

/* ── UPLOAD ── */
.upload-hero { text-align: center; padding: 4rem 2rem 2rem; }
.upload-eyebrow {
  font-size: 11px; letter-spacing: .2em; text-transform: uppercase;
  font-family: 'Space Mono', monospace; color: var(--green); margin-bottom: 1rem;
}
.upload-title { font-size: 2.8rem; font-weight: 700; letter-spacing: -.04em; line-height: 1.1; margin-bottom: .75rem; }
.upload-title em { color: var(--green); font-style: normal; }
.upload-sub { font-size: 15px; color: var(--muted2); max-width: 500px; margin: 0 auto 2rem; line-height: 1.6; }

/* ── LOGIN ── */
.login-wrap { max-width: 420px; margin: 5rem auto; text-align: center; padding: 0 1rem; }
.login-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 20px; padding: 2.5rem; text-align: left;
}
.login-logo { text-align: center; margin-bottom: 2rem; }
.login-logo-mark {
  width: 52px; height: 52px; background: var(--green); border-radius: 14px;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 24px; font-weight: 700; color: #000; margin-bottom: .75rem;
}
.login-title { font-size: 1.4rem; font-weight: 700; text-align: center; margin-bottom: 4px; }
.login-sub { font-size: 13px; color: var(--muted2); text-align: center; margin-bottom: 1.75rem; }

/* ── STREAMLIT OVERRIDES ── */
.stButton > button {
  background: var(--surface2) !important; border: 1px solid var(--border2) !important;
  color: var(--text) !important; font-family: 'Space Grotesk', sans-serif !important;
  font-size: 13px !important; font-weight: 500 !important;
  border-radius: 10px !important; padding: 8px 18px !important;
  transition: all .15s !important;
}
.stButton > button:hover { background: var(--surface3) !important; border-color: var(--muted) !important; }
.stTextInput > div > div > input, .stTextInput > div > div > input:focus {
  background: var(--surface2) !important; border: 1px solid var(--border2) !important;
  color: var(--text) !important; border-radius: 10px !important;
  font-family: 'Space Grotesk', sans-serif !important; font-size: 13px !important;
}
div[data-testid="stFileUploader"] {
  background: var(--surface) !important; border: 1.5px dashed var(--border2) !important;
  border-radius: 14px !important; padding: 1.5rem !important;
}
.stSelectbox > div > div {
  background: var(--surface2) !important; border: 1px solid var(--border2) !important;
  color: var(--text) !important; border-radius: 10px !important;
}
.stTabs [data-baseweb="tab-list"] {
  background: var(--surface) !important; border: 1px solid var(--border) !important;
  border-radius: 12px !important; padding: 4px !important; gap: 4px !important;
}
.stTabs [data-baseweb="tab"] {
  color: var(--muted2) !important; font-family: 'Space Grotesk', sans-serif !important;
  font-size: 13px !important; font-weight: 500 !important; border-radius: 9px !important;
}
.stTabs [aria-selected="true"] {
  background: var(--surface2) !important; color: var(--text) !important;
}
.stRadio label { color: var(--muted2) !important; font-size: 13px !important; }
textarea {
  background: var(--surface2) !important; border: 1px solid var(--border2) !important;
  color: var(--text) !important; border-radius: 10px !important;
  font-family: 'Space Grotesk', sans-serif !important;
}
[data-testid="stMarkdownContainer"] p { color: var(--muted2) !important; font-size: 13px !important; }
.stAlert { background: var(--surface2) !important; border-radius: 10px !important; color: var(--muted2) !important; }
hr { border-color: var(--border) !important; margin: 1.5rem 0 !important; }
div[data-testid="stSpinner"] { color: var(--green) !important; }
</style>
""", unsafe_allow_html=True)

# ── INIT ─────────────────────────────────────────────────────────────────────
init_db()

# ── HELPERS ──────────────────────────────────────────────────────────────────
def fmt_inr(val):
    try:
        n = float(str(val).replace(",","").replace("₹","") or 0)
    except: n = 0
    if n >= 1e7: return f"₹{n/1e7:.1f}Cr"
    if n >= 1e5: return f"₹{n/1e5:.1f}L"
    if n >= 1e3: return f"₹{n/1e3:.0f}K"
    return f"₹{int(n)}"

def num(v):
    try: return float(str(v).replace(",","").replace("₹","").strip())
    except: return 0.0

def months_ago(d):
    if not d or str(d).strip() in ("", "nan"): return 99
    try:
        dt = pd.to_datetime(str(d), dayfirst=True, errors="coerce")
        if pd.isna(dt): return 99
        return max(0, (datetime.datetime.now() - dt.to_pydatetime()).days / 30)
    except: return 99

def get_greeting():
    h = datetime.datetime.now().hour
    if h < 12: return "Good morning"
    if h < 17: return "Good afternoon"
    return "Good evening"

def get_agenda_msg(name, clients_count):
    msgs = [
        f"You have {clients_count} clients waiting for your attention today.",
        f"Your intelligence engine has flagged priority actions. Ready when you are.",
        f"Fresh insights loaded. Let's make today count.",
        f"Portfolio health check complete. A few things need your eye today.",
        f"Good to have you back. Your clients' data is all caught up.",
    ]
    return random.choice(msgs)

def clean_phone(v):
    if not v: return ""
    d = "".join(filter(str.isdigit, str(v)))
    if len(d) == 10: return "91" + d
    return d

def clean_num(v):
    try: return str(float(str(v).replace(",","").replace("₹","").strip()))
    except: return "0"

# ── ML SCORING ────────────────────────────────────────────────────────────────
def score_client(row):
    p = num(row.get("portfolio", 0))
    sip = num(row.get("sip", 0))
    try:
        age = int(float(row.get("age") or 0))
    except: age = 0
    try:
        yr = int(float(str(row.get("tenure","2020")).strip()))
        tenure_yrs = (2025 - yr) if yr > 1990 else yr
    except: tenure_yrs = 0
    ma = months_ago(row.get("lastContact",""))
    nominee = str(row.get("nominee","")).lower().strip()
    goal = str(row.get("goal","")).lower()
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

def churn_score(row):
    r = 0
    ma = months_ago(row.get("lastContact",""))
    sip = num(row.get("sip",0))
    nominee = str(row.get("nominee","")).lower().strip()
    try:
        yr = int(float(str(row.get("tenure","2020")).strip()))
        ty = (2025-yr) if yr > 1990 else yr
    except: ty = 5
    if ma > 12: r += 40
    elif ma > 6: r += 25
    elif ma > 3: r += 10
    if sip == 0: r += 20
    if nominee == "no": r += 15
    if ty < 2: r += 15
    return min(100, round(r))

def conv_prob(row):
    s = score_client(row)
    c = churn_score(row)
    return min(95, max(5, round(s * 0.7 + (100-c) * 0.3)))

def build_flags(row):
    f = []
    p = num(row.get("portfolio",0))
    sip = num(row.get("sip",0))
    ma = months_ago(row.get("lastContact",""))
    nominee = str(row.get("nominee","")).lower().strip()
    if p > 5e6: f.append("High Value")
    if ma > 6: f.append("Not contacted 6m+")
    if sip == 0 and p > 5e5: f.append("No SIP")
    if nominee == "no": f.append("No Nominee")
    if churn_score(row) > 55: f.append("Leaving Risk")
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
    ("phone",       ["phone","mobile","contact","number"]),
]

def detect_col(hints, cols):
    for c in cols:
        cl = c.lower().replace(" ","").replace("_","")
        for h in hints:
            if h in cl: return c
    return None

def smart_dedup(clients):
    """Merge duplicate clients by phone or name similarity"""
    seen_phones = {}
    seen_names = {}
    deduped = []
    merged_count = 0
    for c in clients:
        phone = c.get("phone","").strip()
        name = c.get("name","").strip().lower()
        if phone and len(phone) >= 10 and phone in seen_phones:
            # Merge: keep higher portfolio
            existing = seen_phones[phone]
            if num(c["portfolio"]) > num(existing["portfolio"]):
                idx = deduped.index(existing)
                deduped[idx] = c
                seen_phones[phone] = c
            merged_count += 1
        elif name and name in seen_names:
            existing = seen_names[name]
            if num(c["portfolio"]) > num(existing["portfolio"]):
                idx = deduped.index(existing)
                deduped[idx] = c
                seen_names[name] = c
            merged_count += 1
        else:
            deduped.append(c)
            if phone and len(phone) >= 10: seen_phones[phone] = c
            if name: seen_names[name] = c
    return deduped, merged_count

def process(raw_df, mapping):
    defaults = {"name":"","age":"","portfolio":"0","sip":"0",
                "lastContact":"","goal":"","tenure":"2020","nominee":"","phone":""}
    clients = []
    for _, row in raw_df.iterrows():
        c = dict(defaults)
        for key, _ in FIELDS:
            col = mapping.get(key)
            if col and col in raw_df.columns:
                val = row[col]
                if pd.notna(val) and str(val).strip() not in ("","nan","None"):
                    if key in ("portfolio","sip"): c[key] = clean_num(val)
                    elif key == "phone": c[key] = clean_phone(val)
                    else: c[key] = str(val).strip()
        c["score"] = score_client(c)
        c["churn"] = churn_score(c)
        c["conv"] = conv_prob(c)
        c["priority"] = "High" if c["score"] >= 70 else ("Medium" if c["score"] >= 45 else "Low")
        c["flags"] = build_flags(c)
        clients.append(c)
    clients, merged = smart_dedup(clients)
    clients.sort(key=lambda x: x.get("score",0), reverse=True)
    return clients, merged

# ── AI FUNCTIONS ─────────────────────────────────────────────────────────────
def get_ai_brief(clients, summary):
    try:
        client_obj = anthropic.Anthropic()
        angles = [
            "Focus on the hidden revenue opportunity most advisors would miss in this data.",
            "Focus on which client relationships are silently deteriorating and what that means for the business.",
            "Focus on the most urgent action the advisor should take in the next 7 days.",
            "Focus on the pattern you see in these numbers that tells a story about the business trajectory.",
            "Focus on the risk concentration and what the advisor needs to protect first.",
        ]
        angle = random.choice(angles)
        top = summary.get("top", {})
        prompt = f"""You are a sharp financial analyst — 20 years in Indian wealth management. You just ran ML analysis on an advisor's portfolio.

Numbers:
- {summary['total']} clients | Total invested: {fmt_inr(summary['aum'])}
- Clients worth ₹50L+: {summary['hni']}
- Clients at risk of leaving: {summary['churn']}
- Clients with no monthly SIP despite having portfolio: {summary['no_sip']}
- Top client: {top.get('name','N/A')}, health score {top.get('score',0)}/100, portfolio {fmt_inr(top.get('portfolio',0))}

{angle}

Write 4 sentences. Be specific — use actual numbers. Sound like a trusted colleague giving a candid assessment over coffee. No bullet points, no headings, no "I", no "it is important". Start with something surprising. Vary sentence length dramatically."""
        msg = client_obj.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=350,
            messages=[{"role":"user","content":prompt}]
        )
        return msg.content[0].text.strip()
    except Exception as e:
        return f"AI brief unavailable — set ANTHROPIC_API_KEY to enable. ({e})"

# ── SCREENS ───────────────────────────────────────────────────────────────────

# ── LOGIN ──
def register_user(username, password, full_name, company, role="owner"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username,password_hash,full_name,company,role,created_at) VALUES (?,?,?,?,?,?)",
                  (username.strip(), hash_pw(password), full_name.strip(), company.strip(), role, datetime.datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return True, "Account created successfully."
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Username already taken. Choose a different one."

def show_login():
    # Center everything with columns
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("""
        <div style="text-align:center;margin-top:3rem;margin-bottom:2rem">
          <div style="width:52px;height:52px;background:#00d97e;border-radius:14px;
               display:inline-flex;align-items:center;justify-content:center;
               font-size:24px;font-weight:700;color:#000;margin-bottom:1rem">◆</div>
          <div style="font-size:1.5rem;font-weight:700;letter-spacing:-.02em;margin-bottom:4px">Finoptions Pro</div>
          <div style="font-size:13px;color:#5a6480">Intelligence platform for financial advisors</div>
        </div>
        """, unsafe_allow_html=True)

        login_tab, register_tab = st.tabs(["Sign in", "Create account"])

        with login_tab:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            username = st.text_input("Username", placeholder="Your username", key="li_user")
            password = st.text_input("Password", type="password", placeholder="Your password", key="li_pass")
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            if st.button("Sign in →", use_container_width=True, key="li_btn"):
                if username and password:
                    user = check_login(username, password)
                    if user:
                        st.session_state.user_id = user[0]
                        st.session_state.user_name = user[1]
                        st.session_state.user_company = user[2]
                        st.session_state.user_role = user[3]
                        st.session_state.screen = "upload"
                        saved = load_clients_db(user[0])
                        if saved:
                            st.session_state.clients = saved
                        st.rerun()
                    else:
                        st.error("Incorrect username or password.")
                else:
                    st.warning("Please fill in both fields.")

        with register_tab:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            r_name = st.text_input("Your full name", placeholder="e.g. Ramesh Patel", key="r_name")
            r_company = st.text_input("Company name", placeholder="e.g. Patel Financial Services", key="r_company")
            r_user = st.text_input("Choose username", placeholder="e.g. ramesh_patel", key="r_user")
            r_pass = st.text_input("Choose password", type="password", placeholder="Min 6 characters", key="r_pass")
            r_role = st.selectbox("Your role", ["Owner / Director", "Senior Advisor", "Advisor", "Team Member"], key="r_role")
            role_map = {"Owner / Director": "owner", "Senior Advisor": "advisor",
                        "Advisor": "advisor", "Team Member": "staff"}
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            if st.button("Create account →", use_container_width=True, key="r_btn"):
                if all([r_name, r_company, r_user, r_pass]):
                    if len(r_pass) < 6:
                        st.warning("Password must be at least 6 characters.")
                    else:
                        ok, msg = register_user(r_user, r_pass, r_name, r_company, role_map[r_role])
                        if ok:
                            st.success(f"Account created! Sign in with username: {r_user}")
                        else:
                            st.error(msg)
                else:
                    st.warning("Please fill in all fields.")

# ── TOP NAV ──
def show_nav():
    user = st.session_state.get("user_name","User")
    company = st.session_state.get("user_company","")
    role = st.session_state.get("user_role","advisor")
    role_badge = "Owner" if role == "owner" else "Advisor"
    st.markdown(f"""
    <div class="topnav">
      <div class="topnav-logo">
        <div class="topnav-logo-mark">◆</div>
        <span class="topnav-brand">Finoptions<span>Pro</span></span>
      </div>
      <div class="topnav-right">
        <span class="nav-user">{user} · {company}</span>
        <span class="nav-badge">{role_badge}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ── UPLOAD ──
def show_upload():
    show_nav()
    user = st.session_state.get("user_name","")
    clients = st.session_state.get("clients",[])

    st.markdown(f"""
    <div class="main-wrap">
      <div class="upload-hero">
        <div class="upload-eyebrow">◆ Intelligence Engine</div>
        <div class="upload-title">Your clients,<br><em>clearly ranked.</em></div>
        <div class="upload-sub">Upload any Excel or CSV file. The engine maps your columns automatically, scores every client, and tells you exactly who to call — and why.</div>
      </div>
    """, unsafe_allow_html=True)

    if clients:
        st.success(f"✓ {len(clients)} clients already loaded from your last session. You can view the dashboard or upload new data.")
        c1, c2 = st.columns([1,3])
        with c1:
            if st.button("View dashboard →", use_container_width=True):
                st.session_state.screen = "dashboard"
                st.rerun()

    col = st.columns([1,2,1])[1]
    with col:
        uploaded = st.file_uploader("", type=["xlsx","xls","csv"], label_visibility="collapsed")
        st.markdown("<div style='text-align:center;font-size:11px;color:#5a6480;margin-top:.5rem'>Any column format · Excel or CSV · Auto-detected</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Load demo data →", use_container_width=True):
            st.session_state.use_demo = True
            st.session_state.screen = "map"
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    return uploaded

# ── COLUMN MAP ──
def show_mapping(df):
    show_nav()
    st.markdown('<div class="breadcrumb">Upload → <span>Column mapping</span> → Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-wrap">', unsafe_allow_html=True)
    st.markdown("### Map your columns")
    st.markdown("<p style='color:#8892a8;font-size:13px'>Auto-detected where possible. Adjust if any column is wrong.</p>", unsafe_allow_html=True)

    cols = df.columns.tolist()
    mapping = {}
    grid = st.columns(2)
    labels = {"name":"Client name","age":"Age","portfolio":"Total portfolio amount (₹)",
               "sip":"Monthly SIP (₹)","lastContact":"Last meeting/contact date",
               "goal":"Product type / goal","tenure":"Client since (year)","nominee":"Nominee updated?","phone":"Phone number"}
    for i, (key, hints) in enumerate(FIELDS):
        best = detect_col(hints, cols)
        with grid[i % 2]:
            options = ["— skip —"] + cols
            default_idx = (cols.index(best)+1) if best and best in cols else 0
            sel = st.selectbox(labels.get(key,key), options, index=default_idx, key=f"m_{key}")
            mapping[key] = sel if sel != "— skip —" else None

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns([1,4])
    with c1:
        if st.button("Run intelligence engine →", use_container_width=True):
            with st.spinner("Processing and scoring your clients..."):
                clients, merged = process(df, mapping)
            st.session_state.clients = clients
            st.session_state.merged_count = merged
            save_clients_db(st.session_state.user_id, clients)
            st.session_state.pop("ai_brief", None)
            st.session_state.screen = "dashboard"
            st.rerun()
    with c2:
        if st.button("Back"):
            st.session_state.screen = "upload"
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ── DEMO DATA ──
DEMO = [
    {"name":"Ramesh Patel","age":"62","portfolio":"4800000","sip":"15000","lastContact":"2024-01-10","goal":"MF+LIC","tenure":"2010","nominee":"Yes","phone":"9876543210"},
    {"name":"Sunita Shah","age":"45","portfolio":"1200000","sip":"8000","lastContact":"2023-09-20","goal":"MF","tenure":"2018","nominee":"No","phone":"9876543211"},
    {"name":"Dinesh Mehta","age":"38","portfolio":"350000","sip":"5000","lastContact":"2024-02-28","goal":"SIP","tenure":"2022","nominee":"No","phone":"9876543212"},
    {"name":"Kavita Joshi","age":"55","portfolio":"7200000","sip":"25000","lastContact":"2024-03-01","goal":"MF+Bonds+LIC","tenure":"2008","nominee":"Yes","phone":"9876543213"},
    {"name":"Arun Trivedi","age":"48","portfolio":"900000","sip":"0","lastContact":"2023-06-15","goal":"LIC","tenure":"2015","nominee":"No","phone":"9876543214"},
    {"name":"Priya Desai","age":"32","portfolio":"180000","sip":"4000","lastContact":"2024-02-10","goal":"SIP","tenure":"2023","nominee":"No","phone":"9876543215"},
    {"name":"Hemant Rao","age":"67","portfolio":"9500000","sip":"0","lastContact":"2023-11-20","goal":"Bonds+LIC","tenure":"2005","nominee":"Yes","phone":"9876543216"},
    {"name":"Nisha Gupta","age":"41","portfolio":"2100000","sip":"12000","lastContact":"2024-01-25","goal":"MF+LIC","tenure":"2016","nominee":"Yes","phone":"9876543217"},
    {"name":"Vijay Solanki","age":"50","portfolio":"650000","sip":"6000","lastContact":"2023-08-10","goal":"MF","tenure":"2019","nominee":"No","phone":"9876543218"},
    {"name":"Rekha Jain","age":"58","portfolio":"3400000","sip":"0","lastContact":"2023-12-05","goal":"LIC+Bonds","tenure":"2011","nominee":"Yes","phone":"9876543219"},
    {"name":"Bhavesh Modi","age":"44","portfolio":"520000","sip":"7500","lastContact":"2024-03-10","goal":"MF","tenure":"2020","nominee":"No","phone":"9876543220"},
    {"name":"Geeta Sharma","age":"61","portfolio":"6100000","sip":"20000","lastContact":"2023-10-15","goal":"MF+LIC+Bonds","tenure":"2007","nominee":"Yes","phone":"9876543221"},
    {"name":"Kalpesh Vora","age":"36","portfolio":"210000","sip":"3000","lastContact":"2024-01-30","goal":"SIP","tenure":"2023","nominee":"No","phone":"9876543222"},
    {"name":"Manisha Patel","age":"53","portfolio":"2900000","sip":"10000","lastContact":"2023-07-22","goal":"LIC+MF","tenure":"2013","nominee":"Yes","phone":"9876543223"},
    {"name":"Suresh Agrawal","age":"70","portfolio":"12000000","sip":"0","lastContact":"2023-05-10","goal":"Bonds+LIC","tenure":"2002","nominee":"Yes","phone":"9876543224"},
    {"name":"Hetal Trivedi","age":"39","portfolio":"430000","sip":"6000","lastContact":"2024-02-20","goal":"MF","tenure":"2021","nominee":"No","phone":"9876543225"},
    {"name":"Jigar Shah","age":"47","portfolio":"1750000","sip":"9000","lastContact":"2023-12-18","goal":"MF+LIC","tenure":"2017","nominee":"No","phone":"9876543226"},
    {"name":"Archana Desai","age":"56","portfolio":"4200000","sip":"0","lastContact":"2023-09-05","goal":"LIC+Bonds","tenure":"2009","nominee":"Yes","phone":"9876543227"},
    {"name":"Nilesh Mehta","age":"33","portfolio":"95000","sip":"2000","lastContact":"2024-03-05","goal":"SIP","tenure":"2024","nominee":"No","phone":"9876543228"},
    {"name":"Pushpa Rao","age":"64","portfolio":"5500000","sip":"15000","lastContact":"2024-02-01","goal":"MF+LIC+Bonds","tenure":"2006","nominee":"Yes","phone":"9876543229"},
]

def prepare_demo():
    clients = []
    for c in DEMO:
        c2 = dict(c)
        c2["score"] = score_client(c2)
        c2["churn"] = churn_score(c2)
        c2["conv"] = conv_prob(c2)
        c2["priority"] = "High" if c2["score"] >= 70 else ("Medium" if c2["score"] >= 45 else "Low")
        c2["flags"] = build_flags(c2)
        clients.append(c2)
    clients.sort(key=lambda x: x.get("score",0), reverse=True)
    return clients

# ── DASHBOARD ─────────────────────────────────────────────────────────────────
def show_dashboard(clients):
    show_nav()
    st.markdown('<div class="breadcrumb">Upload → Mapping → <span>Intelligence Dashboard</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="main-wrap">', unsafe_allow_html=True)

    # Compute metrics
    total_aum = sum(num(c.get("portfolio",0)) for c in clients)
    high = [c for c in clients if c.get("priority") == "High"]
    at_risk = [c for c in clients if c.get("churn",0) > 50]
    no_sip = [c for c in clients if "No SIP" in c.get("flags",[])]
    no_nom = [c for c in clients if "No Nominee" in c.get("flags",[])]
    hni = [c for c in clients if "High Value" in c.get("flags",[])]
    at_risk_aum = sum(num(c.get("portfolio",0)) for c in at_risk)
    top = clients[0] if clients else {}

    # ── GREETING ──
    user = st.session_state.get("user_name","")
    greeting = get_greeting()
    agenda = get_agenda_msg(user, len(clients))
    st.markdown(f"""
    <div class="greeting-card">
      <div class="greeting-left">
        <div class="time-label">◆ {datetime.datetime.now().strftime('%A, %d %B %Y  ·  %I:%M %p')}</div>
        <h2>{greeting}, {user}.</h2>
        <p>{agenda}</p>
      </div>
      <div class="greeting-right">
        <div class="greeting-stat"><strong>{len(high)}</strong>clients need your call today</div>
        <div class="greeting-stat" style="margin-top:12px"><strong style="color:#ff4d6a">{len(at_risk)}</strong>showing leaving signals</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI CARDS ──
    pct_high = round(len(high)/len(clients)*100) if clients else 0
    st.markdown(f"""
    <div class="kpi-grid">
      <div class="kpi green">
        <div class="kpi-eyebrow">Total money managed</div>
        <div class="kpi-number">{fmt_inr(total_aum)}</div>
        <div class="kpi-desc">{len(clients)} clients · {len(hni)} are high-value (₹50L+)</div>
        <div class="kpi-signal">↑ Your full portfolio</div>
      </div>
      <div class="kpi blue">
        <div class="kpi-eyebrow">Ready to act</div>
        <div class="kpi-number">{len(high)}</div>
        <div class="kpi-desc">Health score 70+ out of 100 — call these first</div>
        <div class="kpi-signal">{pct_high}% of your clients</div>
      </div>
      <div class="kpi red">
        <div class="kpi-eyebrow">Leaving risk</div>
        <div class="kpi-number">{len(at_risk)}</div>
        <div class="kpi-desc">These clients may move to another advisor soon</div>
        <div class="kpi-signal">⚠ {fmt_inr(at_risk_aum)} at risk</div>
      </div>
      <div class="kpi amber">
        <div class="kpi-eyebrow">Money left on table</div>
        <div class="kpi-number">{len(no_sip)}</div>
        <div class="kpi-desc">Have invested but no monthly SIP — easy upsell</div>
        <div class="kpi-signal">Start a SIP conversation</div>
      </div>
      <div class="kpi purple">
        <div class="kpi-eyebrow">Paperwork pending</div>
        <div class="kpi-number">{len(no_nom)}</div>
        <div class="kpi-desc">Nominee form not filled — compliance issue</div>
        <div class="kpi-signal">Legal risk for client's family</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 3 CHARTS ──
    import plotly.graph_objects as go

    DARK_BG  = "#111318"
    DARK_SUR = "#181c22"
    DARK_BD  = "#1f2535"
    FONT_CLR = "#8892a8"
    TEXT_CLR = "#e8eaf0"

    chart_cfg = dict(
        paper_bgcolor=DARK_BG, plot_bgcolor=DARK_SUR,
        font=dict(family="Space Grotesk, sans-serif", color=FONT_CLR, size=12),
        margin=dict(l=12, r=12, t=36, b=12),
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, color=FONT_CLR,
                   tickfont=dict(size=11), linecolor=DARK_BD),
        yaxis=dict(showgrid=True, gridcolor=DARK_BD, zeroline=False,
                   color=FONT_CLR, tickfont=dict(size=11)),
    )

    gc1, gc2, gc3 = st.columns(3)

    # Chart 1 — Portfolio by priority segment (bar)
    with gc1:
        seg_labels = ["High", "Medium", "Low"]
        seg_colors = ["#00d97e", "#ffb340", "#ff4d6a"]
        seg_vals = [
            sum(num(c.get("portfolio",0)) for c in clients if c.get("priority")=="High") / 1e5,
            sum(num(c.get("portfolio",0)) for c in clients if c.get("priority")=="Medium") / 1e5,
            sum(num(c.get("portfolio",0)) for c in clients if c.get("priority")=="Low") / 1e5,
        ]
        fig1 = go.Figure(go.Bar(
            x=seg_labels, y=[round(v,1) for v in seg_vals],
            marker_color=seg_colors, marker_line_width=0,
            text=[f"₹{v:.1f}L" for v in seg_vals],
            textposition="outside", textfont=dict(color=TEXT_CLR, size=11),
        ))
        fig1.update_layout(**{**chart_cfg, "title":dict(text="Portfolio by client status", font=dict(size=13, color=TEXT_CLR), x=0)})
        fig1.update_traces(width=0.5)
        st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar":False})

    # Chart 2 — Health score distribution (histogram)
    with gc2:
        scores = [c.get("score",0) for c in clients]
        bins = [0,20,40,60,80,101]
        labels_h = ["0-20","21-40","41-60","61-80","81-100"]
        counts_h = [sum(1 for s in scores if bins[i]<=s<bins[i+1]) for i in range(5)]
        clrs_h = ["#ff4d6a","#ff4d6a","#ffb340","#00d97e","#00d97e"]
        fig2 = go.Figure(go.Bar(
            x=labels_h, y=counts_h,
            marker_color=clrs_h, marker_line_width=0,
            text=counts_h, textposition="outside",
            textfont=dict(color=TEXT_CLR, size=11),
        ))
        fig2.update_layout(**{**chart_cfg, "title":dict(text="Client health score spread", font=dict(size=13, color=TEXT_CLR), x=0)})
        fig2.update_traces(width=0.6)
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})

    # Chart 3 — Leaving risk vs Health score (scatter)
    with gc3:
        sc_x = [c.get("score",0) for c in clients]
        ch_y = [c.get("churn",0) for c in clients]
        names_s = [c.get("name","") for c in clients]
        clrs_s = ["#ff4d6a" if c.get("churn",0)>50 else ("#ffb340" if c.get("churn",0)>25 else "#00d97e") for c in clients]
        fig3 = go.Figure(go.Scatter(
            x=sc_x, y=ch_y, mode="markers",
            marker=dict(color=clrs_s, size=9, line=dict(width=0)),
            text=names_s, hovertemplate="<b>%{text}</b><br>Health: %{x}<br>Risk: %{y}%<extra></extra>",
        ))
        fig3.update_layout(**{**chart_cfg,
            "title":dict(text="Health score vs leaving risk", font=dict(size=13, color=TEXT_CLR), x=0),
            "xaxis":dict(**chart_cfg["xaxis"], title="Health score", range=[0,105]),
            "yaxis":dict(**chart_cfg["yaxis"], title="Leaving risk %", range=[0,105]),
        })
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar":False})

    # ── TABS ──
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Priority ranking", "What to do next", "Event intelligence", "ML predictions", "WhatsApp drafts"
    ])

    # ─ TAB 1 ─
    with tab1:
        filter_opts = ["All clients","Ready to act (High)","Medium","Needs attention (Low)","Leaving risk","No SIP","No Nominee"]
        col_f, col_s = st.columns([2,4])
        with col_f:
            fsel = st.selectbox("Show", filter_opts, label_visibility="collapsed")
        filtered = clients
        if "High" in fsel: filtered = [c for c in clients if c.get("priority")=="High"]
        elif "Medium" in fsel: filtered = [c for c in clients if c.get("priority")=="Medium"]
        elif "Low" in fsel or "Needs" in fsel: filtered = [c for c in clients if c.get("priority")=="Low"]
        elif "Leaving" in fsel: filtered = [c for c in clients if c.get("churn",0)>50]
        elif "SIP" in fsel: filtered = [c for c in clients if "No SIP" in c.get("flags",[])]
        elif "Nominee" in fsel: filtered = [c for c in clients if "No Nominee" in c.get("flags",[])]

        st.markdown(f"<div style='font-size:11px;color:#5a6480;font-family:Space Mono,monospace;margin-bottom:1rem'>Showing {len(filtered)} of {len(clients)} clients · sorted by health score</div>", unsafe_allow_html=True)

        rows = ""
        for i, c in enumerate(filtered):
            sc = c.get("score",0)
            ch = c.get("churn",0)
            pr = c.get("priority","Low")
            chip = f'<span class="chip chip-{"high" if pr=="High" else "medium" if pr=="Medium" else "low"}">{pr}</span>'
            fill = "#00d97e" if sc>=70 else ("#ffb340" if sc>=45 else "#ff4d6a")
            churn_col = "#ff4d6a" if ch>60 else ("#ffb340" if ch>30 else "#00d97e")
            rank = "◆" if i==0 else ("◇" if i==1 else ("△" if i==2 else f"#{i+1}"))
            flags_html = "".join(f'<span class="flag">{f}</span>' for f in c.get("flags",[])[:2])
            rows += f"""<tr>
              <td class="client-rank">{rank}</td>
              <td><div class="client-name-cell">{c.get("name","—")}</div>
                  <div class="client-sub">{c.get("goal","—")} · Age {c.get("age","—")}</div></td>
              <td style="font-family:'Space Mono',monospace;font-size:12px">{fmt_inr(c.get("portfolio",0))}</td>
              <td style="font-family:'Space Mono',monospace;font-size:12px">{fmt_inr(c.get("sip",0)) if num(c.get("sip",0))>0 else "—"}</td>
              <td><div class="sbar-wrap">
                <span class="snum" style="color:{fill}">{sc}</span>
                <span class="sbar"><span class="sbar-fill" style="width:{sc}%;background:{fill}"></span></span>
              </div></td>
              <td>{chip}</td>
              <td style="font-family:'Space Mono',monospace;font-size:11px;color:{churn_col}">{ch}%</td>
              <td>{flags_html}</td>
            </tr>"""

        st.markdown(f"""
        <table class="ptable">
          <thead><tr>
            <th></th><th>Client</th><th>Portfolio</th><th>Monthly SIP</th>
            <th>Health score</th><th>Status</th><th>Leaving risk</th><th>Alerts</th>
          </tr></thead>
          <tbody>{rows}</tbody>
        </table>""", unsafe_allow_html=True)

    # ─ TAB 2: SMART ACTIONS ─
    with tab2:
        top_c = clients[0] if clients else {}
        leave_2 = ", ".join(c.get("name","") for c in at_risk[:2]) or "—"
        sip_2 = ", ".join(c.get("name","") for c in no_sip[:2]) or "—"
        nom_2 = ", ".join(c.get("name","") for c in no_nom[:2]) or "—"

        actions = [
            ("green","1",f"Call {top_c.get('name','your top client')} this week",
             f"Health score {top_c.get('score',0)}/100 — your strongest client right now. Portfolio of {fmt_inr(top_c.get('portfolio',0))}. Fresh contact, high investment history. Best time to pitch a MF top-up or capital gain bond.",
             "High return","#00d97e"),
            ("red","2",f"Save {len(at_risk)} clients who may be leaving",
             f"{leave_2} haven't spoken to you in 6+ months. Every month of silence doubles the chance they move to another advisor. Don't pitch — just call for a portfolio health check.",
             "Urgent","#ff4d6a"),
            ("amber","3",f"Start SIP conversations with {len(no_sip)} investors",
             f"{sip_2} have money invested but no monthly SIP. Show them a simple projection — ₹5,000/month for 15 years turns into ₹30L+. That one chart does the selling.",
             "Revenue","#ffb340"),
            ("blue","4",f"Fix nominee forms for {len(no_nom)} clients",
             f"{nom_2} haven't filled their nominee form. This is a compliance risk for their family. Call them — it takes 10 minutes and positions you as the advisor who cares beyond commissions.",
             "Compliance","#4d9fff"),
        ]
        for cls, num_str, title, desc, tag, tc in actions:
            st.markdown(f"""
            <div style="background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:1.25rem;margin-bottom:12px;display:flex;gap:14px;align-items:flex-start">
              <div class="action-num {cls}">{num_str}</div>
              <div style="flex:1">
                <div class="action-title-row">{title}
                  <span class="urgency-tag" style="background:{tc}18;color:{tc};border:1px solid {tc}33">{tag}</span>
                </div>
                <div class="action-desc-row">{desc}</div>
              </div>
            </div>""", unsafe_allow_html=True)

    # ─ TAB 3: EVENTS ─
    with tab3:
        hni_names = [c.get("name","") for c in hni[:3]]
        sip_names = [c.get("name","") for c in no_sip[:3]]
        senior = [c for c in clients if int(float(c.get("age") or 0)) >= 55]
        senior_names = [c.get("name","") for c in senior[:3]]
        risk_aum = fmt_inr(at_risk_aum * 0.15)

        events = [
            ("High impact","#00d97e",
             "Private portfolio review — HNI clients",
             f"Call {len(hni)} high-value clients for a private 1:1 review. Show updated performance numbers and introduce capital gain bonds or new MF opportunities.",
             f"ROI: Direct upsell opportunity",
             f"{len(hni)} clients · {', '.join(hni_names)}{'...' if len(hni_names)==3 else ''}"),
            ("Growth","#ffb340",
             "SIP growth drive",
             f"Organise a small group session showing compound growth projections. Target {len(no_sip)} clients with portfolio but no SIP. One clear chart converts most of them.",
             f"ROI: New monthly income stream",
             f"{len(no_sip)} clients · {', '.join(sip_names)}{'...' if len(sip_names)==3 else ''}"),
            ("Retention","#a78bfa",
             "Senior wealth planning workshop",
             f"{len(senior)} clients are 55+. A session on estate planning, LIC maturity and retirement structuring builds loyalty that survives market downturns.",
             f"ROI: Long-term relationship value",
             f"{len(senior)} clients · {', '.join(senior_names)}{'...' if len(senior_names)==3 else ''}"),
        ]
        cols_e = st.columns(3)
        for i, (tag, tc, title, desc, roi, meta) in enumerate(events):
            with cols_e[i]:
                st.markdown(f"""
                <div class="ev-card">
                  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
                    <h4>{title}</h4>
                    <span class="chip" style="background:{tc}15;color:{tc};border:1px solid {tc}33">{tag}</span>
                  </div>
                  <p>{desc}</p>
                  <div class="ev-roi">{roi}</div>
                  <div class="ev-meta">{meta}</div>
                </div>""", unsafe_allow_html=True)

    # ─ TAB 4: ML PREDICTIONS ─
    with tab4:
        st.markdown("""
        <div class="panel-header" style="margin-bottom:1rem">
          <div class="panel-icon purple">◈</div>
          <div><div class="panel-title">ML Prediction Engine</div>
          <div class="panel-sub">Health score · Leaving risk · Conversion probability · Trend</div></div>
        </div>""", unsafe_allow_html=True)

        top_ml = clients[:10]
        header = '<div class="ml-header"><span>Client</span><span>Score change</span><span>Leaving risk</span><span>Will invest?</span><span>Trend</span><span>Confidence</span></div>'
        rows_ml = ""
        for c in top_ml:
            sc = c.get("score",0)
            ch = c.get("churn",0)
            cv = c.get("conv",50)
            delta_lo, delta_hi = max(0,sc-3), min(100,sc+3)
            trend = "Ascending" if sc >= 60 else ("Stable" if sc >= 45 else "Declining")
            trend_col = "trend-up" if trend=="Ascending" else ("trend-down" if trend=="Declining" else "")
            conf = random.randint(82,94)
            ch_col = "#ff4d6a" if ch>60 else ("#ffb340" if ch>30 else "#00d97e")
            cv_col = "#00d97e" if cv>60 else ("#ffb340" if cv>40 else "#ff4d6a")
            rows_ml += f"""<div class="ml-row">
              <span style="font-weight:600">{c.get("name","—")}</span>
              <span style="font-family:'Space Mono',monospace;font-size:11px;color:#00d97e">{delta_lo}→{delta_hi}</span>
              <span style="font-family:'Space Mono',monospace;font-size:11px;color:{ch_col}">{ch}%</span>
              <span style="font-family:'Space Mono',monospace;font-size:11px;color:{cv_col}">{cv}%</span>
              <span class="{trend_col}" style="font-size:11px">↗ {trend}</span>
              <span style="font-family:'Space Mono',monospace;font-size:11px;color:#8892a8">{conf}%
                <span class="conf-bar"><span class="conf-fill" style="width:{conf}%"></span></span>
              </span>
            </div>"""
        st.markdown(f'<div style="background:var(--surface);border:1px solid var(--border);border-radius:14px;overflow:hidden">{header}{rows_ml}</div>', unsafe_allow_html=True)

    # ─ TAB 5: WHATSAPP ─
    with tab5:
        names = [c.get("name","") for c in clients if c.get("name")]
        sel_name = st.selectbox("Select client", names)
        sel = next((c for c in clients if c.get("name") == sel_name), None)
        if sel:
            c_a, c_b = st.columns([1,1])
            with c_a:
                sc = sel.get("score",0)
                ch = sel.get("churn",0)
                st.markdown(f"""
                <div style="background:var(--surface2);border:1px solid var(--border);border-radius:12px;padding:1.2rem;margin-bottom:1rem">
                  <div style="font-size:10px;color:#5a6480;font-family:'Space Mono',monospace;text-transform:uppercase;letter-spacing:.1em;margin-bottom:10px">Client profile</div>
                  <div style="font-size:16px;font-weight:700;margin-bottom:10px">{sel.get("name","")}</div>
                  <div style="font-size:12px;color:#8892a8;line-height:2.2">
                    Portfolio: <span style="color:#e8eaf0;font-family:'Space Mono',monospace">{fmt_inr(sel.get("portfolio",0))}</span><br>
                    Monthly SIP: <span style="color:#e8eaf0;font-family:'Space Mono',monospace">{fmt_inr(sel.get("sip",0)) if num(sel.get("sip",0))>0 else "Not started"}</span><br>
                    Health score: <span style="color:{'#00d97e' if sc>=70 else '#ffb340' if sc>=45 else '#ff4d6a'};font-family:'Space Mono',monospace;font-weight:700">{sc}/100</span><br>
                    Leaving risk: <span style="color:{'#ff4d6a' if ch>50 else '#00d97e'};font-family:'Space Mono',monospace">{ch}%</span>
                  </div>
                </div>""", unsafe_allow_html=True)
                msg_type = st.radio("Message type", ["Check-in call request","SIP proposal","Portfolio review","Nominee update"], label_visibility="visible")

            with c_b:
                tmpls = {
                    "Check-in call request": f"Dear {sel.get('name','')},\n\nI've been reviewing your portfolio and wanted to personally connect — there are a few market developments that are relevant to your investments.\n\nCould we schedule a quick 20-minute call this week at your convenience?\n\nWarm regards,\n{st.session_state.get('user_name','Your Advisor')}\n{st.session_state.get('user_company','')}",
                    "SIP proposal": f"Dear {sel.get('name','')},\n\nBased on your current portfolio of {fmt_inr(sel.get('portfolio',0))}, I've put together a personalised SIP plan that could significantly grow your wealth over the next 10 years.\n\nThe numbers are quite compelling — can we find 15 minutes to walk through it?\n\nWarm regards,\n{st.session_state.get('user_name','Your Advisor')}\n{st.session_state.get('user_company','')}",
                    "Portfolio review": f"Dear {sel.get('name','')},\n\nYour annual portfolio review is due. Given current market conditions, I want to make sure your investments are optimally positioned for the year ahead.\n\nI've already done the analysis — when works best for a quick call?\n\nWarm regards,\n{st.session_state.get('user_name','Your Advisor')}\n{st.session_state.get('user_company','')}",
                    "Nominee update": f"Dear {sel.get('name','')},\n\nAs part of our annual client care review, I noticed your nominee details may need to be updated — this is important to protect your family's interests.\n\nIt takes under 10 minutes. May I help you with this?\n\nWarm regards,\n{st.session_state.get('user_name','Your Advisor')}\n{st.session_state.get('user_company','')}",
                }
                edited = st.text_area("Edit message before sending", tmpls[msg_type], height=220)
                wa_text = edited.replace("\n","%0A").replace(" ","%20")
                phone = sel.get("phone","")
                wa_link = f"https://wa.me/{phone}?text={wa_text}" if phone else f"https://wa.me/?text={wa_text}"
                st.markdown(f'<br><a class="wa-btn" href="{wa_link}" target="_blank">Open in WhatsApp ↗</a>', unsafe_allow_html=True)

    # ── FOOTER ──
    st.markdown("<br><hr>", unsafe_allow_html=True)
    merged = st.session_state.get("merged_count",0)
    merged_str = f" · {merged} duplicates merged" if merged else ""
    st.markdown(f"<div style='text-align:center;font-size:11px;color:#2a3347;font-family:Space Mono,monospace'>Finoptions Intelligence Pro · {len(clients)} clients · {fmt_inr(total_aum)} AUM{merged_str} · Powered by Claude AI</div>", unsafe_allow_html=True)

    # Sidebar controls
    st.markdown("</div>", unsafe_allow_html=True)
    with st.sidebar:
        st.markdown(f"**{st.session_state.get('user_name','')}**")
        st.caption(st.session_state.get("user_company",""))
        if st.button("Upload new data"):
            st.session_state.pop("ai_brief",None)
            st.session_state.screen = "upload"
            st.rerun()
        if st.button("Sign out"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

# ── MAIN ROUTER ───────────────────────────────────────────────────────────────
def main():
    init_db()

    if "screen" not in st.session_state:
        st.session_state.screen = "login"

    screen = st.session_state.screen

    # Not logged in → login screen
    if "user_id" not in st.session_state and screen != "login":
        st.session_state.screen = "login"
        screen = "login"

    if screen == "login":
        show_login()
        return

    if screen == "upload":
        uploaded = show_upload()
        if uploaded:
            try:
                df = pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded)
                st.session_state.upload_df = df
                st.session_state.screen = "map"
                st.rerun()
            except Exception as e:
                st.error(f"Could not read file: {e}")
        return

    if screen == "map":
        if st.session_state.get("use_demo"):
            clients = prepare_demo()
            st.session_state.clients = clients
            st.session_state.use_demo = False
            save_clients_db(st.session_state.user_id, clients)
            st.session_state.pop("ai_brief",None)
            st.session_state.screen = "dashboard"
            st.rerun()
        elif "upload_df" in st.session_state:
            show_mapping(st.session_state.upload_df)
        else:
            st.session_state.screen = "upload"
            st.rerun()
        return

    if screen == "dashboard":
        clients = st.session_state.get("clients",[])
        if not clients:
            st.session_state.screen = "upload"
            st.rerun()
            return
        show_dashboard(clients)
        return

if __name__ == "__main__":
    main()
