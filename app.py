import streamlit as st
import pandas as pd
import datetime
import random
import plotly.express as px
from sklearn.ensemble import RandomForestClassifier

st.set_page_config(page_title="Finoptions Intelligence Pro", layout="wide")

# ---------------- SESSION ----------------
if "clients" not in st.session_state:
    st.session_state.clients = None
if "screen" not in st.session_state:
    st.session_state.screen = "upload"
if "kpi_filter" not in st.session_state:
    st.session_state.kpi_filter = "All"

# ---------------- HELPERS ----------------
def num(x):
    try: return float(x)
    except: return 0

def months_ago(d):
    try:
        return (datetime.datetime.now() - pd.to_datetime(d)).days / 30
    except:
        return 12

def fmt(x):
    x = float(x)
    if x > 1e7: return f"₹{x/1e7:.1f}Cr"
    if x > 1e5: return f"₹{x/1e5:.1f}L"
    return f"₹{x:.0f}"

# ---------------- ML MODEL ----------------
def run_ml(df):
    df['portfolio'] = df['portfolio'].astype(float)
    df['sip'] = df['sip'].astype(float)
    df['days'] = df['lastContact'].apply(months_ago)

    df['target'] = ((df['portfolio'] > df['portfolio'].median()) & (df['days'] < 3)).astype(int)

    X = df[['portfolio','sip','days']]
    y = df['target']

    model = RandomForestClassifier()

    if len(y.unique()) > 1:
        model.fit(X,y)
        df['score'] = model.predict_proba(X)[:,1] * 100
    else:
        df['score'] = (df['portfolio']/df['portfolio'].max())*100

    return df

# ---------------- PROCESS ----------------
def process(df):

    df.columns = df.columns.str.lower().str.replace(" ","")

    df.rename(columns={
        "clientname":"name",
        "investment":"portfolio",
        "amount":"portfolio",
        "sipamount":"sip",
        "last":"lastcontact"
    }, inplace=True)

    df['portfolio'] = df['portfolio'].fillna(0)
    df['sip'] = df.get('sip',0)

    df = run_ml(df)

    clients = []

    for _, r in df.iterrows():
        c = dict(r)
        c['priority'] = "High" if c['score']>70 else ("Medium" if c['score']>40 else "Low")
        c['churn'] = 100 if months_ago(c['lastcontact'])>6 else 20
        clients.append(c)

    clients.sort(key=lambda x:x['score'], reverse=True)

    return clients

# ---------------- UPLOAD SCREEN ----------------
if st.session_state.screen == "upload":

    st.markdown("## ◆ Finoptions Intelligence Pro")
    st.markdown("### Your clients, intelligently ranked.")

    file = st.file_uploader("Upload Excel/CSV")

    if st.button("Load Demo"):
        demo = pd.DataFrame({
            "clientname":["Ramesh","Amit","Priya","Neha","Raj"],
            "investment":[500000,200000,800000,100000,900000],
            "sip":[10000,5000,15000,2000,20000],
            "last":["2024-01-01","2023-06-01","2024-02-01","2023-05-01","2024-03-01"]
        })
        st.session_state.clients = process(demo)
        st.session_state.screen = "dashboard"
        st.rerun()

    if file:
        if file.name.endswith("csv"):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        st.session_state.clients = process(df)
        st.session_state.screen = "dashboard"
        st.rerun()

# ---------------- DASHBOARD ----------------
if st.session_state.screen == "dashboard":

    clients = st.session_state.clients

    total = sum(num(c['portfolio']) for c in clients)
    high = len([c for c in clients if c['priority']=="High"])
    churn = len([c for c in clients if c['churn']>50])

    # -------- KPI (CLICKABLE) --------
    st.subheader("📊 Business Overview")

    c1,c2,c3 = st.columns(3)

    if c1.button(f"Total {fmt(total)}"):
        st.session_state.kpi_filter="All"
    if c2.button(f"High {high}"):
        st.session_state.kpi_filter="High"
    if c3.button(f"Churn {churn}"):
        st.session_state.kpi_filter="Churn"

    # -------- FILTER --------
    filtered = clients

    if st.session_state.kpi_filter=="High":
        filtered = [c for c in clients if c['priority']=="High"]
    elif st.session_state.kpi_filter=="Churn":
        filtered = [c for c in clients if c['churn']>50]

    # -------- AI INSIGHT --------
    st.subheader("🧠 Insights")

    top = clients[0]

    st.info(f"""
    Your portfolio contains {high} high-value clients driving most of the revenue potential.
    However, {churn} clients are at risk due to inactivity.
    {top['name']} is your strongest opportunity with score {int(top['score'])}.
    """)

    # -------- PORTFOLIO CHARTS --------
    st.subheader("📊 Portfolio Intelligence")

    df_chart = pd.DataFrame(clients)

    col1,col2 = st.columns(2)

    with col1:
        fig = px.pie(df_chart, names="priority", values="portfolio",
                     color="priority",
                     color_discrete_map={
                         "High":"green","Medium":"orange","Low":"red"
                     })
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.scatter(df_chart,
                          x="score",
                          y="churn",
                          size="portfolio",
                          color="priority")
        st.plotly_chart(fig2, use_container_width=True)

    # -------- CLIENT LIST --------
    st.subheader("📋 Clients")

    for i,c in enumerate(filtered):

        st.markdown(f"""
        **{c['name']}**  
        Portfolio: {fmt(c['portfolio'])}  
        Score: {int(c['score'])}  
        """)

        colA,colB = st.columns(2)

        with colA:
            if st.button(f"Action → {c['name']}", key=i):
                st.success("Action triggered")

        with colB:
            msg = f"Hi {c['name']}, let's connect regarding your portfolio."
            wa = msg.replace(" ","%20")
            st.markdown(f"[WhatsApp](https://wa.me/?text={wa})")
