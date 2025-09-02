#!/usr/bin/env python3
"""
Script pour afficher les graphiques de manière interactive
"""

import sys
sys.path.append('src')

# Utiliser le backend interactif par défaut
import matplotlib.pyplot as plt
from fetch_data import load_with_fallback
from calibration import calibrate_vasicek_mle
from simulation import run_monte_carlo_simulation

def generate_interactive_plots():
    print("🎨 Génération des graphiques interactifs")
    
    # Chargement et simulation
    data, _ = load_with_fallback()
    params = calibrate_vasicek_mle(data['rate'])
    paths, stats = run_monte_carlo_simulation(params, horizon=252, n_paths=1000, seed=42)
    
    # 1. Graphique des données historiques
    plt.figure(figsize=(12, 4))
    plt.plot(data['date'], data['rate'], linewidth=1, color='navy')
    plt.title('Évolution historique Euribor 3M')
    plt.xlabel('Date')
    plt.ylabel('Taux')
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
    
    # 2. Trajectoires simulées
    plt.figure(figsize=(12, 6))
    time_axis = range(paths.shape[0])
    
    # Échantillon de trajectoires
    for i in range(min(20, paths.shape[1])):
        plt.plot(time_axis, paths[:, i], alpha=0.6, linewidth=0.8)
    
    # Moyenne et percentiles
    mean_path = paths.mean(axis=1)
    p05_path = np.percentile(paths, 5, axis=1)
    p95_path = np.percentile(paths, 95, axis=1)
    
    plt.plot(time_axis, mean_path, 'red', linewidth=2, label='Moyenne')
    plt.fill_between(time_axis, p05_path, p95_path, alpha=0.3, color='red', label='IC 90%')
    
    plt.title('Trajectoires Euribor simulées (Vasicek)')
    plt.xlabel('Pas de temps (jours ouvrés)')
    plt.ylabel('Taux')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()
    
    # 3. Distribution terminale
    terminal_rates = paths[-1]
    
    plt.figure(figsize=(10, 6))
    plt.hist(terminal_rates, bins=50, density=True, alpha=0.7, color='skyblue', edgecolor='black')
    
    mean_term = terminal_rates.mean()
    plt.axvline(mean_term, color='red', linestyle='--', linewidth=2, label=f'Moyenne: {mean_term:.4f}')
    plt.axvline(stats['terminal']['p05'], color='orange', linestyle=':', label=f"P5: {stats['terminal']['p05']:.4f}")
    plt.axvline(stats['terminal']['p95'], color='orange', linestyle=':', label=f"P95: {stats['terminal']['p95']:.4f}")
    
    plt.title('Distribution des taux terminaux (1 an)')
    plt.xlabel('Taux Euribor 3M')
    plt.ylabel('Densité')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()
    
    print(f"📊 Statistiques:")
    print(f"   • Taux moyen: {stats['terminal']['mean']:.4f}")
    print(f"   • Volatilité: {stats['terminal']['std']:.4f}")
    print(f"   • Intervalle 90%: [{stats['terminal']['p05']:.4f}, {stats['terminal']['p95']:.4f}]")

if __name__ == "__main__":
    import numpy as np
    generate_interactive_plots()
