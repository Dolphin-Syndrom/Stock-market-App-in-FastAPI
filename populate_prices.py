import sqlite3, config
import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import REST, TimeFrame
from datetime import datetime, timedelta

connection = sqlite3.connect(config.DB_FILE)
connection.row_factory = sqlite3.Row
cursor = connection.cursor()

if stock_filter == "new_intraday_highs":
    cursor.execute("""
            select * from(
                SELECT s.id, s.symbol, s.name FROM stock s
                JOIN stock_price sp ON s.id = sp.stock_id
                WHERE sp.close >= sp.high
                GROUP BY s.id, s.symbol, s.name
                ORDER BY s.symbol
                   ) where date = ?
                """, (datetime.now().date(),)) 
else:
    cursor.execute("""
            SELECT id, symbol, name FROM stock ORDER by symbol
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

# Get dates for the last 5 trading days
end_date = datetime.now() - timedelta(days=1)  # Yesterday
start_date = end_date - timedelta(days=5)  # 5 days before

chunk_size = 200
for i in range(0, len(valid_symbols), chunk_size):
    symbol_chunk = valid_symbols[i:i+chunk_size]
    try:
        barsets = api.get_bars(
            symbol_chunk,
            TimeFrame.Day,
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            adjustment='raw'
        )
        
        for bar in barsets:
            symbol = bar.S
            print(f"Processing symbol {symbol} - Date: {bar.t.date()}")
            
            stock_id = stock_dict[symbol]

            timestamp = bar.t.split('T')[0] if isinstance(bar.t, str) else bar.t.date()
            print(f"Timestamp: {timestamp}")

            cursor.execute("""
                INSERT INTO stock_price (stock_id, date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (stock_id, timestamp, bar.o, bar.h, bar.l, bar.c, bar.v))
            
    except tradeapi.rest.APIError as e:
        print(f"Error fetching data for symbols {symbol_chunk}: {e}")

connection.commit()