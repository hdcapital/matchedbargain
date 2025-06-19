import streamlit as st
import pandas as pd
import time

st.set_page_config(page_title="Order Matching App", layout="wide")
st.title("🧮 Order Matching System")

# Initialize session state
if "orders" not in st.session_state:
    st.session_state.orders = []
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = None  # Order ID being edited

# Generate a new order ID
def next_order_id():
    if not st.session_state.orders:
        return 1
    return max(o['ID'] for o in st.session_state.orders) + 1

# Add or amend order
def save_order(order_data):
    if st.session_state.edit_mode is not None:
        # Amend mode
        st.session_state.orders = [
            o if o['ID'] != st.session_state.edit_mode else order_data
            for o in st.session_state.orders
        ]
        st.session_state.edit_mode = None
    else:
        # New order
        st.session_state.orders.append(order_data)

# Cancel order by ID
def cancel_order(order_id):
    st.session_state.orders = [o for o in st.session_state.orders if o['ID'] != order_id]

# Start amend
def start_amend(order_id):
    st.session_state.edit_mode = order_id

# Clear all
def clear_orders():
    st.session_state.orders = []
    st.session_state.edit_mode = None

# Form input
with st.form("order_form"):
    col1, col2, col3, col4 = st.columns(4)

    default = None
    if st.session_state.edit_mode is not None:
        # Fill form with existing order data
        target = next(o for o in st.session_state.orders if o['ID'] == st.session_state.edit_mode)
        default = target

    side = col1.selectbox("Side", ["Buy", "Sell"], index=0 if not default else (0 if default["Side"] == "Buy" else 1))
    price = col2.number_input("Price", min_value=0.0, format="%.2f", value=default["Price"] if default else 0.0)
    quantity = col3.number_input("Quantity", min_value=1, step=1, value=default["Quantity"] if default else 1)
    participant = col4.text_input("Participant", value=default["Participant"] if default else "")

    submitted = st.form_submit_button("Amend Order" if default else "Add Order")
    if submitted:
        if participant.strip() == "":
            st.warning("Participant name is required.")
        else:
            order_data = {
                "ID": default["ID"] if default else next_order_id(),
                "Side": side,
                "Price": price,
                "Quantity": quantity,
                "Participant": participant.strip(),
                "Time": time.time()
            }
            save_order(order_data)

# Show orders with Cancel/Amend buttons
if st.session_state.orders:
    st.subheader("📘 Order Book")

    order_df = pd.DataFrame(st.session_state.orders).sort_values(
        by=["Price", "Time"], ascending=[False, True]  # sort Buy/Sell later
    )
    order_df_display = order_df.drop(columns=["Time"])
    st.dataframe(order_df_display, use_container_width=True)

    for o in st.session_state.orders:
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button(f"✏️ Amend #{o['ID']}", key=f"amend_{o['ID']}"):
                start_amend(o['ID'])
        with col2:
            if st.button(f"❌ Cancel #{o['ID']}", key=f"cancel_{o['ID']}"):
                cancel_order(o['ID'])

    st.button("🧹 Clear All Orders", on_click=clear_orders)

    # Depth Table
    order_df_grouped = pd.DataFrame(st.session_state.orders)
    buy_depth = order_df_grouped[order_df_grouped['Side'] == 'Buy'].groupby('Price')['Quantity'].sum().sort_index(ascending=False)
    sell_depth = order_df_grouped[order_df_grouped['Side'] == 'Sell'].groupby('Price')['Quantity'].sum().sort_index()

    depth_df = pd.DataFrame({
        'Sell Quantity': sell_depth,
        'Buy Quantity': buy_depth
    }).fillna(0).astype(int)

    st.subheader("📊 Order Book Depth")
    st.dataframe(depth_df)

    # Match Orders
    if st.button("⚖️ Match Orders"):
        df = pd.DataFrame(st.session_state.orders)
        prices = sorted(set(df['Price']))
        results = []
        for price in prices:
            buy_volume = df[(df['Side'] == 'Buy') & (df['Price'] >= price)]['Quantity'].sum()
            sell_volume = df[(df['Side'] == 'Sell') & (df['Price'] <= price)]['Quantity'].sum()
            matched_volume = min(buy_volume, sell_volume)
            results.append((price, matched_volume))

        clearing_price, max_volume = max(results, key=lambda x: (x[1], -x[0]))

        buy_orders = df[(df['Side'] == 'Buy') & (df['Price'] >= clearing_price)].sort_values(by=['Price', 'Time'], ascending=[False, True])
        sell_orders = df[(df['Side'] == 'Sell') & (df['Price'] <= clearing_price)].sort_values(by=['Price', 'Time'])

        trades = []
        remaining_buy = buy_orders.copy()
        remaining_sell = sell_orders.copy()

        for s_index, sell_row in remaining_sell.iterrows():
            for b_index, buy_row in remaining_buy.iterrows():
                if remaining_sell.at[s_index, 'Quantity'] == 0:
                    break
                trade_qty = min(sell_row['Quantity'], remaining_buy.at[b_index, 'Quantity'])
                if trade_qty > 0:
                    trades.append({
                        'Buyer': buy_row['Participant'],
                        'Seller': sell_row['Participant'],
                        'Price': clearing_price,
                        'Quantity': trade_qty
                    })
                    remaining_sell.at[s_index, 'Quantity'] -= trade_qty
                    remaining_buy.at[b_index, 'Quantity'] -= trade_qty

        st.subheader("✅ Matched Trades")
        if trades:
            st.dataframe(pd.DataFrame(trades))
        else:
            st.write("No trades matched.")

        st.info(f"Clearing Price: **{clearing_price}**, Matched Volume: **{max_volume}**")

else:
    st.info("No orders entered yet.")
