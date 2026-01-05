import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime

# Añadir el directorio raíz al PYTHONPATH para evitar errores de importación de módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from exchange.bingx_client import fetch_ohlcv
from strategy.indicators import calculate_indicators
from strategy.daytrading import generate_signal

def run_backtest(symbol="BTC/USDT:USDT", timeframe="5m", limit=1440, atr_mult=2.5, risk_reward=1.5, trailing=True, use_be=True):
    """
    Simula la estrategia con Gestión de Riesgo Avanzada: Trailing Stop, Break Even y Filtro de Tendencia.
    """
    ohlcv = fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)
    if not ohlcv:
        return None

    df = calculate_indicators(ohlcv)
    
    # Añadimos ADX manualmente para el filtro de fuerza de tendencia
    # (En una versión real esto iría en indicators.py)
    plus_dm = df['high'].diff()
    minus_dm = df['low'].diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm > 0] = 0
    minus_dm = abs(minus_dm)
    
    tr = pd.concat([df['high'] - df['low'], 
                    abs(df['high'] - df['close'].shift()), 
                    abs(df['low'] - df['close'].shift())], axis=1).max(axis=1)
    
    atr_14 = tr.rolling(14).mean()
    plus_di = 100 * (plus_dm.rolling(14).mean() / atr_14)
    minus_di = 100 * (minus_dm.rolling(14).mean() / atr_14)
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    df['adx'] = dx.rolling(14).mean()

    pnl_acumulado = 0.0
    total_trades = 0
    ganadores = 0
    perdedores = 0
    max_drawdown = 0.0
    pnl_maximo = 0.0
    
    history = []

    i = 200
    while i < len(df) - 1:
        current_row = df.iloc[i]
        signal = generate_signal(df.iloc[:i+1])
        
        # Filtro de Tendencia EMA 200 + Filtro de Fuerza ADX
        trend_signal = "NO_TRADE"
        adx_minimo = 20 # Solo operamos si hay algo de tendencia
        
        if current_row.get('adx', 0) > adx_minimo:
            if signal == 'LONG' and current_row['close'] > current_row['ema200']:
                trend_signal = 'LONG'
            elif signal == 'SHORT' and current_row['close'] < current_row['ema200']:
                trend_signal = 'SHORT'
        
        if trend_signal in ['LONG', 'SHORT']:
            total_trades += 1
            entry_price = current_row['close']
            atr = current_row['atr']
            
            sl_dist = atr * atr_mult
            tp_dist = sl_dist * risk_reward
            be_trigger = tp_dist * 0.5 # Activar Break Even al 50% del camino al TP
            
            # Inicializar niveles
            if trend_signal == 'LONG':
                stop_loss = entry_price - sl_dist
                take_profit = entry_price + tp_dist
            else:
                stop_loss = entry_price + sl_dist
                take_profit = entry_price - tp_dist
            
            trade_closed = False
            be_activated = False
            
            for j in range(i + 1, len(df)):
                future_row = df.iloc[j]
                
                # --- Lógica de Break Even ---
                if use_be and not be_activated:
                    if trend_signal == 'LONG' and (future_row['high'] - entry_price) >= be_trigger:
                        stop_loss = entry_price # Mover SL a precio de entrada
                        be_activated = True
                    elif trend_signal == 'SHORT' and (entry_price - future_row['low']) >= be_trigger:
                        stop_loss = entry_price
                        be_activated = True

                # --- Lógica de Trailing Stop ---
                if trailing and not be_activated: # Priorizamos BE sobre Trailing inicial
                    if trend_signal == 'LONG':
                        new_sl = future_row['close'] - sl_dist
                        if new_sl > stop_loss: stop_loss = new_sl
                    else:
                        new_sl = future_row['close'] + sl_dist
                        if new_sl < stop_loss: stop_loss = new_sl

                # Verificación de Salida
                if trend_signal == 'LONG':
                    if future_row['low'] <= stop_loss:
                        trade_pnl = ((stop_loss - entry_price) / entry_price) * 100
                        trade_closed = True
                    elif future_row['high'] >= take_profit:
                        trade_pnl = ((take_profit - entry_price) / entry_price) * 100
                        trade_closed = True
                else: # SHORT
                    if future_row['high'] >= stop_loss:
                        trade_pnl = ((entry_price - stop_loss) / entry_price) * 100
                        trade_closed = True
                    elif future_row['low'] <= take_profit:
                        trade_pnl = ((entry_price - take_profit) / entry_price) * 100
                        trade_closed = True
                
                if trade_closed:
                    trade_pnl -= 0.04 # Comisiones
                    pnl_acumulado += trade_pnl
                    if trade_pnl > 0: ganadores += 1
                    else: perdedores += 1
                    
                    history.append({
                        'fecha': datetime.fromtimestamp(current_row['timestamp']/1000),
                        'pnl': trade_pnl,
                        'balance': pnl_acumulado,
                        'be': be_activated
                    })
                    i = j
                    break
            
            if not trade_closed: i = len(df)
        else:
            i += 1
            
        if pnl_acumulado > pnl_maximo: pnl_maximo = pnl_acumulado
        drawdown = pnl_maximo - pnl_acumulado
        if drawdown > max_drawdown: max_drawdown = drawdown

    win_rate = (ganadores / total_trades * 100) if total_trades > 0 else 0
    return {
        "pnl": pnl_acumulado,
        "win_rate": win_rate,
        "trades": total_trades,
        "dd": max_drawdown,
        "history": history
    }

def optimize():
    """
    Prueba diferentes configuraciones incluyendo filtros de ADX y Break Even.
    """
    print("🚀 Iniciando Motor de Optimización Pro...")
    results = []
    
    # Rango de parámetros refinados tras el último test
    for mult in [2.0, 2.5, 3.0]:
        for rr in [1.2, 1.5, 2.0]:
            res = run_backtest(atr_mult=mult, risk_reward=rr, limit=1440)
            if res:
                results.append({
                    "ATR_Mult": mult,
                    "RR": rr,
                    "PnL": res['pnl'],
                    "WinRate": res['win_rate'],
                    "Trades": res['trades']
                })
    
    df_res = pd.DataFrame(results)
    df_res = df_res.sort_values(by="PnL", ascending=False)
    
    print("\nRanking de Configuraciones (Top 5 con ADX + BreakEven):")
    print(df_res.head(5).to_string(index=False))
    
    if not df_res.empty:
        best = df_res.iloc[0]
        print(f"\n✅ Detalle Mejor Config: ATR x{best['ATR_Mult']} | RR 1:{best['RR']}")
        final = run_backtest(atr_mult=best['ATR_Mult'], risk_reward=best['RR'])
        
        print("\n" + "="*45)
        print("📊 REPORTE ESTRATEGIA REFINADA")
        print("="*45)
        print(f"Win Rate:               {final['win_rate']:.2f}%")
        print(f"PnL Acumulado Total:    {final['pnl']:.4f}%")
        print(f"Máximo Drawdown:        {final['dd']:.4f}%")
        print(f"Total Operaciones:      {final['trades']}")
        print("="*45)

if __name__ == "__main__":
    optimize()