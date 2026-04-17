import streamlit as st
import pandas as pd
import datetime
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# --- CONFIGURATION & UI ---
st.set_page_config(page_title="FinIntelligence Pro", layout="wide")

# --- 1. PERSONALIZED GREETING LOGIC ---
def get_greeting(name):
    hour = datetime.datetime.now().hour
    if hour < 12:
        greet = "Good Morning"
    elif 12 <= hour < 17:
        greet = "Good Afternoon"
    else:
        greet = "Good Evening"
    return f"Hi {name}, {greet}! ✨"

# --- SIDEBAR: LOGIN & SETUP ---
with st.sidebar:
    st.title("Settings")
    user_name = st.text_input("Enter your name", value="Advisor")
    st.divider()
    uploaded_file = st.file_uploader("Upload your Excel/CSV Data", type=['xlsx', 'csv'])

# --- MAIN INTERFACE ---
st.title(get_greeting(user_name))
st.subheader("What's on your mind today?")

if uploaded_file:
    # Load Data
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.success("Data loaded successfully!")
    
    # --- 2. GENERAL MAPPING (The "Smart" part) ---
    st.info("Identify your data columns so the AI can analyze them:")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        name_col = st.selectbox("Client Name Column", df.columns)
    with col2:
        date_col = st.selectbox("Last Transaction Date", df.columns)
    with col3:
        val_col = st.selectbox("Total Investment/AUM Column", df.columns)

    # Convert date
    df[date_col] = pd.to_datetime(df[date_col])
    
    # --- 3. DATA SCIENCE ENGINE (Clustering) ---
    # We calculate 'Recency' automatically for the user
    df['DaysSinceLast'] = (pd.Timestamp.now() - df[date_col]).dt.days
    
    # Simple Clustering Logic
    X = df[['DaysSinceLast', val_col]].fillna(0)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    model = KMeans(n_clusters=3, random_state=42)
    df['Segment'] = model.fit_predict(X_scaled)

    # --- 4. ACTIONABLE DASHBOARD ---
    st.divider()
    st.header("🎯 Your Strategic Action Plan")
    
    tab1, tab2, tab3 = st.tabs(["Priority Meetings", "Event Planner", "Revenue Opportunities"])

    with tab1:
        st.write("### 🚨 Clients to Call Today (Risk of Churn)")
        # Logic: High DaysSinceLast = High Risk
        risk_clients = df.sort_values(by='DaysSinceLast', ascending=False).head(5)
        st.table(risk_clients[[name_col, 'DaysSinceLast', val_col]])

    with tab2:
        st.write("### 📅 Micro-Event Suggestions")
        st.write("Based on your data, group these clients for a tea-meet or webinar:")
        # Logic: Suggesting the "Champion" segment for a referral event
        champion_cluster = df[df['Segment'] == 0].head(10)
        st.write(f"**Target Group:** Top Investors")
        st.write(f"**Topic:** 'Exclusive Wealth Strategies for 2024'")
        st.dataframe(champion_cluster[[name_col, val_col]])

    with tab3:
        st.write("### 💰 Cross-Sell Potential")
        # Logic: Low days since last but low AUM = Potential to grow
        potential = df[(df['DaysSinceLast'] < 30) & (df[val_col] < df[val_col].median())]
        st.write("These clients are active but have small portfolios. Pitch a new SIP!")
        st.dataframe(potential[[name_col, val_col]])

else:
    # DEFAULT VIEW (Before upload)
    st.warning("Please upload your client data in the sidebar to begin.")
    
    # Visualizing how the data flows
    
    
    st.write("""
    ### Why use this instead of Excel?
    1. **Predictive Alerts:** Excel shows what happened. This shows who is *leaving*.
    2. **Automated Segmentation:** No manual pivot tables. The AI groups your clients for you.
    3. **Action-Oriented:** It gives you a 'Call List' every morning.
    """)    
