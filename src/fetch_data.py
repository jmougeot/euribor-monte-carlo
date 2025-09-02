import io
import pandas as pd
import requests
import warnings
warnings.filterwarnings('ignore')

ECB_BASE = "https://sdw-wsrest.ecb.europa.eu/service/data"

# Série Euribor 3M via ECB Statistical Data Warehouse
CANDIDATE_SERIES = {
    "Euribor 3M (FM)": ("FM", "M.U2.EUR.RT.MM.EURIBOR3MD_.HSTA"),
    "Euribor 3M (MIR)": ("MIR", "M.B.U2.EUR.4F.KR.MRR_FR.LEV"),
}

HEADERS = {"Accept": "text/csv"}

def fetch_euribor(tenor="3M", last_n=600, timeout=15):
    """
    Récupère les données Euribor via l'API ECB SDW
    """
    errors = {}
    
    for label, (dataset, keypath) in CANDIDATE_SERIES.items():
        url = f"{ECB_BASE}/{dataset}/{keypath}?lastNObservations={last_n}"
        
        try:
            print(f"Tentative de récupération: {label}")
            r = requests.get(url, headers=HEADERS, timeout=timeout)
            
            if r.status_code != 200:
                errors[label] = f"HTTP {r.status_code}"
                continue
                
            df = pd.read_csv(io.StringIO(r.text))
            
            # Recherche des colonnes date et valeur
            date_col = None
            for col in df.columns:
                if col.lower() in ("time_period", "date", "time"):
                    date_col = col
                    break
                    
            val_col = None
            for col in df.columns:
                if col.upper() in ("OBS_VALUE", "VALUE", "RATE"):
                    val_col = col
                    break
            
            if not date_col or not val_col:
                errors[label] = f"Colonnes manquantes. Disponibles: {list(df.columns)}"
                continue
                
            # Nettoyage des données
            out = df[[date_col, val_col]].copy()
            out.columns = ["date", "rate"]
            out["date"] = pd.to_datetime(out["date"])
            out = out.sort_values("date").dropna()
            
            # Conversion en décimal si nécessaire
            if out["rate"].max() > 2:
                out["rate"] = out["rate"] / 100.0
                
            print(f"✓ Récupération réussie: {len(out)} observations")
            return out.reset_index(drop=True), {
                "source": "ECB_SDW", 
                "series_label": label, 
                "url": url,
                "last_date": str(out["date"].max().date()),
                "rate_range": f"{out['rate'].min():.4f} - {out['rate'].max():.4f}"
            }
            
        except Exception as e:
            errors[label] = str(e)
    
    raise RuntimeError(f"Échec récupération ECB pour toutes les séries. Détails: {errors}")

def load_with_fallback(tenor="3M", path_csv="data/sample_euribor3m.csv"):
    """
    Charge les données Euribor avec fallback sur fichier CSV local
    """
    try:
        df, meta = fetch_euribor(tenor=tenor)
        print(f"✓ Données API récupérées: {meta}")
        return df, meta
    except Exception as e:
        print(f"⚠ Échec API ECB: {e}")
        try:
            print(f"→ Utilisation du fallback CSV: {path_csv}")
            df = pd.read_csv(path_csv, parse_dates=["date"])
            df = df.sort_values("date").dropna()
            print(f"✓ Données CSV chargées: {len(df)} observations")
            return df, {
                "source": "fallback_csv", 
                "error_api": str(e),
                "last_date": str(df["date"].max().date())
            }
        except Exception as e2:
            raise RuntimeError(f"Impossible de charger les données (API + CSV). API: {e}; CSV: {e2}")

if __name__ == "__main__":
    # Test du module
    try:
        data, meta = load_with_fallback()
        print(f"\nDonnées chargées:")
        print(data.head())
        print(f"\nMétadonnées: {meta}")
    except Exception as e:
        print(f"Erreur: {e}")
