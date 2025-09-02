import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import Optional, Tuple
import seaborn as sns

# Configuration matplotlib
plt.style.use('seaborn-v0_8' if 'seaborn-v0_8' in plt.style.available else 'default')
sns.set_palette("husl")

def plot_simulation_results(
    paths: np.ndarray,
    stats: dict,
    params,
    n_sample_paths: int = 50,
    figsize: Tuple[int, int] = (14, 10),
    save_path: Optional[str] = None
):
    """
    Crée un graphique complet des résultats de simulation
    """
    fig, axes = plt.subplots(2, 2, figsize=figsize)
    fig.suptitle("Simulation Monte Carlo Euribor - Modèle de Vasicek", fontsize=16, fontweight='bold')
    
    time_axis = np.arange(paths.shape[0]) * stats['simulation_info']['dt']
    
    # 1. Trajectoires échantillon
    ax1 = axes[0, 0]
    sample_indices = np.random.choice(paths.shape[1], min(n_sample_paths, paths.shape[1]), replace=False)
    
    for i in sample_indices:
        ax1.plot(time_axis, paths[:, i], alpha=0.6, linewidth=0.8)
    
    # Moyenne et percentiles
    mean_path = np.mean(paths, axis=1)
    p05_path = np.percentile(paths, 5, axis=1)
    p95_path = np.percentile(paths, 95, axis=1)
    
    ax1.plot(time_axis, mean_path, 'red', linewidth=2, label='Moyenne')
    ax1.fill_between(time_axis, p05_path, p95_path, alpha=0.3, color='red', label='IC 90%')
    
    ax1.set_title('Trajectoires simulées')
    ax1.set_xlabel('Temps (années)')
    ax1.set_ylabel('Taux')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Distribution terminale
    ax2 = axes[0, 1]
    terminal_rates = paths[-1]
    
    ax2.hist(terminal_rates, bins=50, density=True, alpha=0.7, color='skyblue', edgecolor='black')
    
    # Statistiques
    mean_term = stats['terminal']['mean']
    std_term = stats['terminal']['std']
    
    ax2.axvline(mean_term, color='red', linestyle='--', linewidth=2, label=f'Moyenne: {mean_term:.4f}')
    ax2.axvline(stats['terminal']['p05'], color='orange', linestyle=':', label=f"P5: {stats['terminal']['p05']:.4f}")
    ax2.axvline(stats['terminal']['p95'], color='orange', linestyle=':', label=f"P95: {stats['terminal']['p95']:.4f}")
    
    # Distribution théorique (si disponible)
    if 'validation' in stats:
        theo_mean = stats['validation']['theoretical_terminal_mean']
        theo_std = stats['validation']['theoretical_terminal_std']
        x_theo = np.linspace(terminal_rates.min(), terminal_rates.max(), 100)
        y_theo = (1/np.sqrt(2*np.pi*theo_std**2)) * np.exp(-0.5*((x_theo-theo_mean)/theo_std)**2)
        ax2.plot(x_theo, y_theo, 'green', linewidth=2, label='Théorique')
    
    ax2.set_title('Distribution des taux terminaux')
    ax2.set_xlabel('Taux')
    ax2.set_ylabel('Densité')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Évolution des percentiles
    ax3 = axes[1, 0]
    percentiles = [5, 25, 50, 75, 95]
    colors = ['red', 'orange', 'blue', 'orange', 'red']
    
    for p, color in zip(percentiles, colors):
        p_path = np.percentile(paths, p, axis=1)
        ax3.plot(time_axis, p_path, color=color, linewidth=1.5, label=f'P{p}')
    
    ax3.set_title('Évolution des percentiles')
    ax3.set_xlabel('Temps (années)')
    ax3.set_ylabel('Taux')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. Statistiques descriptives
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    # Texte avec statistiques
    stats_text = f"""
PARAMÈTRES VASICEK:
κ (mean reversion): {params.kappa:.4f}
θ (niveau LT): {params.theta:.4f}
σ (volatilité): {params.sigma:.4f}
r₀ (taux initial): {params.r0:.4f}

STATISTIQUES TERMINALES:
Moyenne: {stats['terminal']['mean']:.4f}
Médiane: {stats['terminal']['median']:.4f}
Écart-type: {stats['terminal']['std']:.4f}
Min/Max: {stats['terminal']['min']:.4f} / {stats['terminal']['max']:.4f}

SIMULATION:
Trajectoires: {stats['simulation_info']['n_paths']:,}
Horizon: {stats['simulation_info']['n_steps']} pas
Durée: {stats['simulation_info']['total_time_years']:.2f} ans
"""
    
    if 'validation' in stats:
        stats_text += f"""
VALIDATION:
Erreur moyenne: {stats['validation']['mean_error']:.5f}
Erreur volatilité: {stats['validation']['std_error']:.5f}
"""
    
    ax4.text(0.05, 0.95, stats_text, transform=ax4.transAxes, fontsize=10,
             verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✓ Graphique sauvegardé: {save_path}")
    
    plt.show()

def plot_data_overview(data: pd.DataFrame, save_path: Optional[str] = None):
    """
    Graphique d'aperçu des données historiques
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle("Données historiques Euribor", fontsize=14, fontweight='bold')
    
    # 1. Série temporelle
    ax1 = axes[0, 0]
    ax1.plot(data['date'], data['rate'], linewidth=1, color='navy')
    ax1.set_title('Évolution temporelle')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Taux')
    ax1.grid(True, alpha=0.3)
    
    # 2. Distribution
    ax2 = axes[0, 1]
    ax2.hist(data['rate'], bins=30, density=True, alpha=0.7, color='lightblue', edgecolor='black')
    ax2.axvline(data['rate'].mean(), color='red', linestyle='--', label=f'Moyenne: {data["rate"].mean():.4f}')
    ax2.set_title('Distribution des taux')
    ax2.set_xlabel('Taux')
    ax2.set_ylabel('Densité')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Variations quotidiennes
    ax3 = axes[1, 0]
    data_sorted = data.sort_values('date')
    rate_diff = data_sorted['rate'].diff().dropna()
    ax3.plot(data_sorted['date'].iloc[1:], rate_diff, linewidth=0.8, alpha=0.8, color='darkgreen')
    ax3.axhline(0, color='red', linestyle='-', alpha=0.5)
    ax3.set_title('Variations quotidiennes')
    ax3.set_xlabel('Date')
    ax3.set_ylabel('Δ Taux')
    ax3.grid(True, alpha=0.3)
    
    # 4. Statistiques
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    stats_text = f"""
STATISTIQUES DESCRIPTIVES:

Observations: {len(data)}
Période: {data['date'].min().date()} 
         → {data['date'].max().date()}

Taux:
  Moyenne: {data['rate'].mean():.4f}
  Médiane: {data['rate'].median():.4f}
  Écart-type: {data['rate'].std():.4f}
  Min/Max: {data['rate'].min():.4f} / {data['rate'].max():.4f}

Variations:
  Moyenne: {rate_diff.mean():.6f}
  Écart-type: {rate_diff.std():.6f}
  Min/Max: {rate_diff.min():.6f} / {rate_diff.max():.6f}
"""
    
    ax4.text(0.05, 0.95, stats_text, transform=ax4.transAxes, fontsize=10,
             verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✓ Graphique données sauvegardé: {save_path}")
    
    plt.show()

if __name__ == "__main__":
    # Test du module de visualisation
    from fetch_data import load_with_fallback
    from calibration import calibrate_vasicek_mle
    from simulation import run_monte_carlo_simulation
    
    try:
        # Chargement et aperçu des données
        data, _ = load_with_fallback()
        plot_data_overview(data)
        
        # Simulation et visualisation
        params = calibrate_vasicek_mle(data["rate"])
        paths, stats = run_monte_carlo_simulation(params, horizon=252, n_paths=2000, seed=42)
        plot_simulation_results(paths, stats, params)
        
    except Exception as e:
        print(f"Erreur: {e}")
