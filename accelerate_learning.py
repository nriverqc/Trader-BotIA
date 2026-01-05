#!/usr/bin/env python3
"""
Script para acelerar el aprendizaje del bot ajustando parámetros agresivamente.
"""

import json
import time
from datetime import datetime

def create_aggressive_params():
    """Crea parámetros ultra-relajados para generar muchas señales rápidamente"""
    
    aggressive_params = {
        "rsi_long_threshold": 45,      # Muy bajo para captar más LONG
        "rsi_short_threshold": 55,     # Muy alto para captar más SHORT
        "volume_multiplier": 1.001,    # Casi cualquier volumen sirve
        "atr_min_percentile": 0.01,    # Casi todo rango de ATR aceptable
        "atr_max_percentile": 0.99,
        "trade_all_hours": True,
        "min_trades_for_analysis": 10,
        "mode": "aggressive_learning",
        "activated_at": datetime.utcnow().isoformat(),
        "duration_hours": 24  # Usar por 24 horas máximo
    }
    
    with open('strategy_params.json', 'w') as f:
        json.dump(aggressive_params, f, indent=2)
    
    print("⚡ PARÁMETROS AGRESIVOS ACTIVADOS")
    print("=================================")
    print("Objetivo: Generar 50+ trades en 24 horas")
    print("Parámetros:")
    print(f"  • RSI LONG > {aggressive_params['rsi_long_threshold']}")
    print(f"  • RSI SHORT < {aggressive_params['rsi_short_threshold']}")
    print(f"  • Volumen mínimo: x{aggressive_params['volume_multiplier']}")
    print(f"  • Opera 24/7")
    print("\n⚠️ ADVERTENCIA: Esta configuración generará muchas señales,")
    print("   algunas pueden ser de baja calidad. Solo para aprendizaje.")
    print("=================================\n")
    
    return aggressive_params

if __name__ == "__main__":
    print("🚀 ACELERADOR DE APRENDIZAJE - TRADER BOTIA")
    print("="*50)
    
    response = input("¿Activar modo aprendizaje acelerado por 24 horas? (s/n): ")
    
    if response.lower() in ['s', 'si', 'y', 'yes']:
        params = create_aggressive_params()
        print("✅ Parámetros aplicados. Reinicia el bot para que surtan efecto.")
        print("\n📋 Comando para reiniciar:")
        print("   1. Detén el bot (Ctrl+C)")
        print("   2. Ejecuta: python -m bot.runner")
        print(f"\n⏰ Este modo se desactivará automáticamente en {params['duration_hours']} horas.")
    else:
        print("❌ Operación cancelada.")