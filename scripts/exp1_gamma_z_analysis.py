#!/usr/bin/env python
# coding: utf-8
"""
Experiment 1 — Metacognitive Sensitivity γ (Fisher-Z Analysis)
===============================================================
Goodman–Kruskal gamma (γ) is a rank-order association measure in [-1, 1]
between confidence ratings and recognition accuracy.

Fisher Z transform  z = arctanh(γ)  maps [-1, 1] → (-∞, +∞), stabilising
variance and improving normality for parametric tests.

Grouping level
--------------
In Exp 1 each trace × model × memory cell has exactly ONE trial, so gamma
cannot be computed at the trace level.  γ is therefore estimated at the
**model × memory** level (288 trials/cell, 144 per source).

Sample size note
----------------
12 groups (6 models × 2 memory conditions); 5 are NaN because accuracy has no
variance within those cells (floor/ceiling effects — perfect accuracy or always
wrong makes γ undefined).  All formal inference is therefore exploratory and
should be interpreted cautiously (n = 7).
"""

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pathlib
import sys

import rmllm
from rmllm import config, gamma as gamma_mod

data_dir  = config.PROCESSED_DATA_DIR
FIGURES   = config.REPORTS_DIR / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("EXP 1 — Metacognitive γ  (Fisher-Z transformed)")
print("=" * 70)

# ─────────────────────────────────────────────────────────────────────────────
# 1. Load data
# ─────────────────────────────────────────────────────────────────────────────
df = pd.read_csv(data_dir / "exp1_trial_data.csv")
for col in ["accuracy", "confidence"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

print(f"\nTrials: {len(df)}   Models: {df['model'].nunique()}"
      f"   Memory: {sorted(df['memory'].unique())}"
      f"   Sources: {sorted(df['source'].unique())}")

# ─────────────────────────────────────────────────────────────────────────────
# 2. Fisher-Z helper
# ─────────────────────────────────────────────────────────────────────────────
def fisher_z(g):
    """arctanh transform clipped to ±0.9999 to avoid ±inf at perfect γ."""
    return np.arctanh(np.clip(np.asarray(g, dtype=float), -0.9999, 0.9999))


# ─────────────────────────────────────────────────────────────────────────────
# 3. Compute γ and apply Fisher Z
# ─────────────────────────────────────────────────────────────────────────────

# 3a. Primary grouping: model × memory  (288 trials/cell)
g_mm = gamma_mod.calculate_gamma_across_groups(df, ["model", "memory"])
g_mm["gamma_z"] = fisher_z(g_mm["gamma"])

# 3b. Source-level grouping: model × memory × source (144 trials/cell)
g_mms = gamma_mod.calculate_gamma_across_groups(df, ["model", "memory", "source"])
g_mms["gamma_z"] = fisher_z(g_mms["gamma"])

print("\n── γ and γ_z by model × memory ─────────────────────────────────────────")
print(g_mm[["model", "memory", "gamma", "gamma_z", "n_trials"]].to_string(index=False))

print("\n── γ and γ_z by model × memory × source ────────────────────────────────")
print(g_mms[["model", "memory", "source", "gamma", "gamma_z"]].to_string(index=False))

valid_n = g_mm["gamma"].notna().sum()
nan_n   = g_mm["gamma"].isna().sum()
print(f"\nValid: {valid_n} / {len(g_mm)}  |  NaN: {nan_n}")
print("NaN conditions: Gemma3:27b (both), Gemma3:27b-QAT (both),"
      " Llama3.3:70b TrialChain")
print("Cause: constant accuracy within cell → γ undefined (no rank variation)")

# ─────────────────────────────────────────────────────────────────────────────
# 4. Formal statistical models  (n = 7 — exploratory)
# ─────────────────────────────────────────────────────────────────────────────
valid = g_mm.dropna(subset=["gamma_z"]).copy()
print(f"\n{'='*70}")
print(f"FORMAL MODELS  (n = {len(valid)} — highly exploratory)")
print(f"{'='*70}")

# ── 4a. Intercept-only: test H₀: mean γ_z = 0 ────────────────────────────────
m0 = smf.ols("gamma_z ~ 1", data=valid).fit()
t0, p0 = stats.ttest_1samp(valid["gamma_z"].dropna(), 0)

print(f"\n[M0] Intercept only  H₀: μ(γ_z) = 0")
print(f"  Mean γ_z = {valid['gamma_z'].mean():.4f}  "
      f"SD = {valid['gamma_z'].std():.4f}  n = {len(valid)}")
print(f"  One-sample t({len(valid)-1}) = {t0:.4f}   p = {p0:.4f}")

# ── 4b. Memory effect ─────────────────────────────────────────────────────────
m1 = smf.ols("gamma_z ~ C(memory, Treatment('SingleTurn'))", data=valid).fit()
st = valid.loc[valid["memory"] == "SingleTurn", "gamma_z"]
tc = valid.loc[valid["memory"] == "TrialChain",  "gamma_z"]

print(f"\n[M1] γ_z ~ memory")
print(f"  SingleTurn  n={len(st)}  mean={st.mean():.4f}  SD={st.std():.4f}")
print(f"  TrialChain  n={len(tc)}  mean={tc.mean():.4f}  SD={tc.std():.4f}")
print(m1.summary2().tables[1].to_string())

# LR test M1 vs M0
lr1   = 2 * (m1.llf - m0.llf)
p_lr1 = stats.chi2.sf(lr1, df=1)
print(f"\n  LR test (memory): χ²(1) = {lr1:.4f}   p = {p_lr1:.4f}")

# Non-parametric
mw_stat, mw_p = stats.mannwhitneyu(st, tc, alternative="two-sided")
print(f"  Mann-Whitney U (SingleTurn vs TrialChain): U = {mw_stat:.1f}   p = {mw_p:.4f}")

# ── 4c. Memory + model (parsimonious — only 2 model levels retained) ───────────
# With n=7 and 6 model levels, a full model is over-parameterised.
# Limit to models that have data in BOTH memory conditions (Gemma3:12b, 12b-QAT,
# Llama4:16x17b) — n=6 complete pairs.
complete_models = (
    valid.groupby("model")["memory"].nunique()
    .loc[lambda s: s == 2]
    .index.tolist()
)
paired = valid[valid["model"].isin(complete_models)].copy()
print(f"\n[M2] Paired subset (models with both memory conditions)  n = {len(paired)}")
if len(paired) >= 4:
    m2 = smf.ols("gamma_z ~ C(memory, Treatment('SingleTurn')) + C(model)",
                 data=paired).fit()
    print(m2.summary2().tables[1].to_string())
    lr2   = 2 * (m2.llf - smf.ols("gamma_z ~ 1", data=paired).fit().llf)
    p_lr2 = stats.chi2.sf(lr2, df=m2.df_model)
    print(f"\n  LR test (memory + model vs null): χ²({int(m2.df_model)}) = {lr2:.4f}  p = {p_lr2:.4f}")

# ── 4d. Source-level (perceived only) ─────────────────────────────────────────
valid_src = g_mms[(g_mms["source"] == "perceived") &
                   g_mms["gamma_z"].notna()].copy()
print(f"\n[M3] Perceived source only  n = {len(valid_src)}")
if len(valid_src) >= 3:
    m3 = smf.ols("gamma_z ~ C(memory, Treatment('SingleTurn'))", data=valid_src).fit()
    print(m3.summary2().tables[1].to_string())

# ─────────────────────────────────────────────────────────────────────────────
# 5. Summary table
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{'='*70}")
print("SUMMARY TABLE: γ and γ_z by condition")
print(f"{'='*70}")
summary = g_mms.pivot_table(
    index=["model", "memory"],
    columns="source",
    values=["gamma", "gamma_z"]
).round(4)
print(summary.to_string())

# ─────────────────────────────────────────────────────────────────────────────
# 6. Figure
# ─────────────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=False)
fig.suptitle("Exp 1 — Metacognitive γ: raw vs Fisher-Z", fontsize=12)

MODEL_ORDER = ["Gemma3:12b", "Gemma3:12b-QAT", "Gemma3:27b", "Gemma3:27b-QAT",
               "Llama4:16x17b", "Llama3.3:70b"]
PALETTE = {"SingleTurn": "#2196F3", "TrialChain": "#FF9800"}

for ax, col, title in zip(axes, ["gamma", "gamma_z"], ["γ (raw)", "γ_z (Fisher Z)"]):
    for mem, grp in g_mm.groupby("memory"):
        grp_ord = grp.set_index("model").reindex(MODEL_ORDER)
        x = range(len(MODEL_ORDER))
        ax.plot(x, grp_ord[col].values, "o-", label=mem,
                color=PALETTE[mem], linewidth=1.5, markersize=6)
    ax.axhline(0, color="grey", linewidth=0.8, linestyle="--")
    ax.set_xticks(range(len(MODEL_ORDER)))
    ax.set_xticklabels(MODEL_ORDER, rotation=35, ha="right", fontsize=8)
    ax.set_title(title)
    ax.set_ylabel(col)
    ax.legend(title="Memory", fontsize=8)

plt.tight_layout()
out_path = FIGURES / "exp1_gamma_z.png"
fig.savefig(out_path, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"\nFigure saved → {out_path.relative_to(config.PROJ_ROOT)}")

print("\nAnalysis complete.")
