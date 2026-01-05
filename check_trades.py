# check_trades.py
from database.db import get_session
from database.models import Trade

session = get_session()
trades = session.query(Trade).order_by(Trade.id.desc()).limit(20).all()

print(f"Total trades en BD: {session.query(Trade).count()}")
print("\nÚltimos 10 trades:")
print("ID | Lado | Entrada | Salida | PnL% | Razón")
print("-" * 60)

for t in trades:
    exit_price = f"{t.exit_price:.2f}" if t.exit_price else "PENDIENTE"
    pnl_str = f"{t.pnl:.2f}%" if t.exit_price else "0.00%"
    print(f"{t.id:3} | {t.side:5} | {t.entry_price:8.2f} | {exit_price:8} | {pnl_str:6} | {t.exit_reason or ''}")

session.close()