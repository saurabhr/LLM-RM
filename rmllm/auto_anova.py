import statsmodels.formula.api as smf
import pandas as pd
from statsmodels.stats.anova import anova_lm
from statsmodels.miscmodels.ordinal_model import OrderedModel
from scipy.stats import chi2
from IPython.display import display, Markdown

def auto_anova_like(model, data, formula, model_name="", distr=None, typ=2):
    """
    Automatic ANOVA-like table for OLS, Logit, and OrderedModel.
    
    - OLS          → Uses proper Type II ANOVA (F-tests)
    - Logit        → Uses Likelihood Ratio tests
    - OrderedModel → Uses Likelihood Ratio tests
    """
    print(f"\n{'='*75}")
    print(f"AUTO ANOVA-LIKE RESULTS — {model_name.upper()}")
    print(f"{'='*75}")
    
    # === 1. OLS Model ===
    if isinstance(model, smf.ols.__class__) or hasattr(model, 'mse_resid'):
        print("Detected: OLS model → Using Type II ANOVA")
        anova_table = anova_lm(model, typ=typ)
        display(Markdown(f"**{model_name} — Type II ANOVA Table**"))
        display(anova_table.round(4).style.set_properties(**{'text-align': 'right'}))
        return anova_table
    
    # === 2. Logit or OrderedModel ===
    else:
        print("Detected: Logit / GLM / Ordinal model → Using Likelihood Ratio Tests")
        results = []
        
        dep_var, rhs = [x.strip() for x in formula.split('~')]
        terms = [t.strip() for t in rhs.split('+') if t.strip()]
        
        for term in terms:
            reduced_terms = [t for t in terms if t != term]
            reduced_formula = f"{dep_var} ~ " + " + ".join(reduced_terms)
            
            try:
                if isinstance(model, OrderedModel) or distr is not None:
                    # Ordinal model
                    reduced_fit = OrderedModel.from_formula(
                        reduced_formula, data=data, distr=distr
                    ).fit(method='bfgs', disp=False, maxiter=100)
                else:
                    # Logit model
                    reduced_fit = smf.logit(reduced_formula, data=data).fit_regularized(
                        alpha=1.0, L1_wt=0.0, disp=False
                    )
                
                # LR test
                lr_stat = 2 * (model.llf - reduced_fit.llf)
                df_diff = model.df_model - reduced_fit.df_model
                p_value = 1 - chi2.cdf(lr_stat, df_diff)
                sig = '***' if p_value < 0.001 else '**' if p_value < 0.01 else '*' if p_value < 0.05 else ''
                
                results.append({
                    'Term': term,
                    'LR Statistic': round(lr_stat, 3),
                    'df_diff': int(df_diff),
                    'p-value': round(p_value, 4),
                    'Significance': sig
                })
                
            except Exception as e:
                print(f"⚠️ Skipping '{term}': {str(e)[:60]}...")
        
        # Overall model test
        if hasattr(model, 'llnull') and model.llnull is not None:
            overall_lr = 2 * (model.llf - model.llnull)
            overall_p = 1 - chi2.cdf(overall_lr, model.df_model)
            print(f"\nOverall model significance (vs null): LR = {overall_lr:.3f}, p = {overall_p:.2e}")
        
        df_results = pd.DataFrame(results)
        display(Markdown(f"**{model_name} — Likelihood Ratio Tests**"))
        display(df_results.style.hide(axis='index'))
        
        return df_results