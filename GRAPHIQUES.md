# 📊 Guide des Graphiques - Simulation Monte Carlo Euribor

Ce guide explique comment générer et interpréter les graphiques de la simulation.

## 🎨 Génération des Graphiques

### Option 1: Graphiques sauvegardés (recommandé)
```bash
# Activer l'environnement
source .venv/bin/activate

# Générer tous les graphiques PNG
python generate_plots.py
```

**Fichiers générés:**
- `euribor_data_overview.png` - Aperçu des données historiques (425 KB)
- `euribor_simulation_results.png` - Dashboard complet (1.6 MB) 
- `euribor_sample_paths.png` - Trajectoires échantillon (1.0 MB)
- `euribor_terminal_distribution.png` - Distribution terminale (126 KB)

### Option 2: Graphiques interactifs (si interface graphique disponible)
```bash
source .venv/bin/activate
python interactive_plots.py
```

### Option 3: Via le module principal avec visualisation
```bash
source .venv/bin/activate
PYTHONPATH=src python -c "
from visualize import *
from fetch_data import load_with_fallback
from calibration import calibrate_vasicek_mle
from simulation import run_monte_carlo_simulation

data, _ = load_with_fallback()
params = calibrate_vasicek_mle(data['rate'])
paths, stats = run_monte_carlo_simulation(params, horizon=252, n_paths=1000)

# Sauvegarder les graphiques
plot_data_overview(data, 'custom_data.png')
plot_simulation_results(paths, stats, params, 'custom_simulation.png')
"
```

## 📈 Description des Graphiques

### 1. Aperçu des Données Historiques (`euribor_data_overview.png`)

**Contenu:**
- **Évolution temporelle**: Série chronologique Euribor 3M (1994-2025)
- **Distribution**: Histogramme des taux observés
- **Variations quotidiennes**: Δ taux jour par jour
- **Statistiques descriptives**: Tableau récapitulatif

**Interprétation:**
- Tendances historiques et cycles économiques
- Volatilité et amplitude des variations
- Périodes de taux négatifs (2015-2022)

### 2. Résultats de Simulation (`euribor_simulation_results.png`)

**Dashboard 2x2 avec:**

**Top-Left: Trajectoires simulées**
- 30 trajectoires échantillon (lignes colorées)
- Moyenne des trajectoires (ligne rouge)
- Intervalle de confiance 90% (zone rouge)

**Top-Right: Distribution terminale**
- Histogramme des taux finaux (après 1 an)
- Moyenne simulée vs théorique
- Percentiles P5 et P95

**Bottom-Left: Évolution des percentiles**
- P5, P25, P50, P75, P95 au cours du temps
- Visualisation de la dispersion temporelle

**Bottom-Right: Statistiques**
- Paramètres du modèle Vasicek
- Statistiques terminales
- Métriques de validation

### 3. Trajectoires Échantillon (`euribor_sample_paths.png`)

**Contenu:**
- 10 trajectoires individuelles
- Moyenne des trajectoires (rouge épaisse)
- Axes: temps (jours ouvrés) vs taux

**Usage:**
- Comprendre la dynamique individuelle
- Visualiser la convergence vers la moyenne long terme
- Observer la variabilité entre scénarios

### 4. Distribution Terminale (`euribor_terminal_distribution.png`)

**Contenu:**
- Histogramme des taux après 1 an
- Ligne verticale: moyenne
- Lignes pointillées: P5 et P95
- Densité de probabilité

**Métriques importantes:**
- Probabilité de taux négatifs
- Asymétrie de la distribution
- Queue de distribution (risques extrêmes)

## 🔧 Personnalisation

### Modifier les paramètres de simulation
```python
# Dans generate_plots.py, ligne ~45:
paths, stats = run_monte_carlo_simulation(
    params, 
    horizon=504,      # 2 ans au lieu de 1
    n_paths=5000,     # Plus de trajectoires
    seed=123,         # Graine différente
    method="euler"    # Méthode alternative
)
```

### Ajuster la qualité des graphiques
```python
# Résolution plus élevée
plt.savefig('mon_graphique.png', dpi=600, bbox_inches='tight')

# Format vectoriel
plt.savefig('mon_graphique.pdf', bbox_inches='tight')
```

### Changer les couleurs et styles
```python
# Dans generate_plots.py
plt.style.use('seaborn-darkgrid')  # Style différent
sns.set_palette("viridis")         # Palette couleurs
```

## 📊 Interprétation des Résultats

### Exemple de résultats typiques:
```
Taux terminal moyen: 0.0093 (0.93%)
Intervalle 90%: [-0.0100, 0.0295] (-1.00% à 2.95%)
Probabilité taux négatifs: 64.2%
```

**Signification:**
- Le modèle prédit une convergence vers 0.93% en moyenne
- 90% des scénarios donnent un taux entre -1% et +2.95%
- 64% de probabilité de taux négatifs (cohérent avec l'historique récent)

### Paramètres du modèle:
```
κ=2.2526 → Retour rapide à la moyenne (2.25 par an)
θ=0.0080 → Niveau long terme à 0.8%
σ=0.0254 → Volatilité annuelle de 2.54%
```

## ⚠️ Limitations

1. **Modèle Vasicek**: Peut générer des taux négatifs (réaliste mais limité)
2. **Calibration**: Basée sur données historiques (peut changer)
3. **Hypothèses**: Paramètres constants (irréaliste sur long terme)

## 🛠️ Dépannage

### Erreur "no display"
```bash
# Utiliser le backend Agg
export MPLBACKEND=Agg
python generate_plots.py
```

### Qualité d'image faible
```bash
# Vérifier la résolution dans le code
grep -n "dpi=" generate_plots.py
# Devrait afficher: dpi=300
```

### Graphiques vides
```bash
# Vérifier que matplotlib utilise le bon backend
python -c "import matplotlib; print(matplotlib.get_backend())"
```

## 📚 Références

- [Matplotlib Gallery](https://matplotlib.org/stable/gallery/)
- [Seaborn Tutorial](https://seaborn.pydata.org/tutorial.html)
- [Vasicek Model Theory](https://en.wikipedia.org/wiki/Vasicek_model)
