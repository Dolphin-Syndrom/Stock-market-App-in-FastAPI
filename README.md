# StockMatrix Analysis

## Overview

The Stock Market Analysis Platform is a comprehensive web application designed to help investors, traders, and analysts make informed decisions using real-time data, technical indicators, and AI-powered insights. This platform combines traditional technical analysis with modern AI assistance to provide a unique approach to stock market analysis.

## Unique Solution

This platform stands out from other stock market tools by offering:

1. **Integrated Technical Analysis & AI Assistance**: Combines traditional technical indicators (RSI, SMA) with AI-powered insights from the embedded LLM model (TinyLLama).

2. **Real-time Filtering**: Quickly identify trading opportunities using pre-configured filters for overbought/oversold conditions, price breakouts, and moving average crossovers.

4. **Interactive AI Financial Advisor**: An AI agent specializing in financial markets that provides tailored advice, explanations, and analysis based on user queries.

5. **Extensible Data Platform**: SQLite database design that facilitates easy addition of new stocks, indicators, and analytical methods.

## Key Features

- **Dashboard with Technical Filters**:
  - New closing highs/lows detection
  - RSI overbought/oversold conditions (>70/<30)
  - Price relative to moving averages (SMA20, SMA50)
  - Historical price data visualization

- **Strategy Management**:
  - Create trading strategies
  - Assign stocks to strategies
  - Track strategy performance

- **Stock Details View**:
  - Comprehensive price information
  - Historical data analysis
  - Technical indicator visualization

- **AI Financial Assistant**:
  - Natural language queries for market information
  - Professional financial advice powered by LLM
  - Educational explanations for beginners

## Who Can Use This Platform

### 1. Individual Traders
- Day traders looking for technical setups
- Swing traders tracking multiple strategies
- Value investors researching stocks systematically

### 2. Financial Analysts
- Professional analysts comparing multiple stocks
- Research teams building and testing strategies
- Portfolio managers tracking market conditions

### 3. Financial Educators
- Teachers demonstrating technical analysis
- Universities providing hands-on market education
- Workshop facilitators showing real-time market dynamics

### 4. Market Beginners
- New investors learning technical analysis
- Students understanding market concepts
- Self-learners exploring trading strategies with AI guidance

## Usage Examples

### For Traders
```
1. Use filters to identify stocks meeting specific technical criteria
2. Monitor strategy performance over time
3. Get AI insights on specific stocks or market conditions
```

### For Analysts
```
1. Track multiple sectors using custom filters
2. Compare stock performance against strategies
3. Generate detailed reports on market conditions
4. Use the AI agent to get alternative perspectives on analysis
```

### For Beginners
```
1. Learn about technical indicators through practical examples
2. Ask the AI agent to explain market concepts
3. Practice building simple trading strategies
4. Understand how professional traders use technical analysis
```

## Future Implementation Possibilities

1. **Advanced Charting**: Integrate more sophisticated charting libraries with pattern recognition.

2. **API Integration**: Connect to external data providers for fundamentals, news sentiment, and alternative data.

## Getting Started

### Prerequisites
- Python 3.8
- FastAPI
- SQLite
- Ollama (for AI functionality)

### Installation
```bash
# Clone the repository
git clone https://github.com/Dolphin-Syndrom/stock-market.git

# Navigate to the project directory
cd stock-market

# Install dependencies
pip install -r requirements.txt

# Set up the database
python create_db.py
python populate_stocks.py
python populate_price.py

#To delete the database
python drop_db.py

# Run the application
uvicorn main:app --reload
```

## License

[MIT License](LICENSE)

## Acknowledgements

- Data provided by Alpaca & Yfinance
- AI capabilities powered by Ollama and TinyLLama
- Developed with FastAPI and SQLite

---

© 2025 StockMatrix Analysis
