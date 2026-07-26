"""Trace-level robustness check for the Exp 2 accuracy -> confidence null.

The manuscript's CLM (exp2_clm_confidence.R) is the one Exp 2 model without
a trace random effect (the CLMM would not converge; see Methods). Its
accuracy coefficient is borderline (b = 0.03, p = .063), so this script
re-tests the effect at the trace level, where observations are independent:

  For each trace (simulated participant), compute
      d = mean(confidence | correct) - mean(confidence | incorrect)
  and test d != 0 across traces (paired design; traces with invariant
  accuracy contribute no contrast and drop out, mirroring the gamma
  exclusions).

Run from project root:  python notebooks/04_exp2/exp2_confidence_trace_robustness.py
Output is also written to reports/logs/exp2_confidence_trace_robustness_out.txt
"""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "reports" / "logs" / "exp2_confidence_trace_robustness_out.txt"

lines = []


def log(msg=""):
    print(msg)
    lines.append(str(msg))


df = pd.read_csv(ROOT / "data" / "processed" / "exp2_trial_data.csv")
log(f"Loaded {len(df):,} test-phase trials")

# trace ids repeat across cells; build a globally unique trace key
df["trace_key"] = (
    df["model"].astype(str) + "|" + df["setsize"].astype(str) + "|"
    + df["fb_exp"].astype(str) + "|" + df["trace"].astype(str)
)
n_traces = df["trace_key"].nunique()
log(f"Unique traces: {n_traces:,}")

# per-trace mean confidence by accuracy
agg = (df.groupby(["trace_key", "model", "setsize", "fb_exp", "accuracy"])
         ["confidence"].mean().unstack("accuracy"))
agg.columns = ["conf_incorrect", "conf_correct"]
paired = agg.dropna()  # traces with both correct and incorrect trials
d = paired["conf_correct"] - paired["conf_incorrect"]

log()
log("=== Primary: paired trace-level test (correct - incorrect) ===")
log(f"Contributing traces: {len(paired):,} of {n_traces:,} "
    f"({n_traces - len(paired):,} invariant-accuracy traces drop out)")
t, p = stats.ttest_1samp(d, 0.0)
ci = stats.t.interval(0.95, len(d) - 1, loc=d.mean(), scale=stats.sem(d))
dz = d.mean() / d.std(ddof=1)
log(f"Mean within-trace difference = {d.mean():+.4f} confidence points "
    f"(95% CI [{ci[0]:+.4f}, {ci[1]:+.4f}])")
log(f"Paired t({len(d)-1}) = {t:.3f}, p = {p:.4g}; Cohen's dz = {dz:+.3f}")
w = stats.wilcoxon(d)
log(f"Wilcoxon signed-rank: W = {w.statistic:.1f}, p = {w.pvalue:.4g}")

log()
log("=== By feedback condition ===")
for fb, grp in d.groupby(paired.index.get_level_values(0).map(
        paired.reset_index().set_index("trace_key")["fb_exp"])):
    t_c, p_c = stats.ttest_1samp(grp, 0.0)
    log(f"feedback={fb!s:5}  n={len(grp):5,}  mean d={grp.mean():+.4f}  "
        f"t={t_c:+.3f}  p={p_c:.4g}")

log()
log("=== By model (descriptive) ===")
md = paired.reset_index()
md["d"] = md["conf_correct"] - md["conf_incorrect"]
for model, grp in md.groupby("model"):
    t_c, p_c = stats.ttest_1samp(grp["d"], 0.0)
    log(f"{model:15s}  n={len(grp):5,}  mean d={grp['d'].mean():+.4f}  p={p_c:.4g}")

OUT.write_text("\n".join(lines) + "\n")
print(f"\nSaved -> {OUT.relative_to(ROOT)}")
