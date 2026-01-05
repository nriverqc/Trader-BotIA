from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from datetime import datetime
from database.db import Base, engine

class Trade(Base):
    """
    Modelo que representa la tabla 'trades' en la base de datos.
    Esta clase define la estructura de la memoria del bot.
    """
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20))
    side = Column(String(10))
    entry_price = Column(Float)
    exit_price = Column(Float, nullable=True)
    exit_reason = Column(Text, nullable=True)  # Nueva columna: motivo de cierre
    pnl = Column(Float, default=0.0)
    rsi = Column(Float)
    ema50 = Column(Float)
    ema200 = Column(Float)
    atr = Column(Float)
    volume = Column(Float)
    stop_loss = Column(Float, nullable=True)   # Nueva columna: nivel de SL
    take_profit = Column(Float, nullable=True) # Nueva columna: nivel de TP
    trade_time = Column(DateTime, default=datetime.utcnow)

def init_db():
    """
    Crea todas las tablas definidas en los modelos si no existen.
    """
    Base.metadata.create_all(bind=engine)