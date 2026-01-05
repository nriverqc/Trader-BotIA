from database.db import get_session
from database.models import Trade
import numpy as np
import logging

# Parámetros de gestión de riesgo (deben coincidir con runner.py)
ATR_MULTIPLIER_SL = 1.5
ATR_MULTIPLIER_TP = 3.0

# Configuración básica de logs para el bot
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BrainMemory")

def _to_float(value):
    """
    Convierte valores de tipos numéricos (incluyendo numpy.float64 de pandas) 
    a float nativo de Python para total compatibilidad con SQLAlchemy y PostgreSQL.
    """
    if value is None:
        return None
    
    # Manejo de valores NaN (Not a Number) de Pandas/Numpy
    if isinstance(value, float) and np.isnan(value):
        return None
        
    try:
        # Conversión explícita de tipos numpy (usando .item()) y otros formatos numéricos
        if hasattr(value, 'item'): 
            return float(value.item())
        return float(value)
    except (TypeError, ValueError):
        return None

def _calculate_sl_tp(side, entry_price, atr):
    """
    Calcula Stop Loss y Take Profit basados en ATR.
    """
    if atr is None or atr <= 0:
        return None, None
    
    if side == 'LONG':
        stop_loss = entry_price - (atr * ATR_MULTIPLIER_SL)
        take_profit = entry_price + (atr * ATR_MULTIPLIER_TP)
    elif side == 'SHORT':
        stop_loss = entry_price + (atr * ATR_MULTIPLIER_SL)
        take_profit = entry_price - (atr * ATR_MULTIPLIER_TP)
    else:
        return None, None
    
    return stop_loss, take_profit

def log_trade(
    symbol,
    side,
    entry_price,
    exit_price,
    pnl,
    rsi,
    ema50,
    ema200,
    atr,
    volume,
    exit_reason=None,
    stop_loss=None,
    take_profit=None,
):
    """
    Guarda una decisión del bot o un registro de trade en la base de datos.
    Asegura que la sesión se cierre correctamente en cualquier escenario.
    """
    session = get_session()
    try:
        # Si no se proporcionan SL/TP y es una entrada nueva (exit_price=None), los calculamos
        if exit_price is None and side in ['LONG', 'SHORT']:
            calc_sl, calc_tp = _calculate_sl_tp(side, entry_price, atr)
            stop_loss = stop_loss or calc_sl
            take_profit = take_profit or calc_tp

        # Creamos la instancia del modelo Trade con los datos limpios y convertidos
        trade = Trade(
            symbol=str(symbol),
            side=str(side),
            entry_price=_to_float(entry_price),
            exit_price=_to_float(exit_price),
            exit_reason=exit_reason,
            pnl=_to_float(pnl),
            rsi=_to_float(rsi),
            ema50=_to_float(ema50),
            ema200=_to_float(ema200),
            atr=_to_float(atr),
            volume=_to_float(volume),
            stop_loss=_to_float(stop_loss),
            take_profit=_to_float(take_profit),
        )

        # Agregamos la instancia a la sesión y confirmamos
        session.add(trade)
        session.commit()
        logger.info(f"💾 Registro guardado con éxito: {symbol} - {side}")
        if stop_loss and take_profit:
            logger.info(f"   SL: {stop_loss:.2f}, TP: {take_profit:.2f}")
        
    except Exception as e:
        # En caso de error, revertimos la transacción
        session.rollback()
        logger.error(f"❌ Error crítico al guardar en la base de datos: {e}")
    finally:
        # Cerramos la sesión SIEMPRE para liberar recursos
        session.close()