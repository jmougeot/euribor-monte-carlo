#!/usr/bin/env python3
"""
Script pour générer les graphiques de la simulation Monte Carlo Euribor
"""

import sys
import os
sys.path.append('src')

import matplotlib
matplotlib.use('Agg')  # Backend pour sauvegarde sans interface graphique
import matplotlib.pyplot as plt

from fetch_data import load_with_fallback
from calibration import calibrate_vasicek_mle
from simulation import run_monte_carlo_simulation
from visualize import plot_simulation_results, plot_data_overview

def main():
    print("🎨 Génération des graphiques de simulation Monte Carlo Euribor")
    print("=" * 60)
    
    try:
        # 1. Chargement des données
        print("📊 Chargement des données...")
        data, meta = load_with_fallback()
        print(f"✓ {len(data)} observations chargées depuis {meta['source']}")
        
        # 2. Graphique des données historiques
        print("\n📈 Génération du graphique des données historiques...")
        plot_data_overview(data, save_path='euribor_data_overview.png')
        
        # 3. Calibration du modèle
        print("\n🔧 Calibration du modèle Vasicek...")
        params = calibrate_vasicek_mle(data['rate'])
        print(f"✓ Paramètres: κ={params.kappa:.4f}, θ={params.theta:.4f}, σ={params.sigma:.4f}")
        
        # 4. Simulation Monte Carlo
        print("\n🎲 Simulation Monte Carlo...")
        paths, stats = run_monte_carlo_simulation(
            params, 
            horizon=252,  # 1 an
            n_paths=2000,
            seed=42,
            method="exact"
        )
        print(f"✓ {stats['simulation_info']['n_paths']} trajectoires simulées")
        
        # 5. Graphique des résultats de simulation
        print("\n📊 Génération du graphique de simulation...")
        plot_simulation_results(
            paths, 
            stats, 
            params, 
            n_sample_paths=30,
            save_path='euribor_simulation_results.png'
        )
        
        # 6. Graphique de quelques trajectoires individuelles
        print("\n�� Génération de trajectoires individuelles...")
        plt.figure(figsize=(12, 6))
        time_axis = range(paths.shape[0])
        
        # Trajectoires échantillon
        for i in range(min(10, paths.shape[1])):
            plt.plot(time_axis, paths[:, i], alpha=0.7, linewidth=1)
        
        # Moyenne
        mean_path = paths.mean(axis=1)
        plt.plot(time_axis, mean_path, 'red', linewidth=3, label='Moyenne')
        
        plt.title('Trajectoires Euribor simulées (échantillon)')
        plt.xlabel('Pas de temps (jours ouvrés)')
        plt.ylabel('Taux Euribor 3M')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('euribor_sample_paths.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Graphique sauvegardé: euribor_sample_paths.png")
        
        # 7. Distribution terminale
        print("\n📊 Génération de la distribution terminale...")
        terminal_rates = paths[-1]
        
        plt.figure(figsize=(10, 6))
        plt.hist(terminal_rates, bins=50, density=True, alpha=0.7, 
                color='skyblue', edgecolor='black', label='Simulation')
        
        # Statistiques
        mean_term = terminal_rates.mean()
        plt.axvline(mean_term, color='red', linestyle='--', linewidth=2, 
                   label=f'Moyenne: {mean_term:.4f}')
        plt.axvline(stats['terminal']['p05'], color='orange', linestyle=':', 
                   label=f"P5: {stats['terminal']['p05']:.4f}")
        plt.axvline(stats['terminal']['p95'], color='orange', linestyle=':', 
                   label=f"P95: {stats['terminal']['p95']:.4f}")
        
        plt.title('Distribution des taux Euribor terminaux (1 an)')
        plt.xlabel('Taux Euribor 3M')
        plt.ylabel('Densité de probabilité')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('euribor_terminal_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Graphique sauvegardé: euribor_terminal_distribution.png")
        
        print(f"\n✅ Tous les graphiques ont été générés avec succès!")
        print(f"📁 Fichiers créés:")
        print(f"   • euribor_data_overview.png - Aperçu des données historiques")
        print(f"   • euribor_simulation_results.png - Résultats complets de simulation")
        print(f"   • euribor_sample_paths.png - Trajectoires échantillon")
        print(f"   • euribor_terminal_distribution.png - Distribution terminale")
        
        print(f"\n📊 Résumé des résultats:")
        print(f"   • Taux terminal moyen: {stats['terminal']['mean']:.4f}")
        print(f"   • Intervalle 90%: [{stats['terminal']['p05']:.4f}, {stats['terminal']['p95']:.4f}]")
        print(f"   • Probabilité taux négatifs: {stats['paths']['negative_rates_prob']:.1%}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
