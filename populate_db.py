import sqlite3
import alpaca_trade_api as tradeapi

api = tradeapi.REST('your-api-key', 'your-secret-key', base_url='https://paper-api.alpaca.markets')
assets = api.list_assets()

connection = sqlite3.connect('app.db')
cursor = connection.cursor()

for asset in assets:
    try:
        if asset.status == 'active' and asset.tradable:
            cursor.execute("INSERT into stock (symbol, company) VALUES (?, ?)", (asset.symbol, asset.name))
    except Exception as e:
        print(asset.symbol)
        print(e)

connection.commit()