import streamlit as st
import pandas as pd
import datetime
import os
from sklearn.ensemble import RandomForestClassifier

st.set_page_config(page_title="AI Growth Engine", layout="wide")

# ---------- SESSION LOGIN ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

st.title("🚀 AI Growth Engine")

# ---------- LOGIN (NO HARDCODE) ----------
if not st.session_state.logged_in:
    st.subheader("🔐 Login")

    username = st.text_input("Enter Your Name")
    company = st.text_input("Enter Company Name")

    if st.button("Login"):
        if username and company:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.company = company
            st.rerun()
        else:
            st.warning("Please fill all details")

    st.stop()

# ---------- AFTER LOGIN ----------
username = st.session_state.username
company = st.session_state.company

st.sidebar.success(f"👤 {username}")
st.sidebar.info(f"🏢 {company}")

if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

st.title(f"📊 Welcome {username} - {company}")

# ---------- STORAGE ----------
DATA_FOLDER = "user_data"
os.makedirs(DATA_FOLDER, exist_ok=True)
file_path = f"{DATA_FOLDER}/{username}.xlsx"

# ---------- FILE UPLOAD ----------
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.to_excel(file_path, index=False)
    st.success("File uploaded & saved")

# ---------- LOAD DATA ----------
if os.path.exists(file_path):

    df = pd.read_excel(file_path)
    df.columns = df.columns.str.lower().str.replace(" ", "_")
    df.fillna(0, inplace=True)

    # REQUIRED COLUMNS CHECK
    required_cols = ['client_name', 'investment_amount', 'last_interaction_date']
    for col in required_cols:
        if col not in df.columns:
            st.error(f"Missing column: {col}")
            st.stop()

    # RENAME
    df.rename(columns={
        'client_name': 'name',
        'investment_amount': 'investment',
        'last_interaction_date': 'last_interaction'
    }, inplace=True)

    # DATE
    df['last_interaction'] = pd.to_datetime(df['last_interaction'], errors='coerce')
    today = datetime.datetime.today()
    df['days_since_last_contact'] = (today - df['last_interaction']).dt.days
    df['days_since_last_contact'].fillna(0, inplace=True)

    # FEATURES
    df['high_value'] = (df['investment'] > 100000).astype(int)
    df['inactive'] = (df['days_since_last_contact'] > 30).astype(int)

    # ---------- ML ----------
    df['will_invest'] = ((df['high_value'] == 1) & (df['days_since_last_contact'] < 15)).astype(int)

    features = df[['days_since_last_contact', 'investment', 'high_value', 'inactive']]
    target = df['will_invest']

    model = RandomForestClassifier(n_estimators=50)

    if len(target.unique()) > 1:
        model.fit(features, target)
        df['probability'] = model.predict_proba(features)[:, 1]
    else:
        # SAFE fallback
        df['probability'] = (
            (df['investment'] / df['investment'].max()) * 0.6 +
            (1 / (df['days_since_last_contact'] + 1)) * 0.4
        )

    # PRIORITY
    df['priority'] = df['probability'] * 0.7 + df['inactive'] * 0.3
    df = df.sort_values(by='priority', ascending=False)

    # ---------- METRICS ----------
    total_clients = len(df)
    avg_prob = round(df['probability'].mean(), 2)

    c1, c2 = st.columns(2)
    c1.metric("👥 Total Clients", total_clients)
    c2.metric("📈 Avg Investment Probability", avg_prob)

    st.divider()

    # ---------- TOP ACTIONS ----------
    st.subheader("🔥 Top Actions")

    top_df = df.head(5)

    for i, row in top_df.iterrows():

        if row['probability'] > 0.7:
            action = "💰 Pitch Investment"
        elif row['inactive'] == 1:
            action = "📞 Reconnect"
        else:
            action = "📩 Engage"

        st.markdown(f"""
        <div style="padding:15px;border-radius:10px;background:#f5f5f5;margin-bottom:10px;">
        <b>{row['name']}</b><br>
        Action: {action}<br>
        Probability: {round(row['probability'],2)}<br>
        Last Contact: {int(row['days_since_last_contact'])} days ago
        </div>
        """, unsafe_allow_html=True)

        if st.button(f"📲 WhatsApp {row['name']}", key=i):
            st.success(f"Message sent to {row['name']}")

    st.divider()

    # ---------- CHARTS ----------
    st.subheader("📊 Dashboard")

    st.bar_chart(df.head(10).set_index("name")["probability"])
    st.line_chart(df['investment'])

    st.divider()

    # ---------- EVENT ----------
    st.subheader("📅 Event Suggestion")

    high_prob = df[df['probability'] > 0.6]

    st.info(f"""
    📌 Event: Investment Seminar  
    🎯 Clients: {len(high_prob)}  
    💰 Potential: ₹{int(high_prob['investment'].sum()*0.1)}
    """)

else:
    st.warning("Upload file to start")
