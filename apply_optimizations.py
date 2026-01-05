#!/usr/bin/env python3
"""
Aplica las optimizaciones sugeridas por el módulo de aprendizaje.
"""

import json
import os
import sys

def apply_optimizations():
    """Aplica las optimizaciones guardadas en optimized_params.json"""
    
    if not os.path.exists('optimized_params.json'):
        print("⚠️ No hay parámetros optimizados para aplicar")
        return False
    
    try:
        with open('optimized_params.json', 'r') as f:
            optimizations = json.load(f)
        
        print("🔧 Aplicando optimizaciones...")
        
        # Aquí podrías modificar archivos de configuración
        # Por ahora, solo mostramos lo que se aplicaría
        
        if 'rsi' in optimizations:
            print(f"  • RSI LONG: {optimizations['rsi'].get('long_threshold', 'Mantener 52')}")
            print(f"  • RSI SHORT: {optimizations['rsi'].get('short_threshold', 'Mantener 48')}")
        
        if 'atr' in optimizations:
            print(f"  • TP Multiplier: {optimizations['atr'].get('tp_multiplier', 'Mantener 3.0')}")
            print(f"  • SL Multiplier: {optimizations['atr'].get('sl_multiplier', 'Mantener 1.5')}")
        
        if 'time' in optimizations:
            print(f"  • Mejor hora: {optimizations['time'].get('best_hour', 'No cambiar')}:00 UTC")
            print(f"  • Peor hora: {optimizations['time'].get('worst_hour', 'No cambiar')}:00 UTC")
        
        # Guardar historial de optimizaciones
        history_file = 'optimization_history.json'
        history = []
        
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                history = json.load(f)
        
        from datetime import datetime
        optimizations['applied_at'] = datetime.utcnow().isoformat()
        history.append(optimizations)
        
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
        
        print("✅ Optimizaciones registradas en 'optimization_history.json'")
        print("📝 Nota: Para aplicar cambios automáticamente, edita los archivos de configuración")
        
        return True
        
    except Exception as e:
        print(f"❌ Error aplicando optimizaciones: {e}")
        return False

if __name__ == "__main__":
    apply_optimizations()