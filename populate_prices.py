import sqlite3, config
import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import REST, TimeFrame
from datetime import datetime, timedelta
import tulipy, numpy

connection = sqlite3.connect(config.DB_FILE)
connection.row_factory = sqlite3.Row
cursor = connection.cursor()

# Before running this script, execute this SQL to add the columns if they don't exist:
# cursor.execute("""
#     ALTER TABLE stock_price ADD COLUMN sma20 REAL;
#     ALTER TABLE stock_price ADD COLUMN sma50 REAL;
#     ALTER TABLE stock_price ADD COLUMN rsi14 REAL;
# """)

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

# 3 months to yesterday of daily data
end_date = datetime.now() - timedelta(days=1)  # Yesterday
start_date = end_date - timedelta(days=90)  

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
        
        symbol_bars = {}
        for bar in barsets:
            if bar.S not in symbol_bars:
                symbol_bars[bar.S] = []
            symbol_bars[bar.S].append(bar)
            
       
        for symbol, bars in symbol_bars.items():
            if symbol not in stock_dict:
                continue
                
            stock_id = stock_dict[symbol]
            recent_closes = [bar.c for bar in bars]
            
            
            sorted_bars = sorted(bars, key=lambda x: x.t)
            
            indicators_calculated = False
            if len(recent_closes) >= 50:
                sma20 = tulipy.sma(numpy.array(recent_closes), period=20)[-1]
                sma50 = tulipy.sma(numpy.array(recent_closes), period=50)[-1]
                rsi_14 = tulipy.rsi(numpy.array(recent_closes), period=14)[-1]
                indicators_calculated = True
                print(f"Latest indicators for {symbol} - SMA20: {sma20}, SMA50: {sma50}, RSI14: {rsi_14}")
            else:
                sma20, sma50, rsi_14 = None, None, None
                
            for i, bar in enumerate(sorted_bars):
                timestamp = bar.t.date()
                print(f"Processing symbol {symbol} - Date: {timestamp}")
                
                if i == len(sorted_bars) - 1 and indicators_calculated:
                    cursor.execute("""
                        INSERT INTO stock_price (stock_id, date, open, high, low, close, volume, sma20, sma50, rsi_14)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (stock_id, timestamp, bar.o, bar.h, bar.l, bar.c, bar.v, sma20, sma50, rsi_14))
                else:
                    cursor.execute("""
                        INSERT INTO stock_price (stock_id, date, open, high, low, close, volume, sma20, sma50, rsi_14)
                        VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL)
                    """, (stock_id, timestamp, bar.o, bar.h, bar.l, bar.c, bar.v))
            
    except tradeapi.rest.APIError as e:
        print(f"Error fetching data for symbols {symbol_chunk}: {e}")

connection.commit()