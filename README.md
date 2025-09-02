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

## Analyse de Stratégies de Trading

Le projet inclut un système d'évaluation de stratégies d'options basé sur les simulations de taux Euribor. Le script `trading_strategy_evaluation.py` permet de comparer différentes stratégies de trading d'options.

### Stratégies Disponibles

#### **Bull Call Spread**
- **Structure** : Achat call ITM + Vente call OTM
- **Objectif** : Profit sur hausse modérée avec risque limité
- **Caractéristiques** :
  - Coût initial limité
  - Gain plafonné
  - Perte maximale = prime payée

#### **Long Straddle**
- **Structure** : Achat call ATM + Achat put ATM
- **Objectif** : Profit sur forte volatilité (hausse ou baisse)
- **Caractéristiques** :
  - Coût initial élevé
  - Profit illimité (théoriquement)
  - Sensible à la volatilité

### Métriques d'Évaluation

Le système calcule automatiquement :
- **Coût initial** de la stratégie
- **Ratio Risque/Rendement** (gain max / perte max)
- **Probabilité de profit** basée sur les simulations Monte Carlo
- **Seuils de rentabilité** (breakeven points)
- **Distribution des P&L** à l'expiration

### Utilisation

```bash
# Exécution de l'analyse comparative
python trading_strategy_evaluation.py

# Génération automatique de :
# - Analyse comparative détaillée
# - Graphique strategy_comparison.png
# - Recommandations basées sur les métriques
```

### Exemple de Résultats

```
=== ANALYSE COMPARATIVE DES STRATÉGIES ===

Bull Call Spread:
- Coût initial: 0.1289
- Ratio Risque/Rendement: 0.07
- Probabilité de profit: 52.4%

Long Straddle:
- Coût initial: 3.3306
- Ratio Risque/Rendement: 1.00
- Probabilité de profit: 55.8%

RECOMMANDATION: Long Straddle (meilleur ratio risque/rendement)
```

### Pricing des Options

Le système utilise le **modèle de Black-Scholes** avec :
- Taux sans risque dérivé des simulations Euribor
- Volatilité calibrée sur les données historiques
- Prix spot simulé pour l'actif sous-jacent
- Maturités configurables

### Extension du Système

Pour ajouter de nouvelles stratégies :

1. **Définir la structure** dans `create_strategy()`
2. **Implémenter le payoff** dans `calculate_payoff()`
3. **Ajouter les métriques** spécifiques
4. **Configurer l'affichage** des résultats

```python
def create_iron_condor():
    # Exemple d'extension
    return {
        'calls': [buy_call_itm, sell_call_atm, sell_put_atm, buy_put_otm],
        'description': 'Iron Condor - Profit sur faible volatilité'
    }
```

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

# Test d'analyse de stratégies
python trading_strategy_evaluation.py
```

## Fichiers Principaux

- **`src/main.py`** : Interface CLI principale
- **`src/fetch_data.py`** : Récupération données ECB API
- **`src/calibration.py`** : Calibration modèle Vasicek
- **`src/simulation.py`** : Simulation Monte Carlo
- **`src/visualize.py`** : Génération graphiques
- **`trading_strategy_evaluation.py`** : Analyse stratégies options
- **`generate_plots.py`** : Génération automatique visualisations
- **`interactive_plots.py`** : Graphiques interactifs

