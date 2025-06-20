import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd

# Set up root window
root = tk.Tk()
root.title("Order Matching App")
root.geometry("800x600")

orders = []

# Function to add order
def add_order():
    side = side_var.get()
    try:
        price = float(price_var.get())
        qty = int(quantity_var.get())
        participant = participant_var.get().strip()
    except ValueError:
        messagebox.showerror("Input Error", "Invalid number format.")
        return
    if participant == "":
        messagebox.showerror("Input Error", "Participant name is required.")
        return
    orders.append({"Side": side, "Price": price, "Quantity": qty, "Participant": participant})
    update_order_list()

# Function to update display
def update_order_list():
    for row in order_tree.get_children():
        order_tree.delete(row)
    for o in orders:
        order_tree.insert('', 'end', values=(o['Side'], o['Price'], o['Quantity'], o['Participant']))

# Function to match orders
def match_orders():
    if not orders:
        messagebox.showinfo("Info", "No orders to match.")
        return

    df = pd.DataFrame(orders)
    prices = sorted(set(df['Price']))
    results = []
    for price in prices:
        buy_volume = df[(df['Side'] == 'Buy') & (df['Price'] >= price)]['Quantity'].sum()
        sell_volume = df[(df['Side'] == 'Sell') & (df['Price'] <= price)]['Quantity'].sum()
        matched_volume = min(buy_volume, sell_volume)
        results.append((price, matched_volume))

    clearing_price, max_volume = max(results, key=lambda x: (x[1], -x[0]))

    buy_orders = df[(df['Side'] == 'Buy') & (df['Price'] >= clearing_price)].sort_values(by='Price', ascending=False)
    sell_orders = df[(df['Side'] == 'Sell') & (df['Price'] <= clearing_price)].sort_values(by='Price')

    trades = []
    remaining_buy = buy_orders.copy()
    remaining_sell = sell_orders.copy()

    for s_index, sell_row in remaining_sell.iterrows():
        for b_index, buy_row in remaining_buy.iterrows():
            if remaining_sell.at[s_index, 'Quantity'] == 0:
                break
            trade_qty = min(remaining_sell.at[s_index, 'Quantity'], remaining_buy.at[b_index, 'Quantity'])
            if trade_qty > 0:
                trades.append({
                    'Buyer': buy_row['Participant'],
                    'Seller': sell_row['Participant'],
                    'Price': clearing_price,
                    'Quantity': trade_qty
                })
                remaining_sell.at[s_index, 'Quantity'] -= trade_qty
                remaining_buy.at[b_index, 'Quantity'] -= trade_qty

    # Show results
    result_text.delete("1.0", tk.END)
    result_text.insert(tk.END, f"Clearing Price: {clearing_price}\nMatched Volume: {max_volume}\n\n")

    if trades:
        trade_df = pd.DataFrame(trades)
        result_text.insert(tk.END, trade_df.to_string(index=False))
    else:
        result_text.insert(tk.END, "No trades matched.")

# Input Fields
frame = tk.Frame(root)
frame.pack(pady=10)

tk.Label(frame, text="Side").grid(row=0, column=0)
side_var = tk.StringVar(value="Buy")
tk.OptionMenu(frame, side_var, "Buy", "Sell").grid(row=0, column=1)

tk.Label(frame, text="Price").grid(row=0, column=2)
price_var = tk.StringVar()
tk.Entry(frame, textvariable=price_var).grid(row=0, column=3)

tk.Label(frame, text="Quantity").grid(row=0, column=4)
quantity_var = tk.StringVar()
tk.Entry(frame, textvariable=quantity_var).grid(row=0, column=5)

tk.Label(frame, text="Participant").grid(row=0, column=6)
participant_var = tk.StringVar()
tk.Entry(frame, textvariable=participant_var).grid(row=0, column=7)

tk.Button(frame, text="Add Order", command=add_order).grid(row=0, column=8, padx=10)

# Order list
order_tree = ttk.Treeview(root, columns=("Side", "Price", "Quantity", "Participant"), show='headings')
for col in ("Side", "Price", "Quantity", "Participant"):
    order_tree.heading(col, text=col)
    order_tree.column(col, width=100)
order_tree.pack(pady=10, fill=tk.X)

# Match button and results
tk.Button(root, text="Match Orders", command=match_orders).pack(pady=10)
result_text = tk.Text(root, height=15)
result_text.pack(fill=tk.BOTH, padx=10, pady=10)

root.mainloop()
