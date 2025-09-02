import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Tuple, Dict, Any
import warnings
warnings.filterwarnings('ignore')

@dataclass
class VasicekParams:
    """Paramètres du modèle de Vasicek"""
    kappa: float
    theta: float  
    sigma: float
    r0: float

def simulate_vasicek_exact(
    params: VasicekParams, 
    n_steps: int, 
    n_paths: int, 
    dt: float, 
    seed: int = None
) -> np.ndarray:
    """
    Simulation exacte du processus de Vasicek (Ornstein-Uhlenbeck)
    
    dr_t = κ(θ - r_t)dt + σ dW_t
    
    Solution exacte:
    r_{t+1} = θ + (r_t - θ)e^{-κΔt} + σ√[(1-e^{-2κΔt})/(2κ)] * Z
    
    Returns:
        Array de shape (n_steps + 1, n_paths) avec les trajectoires
    """
    if seed is not None:
        np.random.seed(seed)
    
    rng = np.random.default_rng(seed)
    kappa, theta, sigma, r0 = params.kappa, params.theta, params.sigma, params.r0
    
    # Pré-calcul des constantes
    exp_kappa_dt = np.exp(-kappa * dt)
    variance = sigma**2 * (1 - np.exp(-2 * kappa * dt)) / (2 * kappa)
    std_dev = np.sqrt(variance)
    
    # Initialisation des trajectoires
    paths = np.zeros((n_steps + 1, n_paths))
    paths[0] = r0
    
    # Simulation pas par pas
    for t in range(1, n_steps + 1):
        # Tirage aléatoire
        z = rng.standard_normal(n_paths)
        
        # Évolution exacte
        prev_rates = paths[t-1]
        mean_rates = theta + (prev_rates - theta) * exp_kappa_dt
        paths[t] = mean_rates + std_dev * z
    
    return paths

def simulate_vasicek_euler(
    params: VasicekParams,
    n_steps: int, 
    n_paths: int,
    dt: float,
    seed: int = None
) -> np.ndarray:
    """
    Simulation par schéma d'Euler (approximation discrète)
    
    r_{t+1} = r_t + κ(θ - r_t)Δt + σ√Δt * Z
    """
    if seed is not None:
        np.random.seed(seed)
        
    rng = np.random.default_rng(seed)
    kappa, theta, sigma, r0 = params.kappa, params.theta, params.sigma, params.r0
    
    paths = np.zeros((n_steps + 1, n_paths))
    paths[0] = r0
    
    sqrt_dt = np.sqrt(dt)
    
    for t in range(1, n_steps + 1):
        z = rng.standard_normal(n_paths)
        prev_rates = paths[t-1]
        
        drift = kappa * (theta - prev_rates) * dt
        diffusion = sigma * sqrt_dt * z
        
        paths[t] = prev_rates + drift + diffusion
    
    return paths

def run_monte_carlo_simulation(
    params: VasicekParams,
    horizon: int = 252,
    n_paths: int = 10000,
    dt: float = 1/252,
    method: str = "exact",
    seed: int = None,
    return_stats: bool = True
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Lance une simulation Monte Carlo complète
    
    Args:
        params: Paramètres du modèle Vasicek
        horizon: Nombre de pas de temps
        n_paths: Nombre de trajectoires
        dt: Pas de temps (en années)
        method: "exact" ou "euler"
        seed: Graine aléatoire
        return_stats: Calculer les statistiques
        
    Returns:
        (paths, statistics)
    """
    print(f"Simulation Monte Carlo: {n_paths} trajectoires, {horizon} pas")
    print(f"Méthode: {method}, dt={dt:.6f}")
    
    # Sélection de la méthode
    if method.lower() == "exact":
        paths = simulate_vasicek_exact(params, horizon, n_paths, dt, seed)
    elif method.lower() == "euler":
        paths = simulate_vasicek_euler(params, horizon, n_paths, dt, seed)
    else:
        raise ValueError(f"Méthode inconnue: {method}. Utilisez 'exact' ou 'euler'")
    
    stats = {}
    if return_stats:
        stats = calculate_simulation_statistics(paths, params, dt)
    
    return paths, stats

def calculate_simulation_statistics(
    paths: np.ndarray, 
    params: VasicekParams, 
    dt: float
) -> Dict[str, Any]:
    """
    Calcule les statistiques de la simulation
    """
    terminal_rates = paths[-1]  # Taux finaux
    initial_rates = paths[0]    # Taux initiaux
    
    # Statistiques terminales
    terminal_stats = {
        "mean": float(np.mean(terminal_rates)),
        "std": float(np.std(terminal_rates, ddof=1)),
        "min": float(np.min(terminal_rates)),
        "max": float(np.max(terminal_rates)),
        "median": float(np.median(terminal_rates)),
        "p05": float(np.percentile(terminal_rates, 5)),
        "p25": float(np.percentile(terminal_rates, 25)),
        "p75": float(np.percentile(terminal_rates, 75)),
        "p95": float(np.percentile(terminal_rates, 95)),
    }
    
    # Statistiques de trajet
    path_stats = {
        "mean_path_volatility": float(np.mean([np.std(paths[:, i], ddof=1) for i in range(paths.shape[1])])),
        "max_drawdown": calculate_max_drawdown(paths),
        "time_above_initial": float(np.mean(terminal_rates > initial_rates)),
        "negative_rates_prob": float(np.mean(np.any(paths < 0, axis=0))),
    }
    
    # Théorie vs simulation (vérification)
    T = len(paths) * dt
    theoretical_mean = params.theta + (params.r0 - params.theta) * np.exp(-params.kappa * T)
    theoretical_var = (params.sigma**2 / (2 * params.kappa)) * (1 - np.exp(-2 * params.kappa * T))
    
    validation = {
        "theoretical_terminal_mean": float(theoretical_mean),
        "theoretical_terminal_std": float(np.sqrt(theoretical_var)),
        "mean_error": float(abs(terminal_stats["mean"] - theoretical_mean)),
        "std_error": float(abs(terminal_stats["std"] - np.sqrt(theoretical_var))),
    }
    
    return {
        "terminal": terminal_stats,
        "paths": path_stats,
        "validation": validation,
        "simulation_info": {
            "n_paths": paths.shape[1],
            "n_steps": paths.shape[0] - 1,
            "total_time_years": T,
            "dt": dt
        }
    }

def calculate_max_drawdown(paths: np.ndarray) -> float:
    """Calcule le drawdown maximum moyen sur toutes les trajectoires"""
    drawdowns = []
    for i in range(paths.shape[1]):
        path = paths[:, i]
        peak = np.maximum.accumulate(path)
        drawdown = (peak - path) / peak
        max_dd = np.max(drawdown)
        drawdowns.append(max_dd)
    return float(np.mean(drawdowns))

def paths_to_dataframe(paths: np.ndarray, dt: float = 1/252) -> pd.DataFrame:
    """
    Convertit les trajectoires en DataFrame avec index temporel
    """
    n_steps, n_paths = paths.shape
    time_index = np.arange(n_steps) * dt
    
    df = pd.DataFrame(
        paths, 
        index=time_index,
        columns=[f"path_{i}" for i in range(n_paths)]
    )
    df.index.name = "time_years"
    
    return df

def export_simulation_results(
    paths: np.ndarray, 
    stats: Dict[str, Any], 
    params: VasicekParams,
    filename: str = "simulation_results.csv",
    export_all_paths: bool = False
):
    """
    Exporte les résultats de simulation
    """
    if export_all_paths:
        # Export toutes les trajectoires
        df = paths_to_dataframe(paths)
        df.to_csv(filename)
        print(f"✓ {len(df)} trajectoires exportées vers {filename}")
    else:
        # Export statistiques + quelques trajectoires échantillon
        sample_size = min(100, paths.shape[1])
        sample_paths = paths[:, :sample_size]
        df = paths_to_dataframe(sample_paths)
        
        # Ajout des statistiques comme métadonnées
        with open(filename, 'w') as f:
            f.write(f"# Simulation Monte Carlo Euribor - Modèle de Vasicek\n")
            f.write(f"# Paramètres: {params}\n")
            f.write(f"# Statistiques: {stats['terminal']}\n")
            f.write("#\n")
            
        df.to_csv(filename, mode='a')
        print(f"✓ Échantillon de {sample_size} trajectoires + stats exporté vers {filename}")

if __name__ == "__main__":
    # Test du module
    from fetch_data import load_with_fallback
    from calibration import calibrate_vasicek_mle
    
    try:
        # Chargement et calibration
        data, _ = load_with_fallback()
        params = calibrate_vasicek_mle(data["rate"])
        print(f"Paramètres calibrés: {params}")
        
        # Simulation test
        paths, stats = run_monte_carlo_simulation(
            params, 
            horizon=100, 
            n_paths=1000, 
            method="exact",
            seed=42
        )
        
        print(f"\nStatistiques de simulation:")
        print(f"Terminal: {stats['terminal']}")
        print(f"Validation: {stats['validation']}")
        
    except Exception as e:
        print(f"Erreur: {e}")
