from exchange.bingx_client import fetch_ohlcv
from strategy.indicators import add_indicators
from strategy.daytrading import generate_signal
from brain.risk import calculate_sl_tp
from brain.memory import log_trade
import pandas as pd

symbol = "BTC/USDT:USDT"

# Datos de mercado
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
last = df.iloc[-1]
price = last["close"]

print("📊 Señal:", signal)

if signal != "NO_TRADE":
    sl, tp = calculate_sl_tp(price, last["atr"], signal)

    print(f"Entrada: {price}")
    print(f"SL: {sl} | TP: {tp}")

    # Guardamos decisión (exit y pnl aún no existen)
    log_trade(
        symbol=symbol,
        side=signal,
        entry_price=price,
        exit_price=None,
        pnl=0,
        rsi=last["rsi"],
        ema50=last["ema50"],
        ema200=last["ema200"],
        atr=last["atr"],
        volume=last["volume"]
    )

    print("🧠 Trade registrado en memoria")
else:
    print("🛑 No se opera")
