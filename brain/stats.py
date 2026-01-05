from sqlalchemy import func
from database.db import get_session
from database.models import Trade

def print_summary():
    """
    Analiza la tabla de trades y genera un reporte detallado del rendimiento.
    Versión mejorada: muestra info incluso con pocos datos.
    """
    session = get_session()
    try:
        # 1. Estadísticas generales
        total_all = session.query(Trade).count()
        closed_trades = session.query(Trade).filter(Trade.exit_price != None).all()
        open_trades = session.query(Trade).filter(Trade.exit_price == None, 
                                                 Trade.side.in_(['LONG', 'SHORT'])).count()
        
        if total_all == 0:
            print("\n📊 [STATS] No hay trades registrados aún.")
            return
        
        print("\n" + "="*60)
        print(f"📈 REPORTE DE RENDIMIENTO - TRADER BOTIA")
        print("-"*60)
        print(f"🔹 Trades Totales: {total_all}")
        print(f"🔹 Trades Cerrados: {len(closed_trades)}")
        print(f"🔹 Trades Abiertos: {open_trades}")
        
        # 2. Distribución de señales
        longs = session.query(Trade).filter(Trade.side == 'LONG').count()
        shorts = session.query(Trade).filter(Trade.side == 'SHORT').count()
        no_trades = session.query(Trade).filter(Trade.side == 'NO_TRADE').count()
        
        print(f"🔹 Distribución: {longs} LONG | {shorts} SHORT | {no_trades} NO_TRADE")
        
        # 3. Solo si hay trades cerrados, mostrar análisis detallado
        if len(closed_trades) >= 3:
            winning_trades = [t for t in closed_trades if (t.pnl is not None and t.pnl > 0)]
            losing_trades = [t for t in closed_trades if (t.pnl is not None and t.pnl < 0)]
            
            win_rate = (len(winning_trades) / len(closed_trades)) * 100
            total_pnl = sum(t.pnl for t in closed_trades if t.pnl is not None)
            
            avg_win = sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0
            avg_loss = sum(t.pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0
            
            gross_profit = sum(t.pnl for t in winning_trades)
            gross_loss = abs(sum(t.pnl for t in losing_trades))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
            
            print("-"*60)
            print(f"💰 PnL Total: {total_pnl:.4f}%")
            print(f"🎯 Win Rate: {win_rate:.2f}%")
            print(f"📊 Profit Factor: {profit_factor:.2f}")
            print(f"✅ Avg Win: {avg_win:.4f}% | ❌ Avg Loss: {avg_loss:.4f}%")
            
            # Razones de cierre
            if closed_trades:
                reasons = {}
                for t in closed_trades:
                    if t.exit_reason:
                        reasons[t.exit_reason] = reasons.get(t.exit_reason, 0) + 1
                
                if reasons:
                    print(f"🔍 Cierres: {', '.join([f'{k}: {v}' for k, v in reasons.items()])}")
        else:
            print("-"*60)
            print(f"⏳ Necesarios {3 - len(closed_trades)} trades más para análisis detallado")
            
            # Mostrar últimos trades
            if closed_trades:
                print("📝 Últimos trades cerrados:")
                for t in closed_trades[-3:]:
                    pnl_str = f"+{t.pnl:.2f}%" if t.pnl > 0 else f"{t.pnl:.2f}%"
                    print(f"   #{t.id}: {t.side} | PnL: {pnl_str} | Razón: {t.exit_reason}")
        
        print("="*60 + "\n")

    except Exception as e:
        print(f"⚠️ Error en stats: {e}")
    finally:
        session.close()

def get_total_pnl():
    """
    Retorna el PnL acumulado actual.
    """
    session = get_session()
    try:
        total = session.query(func.sum(Trade.pnl)).filter(Trade.exit_price != None).scalar()
        return float(total) if total else 0.0
    except Exception:
        return 0.0
    finally:
        session.close()