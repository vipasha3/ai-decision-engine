import streamlit as st
import pandas as pd
import datetime
import random
import os

st.set_page_config(page_title="AI Decision Engine", layout="wide")

# 🎨 UI Styling
st.markdown("""
    <style>
        .stTextInput>div>div>input {
            border-radius: 10px;
            padding: 10px;
        }
        .stButton button {
            border-radius: 10px;
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
        }
        .block-container {
            padding-top: 2rem;
        }
    </style>
""", unsafe_allow_html=True)

# ---------- LOGIN SYSTEM ----------
if "logged_in" not in st.session_state:
    
    st.title("🚀 AI Decision Engine")
    st.subheader("🔐 Login to Continue")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == "admin" and password == "1234":
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.success("✅ Login successful")
            st.rerun()
        else:
            st.error("❌ Invalid credentials")

    st.stop()

# ---------- MAIN APP ----------
username = st.session_state["username"]

st.sidebar.success(f"👤 Logged in as: {username}")

if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

st.title("🚀 AI Decision Engine (SaaS Version)")

# ---------- FILE STORAGE ----------
DATA_FOLDER = "user_data"
os.makedirs(DATA_FOLDER, exist_ok=True)

user_file_path = f"{DATA_FOLDER}/{username}.xlsx"

# ---------- UPLOAD ----------
uploaded_file = st.file_uploader("Upload Your Excel (First Time Only)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.to_excel(user_file_path, index=False)
    st.success("✅ File saved successfully!")

# ---------- LOAD DATA ----------
if os.path.exists(user_file_path):
    df = pd.read_excel(user_file_path)

    df.columns = df.columns.str.lower().str.replace(" ", "_")
    df.fillna(0, inplace=True)

    # Mapping
    if 'client_name' in df.columns:
        df.rename(columns={'client_name': 'name'}, inplace=True)
    if 'investment_amount' in df.columns:
        df.rename(columns={'investment_amount': 'investment'}, inplace=True)
    if 'last_interaction_date' in df.columns:
        df.rename(columns={'last_interaction_date': 'last_interaction'}, inplace=True)

    # Date processing
    df['last_interaction'] = pd.to_datetime(df['last_interaction'], errors='coerce')
    today = datetime.datetime.today()
    df['days_since_last_contact'] = (today - df['last_interaction']).dt.days
    df['days_since_last_contact'].fillna(0, inplace=True)

    # Scores
    df['churn_score'] = (
        (df['days_since_last_contact'] > 30)*40 +
        (df['investment'] < 50000)*30
    )

    df['invest_score'] = (
        (df['investment'] > 100000)*30 +
        (df['days_since_last_contact'] < 10)*30
    )

    df['engagement_score'] = (
        (df['days_since_last_contact'] > 7)*40
    )

    df['priority_score'] = (
        df['churn_score'] * 0.5 +
        df['invest_score'] * 0.3 +
        df['engagement_score'] * 0.2
    )

    df = df.sort_values(by='priority_score', ascending=False)
    top_df = df.head(5)

    # Insight generator
    def generate_insight(row, impact):
        options = [
            f"{row['name']} is at risk. Act now to protect ₹{impact}.",
            f"Opportunity detected: ₹{impact} potential from {row['name']}.",
            f"Follow-up needed — may unlock ₹{impact}.",
            f"High-value client — don’t miss this chance."
        ]
        return random.choice(options)

    actions = []

    for _, row in top_df.iterrows():

        if row['churn_score'] > 50:
            action = f"📞 Call {row['name']}"
            impact = int(row['investment'])
            tag = "🔴 High Risk"

        elif row['invest_score'] > 40:
            action = f"💰 Upsell {row['name']}"
            impact = int(row['investment'] * 0.3)
            tag = "🟢 Opportunity"

        else:
            action = f"🔁 Follow-up {row['name']}"
            impact = int(row['investment'] * 0.1)
            tag = "🟡 Follow-up"

        insight = generate_insight(row, impact)

        actions.append({
            "Client": row['name'],
            "Category": tag,
            "Action": action,
            "Impact": impact,
            "Insight": insight
        })

    actions_df = pd.DataFrame(actions)

    # Metrics
    total_opportunity = actions_df['Impact'].sum()

    col1, col2 = st.columns(2)
    col1.metric("💰 Revenue Opportunity", f"₹{total_opportunity}")
    col2.metric("🎯 Priority Actions", len(actions_df))

    st.divider()

    # Display actions
    for _, row in actions_df.iterrows():
        st.markdown(f"""
        ### {row['Client']} ({row['Category']})
        **Action:** {row['Action']}  
        **Impact:** ₹{row['Impact']}  

        💡 *{row['Insight']}*
        """)
        st.divider()

else:
    st.warning("📂 Upload your Excel file to begin.")
