import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Advisor AI System", layout="wide")
st.title("📊 Advisor AI Growth System")

# -----------------------------
# SESSION STATE
# -----------------------------
if "data" not in st.session_state:
    st.session_state.data = None

# -----------------------------
# AUTO COLUMN DETECTION
# -----------------------------
def detect_column(possible_names, columns):
    for col in columns:
        col_clean = col.lower().replace(" ", "").replace("_", "")
        for name in possible_names:
            if name in col_clean:
                return col
    return None

# -----------------------------
# DATA CLEANING FUNCTIONS
# -----------------------------
def clean_phone(phone):
    phone = str(phone)
    phone = ''.join(filter(str.isdigit, phone))
    if len(phone) == 10:
        return "91" + phone
    return phone

def clean_investment(val):
    try:
        return float(str(val).replace(",", "").replace("₹", ""))
    except:
        return 0

def clean_days(val):
    try:
        return int(val)
    except:
        return 30

# -----------------------------
# FILE UPLOAD
# -----------------------------
st.sidebar.header("📂 Upload Client Data")

uploaded_file = st.sidebar.file_uploader("Upload Excel/CSV", type=["xlsx", "csv"])

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.subheader("🔍 Raw Data Preview")
    st.dataframe(df.head())

    columns = df.columns.tolist()

    # -----------------------------
    # AUTO DETECT
    # -----------------------------
    name_col = detect_column(["name", "client"], columns)
    phone_col = detect_column(["phone", "mobile", "contact"], columns)
    investment_col = detect_column(["investment", "amount", "value"], columns)
    last_contact_col = detect_column(["last", "days", "contact"], columns)

    st.info("✅ Columns auto-detected. You can change if needed.")

    name_col = st.selectbox("Client Name", columns, index=columns.index(name_col) if name_col in columns else 0)
    phone_col = st.selectbox("Phone", columns, index=columns.index(phone_col) if phone_col in columns else 0)
    investment_col = st.selectbox("Investment", columns, index=columns.index(investment_col) if investment_col in columns else 0)
    last_contact_col = st.selectbox("Last Contact Days", columns, index=columns.index(last_contact_col) if last_contact_col in columns else 0)

    if st.button("🚀 Process Data"):

        # -----------------------------
        # CLEAN DATA
        # -----------------------------
        mapped_df = pd.DataFrame({
            "name": df[name_col].astype(str).str.strip(),
            "phone": df[phone_col].apply(clean_phone),
            "investment": df[investment_col].apply(clean_investment),
            "last_contact_days": df[last_contact_col].apply(clean_days)
        })

        # Handle missing
        mapped_df["name"].replace("", "Unknown", inplace=True)
        mapped_df["phone"].replace("", "0000000000", inplace=True)

        # -----------------------------
        # SMART DEDUPE (MERGE)
        # -----------------------------
        before = len(mapped_df)

        grouped_df = mapped_df.groupby("phone").agg({
            "name": lambda x: x.mode()[0] if not x.mode().empty else x.iloc[0],
            "investment": "sum",
            "last_contact_days": "min"
        }).reset_index()

        after = len(grouped_df)

        if before != after:
            st.warning(f"⚠️ {before - after} duplicate entries merged intelligently")

        # -----------------------------
        # SCORING ENGINE
        # -----------------------------
        grouped_df["score"] = (
            grouped_df["investment"] * 0.6 +
            grouped_df["last_contact_days"] * 10
        )

        grouped_df["priority"] = pd.cut(
            grouped_df["score"],
            bins=[-1, 10000, 50000, 100000000],
            labels=["Low", "Medium", "High"]
        )

        st.session_state.data = grouped_df

        st.success("✅ Data cleaned, merged, and processed successfully!")

# -----------------------------
# MAIN APP
# -----------------------------
if st.session_state.data is not None:

    df = st.session_state.data

    st.subheader("📊 Dashboard")

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Clients", len(df))
    col2.metric("Total Investment", int(df["investment"].sum()))
    col3.metric("High Priority Clients", len(df[df["priority"] == "High"]))

    st.dataframe(df)

    # -----------------------------
    # DECISION ENGINE
    # -----------------------------
    st.subheader("🧠 Next Best Actions")

    high_priority = df[df["priority"] == "High"]

    if len(high_priority) == 0:
        st.info("No high priority clients found")
    else:
        for i, row in high_priority.head(5).iterrows():
            st.write(f"👉 Call {row['name']} (High Potential)")

    # -----------------------------
    # WHATSAPP
    # -----------------------------
    st.subheader("💬 WhatsApp Message")

    selected_client = st.selectbox("Select Client", df["name"])

    client_data = df[df["name"] == selected_client].iloc[0]

    message = f"""
Hi {client_data['name']},  
I wanted to discuss a good investment opportunity with you.  
Let me know a convenient time.  
"""

    st.text_area("Message", message)

    phone = client_data["phone"]
    wa_link = f"https://wa.me/{phone}?text={message.replace(' ', '%20')}"

    st.markdown(f"[📲 Send WhatsApp]({wa_link})")

    # -----------------------------
    # EVENT ENGINE
    # -----------------------------
    st.subheader("🎯 Event Target Clients")

    event_df = df[df["priority"] != "Low"]

    st.dataframe(event_df[["name", "priority"]])

    if st.button("📩 Generate Invite"):
        st.text("""
Hello,  
We are hosting an exclusive investment session.  
Reply YES to confirm your seat.
        """)

    # -----------------------------
    # DOWNLOAD
    # -----------------------------
    st.subheader("⬇️ Download Clean Data")

    st.download_button(
        "Download CSV",
        df.to_csv(index=False),
        file_name="clean_clients.csv"
    )

else:
    st.info("👈 Upload file to begin")
    
