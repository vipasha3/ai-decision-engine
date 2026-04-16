import streamlit as st
import pandas as pd
import datetime
import os
import random
from sklearn.ensemble import RandomForestClassifier

st.set_page_config(page_title="AI Growth Engine Pro", layout="wide")

# ---------- USER DATABASE ----------
users = {
    "aditya": {"password": "1234", "company": "Aditya Finoptions"},
    "demo": {"password": "demo", "company": "Demo Advisory"},
}

# ---------- LOGIN ----------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

st.title("🚀 AI Growth Engine PRO")

if not st.session_state["logged_in"]:
    st.subheader("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in users and users[username]["password"] == password:
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.session_state["company"] = users[username]["company"]
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.stop()

# ---------- USER INFO ----------
username = st.session_state["username"]
company = st.session_state["company"]

st.sidebar.success(f"👤 {company}")

if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

st.title(f"📊 {company} Dashboard")

# ---------- STORAGE ----------
DATA_FOLDER = "user_data"
os.makedirs(DATA_FOLDER, exist_ok=True)
user_file_path = f"{DATA_FOLDER}/{username}.xlsx"

# ---------- UPLOAD ----------
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.to_excel(user_file_path, index=False)
    st.success("File saved successfully")

# ---------- LOAD ----------
if os.path.exists(user_file_path):

    df = pd.read_excel(user_file_path)
    df.columns = df.columns.str.lower().str.replace(" ", "_")
    df.fillna(0, inplace=True)

    # Column mapping
    df.rename(columns={
        'client_name': 'name',
        'investment_amount': 'investment',
        'last_interaction_date': 'last_interaction'
    }, inplace=True)

    # ---------- DATE ----------
    df['last_interaction'] = pd.to_datetime(df['last_interaction'], errors='coerce')
    today = datetime.datetime.today()
    df['days_since_last_contact'] = (today - df['last_interaction']).dt.days
    df['days_since_last_contact'].fillna(0, inplace=True)

    # ---------- BASIC FEATURES ----------
    df['high_value'] = (df['investment'] > 100000).astype(int)
    df['inactive'] = (df['days_since_last_contact'] > 30).astype(int)

    # ---------- ML MODEL ----------
    # Create training label (proxy logic for now)
    df['will_invest'] = ((df['high_value'] == 1) & (df['days_since_last_contact'] < 15)).astype(int)

    features = df[['days_since_last_contact', 'investment', 'high_value', 'inactive']]
    target = df['will_invest']

    model = RandomForestClassifier(n_estimators=50)
    model.fit(features, target)

    df['invest_probability'] = model.predict_proba(features)[:, 1]

    # ---------- PRIORITY ----------
    df['priority_score'] = (
        df['invest_probability'] * 0.6 +
        df['inactive'] * 0.3 +
        df['high_value'] * 0.1
    )

    df = df.sort_values(by='priority_score', ascending=False)
    top_df = df.head(5)

    # ---------- INSIGHT ENGINE ----------
    def generate_insight(row):
        if row['invest_probability'] > 0.7:
            return f"{row['name']} is highly likely to invest soon. Act fast."
        elif row['inactive'] == 1:
            return f"{row['name']} is inactive for {int(row['days_since_last_contact'])} days. Risk of churn."
        else:
            return f"{row['name']} needs engagement to unlock potential."

    # ---------- ACTION ENGINE ----------
    actions = []

    for _, row in top_df.iterrows():

        if row['invest_probability'] > 0.7:
            action = f"💰 Pitch investment to {row['name']}"
            impact = int(row['investment'] * 0.3)
            tag = "🟢 High Conversion"

        elif row['inactive'] == 1:
            action = f"📞 Reconnect with {row['name']}"
            impact = int(row['investment'] * 0.2)
            tag = "🔴 Churn Risk"

        else:
            action = f"📩 Engage {row['name']}"
            impact = int(row['investment'] * 0.1)
            tag = "🟡 Nurture"

        insight = generate_insight(row)

        actions.append({
            "Client": row['name'],
            "Category": tag,
            "Action": action,
            "Impact": impact,
            "Insight": insight,
            "Probability": round(row['invest_probability'], 2)
        })

    actions_df = pd.DataFrame(actions)

    # ---------- METRICS ----------
    total_opportunity = actions_df['Impact'].sum()
    total_clients = len(df)

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Revenue Opportunity", f"₹{total_opportunity}")
    col2.metric("👥 Total Clients", total_clients)
    col3.metric("🎯 Priority Actions", len(actions_df))

    st.divider()

    # ---------- CHARTS ----------
    st.subheader("📊 Insights Dashboard")

    st.bar_chart(actions_df.set_index("Client")["Probability"])
    st.line_chart(df['investment'])

    st.divider()

    # ---------- TOP ACTIONS ----------
    st.subheader("🔥 Top 5 AI Actions")

    for _, row in actions_df.iterrows():
        st.markdown(f"""
        <div style="padding:15px;border-radius:10px;background:#f4f6f8;margin-bottom:10px;">
        <b>{row['Client']} ({row['Category']})</b><br>
        Action: {row['Action']}<br>
        Impact: ₹{row['Impact']}<br>
        Probability: {row['Probability']}<br>
        <i>{row['Insight']}</i>
        </div>
        """, unsafe_allow_html=True)

        # ---------- WHATSAPP BUTTON ----------
        if st.button(f"📲 WhatsApp {row['Client']}"):
            st.success(f"Message sent to {row['Client']} (simulation)")

    st.divider()

    # ---------- EVENT RECOMMENDATION ----------
    st.subheader("📅 Smart Event Recommendation")

    high_prob_clients = df[df['invest_probability'] > 0.6]

    st.info(f"""
    📌 Event: Wealth Growth Seminar  
    🎯 Target Clients: {len(high_prob_clients)}  
    👥 Expected Conversion: {len(high_prob_clients)//2}  
    💰 Potential Revenue: ₹{int(high_prob_clients['investment'].sum() * 0.1)}  

    💡 Reason: Clients show high investment probability.
    """)

else:
    st.warning("Upload your Excel file to begin")
