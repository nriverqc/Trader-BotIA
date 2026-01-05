# brain/learning.py
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine
import matplotlib
matplotlib.use('Agg')  # Para servidores sin interfaz gráfica
import matplotlib.pyplot as plt
from database.db import get_session
from database.models import Trade
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LearningModule")

class TradingAnalyzer:
    def __init__(self):
        self.session = get_session()
        
    def get_trading_dataframe(self):
        """Obtiene todos los trades como DataFrame de pandas"""
        try:
            query = self.session.query(Trade)
            df = pd.read_sql(query.statement, query.session.bind)
            
            if df.empty:
                logger.warning("No hay datos en la base de datos")
                return None
                
            # Convertir tipos
            df['trade_time'] = pd.to_datetime(df['trade_time'])
            
            # Calcular duración de trades (si están cerrados)
            df['trade_duration'] = None
            closed_trades = df[df['exit_price'].notna()]
            if not closed_trades.empty:
                # Para análisis, asumimos 1 minuto por ciclo si no tenemos timestamp de cierre
                df.loc[df['exit_price'].notna(), 'trade_duration'] = 1
                
            return df
        except Exception as e:
            logger.error(f"Error obteniendo datos: {e}")
            return None
    
    def analyze_performance(self):
        """Analiza rendimiento general"""
        df = self.get_trading_dataframe()
        if df is None or df.empty:
            return {"error": "No hay datos para analizar"}
        
        results = {
            "summary": {},
            "patterns": {},
            "recommendations": []
        }
        
        # 1. ANÁLISIS BÁSICO
        total_trades = len(df)
        closed_trades = df[df['exit_price'].notna()]
        open_trades = df[df['exit_price'].isna()]
        
        results["summary"]["total_trades"] = total_trades
        results["summary"]["closed_trades"] = len(closed_trades)
        results["summary"]["open_trades"] = len(open_trades)
        
        # 2. WIN RATE Y PNL
        if len(closed_trades) > 0:
            winning = closed_trades[closed_trades['pnl'] > 0]
            losing = closed_trades[closed_trades['pnl'] < 0]
            neutral = closed_trades[closed_trades['pnl'] == 0]
            
            win_rate = (len(winning) / len(closed_trades)) * 100
            avg_win = winning['pnl'].mean() if len(winning) > 0 else 0
            avg_loss = losing['pnl'].mean() if len(losing) > 0 else 0
            total_pnl = closed_trades['pnl'].sum()
            
            results["summary"]["win_rate"] = round(win_rate, 2)
            results["summary"]["avg_win"] = round(avg_win, 4)
            results["summary"]["avg_loss"] = round(avg_loss, 4)
            results["summary"]["total_pnl"] = round(total_pnl, 4)
            results["summary"]["profit_factor"] = round(abs(winning['pnl'].sum() / losing['pnl'].sum()), 2) if len(losing) > 0 and losing['pnl'].sum() != 0 else 0
            
        # 3. ANÁLISIS POR CONDICIONES DE MERCADO
        if len(closed_trades) >= 5:
            # Patrones en trades perdedores
            losing_trades = closed_trades[closed_trades['pnl'] < 0]
            
            patterns = {
                "losing_trades_rsi_mean": round(losing_trades['rsi'].mean(), 1) if not losing_trades.empty else None,
                "losing_trades_atr_mean": round(losing_trades['atr'].mean(), 2) if not losing_trades.empty else None,
                "losing_trades_hour_mode": losing_trades['trade_time'].dt.hour.mode().iloc[0] if not losing_trades.empty and len(losing_trades['trade_time'].dt.hour.mode()) > 0 else None,
                "volume_too_low": len(df[(df['volume'] < df['vol_mean'] * 1.05) & (df['side'] != 'NO_TRADE')]),
                "high_volatility_losses": len(losing_trades[losing_trades['atr'] > losing_trades['atr'].quantile(0.75)]) if not losing_trades.empty else 0
            }
            
            results["patterns"] = patterns
            
            # 4. RECOMENDACIONES
            recommendations = []
            
            if patterns.get("losing_trades_rsi_mean"):
                rsi_mean = patterns["losing_trades_rsi_mean"]
                if rsi_mean > 55:
                    recommendations.append(f"Ajustar RSI LONG a >{int(rsi_mean + 2)} (actual >52)")
                elif rsi_mean < 45:
                    recommendations.append(f"Ajustar RSI SHORT a <{int(rsi_mean - 2)} (actual <48)")
            
            if patterns.get("losing_trades_hour_mode"):
                hour = patterns["losing_trades_hour_mode"]
                recommendations.append(f"Considerar desactivar trading entre {hour}:00-{(hour+1)%24}:00 UTC")
            
            if patterns.get("volume_too_low", 0) > len(closed_trades) * 0.3:
                recommendations.append("Relajar filtro de volumen: cambiar de 10% a 5% sobre promedio")
            
            if patterns.get("high_volatility_losses", 0) > len(losing_trades) * 0.5:
                recommendations.append("Reducir multiplicador ATR para SL de 1.5 a 1.2 en alta volatilidad")
            
            results["recommendations"] = recommendations
        
        # 5. EVOLUCIÓN TEMPORAL
        if len(closed_trades) >= 10:
            closed_trades_sorted = closed_trades.sort_values('trade_time')
            closed_trades_sorted['cumulative_pnl'] = closed_trades_sorted['pnl'].cumsum()
            results["summary"]["pnl_trend"] = "positivo" if closed_trades_sorted['cumulative_pnl'].iloc[-1] > 0 else "negativo"
        
        return results
    
    def generate_report(self, results, save_path="learning_report.json"):
        """Genera reporte completo y lo guarda"""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "analysis": results
        }
        
        # Guardar reporte
        with open(save_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Generar visualización si hay suficientes datos
        if results.get("summary", {}).get("closed_trades", 0) >= 5:
            self.generate_visualizations(results)
        
        return report
    
    def generate_visualizations(self, results):
        """Genera gráficos de análisis"""
        try:
            df = self.get_trading_dataframe()
            if df is None:
                return
            
            closed_trades = df[df['exit_price'].notna()]
            
            if len(closed_trades) >= 3:
                # Gráfico 1: Evolución de PnL
                plt.figure(figsize=(10, 6))
                closed_sorted = closed_trades.sort_values('trade_time')
                closed_sorted['cumulative_pnl'] = closed_sorted['pnl'].cumsum()
                
                plt.plot(closed_sorted['trade_time'], closed_sorted['cumulative_pnl'], 
                        marker='o', linewidth=2, markersize=4)
                plt.axhline(y=0, color='r', linestyle='--', alpha=0.5)
                plt.xlabel('Fecha')
                plt.ylabel('PnL Acumulado (%)')
                plt.title('Evolución del Rendimiento')
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                plt.savefig('performance_evolution.png', dpi=150)
                plt.close()
                
                # Gráfico 2: Distribución de PnL
                if len(closed_trades) >= 5:
                    plt.figure(figsize=(8, 6))
                    plt.hist(closed_trades['pnl'], bins=15, edgecolor='black', alpha=0.7)
                    plt.axvline(x=0, color='r', linestyle='--', linewidth=2)
                    plt.xlabel('PnL (%)')
                    plt.ylabel('Frecuencia')
                    plt.title('Distribución de Resultados')
                    plt.grid(True, alpha=0.3)
                    plt.tight_layout()
                    plt.savefig('pnl_distribution.png', dpi=150)
                    plt.close()
                    
                logger.info("Gráficos generados: performance_evolution.png, pnl_distribution.png")
                
        except Exception as e:
            logger.error(f"Error generando visualizaciones: {e}")
    
    def optimize_parameters(self):
        """Sugiere optimizaciones basadas en datos"""
        df = self.get_trading_dataframe()
        if df is None or len(df) < 20:
            return {"status": "insufficient_data", "message": "Se necesitan al menos 20 trades para optimización"}
        
        closed_trades = df[df['exit_price'].notna()]
        if len(closed_trades) < 10:
            return {"status": "insufficient_closed_trades", "message": "Se necesitan al menos 10 trades cerrados"}
        
        optimizations = {
            "rsi": {},
            "atr": {},
            "volume": {},
            "time": {}
        }
        
        # Optimizar RSI thresholds
        winning_long = closed_trades[(closed_trades['side'] == 'LONG') & (closed_trades['pnl'] > 0)]
        losing_long = closed_trades[(closed_trades['side'] == 'LONG') & (closed_trades['pnl'] < 0)]
        
        if len(winning_long) > 2 and len(losing_long) > 2:
            optimal_rsi_long = winning_long['rsi'].mean()
            optimizations["rsi"]["long_threshold"] = round(max(50, optimal_rsi_long), 1)
        
        winning_short = closed_trades[(closed_trades['side'] == 'SHORT') & (closed_trades['pnl'] > 0)]
        losing_short = closed_trades[(closed_trades['side'] == 'SHORT') & (closed_trades['pnl'] < 0)]
        
        if len(winning_short) > 2 and len(losing_short) > 2:
            optimal_rsi_short = winning_short['rsi'].mean()
            optimizations["rsi"]["short_threshold"] = round(min(50, optimal_rsi_short), 1)
        
        # Optimizar ATR multiplicadores
        profitable_trades = closed_trades[closed_trades['pnl'] > 0]
        if len(profitable_trades) > 5:
            avg_profit = profitable_trades['pnl'].mean()
            avg_atr_profit = profitable_trades['atr'].mean()
            
            # Calcular ratio óptimo
            if avg_atr_profit > 0:
                optimal_ratio = avg_profit / avg_atr_profit
                optimizations["atr"]["tp_multiplier"] = round(max(2.0, min(4.0, optimal_ratio * 2)), 1)
                optimizations["atr"]["sl_multiplier"] = round(max(1.0, min(2.0, optimizations["atr"]["tp_multiplier"] / 2)), 1)
        
        # Horarios óptimos
        df['hour'] = df['trade_time'].dt.hour
        hour_performance = df.groupby('hour')['pnl'].mean()
        if not hour_performance.empty:
            best_hour = hour_performance.idxmax()
            worst_hour = hour_performance.idxmin()
            optimizations["time"]["best_hour"] = int(best_hour)
            optimizations["time"]["worst_hour"] = int(worst_hour)
        
        return optimizations
    
    def close(self):
        """Cierra la sesión de base de datos"""
        if self.session:
            self.session.close()

def analyze_failure_patterns():
    """Función principal para análisis de patrones"""
    analyzer = TradingAnalyzer()
    try:
        # 1. Analizar rendimiento
        results = analyzer.analyze_performance()
        
        # 2. Optimizar parámetros
        optimizations = analyzer.optimize_parameters()
        results["optimizations"] = optimizations
        
        # 3. Generar reporte
        report = analyzer.generate_report(results)
        
        # 4. Mostrar resumen en consola
        print("\n" + "="*70)
        print("🧠 INFORME DE APRENDIZAJE - TRADER BOTIA")
        print("="*70)
        
        if "error" in results:
            print(f"⚠️ {results['error']}")
        else:
            summary = results.get("summary", {})
            print(f"📊 Estadísticas:")
            print(f"   • Trades totales: {summary.get('total_trades', 0)}")
            print(f"   • Trades cerrados: {summary.get('closed_trades', 0)}")
            
            if summary.get('closed_trades', 0) > 0:
                print(f"   • Win Rate: {summary.get('win_rate', 0):.1f}%")
                print(f"   • PnL Total: {summary.get('total_pnl', 0):.4f}%")
                print(f"   • Profit Factor: {summary.get('profit_factor', 0):.2f}")
            
            patterns = results.get("patterns", {})
            if patterns:
                print(f"\n🔍 Patrones identificados:")
                if patterns.get("losing_trades_rsi_mean"):
                    print(f"   • RSI promedio en pérdidas: {patterns['losing_trades_rsi_mean']}")
                if patterns.get("losing_trades_hour_mode") is not None:
                    print(f"   • Hora problemática: {patterns['losing_trades_hour_mode']}:00 UTC")
            
            recommendations = results.get("recommendations", [])
            if recommendations:
                print(f"\n💡 Recomendaciones:")
                for i, rec in enumerate(recommendations, 1):
                    print(f"   {i}. {rec}")
            else:
                print(f"\n💡 No hay recomendaciones aún (pocos datos)")
            
            if optimizations.get("status") != "insufficient_data":
                print(f"\n⚙️ Optimizaciones sugeridas:")
                if optimizations.get("rsi"):
                    if "long_threshold" in optimizations["rsi"]:
                        print(f"   • RSI LONG: {optimizations['rsi']['long_threshold']} (actual: 52)")
                    if "short_threshold" in optimizations["rsi"]:
                        print(f"   • RSI SHORT: {optimizations['rsi']['short_threshold']} (actual: 48)")
                if optimizations.get("atr"):
                    print(f"   • TP Multiplier: {optimizations['atr'].get('tp_multiplier', 3.0)} (actual: 3.0)")
                    print(f"   • SL Multiplier: {optimizations['atr'].get('sl_multiplier', 1.5)} (actual: 1.5)")
        
        print("="*70 + "\n")
        
        # 5. Guardar configuraciones optimizadas
        if optimizations and "status" not in optimizations:
            with open('optimized_params.json', 'w') as f:
                json.dump(optimizations, f, indent=2)
            print("✅ Parámetros optimizados guardados en 'optimized_params.json'")
        
        return report
        
    finally:
        analyzer.close()