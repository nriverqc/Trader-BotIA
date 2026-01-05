import pandas as pd
import numpy as np


def calculate_indicators(ohlcv):
    """
    Recibe velas OHLCV y devuelve un DataFrame con indicadores
    """
    df = pd.DataFrame(
        ohlcv,
        columns=["timestamp", "open", "high", "low", "close", "volume"]
    )

    # EMA
    df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()
    df["ema200"] = df["close"].ewm(span=200, adjust=False).mean()

    # RSI
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss
    df["rsi"] = 100 - (100 / (1 + rs))

    # ATR
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()

    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["atr"] = tr.rolling(14).mean()

    # Volumen medio - con relleno hacia adelante para evitar NaN
    df["vol_mean"] = df["volume"].rolling(20, min_periods=1).mean()
    
    # Rellenar valores NaN restantes (primera fila de cada columna)
    df = df.bfill().ffill()  # CORRECCIÓN AQUÍ
    
    return df