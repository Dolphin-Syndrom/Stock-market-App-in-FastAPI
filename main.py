import sqlite3, config
from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import date, timedelta
import ollama
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


app = FastAPI()

templates = Jinja2Templates(directory="templates")

@app.get("/")
def index(request: Request):
    stock_filter = request.query_params.get("filter", None)

    connection = sqlite3.connect(config.DB_FILE)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    
    # Get the latest date available in the database
    cursor.execute("""
        SELECT date FROM stock_price
        ORDER BY date DESC
        LIMIT 1
    """)
    latest_date_row = cursor.fetchone()
    
    if not latest_date_row:
        return templates.TemplateResponse("index.html", {"request": request, "stocks": [], "indicator_values": {}, "error": "No stock data available"})
    
    latest_date = latest_date_row['date']
    print(f"Using latest date for filtering: {latest_date}")

    if stock_filter == "new_closing_highs":
        cursor.execute("""
            select * from(
            SELECT symbol, name, stock_id, max(close), date
               from stock_price join stock on stock.id = stock_price.stock_id
               group by stock_id
               order by symbol
            ) where date = ?
            """, (latest_date,))
        
    elif stock_filter == "new_closing_lows":
        cursor.execute("""
            select * from(
            SELECT symbol, name, stock_id, min(close), date
               from stock_price join stock on stock.id = stock_price.stock_id
               group by stock_id
               order by symbol
            ) where date = ?
            """, (latest_date,))
        
    elif stock_filter == "RSI_overbought":
        cursor.execute("""
            SELECT symbol, name, stock_id, rsi_14, date
               from stock_price join stock on stock.id = stock_price.stock_id
               where rsi_14 > 70 and date = ?
               order by symbol
            """, (latest_date,))
        
    elif stock_filter == "RSI_oversold":
        cursor.execute("""
            SELECT symbol, name, stock_id, rsi_14, date
               from stock_price join stock on stock.id = stock_price.stock_id
               where rsi_14 < 30 and date = ?
               order by symbol
            """, (latest_date,))
        
    elif stock_filter == "above_sma20":
        cursor.execute("""
            SELECT symbol, name, stock_id, sma20, date
               from stock_price join stock on stock.id = stock_price.stock_id
               where close > sma20 and date = ?
               order by symbol
            """, (latest_date,))
    elif stock_filter == "below_sma20":
        cursor.execute("""
            SELECT symbol, name, stock_id, sma20, date
               from stock_price join stock on stock.id = stock_price.stock_id
               where close < sma20 and date = ?
               order by symbol
            """, (latest_date,))
    elif stock_filter == "above_sma50":
        cursor.execute("""
            SELECT symbol, name, stock_id, sma50, date
               from stock_price join stock on stock.id = stock_price.stock_id
               where close > sma50 and date = ?
               order by symbol
            """, (latest_date,))
    elif stock_filter == "below_sma50":
        cursor.execute("""
            SELECT symbol, name, stock_id, sma50, date
               from stock_price join stock on stock.id = stock_price.stock_id
               where close < sma50 and date = ?
               order by symbol
            """, (latest_date,))
    else:
        cursor.execute("""
                    SELECT id, symbol, name FROM stock ORDER BY symbol 
                    """)
        
    rows = cursor.fetchall()
    print(f"Filter: {stock_filter}, Records found: {len(rows)}")

    # Query for indicator values using the latest date
    cursor.execute("""
        SELECT stock_id, symbol, rsi_14, sma20, sma50, close 
        FROM stock_price JOIN stock ON stock.id = stock_price.stock_id
        WHERE date = ?
    """, (latest_date,))
    
    indicator_rows = cursor.fetchall()
    
    indicator_values = {}
    for row in indicator_rows:
        indicator_values[row['symbol']] = {
            "rsi_14": row["rsi_14"],
            "sma20": row["sma20"],
            "sma50": row["sma50"],
            "close": row["close"]
        }

    print(f"Found {len(indicator_values)} stocks with indicator values")

    return templates.TemplateResponse("index.html", {
        "request": request, 
        "stocks": rows, 
        "indicator_values": indicator_values,
        "filter": stock_filter,
        "date": latest_date
    })

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


@app.get("/strategies")
def strategies(request: Request):
    connection = sqlite3.connect(config.DB_FILE)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
                SELECT id, name FROM strategy
                """)

    strategies = cursor.fetchall()

    return templates.TemplateResponse("strategies.html", {"request": request, "strategies": strategies})

    

router = APIRouter()

class FinancialQuery(BaseModel):
    question: str

def get_financial_advice(user_input):
    prompt = f"""
    You are a professional financial advisor specializing in stock market analysis.
    Please address the following user query directly and precisely:
    
    "{user_input}"
    
    Focus only on what the user is specifically asking about. Do not add unrequested information.
    If it's a straightforward question, give a direct answer without unnecessary sections.
    
    For complex questions about investments or market analysis, use this structure:
    
    1. Direct Answer: [Directly address the specific question asked]
    2. Key Considerations: [Only relevant factors to the specific question]
    3. Recommended Actions: [Specific to what was asked]
    4. Brief Disclaimer: [Short investment disclaimer]
    
    Only provide advice related to stocks, investing, or financial markets.
    If the question is not finance-related, politely decline to answer.
    """

    response = ollama.chat(
        model="tinyllama",
        messages=[
            {
                "role": "system",
                "content": "You are an expert financial advisor. Answer exactly what is asked, nothing more and nothing less."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.get('message', {}).get('content', 'No response generated.')

@router.post("/ai-agent")
def financial_advice(query: FinancialQuery):
    if not query.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
        
    try:
        advice = get_financial_advice(query.question)
        return {"advice": advice}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating advice: {str(e)}")

@app.get("/ai-agent")
def ai_agent_page(request: Request):
    return templates.TemplateResponse("ai-agent.html", {"request": request})
app.include_router(router)

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

