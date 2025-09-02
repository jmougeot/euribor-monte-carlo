#!/usr/bin/env python3
"""
Script principal pour la simulation Monte Carlo Euribor
"""

import argparse
import json
import sys
import time
from pathlib import Path

# Ajouter le répertoire src au path Python
sys.path.insert(0, str(Path(__file__).parent))

# Import des modules locaux
from fetch_data import load_with_fallback
from calibration import calibrate_vasicek_mle, calibrate_vasicek_ols, estimate_model_quality
from simulation import run_monte_carlo_simulation, export_simulation_results

def parse_arguments():
    """Parse les arguments de ligne de commande"""
    parser = argparse.ArgumentParser(
        description="Simulation Monte Carlo Euribor avec modèle de Vasicek",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Paramètres de données
    parser.add_argument("--tenor", default="3M", 
                       help="Tenor Euribor (3M par défaut)")
    parser.add_argument("--data-csv", default="data/sample_euribor3m.csv",
                       help="Fichier CSV de fallback")
    
    # Paramètres de calibration
    parser.add_argument("--calibration", choices=["ols", "mle"], default="mle",
                       help="Méthode de calibration")
    parser.add_argument("--show-quality", action="store_true",
                       help="Afficher la qualité de l'ajustement")
    
    # Paramètres de simulation
    parser.add_argument("--horizon", type=int, default=252,
                       help="Horizon de simulation (jours ouvrés)")
    parser.add_argument("--dt", type=float, default=1/252,
                       help="Pas de temps (fraction d'année)")
    parser.add_argument("--n-paths", type=int, default=10000,
                       help="Nombre de trajectoires Monte Carlo")
    parser.add_argument("--method", choices=["exact", "euler"], default="exact",
                       help="Méthode de simulation")
    parser.add_argument("--seed", type=int, default=None,
                       help="Graine aléatoire pour reproductibilité")
    
    # Sortie et export
    parser.add_argument("--export-csv", 
                       help="Fichier CSV pour export des trajectoires")
    parser.add_argument("--export-all-paths", action="store_true",
                       help="Exporter toutes les trajectoires (sinon échantillon)")
    parser.add_argument("--export-stats", 
                       help="Fichier JSON pour export des statistiques")
    parser.add_argument("--quiet", "-q", action="store_true",
                       help="Mode silencieux")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Mode verbeux")
    
    return parser.parse_args()

def main():
    """Fonction principale"""
    args = parse_arguments()
    
    try:
        # 1. Chargement des données
        data, meta = load_with_fallback(tenor=args.tenor, path_csv=args.data_csv)
        
        # 2. Calibration du modèle
        if args.calibration == "mle":
            params = calibrate_vasicek_mle(data["rate"], dt=args.dt)
        else:
            params = calibrate_vasicek_ols(data["rate"], dt=args.dt)
        
        # 3. Qualité de l'ajustement (optionnel)
        if args.show_quality:
            quality = estimate_model_quality(data["rate"], params, dt=args.dt)
        
        # 4. Simulation Monte Carlo
        paths, stats = run_monte_carlo_simulation(
            params=params,
            horizon=args.horizon,
            n_paths=args.n_paths,
            dt=args.dt,
            method=args.method,
            seed=args.seed,
            return_stats=True
        )
        
        # 5. Exports
        if args.export_csv:
            export_simulation_results(
                paths, stats, params, 
                filename=args.export_csv,
                export_all_paths=args.export_all_paths
            )
        
        if args.export_stats:
            start_time = time.time()
            with open(args.export_stats, 'w') as f:
                export_data = {
                    "parameters": {
                        "kappa": params.kappa,
                        "theta": params.theta,
                        "sigma": params.sigma,
                        "r0": params.r0
                    },
                    "statistics": stats,
                    "metadata": {
                        "data_source": meta,
                        "simulation_args": vars(args),
                        "execution_time_seconds": time.time() - start_time
                    }
                }
                json.dump(export_data, f, indent=2, default=str)
            
    except Exception as e:
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
