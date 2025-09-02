#!/usr/bin/env python3
"""
Évaluation de stratégies de trading options
Comparaison: Bull Call Spread vs Long Straddle
Critère principal: Risk/Reward Ratio
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import List, Dict, Tuple
import math

@dataclass
class OptionLeg:
    """Représente une jambe d'option"""
    option_type: str  # 'call' ou 'put'
    strike: float
    expiry_days: int
    action: str       # 'buy' ou 'sell'
    quantity: int = 1
    price: float = 0.0

@dataclass
class StrategyMetrics:
    """Métriques d'évaluation d'une stratégie"""
    name: str
    cost: float
    payoff_at_target: float
    max_gain: float
    max_loss: float
    risk_reward_ratio: float
    breakeven_points: List[float]
    breakeven_probability: float
    
class OptionPricer:
    """Pricing d'options simplifié (Black-Scholes)"""
    
    @staticmethod
    def black_scholes_call(S, K, T, r, sigma):
        """Prix d'un call Black-Scholes"""
        if T <= 0:
            return max(S - K, 0)
        
        d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
        d2 = d1 - sigma*np.sqrt(T)
        
        from scipy.stats import norm
        call_price = S*norm.cdf(d1) - K*np.exp(-r*T)*norm.cdf(d2)
        return max(call_price, 0)
    
    @staticmethod
    def black_scholes_put(S, K, T, r, sigma):
        """Prix d'un put Black-Scholes"""
        call_price = OptionPricer.black_scholes_call(S, K, T, r, sigma)
        put_price = call_price - S + K*np.exp(-r*T)
        return max(put_price, 0)

class StrategyEvaluator:
    """Évaluateur de stratégies d'options"""
    
    def __init__(self, current_price=97.00, target_price=97.12, 
                 risk_free_rate=0.05, volatility=0.20):
        self.S0 = current_price
        self.target = target_price
        self.r = risk_free_rate
        self.sigma = volatility
        self.pricer = OptionPricer()
    
    def price_option(self, leg: OptionLeg) -> float:
        """Prix une option"""
        T = leg.expiry_days / 365.0
        
        if leg.option_type.lower() == 'call':
            return self.pricer.black_scholes_call(self.S0, leg.strike, T, self.r, self.sigma)
        else:
            return self.pricer.black_scholes_put(self.S0, leg.strike, T, self.r, self.sigma)
    
    def calculate_strategy_cost(self, legs: List[OptionLeg]) -> float:
        """Calcule le coût net de la stratégie"""
        total_cost = 0
        
        for leg in legs:
            option_price = self.price_option(leg)
            leg.price = option_price
            
            if leg.action.lower() == 'buy':
                total_cost += option_price * leg.quantity
            else:  # sell
                total_cost -= option_price * leg.quantity
        
        return total_cost
    
    def calculate_payoff(self, legs: List[OptionLeg], spot_price: float) -> float:
        """Calcule le payoff à un prix spot donné"""
        total_payoff = 0
        
        for leg in legs:
            if leg.option_type.lower() == 'call':
                intrinsic = max(spot_price - leg.strike, 0)
            else:  # put
                intrinsic = max(leg.strike - spot_price, 0)
            
            if leg.action.lower() == 'buy':
                total_payoff += intrinsic * leg.quantity
            else:  # sell
                total_payoff -= intrinsic * leg.quantity
        
        return total_payoff
    
    def find_breakeven_points(self, legs: List[OptionLeg], 
                            strategy_cost: float) -> List[float]:
        """Trouve les points de break-even"""
        spot_range = np.linspace(90, 105, 1000)
        breakevens = []
        
        for i, spot in enumerate(spot_range[:-1]):
            payoff_current = self.calculate_payoff(legs, spot)
            payoff_next = self.calculate_payoff(legs, spot_range[i+1])
            
            pnl_current = payoff_current - strategy_cost
            pnl_next = payoff_next - strategy_cost
            
            # Changement de signe = breakeven
            if pnl_current * pnl_next < 0:
                breakevens.append(spot)
        
        return breakevens
    
    def evaluate_strategy(self, name: str, legs: List[OptionLeg]) -> StrategyMetrics:
        """Évalue une stratégie complète"""
        
        # 1. Coût de la stratégie
        cost = self.calculate_strategy_cost(legs)
        
        # 2. Payoff au target
        payoff_at_target = self.calculate_payoff(legs, self.target)
        pnl_at_target = payoff_at_target - cost
        
        # 3. Max gain/loss sur une plage de prix
        spot_range = np.linspace(90, 105, 500)
        pnls = []
        
        for spot in spot_range:
            payoff = self.calculate_payoff(legs, spot)
            pnl = payoff - cost
            pnls.append(pnl)
        
        max_gain = max(pnls)
        max_loss = min(pnls)
        
        # 4. Risk/Reward Ratio
        if max_loss != 0:
            risk_reward_ratio = abs(pnl_at_target / max_loss)
        else:
            risk_reward_ratio = float('inf') if pnl_at_target > 0 else 0
        
        # 5. Points de break-even
        breakeven_points = self.find_breakeven_points(legs, cost)
        
        # 6. Probabilité de break-even (approximation)
        profitable_scenarios = sum(1 for pnl in pnls if pnl > 0)
        breakeven_probability = profitable_scenarios / len(pnls)
        
        return StrategyMetrics(
            name=name,
            cost=cost,
            payoff_at_target=pnl_at_target,
            max_gain=max_gain,
            max_loss=max_loss,
            risk_reward_ratio=risk_reward_ratio,
            breakeven_points=breakeven_points,
            breakeven_probability=breakeven_probability
        )

def create_bull_call_spread() -> List[OptionLeg]:
    """Stratégie 1: Bull Call Spread"""
    return [
        OptionLeg('call', 97.00, 30, 'buy', 1),   # Buy call ITM
        OptionLeg('call', 97.25, 30, 'sell', 1)   # Sell call OTM
    ]

def create_long_straddle() -> List[OptionLeg]:
    """Stratégie 2: Long Straddle"""
    return [
        OptionLeg('call', 97.12, 30, 'buy', 1),   # Buy call ATM
        OptionLeg('put', 97.12, 30, 'buy', 1)     # Buy put ATM
    ]

def plot_strategy_comparison(evaluator: StrategyEvaluator, 
                           strategies: Dict[str, List[OptionLeg]]):
    """Graphique de comparaison des stratégies"""
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    spot_range = np.linspace(95, 99, 200)
    colors = ['blue', 'red', 'green', 'orange']
    
    # Graphique 1: P&L par stratégie
    for i, (name, legs) in enumerate(strategies.items()):
        cost = evaluator.calculate_strategy_cost(legs)
        pnls = []
        
        for spot in spot_range:
            payoff = evaluator.calculate_payoff(legs, spot)
            pnl = payoff - cost
            pnls.append(pnl)
        
        ax1.plot(spot_range, pnls, label=name, color=colors[i], linewidth=2)
    
    ax1.axvline(evaluator.target, color='black', linestyle='--', alpha=0.7, label='Target 97.12')
    ax1.axhline(0, color='gray', linestyle='-', alpha=0.5)
    ax1.set_xlabel('Prix du sous-jacent')
    ax1.set_ylabel('P&L')
    ax1.set_title('Profil de P&L des stratégies')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Graphique 2: Métriques comparatives
    metrics_data = {}
    for name, legs in strategies.items():
        metrics = evaluator.evaluate_strategy(name, legs)
        metrics_data[name] = {
            'Cost': abs(metrics.cost),
            'Payoff@Target': metrics.payoff_at_target,
            'Risk/Reward': metrics.risk_reward_ratio,
            'Breakeven Prob': metrics.breakeven_probability
        }
    
    df_metrics = pd.DataFrame(metrics_data).T
    df_metrics.plot(kind='bar', ax=ax2, width=0.8)
    ax2.set_title('Comparaison des métriques')
    ax2.set_ylabel('Valeur')
    ax2.tick_params(axis='x', rotation=45)
    ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    plt.tight_layout()
    plt.savefig('strategy_comparison.png', dpi=300, bbox_inches='tight')
    plt.show()

def main():
    """Fonction principale"""
    print("📊 Évaluation de Stratégies de Trading Options")
    print("=" * 60)
    print(f"Sous-jacent actuel: 97.00")
    print(f"Prix cible: 97.12")
    print(f"Critère principal: Risk/Reward Ratio")
    print()
    
    # Initialisation de l'évaluateur
    evaluator = StrategyEvaluator(
        current_price=97.00,
        target_price=97.12,
        volatility=0.15,  # Vol implicite 15%
        risk_free_rate=0.05
    )
    
    # Définition des stratégies
    strategies = {
        'Bull Call Spread': create_bull_call_spread(),
        'Long Straddle': create_long_straddle()
    }
    
    # Évaluation des stratégies
    results = {}
    for name, legs in strategies.items():
        metrics = evaluator.evaluate_strategy(name, legs)
        results[name] = metrics
        
        print(f"🎯 {name}")
        print(f"   Coût net: {metrics.cost:.4f}")
        print(f"   P&L au target (97.12): {metrics.payoff_at_target:.4f}")
        print(f"   Gain maximum: {metrics.max_gain:.4f}")
        print(f"   Perte maximum: {metrics.max_loss:.4f}")
        print(f"   ⭐ Risk/Reward Ratio: {metrics.risk_reward_ratio:.2f}")
        print(f"   Points break-even: {[f'{bp:.2f}' for bp in metrics.breakeven_points]}")
        print(f"   Probabilité de profit: {metrics.breakeven_probability:.1%}")
        print()
    
    # Comparaison et recommandation
    print("🏆 RECOMMANDATION BASÉE SUR RISK/REWARD RATIO:")
    best_strategy = max(results.items(), key=lambda x: x[1].risk_reward_ratio)
    print(f"   Meilleure stratégie: {best_strategy[0]}")
    print(f"   Risk/Reward: {best_strategy[1].risk_reward_ratio:.2f}")
    print()
    
    # Analyse détaillée
    print("📋 ANALYSE COMPARATIVE:")
    comparison_data = []
    for name, metrics in results.items():
        comparison_data.append({
            'Stratégie': name,
            'Coût': f"{metrics.cost:.4f}",
            'P&L@Target': f"{metrics.payoff_at_target:.4f}",
            'Risk/Reward': f"{metrics.risk_reward_ratio:.2f}",
            'Prob.Profit': f"{metrics.breakeven_probability:.1%}"
        })
    
    df = pd.DataFrame(comparison_data)
    print(df.to_string(index=False))
    
    # Génération du graphique
    print("\n📈 Génération du graphique de comparaison...")
    plot_strategy_comparison(evaluator, strategies)
    print("✅ Graphique sauvegardé: strategy_comparison.png")

if __name__ == "__main__":
    main()
