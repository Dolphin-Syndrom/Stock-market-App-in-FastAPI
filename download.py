import yfinance
from rich.table import Table
from rich.console import Console

console = Console()

df = yfinance.download('AAPL', start='2020-01-01', end='2020-12-31')
print(df.head())

table = Table(title="AAPL stock data", header_style="bold magenta", width=100)
table.add_column("Date", style="cyan")
table.add_column("Open", style='green')
table.add_column("High", style='red')
table.add_column("Low")
table.add_column("Close")
table.add_column("Volume")


for index, row in df.head().iterrows():
    table.add_row(
        str(index),
        str(row['Open']),
        str(row['High']),
        str(row['Low']),
        str(row['Close']),
        str(row['Volume'])
    )

console.print(table)