import numpy as np
import pandas as pd
from dataclasses import dataclass
from scipy.optimize import minimize
import warnings
warnings.filterwarnings('ignore')

@dataclass
class VasicekParams:
    """Paramètres du modèle de Vasicek"""
    kappa: float  # vitesse de retour à la moyenne
    theta: float  # niveau de long terme
    sigma: float  # volatilité
    r0: float     # taux initial

    def __str__(self):
        return (f"VasicekParams(κ={self.kappa:.4f}, θ={self.theta:.4f}, "
                f"σ={self.sigma:.4f}, r0={self.r0:.4f})")

def calibrate_vasicek_ols(rates: pd.Series, dt=1/252):
    """
    Calibration Vasicek via régression AR(1):
    r_{t+1} = a + b * r_t + ε_t
    
    Mapping:
    kappa = -ln(b) / dt
    theta = a / (1 - b)  
    sigma = std(ε) * sqrt(2*kappa / (1 - b²))
    """
    r = rates.values
    x = r[:-1]  # r_t
    y = r[1:]   # r_{t+1}
    n = len(x)
    
    if n < 10:
        raise ValueError(f"Série trop courte pour calibrer: {n} observations")
    
    # Régression linéaire: y = a + b*x + ε
    X = np.column_stack([np.ones(n), x])
    try:
        beta = np.linalg.lstsq(X, y, rcond=None)[0]
        a, b = beta
    except np.linalg.LinAlgError:
        raise ValueError("Échec de la régression linéaire")
    
    # Contraintes sur b pour assurer stabilité
    if b <= 0 or b >= 1:
        b = max(0.001, min(0.999, b))
    
    # Calcul des paramètres Vasicek
    kappa = -np.log(b) / dt
    theta = a / (1 - b)
    
    # Estimation de sigma via résidus
    residuals = y - (a + b * x)
    sigma_hat = residuals.std(ddof=2)
    
    # Ajustement pour processus continu
    if kappa > 0:
        sigma = sigma_hat * np.sqrt(2 * kappa / (1 - b**2))
    else:
        sigma = sigma_hat / np.sqrt(dt)
    
    # Validation des paramètres
    if sigma <= 0:
        sigma = 0.01
    
    return VasicekParams(
        kappa=max(0.001, kappa),
        theta=theta, 
        sigma=sigma,
        r0=r[-1]
    )

def calibrate_vasicek_mle(rates: pd.Series, dt=1/252):
    """
    Calibration par maximum de vraisemblance (plus précise)
    """
    r = rates.values
    n = len(r)
    
    if n < 10:
        raise ValueError(f"Série trop courte: {n} observations")
    
    def neg_log_likelihood(params):
        kappa, theta, sigma = params
        if kappa <= 0 or sigma <= 0:
            return 1e10
            
        try:
            # Calculs pour la vraisemblance exacte du processus d'Ornstein-Uhlenbeck
            exp_kappa_dt = np.exp(-kappa * dt)
            var_r = sigma**2 * (1 - exp_kappa_dt**2) / (2 * kappa)
            
            if var_r <= 0:
                return 1e10
                
            log_lik = 0
            for i in range(1, n):
                mean_r = theta + (r[i-1] - theta) * exp_kappa_dt
                log_lik += -0.5 * np.log(2 * np.pi * var_r) - 0.5 * (r[i] - mean_r)**2 / var_r
                
            return -log_lik
            
        except (OverflowError, ZeroDivisionError):
            return 1e10
    
    # Estimation initiale via OLS
    try:
        initial_params = calibrate_vasicek_ols(rates, dt)
        x0 = [initial_params.kappa, initial_params.theta, initial_params.sigma]
    except:
        # Valeurs par défaut si OLS échoue
        x0 = [0.1, rates.mean(), rates.std()]
    
    # Optimisation
    bounds = [(0.001, 10), (rates.min() - 0.01, rates.max() + 0.01), (0.001, 1)]
    
    try:
        result = minimize(neg_log_likelihood, x0, bounds=bounds, method='L-BFGS-B')
        
        if result.success:
            kappa_opt, theta_opt, sigma_opt = result.x
            return VasicekParams(
                kappa=kappa_opt,
                theta=theta_opt,
                sigma=sigma_opt,
                r0=r[-1]
            )
        else:
            return calibrate_vasicek_ols(rates, dt)
            
    except Exception as e:
        return calibrate_vasicek_ols(rates, dt)

def estimate_model_quality(rates: pd.Series, params: VasicekParams, dt=1/252):
    """
    Évalue la qualité de l'ajustement du modèle
    """
    r = rates.values
    n = len(r)
    
    # Calcul des résidus standardisés
    exp_kappa_dt = np.exp(-params.kappa * dt)
    var_r = params.sigma**2 * (1 - exp_kappa_dt**2) / (2 * params.kappa)
    
    residuals = []
    for i in range(1, n):
        mean_r = params.theta + (r[i-1] - params.theta) * exp_kappa_dt
        residual = (r[i] - mean_r) / np.sqrt(var_r)
        residuals.append(residual)
    
    residuals = np.array(residuals)
    
    return {
        'rmse': np.sqrt(np.mean(residuals**2)),
        'mean_residual': np.mean(residuals),
        'residual_autocorr': np.corrcoef(residuals[:-1], residuals[1:])[0,1] if len(residuals) > 1 else 0,
        'ljung_box_pvalue': None  # Pourrait ajouter le test de Ljung-Box
    }

if __name__ == "__main__":
    # Test du module
    from fetch_data import load_with_fallback
    
    try:
        data, _ = load_with_fallback()
        
        # Test OLS
        params_ols = calibrate_vasicek_ols(data["rate"])
        
        # Test MLE  
        params_mle = calibrate_vasicek_mle(data["rate"])
        
        # Qualité
        quality = estimate_model_quality(data["rate"], params_mle)
        
    except Exception as e:
        pass
