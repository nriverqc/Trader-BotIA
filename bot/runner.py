from config.optimizer import optimizer
from datetime import datetime
import time
import pandas as pd

from exchange.bingx_client import fetch_ohlcv
from strategy.indicators import calculate_indicators
from strategy.daytrading import generate_signal, is_liquid_hour
from brain.memory import log_trade, get_session
from brain.stats import print_summary
from database.models import Trade, init_db

# Configuración global
SYMBOL = "BTC/USDT:USDT"
INTERVALO_SEGUNDOS = 60  # Frecuencia de análisis (1 minuto)

# Parámetros de Gestión de Riesgo (Fase 1 del Roadmap)
ATR_MULTIPLIER_SL = 1.5  # Stop Loss a 1.5 veces el ATR
ATR_MULTIPLIER_TP = 3.0  # Take Profit a 3 veces el ATR (Ratio 1:2)

def close_pending_trades(current_price, current_signal):
    """
    Busca trades abiertos y evalúa si deben cerrarse por:
    1. Alcance de niveles de Stop Loss o Take Profit (Gestión de Riesgo).
    2. Cambio de señal (si la señal actual es diferente a la del trade abierto).
    """
    session = get_session()
    try:
        # Buscamos trades LONG o SHORT que aún no tienen precio de salida registrado
        pending_trades = session.query(Trade).filter(
            Trade.side.in_(['LONG', 'SHORT']),
            Trade.exit_price == None
        ).all()

        if not pending_trades:
            return

        for trade in pending_trades:
            should_close = False
            reason = ""

            # 1. Cierre por cambio de señal (si la señal actual es opuesta o NO_TRADE)
            if current_signal != trade.side:
                should_close = True
                reason = "CAMBIO DE SEÑAL"

            # 2. Cierre por gestión de riesgo (SL/TP) solo si no se cerró por cambio de señal
            if not should_close and trade.atr:
                current_atr = trade.atr
                if trade.side == 'LONG':
                    sl_level = trade.entry_price - (current_atr * ATR_MULTIPLIER_SL)
                    tp_level = trade.entry_price + (current_atr * ATR_MULTIPLIER_TP)
                    if current_price <= sl_level:
                        should_close = True
                        reason = "STOP LOSS (ATR)"
                    elif current_price >= tp_level:
                        should_close = True
                        reason = "TAKE PROFIT (ATR)"
                
                elif trade.side == 'SHORT':
                    sl_level = trade.entry_price + (current_atr * ATR_MULTIPLIER_SL)
                    tp_level = trade.entry_price - (current_atr * ATR_MULTIPLIER_TP)
                    if current_price >= sl_level:
                        should_close = True
                        reason = "STOP LOSS (ATR)"
                    elif current_price <= tp_level:
                        should_close = True
                        reason = "TAKE PROFIT (ATR)"

            # Si se debe cerrar, actualizamos la base de datos
            if should_close:
                trade.exit_price = float(current_price)
                trade.exit_reason = reason
                
                # Cálculo de PnL Porcentual
                if trade.side == 'LONG':
                    trade.pnl = ((trade.exit_price - trade.entry_price) / trade.entry_price) * 100
                elif trade.side == 'SHORT':
                    trade.pnl = ((trade.entry_price - trade.exit_price) / trade.entry_price) * 100
                
                print(f"✅ Trade {trade.id} cerrado ({reason}). PnL: {trade.pnl:.4f}%")

        session.commit()
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error al procesar cierres: {e}")
    finally:
        session.close()

def run_bot_cycle():
    """
    Ciclo operativo: Datos -> Cierre -> Análisis -> Registro
    """
    now = datetime.utcnow()
    
    try:
        # 1. Obtención de datos reales de BingX
        ohlcv = fetch_ohlcv(symbol=SYMBOL, timeframe="1m", limit=100, use_sandbox=False)
        if not ohlcv:
            print("⚠️ Datos no disponibles.")
            return
        
        df = calculate_indicators(ohlcv)
        last = df.iloc[-1]
        current_price = last["close"]
    except Exception as e:
        print(f"⚠️ Error de red/indicadores: {e}")
        return

    # 2. Análisis de estrategia actual
    signal = generate_signal(df)
    mode = "ACTIVO" if is_liquid_hour(now.hour) else "MONITOREO"
    
    print(
        f"[{now.strftime('%H:%M:%S')}] BTC: {current_price:.2f} | "
        f"Señal: {signal} | Modo: {mode} | ATR: {last['atr']:.2f}"
    )

    # 3. Gestión de salidas del ciclo previo (SL/TP o cambio de señal)
    close_pending_trades(current_price, signal)

    # 4. Solo abrimos nuevo trade si no hay uno abierto del mismo lado
    if signal in ['LONG', 'SHORT']:
        session = get_session()
        try:
            open_trade = session.query(Trade).filter(
                Trade.side == signal,
                Trade.exit_price == None
            ).first()
            
            if not open_trade:
                # Calculamos SL y TP basados en ATR
                atr_value = last['atr']
                if signal == 'LONG':
                    stop_loss = current_price - (atr_value * ATR_MULTIPLIER_SL)
                    take_profit = current_price + (atr_value * ATR_MULTIPLIER_TP)
                else:  # SHORT
                    stop_loss = current_price + (atr_value * ATR_MULTIPLIER_SL)
                    take_profit = current_price - (atr_value * ATR_MULTIPLIER_TP)
                
                log_trade(
                    symbol=SYMBOL,
                    side=signal,
                    entry_price=current_price,
                    exit_price=None,
                    pnl=0.0,
                    rsi=last["rsi"],
                    ema50=last["ema50"],
                    ema200=last["ema200"],
                    atr=atr_value,
                    volume=last["volume"],
                    exit_reason=None,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                )
                print(f"📈 Nueva entrada: {signal} a {current_price:.2f}")
                print(f"   SL: {stop_loss:.2f}, TP: {take_profit:.2f}")
        except Exception as e:
            print(f"⚠️ Error al verificar trades abiertos: {e}")
        finally:
            session.close()

def main():
    print("==================================================")
    print("🤖 TRADER BOTIA - MODO APRENDIZAJE ACTIVADO")
    print("==================================================")
    
    # Mostrar parámetros actuales
    params = optimizer.get_strategy_params()
    print(f"🔧 Modo: {params['mode']}")
    print(f"📊 Parámetros: RSI LONG>{params['rsi_long']}, SHORT<{params['rsi_short']}")
    print(f"   Volumen: x{params['volume_multiplier']}, ATR: {params['atr_min_percentile']}-{params['atr_max_percentile']}")
    print("="*50 + "\n")
    
    try:
        init_db()
        print("✅ Base de datos conectada.")
    except Exception as e:
        print(f"❌ Error DB: {e}")
        return

    # Contador de ciclos para optimización periódica
    cycle_count = 0
    
    try:
        while True:
            run_bot_cycle()
            
            # Cada 60 ciclos (1 hora), ejecutar análisis y optimización
            cycle_count += 1
            if cycle_count % 60 == 0:
                print("\n🔄 Ejecutando análisis de optimización...")
                try:
                    from brain.learning import TradingAnalyzer
                    analyzer = TradingAnalyzer()
                    results = analyzer.analyze_performance()
                    analyzer.close()
                    
                    if "summary" in results:
                        total = results["summary"].get("closed_trades", 0)
                        win_rate = results["summary"].get("win_rate", 0)
                        total_pnl = results["summary"].get("total_pnl", 0)
                        
                        if total > 0:
                            avg_pnl = total_pnl / total
                            optimizer.analyze_and_optimize(total, win_rate, avg_pnl)
                except Exception as e:
                    print(f"⚠️ Error en optimización: {e}")
            
            print_summary()
            time.sleep(INTERVALO_SEGUNDOS)
            
    except KeyboardInterrupt:
        print("\n🛑 Apagado por el usuario.")
    except Exception as e:
        print(f"💥 Error crítico: {e}")

if __name__ == "__main__":
    main()