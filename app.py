import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Advisor AI System", layout="wide")

st.title("📊 Advisor AI Growth System")

# -----------------------------
# SESSION STATE INIT
# -----------------------------
if "data" not in st.session_state:
    st.session_state.data = None

# -----------------------------
# FILE UPLOAD
# -----------------------------
st.sidebar.header("📂 Upload Client Data")

uploaded_file = st.sidebar.file_uploader("Upload Excel File", type=["xlsx", "csv"])

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.subheader("🔍 Raw Data Preview")
    st.dataframe(df.head())

    # -----------------------------
    # COLUMN MAPPING
    # -----------------------------
    st.subheader("⚙️ Map Your Columns")

    columns = df.columns.tolist()

    name_col = st.selectbox("Client Name Column", columns)
    phone_col = st.selectbox("Phone Column", columns)
    investment_col = st.selectbox("Investment Amount Column", columns)
    last_contact_col = st.selectbox("Last Contact Days Column", columns)

    if st.button("✅ Confirm Mapping"):
        mapped_df = pd.DataFrame({
            "name": df[name_col],
            "phone": df[phone_col],
            "investment": pd.to_numeric(df[investment_col], errors="coerce").fillna(0),
            "last_contact_days": pd.to_numeric(df[last_contact_col], errors="coerce").fillna(30)
        })

        # -----------------------------
        # SCORING ENGINE (RULE-BASED)
        # -----------------------------
        mapped_df["score"] = (
            mapped_df["investment"] * 0.6 +
            mapped_df["last_contact_days"] * 10
        )

        mapped_df["priority"] = pd.cut(
            mapped_df["score"],
            bins=[-1, 10000, 50000, 100000000],
            labels=["Low", "Medium", "High"]
        )

        st.session_state.data = mapped_df
        st.success("✅ Data Processed Successfully!")

# -----------------------------
# MAIN APP (AFTER DATA LOAD)
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

    for i, row in high_priority.head(5).iterrows():
        st.write(f"👉 Call {row['name']} (High Potential Client)")

    # -----------------------------
    # WHATSAPP GENERATOR
    # -----------------------------
    st.subheader("💬 WhatsApp Message Generator")

    selected_client = st.selectbox("Select Client", df["name"])

    client_data = df[df["name"] == selected_client].iloc[0]

    message = f"""
Hi {client_data['name']},  
I wanted to discuss a good investment opportunity with you based on your profile.  
Let me know a convenient time to connect.  
"""

    st.text_area("Generated Message", message, height=150)

    phone = str(client_data["phone"])

    wa_link = f"https://wa.me/{phone}?text={message.replace(' ', '%20')}"

    st.markdown(f"[📲 Send WhatsApp Message]({wa_link})")

    # -----------------------------
    # EVENT ENGINE (LITE)
    # -----------------------------
    st.subheader("🎯 Smart Event Engine")

    event_clients = df[df["priority"] != "Low"]

    st.write("Suggested Clients for Event:")
    st.dataframe(event_clients[["name", "priority"]])

    if st.button("📩 Generate Event Invite Message"):
        st.text("""
Hello,  
We are आयोजन an exclusive investment session.  
Join us to explore new opportunities.  
Reply YES to confirm your seat.
        """)

    # -----------------------------
    # DOWNLOAD PROCESSED DATA
    # -----------------------------
    st.subheader("⬇️ Download Processed Data")

    st.download_button(
        "Download CSV",
        df.to_csv(index=False),
        file_name="processed_clients.csv"
    )

else:
    st.info("👈 Upload an Excel file to start")
