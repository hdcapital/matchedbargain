import streamlit as st
import pandas as pd
import socket
import requests
from datetime import datetime
from supabase import create_client, Client

# --- Supabase Setup ---
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase: Client = create_client(url, key)

# --- Page Setup ---
st.set_page_config(page_title="Order Matching System", layout="wide")
col_logo, col_title = st.columns([1, 6])
with col_logo:
    pass  # logo removed for now
with col_title:
    st.title("🧮 Order Matching System")

# --- Get Participant (based on IP as proxy) ---
def get_ip():
    try:
        return requests.get('https://api.ipify.org').text
    except:
        return "Unknown"

participant_ip = get_ip()

# --- Submit Order ---
st.markdown("### Submit Order")
with st.form("order_form"):
    side, price, quantity = st.columns(3)
    order_side = side.selectbox("Side", ["Buy", "Sell"])
    order_price = price.number_input("Price ($)", min_value=0.01, step=0.01)
    order_qty = quantity.number_input("Quantity", min_value=1, step=1)

    submitted = st.form_submit_button("Submit Order")
    if submitted:
        try:
            supabase.table("orders").insert({
                "side": order_side,
                "price": order_price,
                "quantity": order_qty,
                "participant": participant_ip,
                "timestamp": datetime.utcnow().isoformat()
            }).execute()
            st.success("✅ Order submitted successfully.")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"❌ Error submitting order: {e}")

# --- Order Book Display ---
st.markdown("### 📘 Live Market Depth")

orders = supabase.table("orders").select("*").order("timestamp", desc=False).execute()
data = orders.data

if not data:
    st.info("No orders yet.")
else:
    df = pd.DataFrame(data)
    df = df[["side", "price", "quantity", "participant", "timestamp"]]

    buyers = df[df["side"] == "Buy"].groupby("price", as_index=False).agg({
        "quantity": "sum",
        "participant": "count"
    }).sort_values(by="price", ascending=False)

    sellers = df[df["side"] == "Sell"].groupby("price", as_index=False).agg({
        "quantity": "sum",
        "participant": "count"
    }).sort_values(by="price", ascending=True)

    buyers.columns = ["Price ($)", "Volume", "No."]
    sellers.columns = ["Price ($)", "Volume", "No."]

    left, right = st.columns(2)
    with left:
        st.markdown("#### Buyers")
        st.dataframe(buyers, use_container_width=True)
    with right:
        st.markdown("#### Sellers")
        st.dataframe(sellers, use_container_width=True)
