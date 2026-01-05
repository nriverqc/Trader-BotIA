# config/optimizer.py
import json
import os

class StrategyOptimizer:
    def __init__(self):
        self.params_file = 'strategy_params.json'
        self.default_params = {
            # RELAJADO para aprendizaje (generar más señales)
            "learning_mode": {
                "rsi_long_threshold": 50,      # Original: 52
                "rsi_short_threshold": 50,     # Original: 48
                "volume_multiplier": 1.01,     # Original: 1.1 (solo 1% más)
                "atr_min_percentile": 0.05,    # Original: 0.15 (más relajado)
                "atr_max_percentile": 0.95,    # Original: 0.85 (más relajado)
                "trade_all_hours": True,       # Operar 24/7 para recolectar datos
                "min_trades_for_analysis": 20  # Cuántos trades necesitamos antes de ajustar
            },
            # MODERADO (después de aprendizaje inicial)
            "moderate_mode": {
                "rsi_long_threshold": 51,
                "rsi_short_threshold": 49,
                "volume_multiplier": 1.05,
                "atr_min_percentile": 0.10,
                "atr_max_percentile": 0.90,
                "trade_all_hours": False,
                "min_trades_for_analysis": 50
            },
            # CONSERVADOR (para trading real)
            "conservative_mode": {
                "rsi_long_threshold": 52,
                "rsi_short_threshold": 48,
                "volume_multiplier": 1.10,
                "atr_min_percentile": 0.15,
                "atr_max_percentile": 0.85,
                "trade_all_hours": False,
                "min_trades_for_analysis": 100
            }
        }
        
        # Cargar o crear parámetros
        self.current_mode = "learning_mode"
        self.current_params = self.load_params()
    
    def load_params(self):
        """Carga parámetros desde archivo o usa defaults"""
        if os.path.exists(self.params_file):
            with open(self.params_file, 'r') as f:
                return json.load(f)
        else:
            # Usar modo aprendizaje por defecto
            params = self.default_params["learning_mode"].copy()
            params["mode"] = "learning_mode"
            self.save_params(params)
            return params
    
    def save_params(self, params):
        """Guarda parámetros en archivo"""
        with open(self.params_file, 'w') as f:
            json.dump(params, f, indent=2)
    
    def get_param(self, key):
        """Obtiene un parámetro específico"""
        return self.current_params.get(key, self.default_params[self.current_mode].get(key))
    
    def analyze_and_optimize(self, total_trades, win_rate, avg_pnl):
        """
        Analiza rendimiento y ajusta modo automáticamente
        """
        if total_trades < self.get_param("min_trades_for_analysis"):
            return False  # No ajustar aún
        
        # Lógica de transición entre modos
        if self.current_mode == "learning_mode" and total_trades >= 30:
            if win_rate > 55 and avg_pnl > 0:
                self.current_mode = "moderate_mode"
            else:
                # Mantener en learning pero ajustar parámetros
                self.adjust_learning_params(win_rate, avg_pnl)
        
        elif self.current_mode == "moderate_mode" and total_trades >= 100:
            if win_rate > 60 and avg_pnl > 0.5:
                self.current_mode = "conservative_mode"
        
        # Actualizar parámetros actuales
        self.current_params = self.default_params[self.current_mode].copy()
        self.current_params["mode"] = self.current_mode
        self.save_params(self.current_params)
        
        print(f"🔄 Cambiado a modo: {self.current_mode}")
        return True
    
    def adjust_learning_params(self, win_rate, avg_pnl):
        """Ajusta parámetros específicos basado en rendimiento"""
        params = self.current_params.copy()
        
        if win_rate < 40:
            # Si win rate bajo, hacer más conservador
            params["rsi_long_threshold"] = max(51, params.get("rsi_long_threshold", 50))
            params["rsi_short_threshold"] = min(49, params.get("rsi_short_threshold", 50))
        elif win_rate > 70:
            # Si win rate alto, podemos ser más agresivos
            params["rsi_long_threshold"] = min(49, params.get("rsi_long_threshold", 50))
            params["rsi_short_threshold"] = max(51, params.get("rsi_short_threshold", 50))
        
        if avg_pnl < -0.1:
            # Si pérdidas grandes, reducir riesgo
            params["volume_multiplier"] = min(1.15, params.get("volume_multiplier", 1.1) + 0.05)
        
        self.current_params = params
        self.save_params(params)
        print(f"📊 Parámetros ajustados: Win Rate={win_rate}%, PnL={avg_pnl}%")
    
    def get_strategy_params(self):
        """Devuelve todos los parámetros para la estrategia"""
        return {
            "rsi_long": self.get_param("rsi_long_threshold"),
            "rsi_short": self.get_param("rsi_short_threshold"),
            "volume_multiplier": self.get_param("volume_multiplier"),
            "atr_min_percentile": self.get_param("atr_min_percentile"),
            "atr_max_percentile": self.get_param("atr_max_percentile"),
            "trade_all_hours": self.get_param("trade_all_hours"),
            "mode": self.current_mode
        }

# Instancia global
optimizer = StrategyOptimizer()