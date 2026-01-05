# database/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Configuración flexible para diferentes entornos
def get_database_url():
    """Obtiene la URL de conexión a la base de datos según el entorno"""
    
    # Para GitHub Actions (con PostgreSQL en services)
    if os.getenv('GITHUB_ACTIONS') == 'true':
        return "postgresql://traderbot:bot123456@localhost:5432/traderdb"
    
    # Para desarrollo local (desde settings.py o secrets.env)
    try:
        from config.settings import DB_CONFIG
        return f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    except:
        # Fallback a SQLite para pruebas rápidas
        return "sqlite:///traderbot.db"

# Crear engine de SQLAlchemy
DATABASE_URL = get_database_url()
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

# Crear session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos
Base = declarative_base()

def get_session():
    """Obtiene una nueva sesión de base de datos"""
    session = SessionLocal()
    try:
        return session
    except Exception as e:
        session.close()
        raise e