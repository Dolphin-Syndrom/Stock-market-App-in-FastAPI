import sqlite3, config
from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import date, timedelta



app = FastAPI()

templates = Jinja2Templates(directory="templates")

@app.get("/")
def index(request: Request):
    stock_filter = request.query_params.get("filter", None)

    connection = sqlite3.connect(config.DB_FILE)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    
    # Define day_before_yesterday at the beginning of the function
    day_before_yesterday = date.today() - timedelta(days=2)

    if stock_filter == "new_closing_highs":
        cursor.execute("""
            select * from(
            SELECT symbol, name, stock_id, max(close), date
               from stock_price join stock on stock.id = stock_price.stock_id
               group by stock_id
               order by symbol
            ) where date = ?
            """, (day_before_yesterday.isoformat(),))
    elif stock_filter == "new_closing_lows":
        cursor.execute("""
            select * from(
            SELECT symbol, name, stock_id, min(close), date
               from stock_price join stock on stock.id = stock_price.stock_id
               group by stock_id
               order by symbol
            ) where date = ?
            """, (day_before_yesterday.isoformat(),))
    elif stock_filter == "RSI_overbought":
        cursor.execute("""
            SELECT symbol, name, stock_id, rsi_14, date
               from stock_price join stock on stock.id = stock_price.stock_id
               where rsi_14 > 70 and date = ?
               order by symbol
            """, (day_before_yesterday.isoformat(),))
    elif stock_filter == "RSI_oversold":
        cursor.execute("""
            SELECT symbol, name, stock_id, rsi_14, date
               from stock_price join stock on stock.id = stock_price.stock_id
               where rsi_14 < 30 and date = ?
               order by symbol
            """, (day_before_yesterday.isoformat(),))
    elif stock_filter == "above_sma20":
        cursor.execute("""
            SELECT symbol, name, stock_id, sma20, date
               from stock_price join stock on stock.id = stock_price.stock_id
               where close > sma20 and date = ?
               order by symbol
            """, (day_before_yesterday.isoformat(),))
    elif stock_filter == "below_sma20":
        cursor.execute("""
            SELECT symbol, name, stock_id, sma20, date
               from stock_price join stock on stock.id = stock_price.stock_id
               where close < sma20 and date = ?
               order by symbol
            """, (day_before_yesterday.isoformat(),))
    elif stock_filter == "above_sma50":
        cursor.execute("""
            SELECT symbol, name, stock_id, sma50, date
               from stock_price join stock on stock.id = stock_price.stock_id
               where close > sma50 and date = ?
               order by symbol
            """, (day_before_yesterday.isoformat(),))
    elif stock_filter == "below_sma50":
        cursor.execute("""
            SELECT symbol, name, stock_id, sma50, date
               from stock_price join stock on stock.id = stock_price.stock_id
               where close < sma50 and date = ?
               order by symbol
            """, (day_before_yesterday.isoformat(),))
    else:
        cursor.execute("""
                    SELECT id, symbol, name FROM stock ORDER BY symbol 
                    """)
        
    rows = cursor.fetchall()
    cursor.execute("""
                SELECT symbol, rsi_14, sma20, sma50, close FROM stock join stock_price on stock.id = stock_price.stock_id
                   WHERE date = ?
                   """, (day_before_yesterday.isoformat(),))

    indicator_rows = cursor.fetchall()
    indicator_values = {row['symbol']: {"rsi_14": row["rsi_14"], "sma20": row["sma20"], "sma50": row["sma50"], "close": row["close"]} for row in indicator_rows}

    

    return templates.TemplateResponse("index.html", {"request": request, "stocks": rows, "indicator_values": indicator_values})

@app.get("/stock/{symbol}")
def stock_detail(request: Request, symbol: str):
    connection = sqlite3.connect(config.DB_FILE)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
                   SELECT * FROM strategy
                   """)
    
    strategies = cursor.fetchall()

    cursor.execute("""
                SELECT id, symbol, name FROM stock WHERE symbol = ?
                """, (symbol,))
    
    stock = cursor.fetchone()

    if not stock:
        return {"error": "Stock not found"}

    cursor.execute("""
                SELECT date, open, high, low, close, volume FROM stock_price WHERE stock_id = ? ORDER BY date DESC
                """, (stock["id"],))
    
    prices = cursor.fetchall()

    return templates.TemplateResponse("stock_detail.html", {"request": request, "stock": stock, "prices": prices, "strategies": strategies})


@app.post("/apply_strategy")
def apply_strategy(strategy_id: int = Form(...), stock_id: int = Form(...)):
    connection = sqlite3.connect(config.DB_FILE)
    cursor = connection.cursor()

    cursor.execute("""
                INSERT INTO strategy_stock (stock_id, strategy_id) VALUES (?, ?)
                """, (stock_id, strategy_id))

    connection.commit()

    return RedirectResponse(url=f"/strategy/{strategy_id}", status_code=303)

@app.get("/strategy/{strategy_id}")
def strategy(request: Request, strategy_id):
    connection = sqlite3.connect(config.DB_FILE)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
                SELECT id, name FROM strategy WHERE id = ?
                """, (strategy_id,))

    strategy = cursor.fetchone()

    cursor.execute("""
                SELECT symbol, name
                FROM stock JOIN strategy_stock ON strategy_stock.stock_id = stock.id
                WHERE strategy_id = ?
                """, (strategy_id,))

    stocks = cursor.fetchall()

    return templates.TemplateResponse("strategy.html", {"request": request, "strategy": strategy, "stocks": stocks})
