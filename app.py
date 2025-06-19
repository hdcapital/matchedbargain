import streamlit as st
import pandas as pd
from supabase import create_client, Client

# 🔐 Load Supabase credentials from secrets
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Order Matching App", layout="wide")
st.title("🧮 Order Matching System")

# --- Order Submission Form ---
with st.form("order_form"):
    col1, col2, col3, col4 = st.columns(4)
    side = col1.selectbox("Side", ["Buy", "Sell"])
    price = col2.number_input("Price", min_value=0.01, step=0.01)
    quantity = col3.number_input("Quantity", min_value=1, step=1)
    participant = col4.text_input("Participant")

    submitted = st.form_submit_button("Add Order")

    if submitted:
        if not participant:
            st.warning("Participant name required.")
        else:
            supabase.table("orders").insert({
                "side": side,
                "price": price,
                "quantity": quantity,
                "participant": participant
            }).execute()
            st.success("✅ Order saved to Supabase.")
            st.experimental_rerun()

# --- Show Order Book from Supabase ---
st.subheader("📘 Live Order Book")

orders = supabase.table("orders").select("*").order("timestamp", desc=False).execute()
data = orders.data

if data:
    df = pd.DataFrame(data)
    df = df[["id", "side", "price", "quantity", "participant", "timestamp"]]
    st.dataframe(df, use_container_width=True)
else:
    st.info("No orders yet.")
