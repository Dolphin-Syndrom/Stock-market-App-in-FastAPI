import sqlite3, config
from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import date
from datetime import timedelta

app = FastAPI()

templates = Jinja2Templates(directory="templates")

@app.get("/")
def index(request: Request):
    stock_filter = request.query_params.get("filter", None)

    connection = sqlite3.connect(config.DB_FILE)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    if stock_filter == "new_closing_highs":
        day_before_yesterday = date.today() - timedelta(days=2)
        cursor.execute("""
            select * from(
            SELECT symbol, name, stock_id, max(close), date
               from stock_price join stock on stock.id = stock_price.stock_id
               group by stock_id
               order by symbol
            ) where date = ?
            """, (day_before_yesterday.isoformat(),))
        
    else:
        cursor.execute("""
                    SELECT id, symbol, name FROM stock ORDER BY symbol 
                    """)
        
    rows = cursor.fetchall()

    return templates.TemplateResponse("index.html", {"request": request, "stocks": rows})

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