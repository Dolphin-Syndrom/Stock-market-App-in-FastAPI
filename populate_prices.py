import sqlite3, config
import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import REST, TimeFrame

connection = sqlite3.connect(config.DB_FILE)
connection.row_factory = sqlite3.Row
cursor = connection.cursor()

cursor.execute("""
            SELECT id, symbol, name FROM stock
               """)

rows = cursor.fetchall()

symbols = []
stock_dict = {}
for row in rows:
    symbol = row['symbol']
    symbols.append(symbol)
    stock_dict[symbol] = row['id']

api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url=config.BASE_URL)

valid_symbols = [symbol for symbol in symbols if "/" not in symbol]

chunk_size = 200
for i in range(0, len(valid_symbols), chunk_size):
    symbol_chunk = valid_symbols[i:i+chunk_size]
    try:
        barsets = api.get_bars(symbol_chunk, TimeFrame.Day, "2021-06-04", "2021-06-04", adjustment='raw')
        for bar in barsets:
            symbol = bar.S
            print(f"Processing symbol {symbol}")
            
            stock_id = stock_dict[symbol]
          
            date = bar.t.date() if hasattr(bar.t, 'date') else str(bar.t).split("T")[0]
            cursor.execute("""
                INSERT INTO stock_price (stock_id, date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (stock_id, date, bar.o, bar.h, bar.l, bar.c, bar.v))
    except tradeapi.rest.APIError as e:
        print(f"Error fetching data for symbols {symbol_chunk}: {e}")

connection.commit()