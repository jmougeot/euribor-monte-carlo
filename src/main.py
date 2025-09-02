#!/usr/bin/env python3
"""
Script principal pour la simulation Monte Carlo Euribor
"""

import argparse
import json
import sys
import time
from pathlib import Path

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
    
    if not args.quiet:
        print("🎯 Simulation Monte Carlo Euribor - Modèle de Vasicek")
        print("=" * 60)
    
    start_time = time.time()
    
    try:
        # 1. Chargement des données
        if args.verbose:
            print(f"📊 Chargement des données Euribor {args.tenor}...")
        
        data, meta = load_with_fallback(tenor=args.tenor, path_csv=args.data_csv)
        
        if not args.quiet:
            print(f"✓ Données chargées: {len(data)} observations")
            print(f"  Source: {meta.get('source', 'unknown')}")
            print(f"  Période: {data['date'].min().date()} → {data['date'].max().date()}")
            print(f"  Taux: {data['rate'].min():.4f} → {data['rate'].max():.4f}")
        
        # 2. Calibration du modèle
        if args.verbose:
            print(f"\n🔧 Calibration du modèle (méthode: {args.calibration})...")
        
        if args.calibration == "mle":
            params = calibrate_vasicek_mle(data["rate"], dt=args.dt)
        else:
            params = calibrate_vasicek_ols(data["rate"], dt=args.dt)
        
        if not args.quiet:
            print(f"✓ Paramètres calibrés:")
            print(f"  κ (mean reversion): {params.kappa:.4f}")
            print(f"  θ (long-term level): {params.theta:.4f}")
            print(f"  σ (volatility): {params.sigma:.4f}")
            print(f"  r₀ (initial rate): {params.r0:.4f}")
        
        # 3. Qualité de l'ajustement (optionnel)
        if args.show_quality:
            if args.verbose:
                print("\n📈 Évaluation de la qualité...")
            quality = estimate_model_quality(data["rate"], params, dt=args.dt)
            print(f"  RMSE: {quality['rmse']:.4f}")
            print(f"  Autocorrélation résiduelle: {quality['residual_autocorr']:.4f}")
        
        # 4. Simulation Monte Carlo
        if args.verbose:
            print(f"\n🎲 Simulation Monte Carlo...")
            print(f"  Trajectoires: {args.n_paths}")
            print(f"  Horizon: {args.horizon} pas ({args.horizon * args.dt:.2f} années)")
            print(f"  Méthode: {args.method}")
        
        paths, stats = run_monte_carlo_simulation(
            params=params,
            horizon=args.horizon,
            n_paths=args.n_paths,
            dt=args.dt,
            method=args.method,
            seed=args.seed,
            return_stats=True
        )
        
        # 5. Affichage des résultats
        if not args.quiet:
            print(f"\n📊 Résultats de simulation:")
            terminal = stats["terminal"]
            print(f"  Taux terminal moyen: {terminal['mean']:.4f}")
            print(f"  Écart-type: {terminal['std']:.4f}")
            print(f"  Médiane: {terminal['median']:.4f}")
            print(f"  Intervalle 90%: [{terminal['p05']:.4f}, {terminal['p95']:.4f}]")
            
            if args.verbose:
                validation = stats["validation"]
                print(f"\n🔍 Validation théorique:")
                print(f"  Moyenne théorique: {validation['theoretical_terminal_mean']:.4f}")
                print(f"  Écart théorique: {validation['theoretical_terminal_std']:.4f}")
                print(f"  Erreur moyenne: {validation['mean_error']:.4f}")
                print(f"  Erreur volatilité: {validation['std_error']:.4f}")
        
        # 6. Exports
        if args.export_csv:
            if args.verbose:
                print(f"\n💾 Export CSV: {args.export_csv}")
            export_simulation_results(
                paths, stats, params, 
                filename=args.export_csv,
                export_all_paths=args.export_all_paths
            )
        
        if args.export_stats:
            if args.verbose:
                print(f"💾 Export statistiques: {args.export_stats}")
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
            print(f"✓ Statistiques exportées vers {args.export_stats}")
        
        # 7. Résumé final
        elapsed = time.time() - start_time
        if not args.quiet:
            print(f"\n✅ Simulation terminée en {elapsed:.2f}s")
            
    except Exception as e:
        print(f"❌ Erreur: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
