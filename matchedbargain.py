import pandas as pd

# ----------- Step 1: Take orders from the user -------------
print("Enter your orders one per line in the format:")
print("Side Price Quantity Participant")
print("Example: Buy 10.50 1000 Alice")
print("Type DONE when finished.\n")

orders = []
while True:
    line = input("Order: ")
    if line.strip().upper() == "DONE":
        break
    try:
        side, price, quantity, participant = line.strip().split()
        orders.append({
            "Side": side.capitalize(),
            "Price": float(price),
            "Quantity": int(quantity),
            "Participant": participant
        })
    except:
        print("Invalid format. Try again (e.g. Buy 10.50 1000 Alice)")

# ----------- Step 2: Create DataFrame -------------
df = pd.DataFrame(orders)
if df.empty:
    print("\nNo orders entered.")
    exit()

# ----------- Step 3: Determine clearing price -------------
prices = sorted(set(df['Price']))
results = []
for price in prices:
    buy_volume = df[(df['Side'] == 'Buy') & (df['Price'] >= price)]['Quantity'].sum()
    sell_volume = df[(df['Side'] == 'Sell') & (df['Price'] <= price)]['Quantity'].sum()
    matched_volume = min(buy_volume, sell_volume)
    results.append((price, matched_volume))

clearing_price, max_volume = max(results, key=lambda x: (x[1], -x[0]))

# ----------- Step 4: Match orders at clearing price -------------
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

# ----------- Step 5: Output results -------------

# Show Order Book Depth
print("\n--- Order Book Depth ---")

buy_depth = df[df['Side'] == 'Buy'].groupby('Price')['Quantity'].sum().sort_index(ascending=False)
sell_depth = df[df['Side'] == 'Sell'].groupby('Price')['Quantity'].sum().sort_index()

depth_df = pd.DataFrame({
    'Sell Quantity': sell_depth,
    'Buy Quantity': buy_depth
}).fillna(0).astype(int)

print(depth_df)

# Show clearing price and matched trades
print(f"\nClearing Price: {clearing_price}, Matched Volume: {max_volume}")

if trades:
    print("\n--- Matched Trades ---\n")
    trades_df = pd.DataFrame(trades)
    print(trades_df)
else:
    print("\nNo trades matched.")

