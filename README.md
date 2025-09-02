# Simulation Monte Carlo Euribor - Modèle de Vasicek

Simulation Monte Carlo des taux Euribor avec modèle de Vasicek, API ECB et analyse de stratégies d'options.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Utilisation

### Simulation basique
```bash
PYTHONPATH=src python -m main --n-paths 10000 --horizon 252
```

### Avec exports
```bash
PYTHONPATH=src python -m main \
  --n-paths 10000 \
  --export-csv trajectoires.csv \
  --export-stats stats.json
```

### Génération graphiques
```bash
python generate_plots.py
```

### Analyse stratégies trading
```bash
python trading_strategy_evaluation.py
```

## Ce que fait le code

1. **Récupère les données Euribor** via API ECB (ou CSV local)
2. **Calibre le modèle de Vasicek** : `dr_t = κ(θ - r_t)dt + σ dW_t`
3. **Simule 10,000 trajectoires** futures sur 1 an
4. **Génère des visualisations** (trajectoires, distributions)
5. **Analyse des stratégies d'options** (Bull Call Spread vs Long Straddle)

## Options principales

| Option | Description | Défaut |
|--------|-------------|---------|
| `--n-paths` | Nombre de trajectoires | 10000 |
| `--horizon` | Horizon (jours) | 252 |
| `--method` | Méthode (exact/euler) | exact |
| `--calibration` | Calibration (ols/mle) | mle |
| `--export-csv` | Export trajectoires | - |
| `--export-stats` | Export statistiques | - |

## Sorties

- **Trajectoires simulées** : CSV avec 10,000 scénarios futurs
- **Statistiques** : JSON avec percentiles, moyenne, volatilité
- **Graphiques** : PNG avec visualisations (4 fichiers)
- **Analyse trading** : Comparaison stratégies d'options

## Fichiers clés

- `src/main.py` : Interface principale
- `src/simulation.py` : Simulation Monte Carlo  
- `trading_strategy_evaluation.py` : Analyse options
- `generate_plots.py` : Visualisations automatiques

## Structure modèle Vasicek

```
dr_t = κ(θ - r_t)dt + σ dW_t
```

- **κ** : vitesse retour à la moyenne
- **θ** : niveau long terme  
- **σ** : volatilité
- **Solution exacte** : `r(t+1) = θ + (r(t)-θ)e^(-κdt) + σ√[(1-e^(-2κdt))/(2κ)] × Z`

## Résultats exemple

```
Paramètres calibrés: κ=2.25, θ=0.008, σ=0.025
Simulation: 10,000 trajectoires sur 252 jours
Taux final moyen: 0.0084 (0.84%)
Intervalle 90%: [0.0021, 0.0147]

Stratégies trading:
- Bull Call Spread: Coût=0.13, R/R=0.07, Profit=52%
- Long Straddle: Coût=3.33, R/R=1.00, Profit=56%
```

