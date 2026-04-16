import streamlit as st
import pandas as pd
import datetime
import os
from sklearn.ensemble import RandomForestClassifier
import plotly.express as px
import random

st.set_page_config(page_title="AI Revenue Intelligence", layout="wide")

# ---------- CSS ----------
st.markdown("""
<style>
.kpi {
    padding:18px;
    border-radius:12px;
    color:white;
    text-align:center;
    font-weight:600;
    cursor:pointer;
}
.kpi-title { font-size:14px; opacity:0.8; }
.kpi-value { font-size:22px; }

.green { background: linear-gradient(135deg,#28a745,#4cd964); }
.yellow { background: linear-gradient(135deg,#ffc107,#ffe066); color:black; }
.red { background: linear-gradient(135deg,#dc3545,#ff6b6b); }
.blue { background: linear-gradient(135deg,#007bff,#66b3ff); }

.card {
    padding:15px;
    border-radius:12px;
    margin-bottom:10px;
    box-shadow:0px 2px 8px rgba(0,0,0,0.08);
}
</style>
""", unsafe_allow_html=True)

# ---------- LOGIN ----------
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("🚀 AI Revenue Intelligence")

    name = st.text_input("Your Name")
    company = st.text_input("Company Name")

    if st.button("Enter Dashboard"):
        if name and company:
            st.session_state.login = True
            st.session_state.name = name
            st.session_state.company = company
            st.rerun()
    st.stop()

name = st.session_state.name
company = st.session_state.company

st.title(f"📊 {company} — Revenue Intelligence")

# ---------- FILE ----------
folder = "data"
os.makedirs(folder, exist_ok=True)
path = f"{folder}/{name}.xlsx"

file = st.file_uploader("Upload Client Data", type=["xlsx"])

if file:
    df = pd.read_excel(file)
    df.to_excel(path, index=False)

# ---------- LOAD ----------
if os.path.exists(path):

    df = pd.read_excel(path)
    df.columns = df.columns.str.lower().str.replace(" ", "_")

    df.rename(columns={
        'client_name': 'name',
        'investment_amount': 'investment',
        'last_interaction_date': 'last'
    }, inplace=True)

    df['last'] = pd.to_datetime(df['last'])
    today = datetime.datetime.today()
    df['days'] = (today - df['last']).dt.days

    df['high'] = (df['investment'] > 100000).astype(int)
    df['inactive'] = (df['days'] > 30).astype(int)

    df['target'] = ((df['high']==1) & (df['days']<15)).astype(int)

    X = df[['days','investment','high','inactive']]
    y = df['target']

    model = RandomForestClassifier()

    if len(y.unique()) > 1:
        model.fit(X,y)
        df['prob'] = model.predict_proba(X)[:,1]
    else:
        df['prob'] = df['investment']/df['investment'].max()

    def seg(p):
        if p > 0.7: return "High"
        elif p > 0.4: return "Medium"
        else: return "Low"

    df['segment'] = df['prob'].apply(seg)

    # ---------- KPI ----------
    total = int(df['investment'].sum())
    high = len(df[df.segment=="High"])
    medium = len(df[df.segment=="Medium"])
    low = len(df[df.segment=="Low"])

    st.subheader("📌 Key Metrics")

    col1,col2,col3,col4 = st.columns(4)

    if col1.button("Total Pipeline"):
        st.session_state.filter="ALL"
    col1.markdown(f'<div class="kpi blue"><div class="kpi-title">Total Pipeline</div><div class="kpi-value">₹{total}</div></div>', unsafe_allow_html=True)

    if col2.button("High"):
        st.session_state.filter="High"
    col2.markdown(f'<div class="kpi green"><div class="kpi-title">High Intent</div><div class="kpi-value">{high}</div></div>', unsafe_allow_html=True)

    if col3.button("Medium"):
        st.session_state.filter="Medium"
    col3.markdown(f'<div class="kpi yellow"><div class="kpi-title">Medium Intent</div><div class="kpi-value">{medium}</div></div>', unsafe_allow_html=True)

    if col4.button("Low"):
        st.session_state.filter="Low"
    col4.markdown(f'<div class="kpi red"><div class="kpi-title">Low Intent</div><div class="kpi-value">{low}</div></div>', unsafe_allow_html=True)

    if "filter" not in st.session_state:
        st.session_state.filter="ALL"

    if st.session_state.filter!="ALL":
        df_view = df[df.segment==st.session_state.filter]
    else:
        df_view = df

    # ---------- INSIGHTS ----------
    st.subheader("🧠 AI Insights")

    top = df.sort_values(by="prob",ascending=False).iloc[0]

    st.info(f"""
    {top['name']} represents the highest conversion probability in your portfolio. 
    With ₹{int(top['investment'])} exposure and strong recency signals, this client sits at the peak of your revenue funnel. 
    Immediate engagement is recommended to capitalize on this opportunity window.
    """)

    # ---------- EVENT ----------
    st.subheader("📅 Event Strategy")

    st.success(f"""
    Growth Workshop Targeting {high} High-Intent Clients  
    Expected Conversion Rate: 40–60%  
    Potential Revenue Impact: ₹{int(df[df.segment=='High']['investment'].sum()*0.1)}
    """)

    # ---------- TABLE ----------
    st.subheader("📊 Client Intelligence Table")

    df_view = df_view.sort_values(by="prob",ascending=False)

    st.dataframe(df_view[['name','investment','prob','segment']])

    # ---------- CHARTS ----------
    st.subheader("📈 Analytics")

    colA,colB = st.columns(2)

    fig1 = px.bar(df, x="segment", y="investment", color="segment",
                  color_discrete_map={"High":"green","Medium":"orange","Low":"red"})
    colA.plotly_chart(fig1, use_container_width=True)

    fig2 = px.scatter(df, x="days", y="investment", color="segment",
                      size="investment", hover_data=["name"])
    colB.plotly_chart(fig2, use_container_width=True)

else:
    st.warning("Upload file to start")
