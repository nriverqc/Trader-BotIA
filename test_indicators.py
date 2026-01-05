from exchange.bingx_client import fetch_ohlcv
from strategy.indicators import add_indicators
import pandas as pd

# Descargar velas
data = fetch_ohlcv()
df = pd.DataFrame(
    data,
    columns=["timestamp", "open", "high", "low", "close", "volume"]
)

# Convertir timestamp
df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

# Agregar indicadores
df = add_indicators(df)

# Mostrar últimas filas
print(df.tail())
