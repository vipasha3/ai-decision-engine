import streamlit as st
import pandas as pd
import numpy as np
import datetime
import plotly.express as px
from sklearn.ensemble import RandomForestClassifier

st.set_page_config(page_title="AI Revenue Intelligence PRO", layout="wide")

# ------------------ SESSION ------------------
if "data" not in st.session_state:
    st.session_state.data = None
if "filter" not in st.session_state:
    st.session_state.filter = "All"

# ------------------ UI STYLE ------------------
st.markdown("""
<style>
.kpi {
    padding:18px;
    border-radius:12px;
    color:white;
    text-align:center;
    cursor:pointer;
}
.green { background:linear-gradient(135deg,#00c853,#69f0ae); }
.red { background:linear-gradient(135deg,#d50000,#ff5252); }
.orange { background:linear-gradient(135deg,#ff6d00,#ffab40); }
.blue { background:linear-gradient(135deg,#2962ff,#82b1ff); }
.purple { background:linear-gradient(135deg,#6a1b9a,#ba68c8); }
</style>
""", unsafe_allow_html=True)

# ------------------ HEADER ------------------
st.title("🚀 AI Revenue Intelligence PRO")

# ------------------ FILE UPLOAD ------------------
file = st.file_uploader("Upload Client Data", type=["xlsx","csv"])

if file:
    if file.name.endswith("csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    df.columns = df.columns.str.lower().str.replace(" ","_")

    # AUTO MAP
    df.rename(columns={
        "client_name":"name",
        "investment_amount":"investment",
        "last_interaction_date":"last"
    }, inplace=True)

    df['last'] = pd.to_datetime(df['last'])
    df['days'] = (datetime.datetime.today() - df['last']).dt.days

    st.session_state.data = df

# ------------------ LOAD ------------------
if st.session_state.data is not None:

    df = st.session_state.data

    # ------------------ ML MODEL ------------------
    df['target'] = ((df['investment'] > df['investment'].median()) & (df['days'] < 20)).astype(int)

    X = df[['investment','days']]
    y = df['target']

    model = RandomForestClassifier()

    if len(y.unique()) > 1:
        model.fit(X,y)
        df['prob'] = model.predict_proba(X)[:,1]
    else:
        df['prob'] = df['investment'] / df['investment'].max()

    # ------------------ SEGMENT ------------------
    def segment(p):
        if p > 0.7: return "High"
        elif p > 0.4: return "Medium"
        else: return "Low"

    df['segment'] = df['prob'].apply(segment)

    # ------------------ KPI ------------------
    total = int(df['investment'].sum())
    high = len(df[df.segment=="High"])
    medium = len(df[df.segment=="Medium"])
    low = len(df[df.segment=="Low"])
    churn = len(df[df['days']>30])

    st.subheader("📊 Business Snapshot")

    c1,c2,c3,c4,c5 = st.columns(5)

    if c1.button(f"₹{total}"):
        st.session_state.filter="All"
    if c2.button(f"High {high}"):
        st.session_state.filter="High"
    if c3.button(f"Medium {medium}"):
        st.session_state.filter="Medium"
    if c4.button(f"Low {low}"):
        st.session_state.filter="Low"
    if c5.button(f"Churn {churn}"):
        st.session_state.filter="Churn"

    # ------------------ FILTER ------------------
    view = df.copy()

    if st.session_state.filter=="High":
        view = df[df.segment=="High"]
    elif st.session_state.filter=="Medium":
        view = df[df.segment=="Medium"]
    elif st.session_state.filter=="Low":
        view = df[df.segment=="Low"]
    elif st.session_state.filter=="Churn":
        view = df[df.days>30]

    # ------------------ AI INSIGHTS (NO API) ------------------
    st.subheader("🧠 AI Insights")

    top = df.sort_values("prob",ascending=False).iloc[0]

    insight = f"""
    Your portfolio shows strong concentration in high-value clients. 
    {high} clients are highly likely to convert, contributing majority of revenue potential.
    However, {churn} clients are inactive, which may lead to revenue leakage.
    Immediate focus on {top['name']} can unlock quick wins due to high probability score.
    """

    st.info(insight)

    # ------------------ PORTFOLIO MODULE ------------------
    st.subheader("🏢 Portfolio Intelligence")

    col1,col2 = st.columns(2)

    with col1:
        fig = px.pie(df, names='segment', values='investment',
                     color='segment',
                     color_discrete_map={
                         "High":"green",
                         "Medium":"orange",
                         "Low":"red"
                     })
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.bar(df, x='name', y='investment',
                      color='segment',
                      title="Client Investment Distribution")
        st.plotly_chart(fig2, use_container_width=True)

    # ------------------ CLIENT TABLE ------------------
    st.subheader("📋 Client Intelligence")

    for i,row in view.iterrows():

        if row.segment=="High":
            color="green"
            action="Close Deal"
        elif row.segment=="Medium":
            color="orange"
            action="Follow Up"
        else:
            color="red"
            action="Nurture"

        st.markdown(f"""
        <div class="kpi {color}">
        {row['name']} | ₹{int(row['investment'])}<br>
        Prob: {round(row['prob'],2)} | Last: {int(row['days'])} days
        </div>
        """, unsafe_allow_html=True)

        colA,colB = st.columns(2)

        with colA:
            if st.button(f"{action} → {row['name']}", key=i):
                st.success("Action Triggered")

        with colB:
            msg = f"Hi {row['name']}, let's connect regarding your investment plan."
            wa_link = f"https://wa.me/?text={msg.replace(' ','%20')}"
            st.markdown(f"[WhatsApp]({wa_link})")

    # ------------------ ADVANCED ANALYTICS ------------------
    st.subheader("📈 Advanced Analytics")

    fig3 = px.scatter(df, x='days', y='investment',
                      color='segment',
                      size='prob',
                      title="Behavior Analysis")

    st.plotly_chart(fig3, use_container_width=True)

else:
    st.warning("Upload data to start")
