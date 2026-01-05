from exchange.bingx_client import fetch_ohlcv
from strategy.indicators import add_indicators
from strategy.daytrading import generate_signal
import pandas as pd

# Descargar velas
data = fetch_ohlcv()
df = pd.DataFrame(
    data,
    columns=["timestamp", "open", "high", "low", "close", "volume"]
)

df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

# Indicadores
df = add_indicators(df)

# Señal
signal = generate_signal(df)

print("📊 Señal actual:", signal)
