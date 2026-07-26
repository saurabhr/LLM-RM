import pandas as pd
import numpy as np


def goodman_kruskal_gamma(acc, conf):
    """Calculates Goodman and Kruskal's gamma for ordinal association."""
    mask = ~(np.isnan(acc) | np.isnan(conf))
    acc = np.asarray(acc)[mask]
    conf = np.asarray(conf)[mask]

    n = len(acc)
    if n < 2:
        return np.nan

    concordant = 0
    discordant = 0
    for i in range(n):
        diff_acc = acc[i] - acc[i + 1 :]
        diff_conf = conf[i] - conf[i + 1 :]
        concordant += np.sum((diff_acc * diff_conf) > 0)
        discordant += np.sum((diff_acc * diff_conf) < 0)

    total_pairs = concordant + discordant
    if total_pairs == 0:
        return np.nan
    return (concordant - discordant) / total_pairs


def calculate_gamma_across_groups(df, group_cols, acc_col="accuracy", conf_col=None):
    """
    Groups the dataframe and calculates Gamma for each group.

    conf_col defaults to 'confidence_num' if present, else 'confidence'.
    """
    df = df.copy()

    # Resolve conf_col
    if conf_col is None:
        conf_col = "confidence_num" if "confidence_num" in df.columns else "confidence"

    df[acc_col] = pd.to_numeric(df[acc_col], errors="coerce")
    df[conf_col] = pd.to_numeric(df[conf_col], errors="coerce")

    results = (
        df.groupby(group_cols, observed=True)
        .apply(
            lambda x: pd.Series(
                {
                    "gamma": goodman_kruskal_gamma(
                        x[acc_col].to_numpy(), x[conf_col].to_numpy()
                    ),
                    "n_trials": len(x),
                    "valid_pairs": (~(x[acc_col].isna() | x[conf_col].isna())).sum(),
                }
            )
        )
        .reset_index()
    )
    return results
