import pandas as pd
from config.optimizer import optimizer

def is_liquid_hour(hour):
    """
    Determina si la hora actual (UTC) corresponde a periodos de alta liquidez.
    Usa parámetros del optimizador.
    """
    params = optimizer.get_strategy_params()
    
    if params["trade_all_hours"]:
        return True  # Modo aprendizaje: opera 24/7
    
    # Horario líquido normal: 12:00-20:00 UTC
    return 12 <= hour <= 20

def generate_signal(df):
    """
    Analiza el DataFrame con indicadores usando parámetros optimizados.
    """
    if df is None or len(df) < 2:
        return "NO_TRADE"

    last = df.iloc[-1]

    # Seguridad: Evitar procesar si hay valores nulos
    required_columns = ['ema50', 'ema200', 'rsi', 'atr', 'volume', 'vol_mean']
    if not all(col in last.index for col in required_columns):
        return "NO_TRADE"
    
    if last[required_columns].isna().any():
        return "NO_TRADE"

    # Obtener parámetros actuales
    params = optimizer.get_strategy_params()
    
    # Extracción de valores
    ema50 = last["ema50"]
    ema200 = last["ema200"]
    rsi = last["rsi"]
    atr = last["atr"]
    volume = last["volume"]
    vol_mean = last["vol_mean"]

    # 1. FILTRO DE VOLUMEN (con parámetro dinámico)
    if vol_mean <= 0 or volume <= (vol_mean * params["volume_multiplier"]):
        return "NO_TRADE"

    # 2. FILTRO DE VOLATILIDAD (ATR) - solo si tenemos datos
    if len(df) >= 30:
        atr_min = df["atr"].quantile(params["atr_min_percentile"])
        atr_max = df["atr"].quantile(params["atr_max_percentile"])
        
        if atr < atr_min or atr > atr_max:
            return "NO_TRADE"

    # 3. LÓGICA DE SEÑALES CON PARÁMETROS DINÁMICOS
    # LONG: Precio sobre EMAs y RSI > umbral_dinámico
    if ema50 > ema200 and rsi > params["rsi_long"]:
        return "LONG"

    # SHORT: Precio bajo EMAs y RSI < umbral_dinámico
    if ema50 < ema200 and rsi < params["rsi_short"]:
        return "SHORT"

    return "NO_TRADE"

def get_current_strategy_mode():
    """Devuelve el modo actual de la estrategia"""
    return optimizer.current_mode