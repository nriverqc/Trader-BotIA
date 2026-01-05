# update_database.py
from database.db import engine
from sqlalchemy import text

def update_trades_table():
    conn = engine.connect()
    trans = conn.begin()
    try:
        # Agregar columnas si no existen
        conn.execute(text("""
            ALTER TABLE trades 
            ADD COLUMN IF NOT EXISTS exit_reason TEXT,
            ADD COLUMN IF NOT EXISTS stop_loss DOUBLE PRECISION,
            ADD COLUMN IF NOT EXISTS take_profit DOUBLE PRECISION;
        """))
        trans.commit()
        print("✅ Tabla 'trades' actualizada con éxito.")
    except Exception as e:
        trans.rollback()
        print(f"❌ Error al actualizar la tabla: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    update_trades_table()