#!/usr/bin/env python3
"""
Script principal de análisis de aprendizaje para Trader BotIA.
Ejecutar periódicamente para analizar rendimiento y sugerir mejoras.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from brain.learning import analyze_failure_patterns
from brain.stats import print_summary
import argparse

def main():
    parser = argparse.ArgumentParser(description='Analiza el aprendizaje del Trader BotIA')
    parser.add_argument('--full', action='store_true', help='Ejecutar análisis completo con visualizaciones')
    parser.add_argument('--optimize', action='store_true', help='Solo optimizar parámetros')
    parser.add_argument('--stats', action='store_true', help='Solo mostrar estadísticas')
    
    args = parser.parse_args()
    
    print("🚀 Iniciando análisis de aprendizaje...")
    
    if args.stats:
        # Solo mostrar estadísticas rápidas
        print_summary()
    elif args.optimize:
        # Solo optimización
        from brain.learning import TradingAnalyzer
        analyzer = TradingAnalyzer()
        try:
            optimizations = analyzer.optimize_parameters()
            print("\n⚙️ Optimizaciones sugeridas:")
            print(optimizations)
        finally:
            analyzer.close()
    else:
        # Análisis completo
        if args.full:
            print("🔍 Ejecutando análisis completo...")
        
        # 1. Mostrar estadísticas actuales
        print_summary()
        
        # 2. Ejecutar análisis de aprendizaje
        report = analyze_failure_patterns()
        
        # 3. Verificar si hay archivos generados
        if os.path.exists('learning_report.json'):
            print("📄 Reporte guardado en 'learning_report.json'")
        if os.path.exists('optimized_params.json'):
            print("⚙️ Parámetros optimizados en 'optimized_params.json'")
        if os.path.exists('performance_evolution.png'):
            print("📈 Gráficos generados: performance_evolution.png, pnl_distribution.png")
        
        return report

if __name__ == "__main__":
    main()