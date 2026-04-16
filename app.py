import streamlit as st
import pandas as pd
import datetime
import os
from sklearn.ensemble import RandomForestClassifier

st.set_page_config(page_title="AI Growth Engine PRO", layout="wide")

# ---------- LOGIN ----------
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("🔐 AI Growth Engine Login")

    name = st.text_input("Enter Name")
    company = st.text_input("Enter Company")

    if st.button("Login"):
        if name and company:
            st.session_state.login = True
            st.session_state.name = name
            st.session_state.company = company
            st.rerun()
        else:
            st.warning("Enter all details")

    st.stop()

# ---------- USER ----------
name = st.session_state.name
company = st.session_state.company

st.sidebar.success(f"👤 {name}")
st.sidebar.info(f"🏢 {company}")

if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

st.title(f"📊 {company} | AI Revenue Intelligence")

# ---------- FILE ----------
folder = "data"
os.makedirs(folder, exist_ok=True)
path = f"{folder}/{name}.xlsx"

file = st.file_uploader("Upload Client Data", type=["xlsx"])

if file:
    df = pd.read_excel(file)
    df.to_excel(path, index=False)
    st.success("Data uploaded")

# ---------- LOAD ----------
if os.path.exists(path):

    df = pd.read_excel(path)
    df.columns = df.columns.str.lower().str.replace(" ", "_")

    df.rename(columns={
        'client_name': 'name',
        'investment_amount': 'investment',
        'last_interaction_date': 'last_interaction'
    }, inplace=True)

    df['last_interaction'] = pd.to_datetime(df['last_interaction'])
    today = datetime.datetime.today()

    df['days'] = (today - df['last_interaction']).dt.days
    df['days'].fillna(0, inplace=True)

    # ---------- FEATURES ----------
    df['high_value'] = (df['investment'] > 100000).astype(int)
    df['inactive'] = (df['days'] > 30).astype(int)

    df['will_invest'] = ((df['high_value'] == 1) & (df['days'] < 15)).astype(int)

    X = df[['days', 'investment', 'high_value', 'inactive']]
    y = df['will_invest']

    model = RandomForestClassifier()

    if len(y.unique()) > 1:
        model.fit(X, y)
        df['prob'] = model.predict_proba(X)[:, 1]
    else:
        df['prob'] = (df['investment'] / df['investment'].max())

    # ---------- PRIORITY ----------
    df['score'] = df['prob'] * 70 + (1 - df['inactive']) * 30

    # ---------- SEGMENT ----------
    def segment(x):
        if x > 0.7:
            return "High"
        elif x > 0.4:
            return "Medium"
        else:
            return "Low"

    df['segment'] = df['prob'].apply(segment)

    # ---------- KPI ----------
    total = int(df['investment'].sum())
    high = len(df[df['segment'] == "High"])
    medium = len(df[df['segment'] == "Medium"])
    low = len(df[df['segment'] == "Low"])

    st.subheader("📌 Key Metrics")

    c1, c2, c3, c4 = st.columns(4)

    if c1.button(f"💰 Pipeline\n₹{total}"):
        st.session_state.filter = "ALL"

    if c2.button(f"🟢 High ({high})"):
        st.session_state.filter = "High"

    if c3.button(f"🟡 Medium ({medium})"):
        st.session_state.filter = "Medium"

    if c4.button(f"🔴 Low ({low})"):
        st.session_state.filter = "Low"

    # ---------- FILTER ----------
    if "filter" not in st.session_state:
        st.session_state.filter = "ALL"

    if st.session_state.filter != "ALL":
        df_display = df[df['segment'] == st.session_state.filter]
    else:
        df_display = df

    st.divider()

    # ---------- INSIGHTS ----------
    st.subheader("🧠 AI Insights")

    top = df.sort_values(by="score", ascending=False).iloc[0]

    st.info(f"""
    🎯 Top Opportunity: {top['name']}  
    💰 Value: ₹{int(top['investment'])}  
    📈 Probability: {round(top['prob'],2)}  
    👉 This client shows strongest conversion signals based on recency and value metrics.
    """)

    # ---------- EVENT ----------
    st.subheader("📅 Event Recommendation")

    st.success(f"""
    📌 Wealth Conversion Event  
    🎯 Target: {high} high-intent clients  
    💰 Potential: ₹{int(df[df['segment']=='High']['investment'].sum()*0.1)}  
    """)

    # ---------- TABLE ----------
    st.subheader("📊 Priority Ranking")

    df_display = df_display.sort_values(by="score", ascending=False)

    for i, row in df_display.iterrows():

        if row['segment'] == "High":
            color = "#d4edda"
        elif row['segment'] == "Medium":
            color = "#fff3cd"
        else:
            color = "#f8d7da"

        st.markdown(f"""
        <div style="background:{color};padding:12px;border-radius:10px;margin-bottom:8px">
        <b>{row['name']}</b> | ₹{int(row['investment'])}<br>
        Score: {round(row['score'],1)} | Prob: {round(row['prob'],2)} | Segment: {row['segment']}
        </div>
        """, unsafe_allow_html=True)

        # ---------- ACTION ----------
        if row['segment'] == "High":
            action = "💰 Pitch Now"
        elif row['segment'] == "Medium":
            action = "📞 Follow-up"
        else:
            action = "📩 Nurture"

        if st.button(f"{action} → {row['name']}", key=i):
            st.success(f"Action triggered for {row['name']}")

        if st.button(f"📲 WhatsApp {row['name']}", key=str(i)+"w"):
            st.success("WhatsApp message sent (demo)")

    st.divider()

    # ---------- CHART ----------
    st.subheader("📈 Analytics")

    st.bar_chart(df.groupby("segment")['investment'].sum())
    st.line_chart(df['investment'])

else:
    st.warning("Upload data to begin")
