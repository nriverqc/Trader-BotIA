#!/usr/bin/env python3
"""
Programa el análisis automático cada X horas.
"""

import schedule
import time
import subprocess
from datetime import datetime

def run_analysis():
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Ejecutando análisis programado...")
    subprocess.run([sys.executable, "analyze_learning.py", "--stats"])
    print("Análisis completado.")

if __name__ == "__main__":
    print("⏰ Programando análisis cada 6 horas...")
    
    # Ejecutar ahora
    run_analysis()
    
    # Programar cada 6 horas
    schedule.every(6).hours.do(run_analysis)
    
    # Mantener el programa corriendo
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Revisar cada minuto
    except KeyboardInterrupt:
        print("\n🛑 Análisis programado detenido.")