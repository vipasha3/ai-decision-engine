import streamlit as st
import pandas as pd
import datetime
import os
from sklearn.ensemble import RandomForestClassifier
import random

st.set_page_config(page_title="AI Revenue Intelligence", layout="wide")

# ---------- CUSTOM CSS (IMPORTANT FOR UI) ----------
st.markdown("""
<style>
.metric-card {
    padding:20px;
    border-radius:12px;
    color:white;
    text-align:center;
    font-weight:bold;
}
.green { background: linear-gradient(135deg,#28a745,#5cd65c); }
.yellow { background: linear-gradient(135deg,#ffc107,#ffe066); color:black; }
.red { background: linear-gradient(135deg,#dc3545,#ff6b6b); }
.blue { background: linear-gradient(135deg,#007bff,#66b3ff); }

.card {
    padding:15px;
    border-radius:12px;
    margin-bottom:10px;
    background:#f9f9f9;
    box-shadow:0px 2px 6px rgba(0,0,0,0.1);
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
        else:
            st.warning("Enter details")

    st.stop()

name = st.session_state.name
company = st.session_state.company

st.title(f"📊 {company} — Revenue Intelligence System")

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

    # ---------- FEATURES ----------
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

    # ---------- SEGMENT ----------
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

    c1,c2,c3,c4 = st.columns(4)

    if c1.button(f"💰 ₹{total}"):
        st.session_state.filter="ALL"

    if c2.button(f"🟢 High {high}"):
        st.session_state.filter="High"

    if c3.button(f"🟡 Medium {medium}"):
        st.session_state.filter="Medium"

    if c4.button(f"🔴 Low {low}"):
        st.session_state.filter="Low"

    if "filter" not in st.session_state:
        st.session_state.filter="ALL"

    if st.session_state.filter!="ALL":
        df_view = df[df.segment==st.session_state.filter]
    else:
        df_view = df

    # ---------- HUMAN-LIKE INSIGHTS ----------
    st.subheader("🧠 AI Insights")

    top = df.sort_values(by="prob",ascending=False).iloc[0]

    insight_templates = [
        f"{top['name']} is showing strong behavioral alignment with high-conversion patterns. With ₹{int(top['investment'])} exposure and recent engagement, this is your most immediate revenue opportunity.",
        f"Data indicates that {top['name']} sits at the intersection of value and timing. Prioritizing this client could unlock significant ROI in the short term.",
        f"{top['name']} demonstrates above-average investment intent signals. Strategic engagement at this stage can maximize conversion probability."
    ]

    st.info(random.choice(insight_templates))

    # ---------- EVENT ----------
    st.subheader("📅 Event Recommendation")

    st.success(f"""
    Growth Acceleration Workshop  
    Target: {high} high-intent clients  
    Expected Conversion: {int(high*0.5)}  
    Revenue Potential: ₹{int(df[df.segment=='High']['investment'].sum()*0.1)}
    """)

    # ---------- CLIENT CARDS ----------
    st.subheader("📊 Priority Clients")

    df_view = df_view.sort_values(by="prob",ascending=False)

    for i,row in df_view.iterrows():

        if row.segment=="High":
            color="#d4edda"
            action="💰 Close Deal"
        elif row.segment=="Medium":
            color="#fff3cd"
            action="📞 Follow-up"
        else:
            color="#f8d7da"
            action="📩 Nurture"

        st.markdown(f"""
        <div class="card" style="background:{color}">
        <b>{row['name']}</b> | ₹{int(row['investment'])}<br>
        Probability: {round(row['prob'],2)}<br>
        Last Contact: {int(row['days'])} days
        </div>
        """, unsafe_allow_html=True)

        if st.button(f"{action} → {row['name']}", key=i):
            st.success(f"Action triggered for {row['name']}")

        if st.button(f"📲 WhatsApp {row['name']}", key=str(i)+"w"):
            st.success("Message sent")

    # ---------- CHARTS ----------
    st.subheader("📈 Analytics")

    st.bar_chart(df.groupby("segment")['investment'].sum())
    st.line_chart(df['investment'])

else:
    st.warning("Upload file to start")
