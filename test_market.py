from exchange.bingx_client import fetch_ohlcv
import pandas as pd

data = fetch_ohlcv()
df = pd.DataFrame(
    data,
    columns=["timestamp", "open", "high", "low", "close", "volume"]
)

print(df.tail())
