#!/usr/bin/env bash
# Run exp2_analysis_v3.ipynb and compare key outputs against reference log.
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export ROOT
VENV="$ROOT/.venv"
PYTHON="$VENV/bin/python3.11"
NB="$ROOT/notebooks/04_exp2/exp2_analysis_v3.ipynb"
EXECUTED_NB="$ROOT/notebooks/04_exp2/exp2_analysis_v3_executed.ipynb"
NB_OUT="$ROOT/reports/logs/exp2_v3_nb_out.txt"
REF_OUT="$ROOT/reports/logs/exp2_v3_fixed_out.txt"
COMPARE_OUT="$ROOT/reports/logs/exp2_v3_comparison.txt"

echo "=== Starting notebook execution: $(date) ===" | tee "$NB_OUT"

# Execute notebook (timeout = 7200s = 2 hours)
"$VENV/bin/jupyter" nbconvert \
    --to notebook \
    --execute \
    --ExecutePreprocessor.timeout=7200 \
    --ExecutePreprocessor.kernel_name=python3 \
    --output "$EXECUTED_NB" \
    "$NB" 2>&1 | tee -a "$NB_OUT"

echo "" | tee -a "$NB_OUT"
echo "=== Notebook execution complete: $(date) ===" | tee -a "$NB_OUT"

# Extract text outputs from the executed notebook
"$PYTHON" - << 'PYEOF' | tee -a "$NB_OUT"
import json, os, pathlib

nb_path = pathlib.Path(os.environ["ROOT"]) / "notebooks/04_exp2/exp2_analysis_v3_executed.ipynb"
nb = json.loads(nb_path.read_text())

print("\n=== EXTRACTED TEXT OUTPUTS ===\n")
for cell in nb["cells"]:
    if cell["cell_type"] != "code":
        continue
    for out in cell.get("outputs", []):
        if out.get("output_type") in ("stream", "execute_result", "display_data"):
            text = out.get("text", "") or "".join(out.get("data", {}).get("text/plain", []))
            if isinstance(text, list):
                text = "".join(text)
            if text.strip():
                print(text, end="" if text.endswith("\n") else "\n")
PYEOF

echo "" | tee -a "$NB_OUT"
echo "=== Output extraction complete ===" | tee -a "$NB_OUT"

# Compare key numerical results against reference
"$PYTHON" - << 'PYEOF' 2>&1 | tee "$COMPARE_OUT"
import re, os, pathlib

_root = pathlib.Path(os.environ["ROOT"])
REF  = (_root / "reports/logs/exp2_v3_fixed_out.txt").read_text()
NB_OUT_PATH = (_root / "reports/logs/exp2_v3_nb_out.txt").read_text()

print("=" * 60)
print("COMPARISON: notebook vs reference (exp2_analysis_v3_fixed.py)")
print("=" * 60)

# Key patterns to extract and compare
patterns = [
    ("Data shape",          r"All trials\s+:\s+[\d,]+\s+Traces:\s+[\d,]+"),
    ("RH rate",             r"Perceived\s+:\s+[\d,]+\s+\(RH rate:\s+[\d.]+\)"),
    ("rating_cen stats",    r"rating_cen: mean=[\d.]+\s+sd=[\d.]+"),
    ("Analysis complete",   r"Analysis complete\."),
    ("Figure saved",        r"Figure saved\."),
    ("OLS R²",              r"R²=[\d.]+\s+Adj-R²=[\d.]+\s+n=\d+"),
    ("Null→Add RH",         r"Null → Additive.*?p=[\d.e+-]+.*?(?:\*+|$)"),
    ("Add→Int RH",          r"Additive → Interactive.*?p=[\d.e+-]+.*?(?:\*+|$)"),
]

all_match = True
for name, pat in patterns:
    ref_m  = re.search(pat, REF,     re.MULTILINE)
    nb_m   = re.search(pat, NB_OUT_PATH, re.MULTILINE)
    ref_v  = ref_m.group(0).strip()  if ref_m  else "NOT FOUND"
    nb_v   = nb_m.group(0).strip()   if nb_m   else "NOT FOUND"
    match  = ref_v == nb_v
    if not match:
        all_match = False
    icon = "✓" if match else "△"
    print(f"\n{icon} {name}")
    print(f"  REF: {ref_v[:100]}")
    print(f"  NB:  {nb_v[:100]}")

print("\n" + "=" * 60)
print("OVERALL:", "✓ ALL MATCH" if all_match else "△ SOME DIFFERENCES (check above)")
print("=" * 60)
PYEOF

echo "=== Comparison saved to $COMPARE_OUT ==="
