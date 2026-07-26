#!/usr/bin/env bash
# =============================================================================
# setup_analysis_env.sh
# Creates a uv virtual environment for the pymer4 / mixed-model analysis.
#
# Usage (from the rmllm root):
#   bash setup_analysis_env.sh
#
# After setup, activate with:
#   source .venv_analysis/bin/activate
# Or run the notebook directly with:
#   uv run --python .venv_analysis/bin/python jupyter lab
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv_analysis"
PYTHON_VERSION="3.11"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   rmllm  ·  analysis environment setup                  ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# ── 0. Prerequisites ──────────────────────────────────────────────────────────
for cmd in uv R Rscript; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "ERROR: '$cmd' not found on PATH."
        [[ "$cmd" == "R" || "$cmd" == "Rscript" ]] && \
            echo "       Install R from https://cran.r-project.org/ and re-run."
        exit 1
    fi
done
echo "✓  uv $(uv --version 2>&1 | head -1)"
echo "✓  R  $(R --version | head -1)"
echo ""

# ── 1. Create virtual environment ─────────────────────────────────────────────
echo "── Step 1: Creating uv venv (Python $PYTHON_VERSION) ──"
uv venv "$VENV_DIR" --python "$PYTHON_VERSION"
echo "   venv: $VENV_DIR"
echo ""

# ── 2. Install Python packages ────────────────────────────────────────────────
echo "── Step 2: Installing Python packages ──"
# Install the rmllm package in editable mode plus the [analysis] extras
uv pip install --python "$VENV_DIR/bin/python" -e "$SCRIPT_DIR[analysis]"
echo ""

# ── 3. Register Jupyter kernel ────────────────────────────────────────────────
echo "── Step 3: Registering Jupyter kernel as 'pymer4' ──"
"$VENV_DIR/bin/python" -m ipykernel install \
    --user \
    --name pymer4 \
    --display-name "Python (pymer4)" \
    --env R_HOME "$(R RHOME)"
echo "   Kernel registered."
echo ""

# ── 4. Install R packages ─────────────────────────────────────────────────────
echo "── Step 4: Installing R packages ──"
Rscript "$SCRIPT_DIR/install_r_packages.R"
echo ""

# ── 5. Smoke-test ─────────────────────────────────────────────────────────────
echo "── Step 5: Smoke-test ──"
"$VENV_DIR/bin/python" - <<'PYEOF'
import sys
print(f"   Python {sys.version.split()[0]}")

ok = True
for pkg in ["pymer4", "rpy2", "polars", "pandas", "numpy",
            "matplotlib", "seaborn", "scipy", "statsmodels"]:
    try:
        mod = __import__(pkg)
        ver = getattr(mod, "__version__", "?")
        print(f"   ✓  {pkg} {ver}")
    except ImportError as e:
        print(f"   ✗  {pkg}  — {e}")
        ok = False

# Quick pymer4 version check
try:
    import pymer4
    from packaging.version import Version
    if Version(pymer4.__version__) < Version("0.9.0"):
        print(f"   ⚠  pymer4 {pymer4.__version__} < 0.9.0 — API mismatch, reinstall")
        ok = False
    else:
        print(f"   ✓  pymer4 API ≥ 0.9  (lmer/glmer/compare)")
except Exception as e:
    print(f"   [pymer4 version check: {e}]")

if ok:
    print("\n   All checks passed.")
else:
    print("\n   One or more packages failed — review output above.")
    sys.exit(1)
PYEOF

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   Setup complete!                                        ║"
echo "║                                                          ║"
echo "║   Activate:  source .venv_analysis/bin/activate         ║"
echo "║   JupyterLab: jupyter lab  (uses 'pymer4' kernel)       ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
