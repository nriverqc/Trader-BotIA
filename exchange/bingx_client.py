import ccxt

def get_bingx(use_sandbox=False):
    """
    Crea y configura la conexión con BingX.
    
    Args:
        use_sandbox (bool): Si True, usa modo sandbox (para pruebas con cuenta demo).
                            Si False, usa mercado real (para datos reales y trading real).
    """
    exchange = ccxt.bingx({
        "enableRateLimit": True,
        "options": {
            "defaultType": "swap",   # FUTUROS
        }
    })

    # IMPORTANTE: Solo activar sandbox para pruebas con cuenta demo
    # Para recolección de datos, necesitamos el mercado REAL
    if use_sandbox:
        exchange.set_sandbox_mode(True)
        print("⚠️ MODO SANDBOX ACTIVADO (datos de prueba)")

    # cargar mercados (MUY IMPORTANTE en BingX)
    exchange.load_markets()

    return exchange


def fetch_ohlcv(symbol="BTC/USDT:USDT", timeframe="5m", limit=200, use_sandbox=False):
    """
    Obtiene velas OHLCV de BingX.
    
    Args:
        use_sandbox (bool): False para datos reales, True para sandbox
    """
    exchange = get_bingx(use_sandbox)
    
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        
        # Verificar que obtenemos datos reales
        if ohlcv and len(ohlcv) > 0:
            last_candle = ohlcv[-1]
            print(f"📊 Datos: {len(ohlcv)} velas | Última: {last_candle[4]:.2f} USD")
        
        return ohlcv
        
    except Exception as e:
        print(f"❌ Error obteniendo datos: {e}")
        return None