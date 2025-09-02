# Simulation Monte Carlo Euribor - Modèle de Vasicek

Ce projet implémente une simulation Monte Carlo complète pour les taux Euribor en utilisant le modèle de Vasicek. Il inclut la récupération automatique de données via l'API ECB Statistical Data Warehouse, la calibration du modèle et la génération de scénarios futurs.

## Fonctionnalités

- **Récupération automatique des données** : API ECB SDW avec fallback CSV
- **Calibration robuste** : Méthodes OLS et Maximum Likelihood
- **Simulation Monte Carlo** : Méthodes exacte et Euler-Maruyama
- **Visualisations complètes** : Trajectoires, distributions, statistiques
- **Export flexible** : CSV, JSON, graphiques haute résolution
- **Interface CLI** : Arguments complets pour tous les paramètres

## Installation rapide

```bash
# Cloner et installer
python -m venv .venv
source .venv/bin/activate  # Sur Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Dépendances

- `requests` : Récupération données API
- `pandas` : Manipulation des données
- `numpy` : Calculs numériques
- `scipy` : Optimisation MLE
- `matplotlib` : Visualisations

## Utilisation

### Simulation de base
```bash
python -m src.main --n-paths 5000 --horizon 252 --seed 42
```

### Avec tous les paramètres
```bash
python -m src.main \
  --tenor 3M \
  --calibration mle \
  --method exact \
  --horizon 252 \
  --n-paths 10000 \
  --seed 42 \
  --export-csv trajectoires.csv \
  --export-stats resultats.json \
  --show-quality \
  --verbose
```

### Tests individuels des modules
```bash
# Test récupération de données
python -m src.fetch_data

# Test calibration
python -m src.calibration  

# Test simulation
python -m src.simulation

# Test visualisation
python -m src.visualize
```

## Structure des données

Le projet fonctionne avec des données au format :
```csv
date,rate
2024-01-02,0.0390
2024-01-03,0.0388
...
```

## Modèle de Vasicek

Le modèle implémente l'équation différentielle stochastique :

```
dr_t = κ(θ - r_t)dt + σ dW_t
```

Où :
- `κ` : vitesse de retour à la moyenne
- `θ` : niveau de long terme  
- `σ` : volatilité
- `dW_t` : mouvement brownien

### Méthodes de simulation

1. **Exacte** (recommandée) : Solution analytique du processus d'Ornstein-Uhlenbeck
2. **Euler** : Approximation discrète par schéma d'Euler-Maruyama

## Sorties

### Statistiques terminales
- Moyenne, médiane, écart-type
- Percentiles (5%, 25%, 75%, 95%)
- Min/max des trajectoires

### Validation théorique
- Comparaison simulation vs formules analytiques
- Erreurs sur moyenne et volatilité terminales

### Exports
- **CSV** : Trajectoires complètes ou échantillon
- **JSON** : Statistiques et métadonnées
- **PNG** : Graphiques haute résolution

## Visualisations

Le module `visualize.py` génère :
- Trajectoires échantillon avec intervalles de confiance
- Distribution terminale vs théorique
- Évolution des percentiles
- Aperçu des données historiques

## Options CLI

| Option | Description | Défaut |
|--------|-------------|---------|
| `--tenor` | Tenor Euribor | 3M |
| `--calibration` | Méthode (ols/mle) | mle |
| `--horizon` | Horizon (jours ouvrés) | 252 |
| `--n-paths` | Nb trajectoires | 10000 |
| `--method` | Simulation (exact/euler) | exact |
| `--seed` | Graine aléatoire | None |
| `--export-csv` | Fichier CSV trajectoires | - |
| `--export-stats` | Fichier JSON stats | - |
| `--show-quality` | Qualité ajustement | False |
| `--verbose` | Mode verbeux | False |

## Exemples d'utilisation

### Analyse de sensibilité
```bash
# Test différentes graines
for seed in 42 123 456; do
  python -m src.main --seed $seed --export-stats "results_$seed.json"
done
```

### Horizons multiples
```bash
# Simulations 1M, 6M, 1Y, 2Y
for horizon in 21 126 252 504; do
  python -m src.main --horizon $horizon --export-csv "paths_${horizon}d.csv"
done
```

### Calibration comparative
```bash
# OLS vs MLE
python -m src.main --calibration ols --export-stats ols_results.json
python -m src.main --calibration mle --export-stats mle_results.json
```

## Avertissements

- **Usage éducatif uniquement** - Pas pour la production sans validation
- **Données ECB** - Respecter les conditions d'utilisation
- **Modèle simplifié** - Vasicek ne capture pas tous les phénomènes de marché
- **Taux négatifs possibles** - Le modèle peut générer des taux négatifs

## Développement

### Ajout de nouveaux modèles
1. Créer une classe de paramètres dans `calibration.py`
2. Implémenter la simulation dans `simulation.py`
3. Ajouter l'option CLI dans `main.py`

### Tests
```bash
# Tests rapides
python -m src.main --n-paths 100 --horizon 10 --quiet

# Validation complète
python -m src.main --show-quality --verbose
```

