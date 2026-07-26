# notebooks

Two environments are needed depending on which notebook you're running — most only need the base `rmllm` install, a few need R + `pymer4`/`rpy2`.

## Inputs & outputs per stage

| Stage | Reads | Writes |
|---|---|---|
| `01_task_gen/` | `data/raw/prepare_task/*.json` (task base + instruction templates) | task JSONs to `data/raw/gen_task/` (see note below) |
| `02_data_prep/` | `data/external/...` (curated, manually-downloaded HPC results) | `data/processed/*.csv` (trial- and group-level data) |
| `03_exp1/`, `04_exp2/` | `data/processed/*.csv` | `reports/figures/...` (manuscript + supplemental figures), some also print/inline stats tables |

**Note:** as of this writing, `01_task_gen/`'s notebooks save to `data/raw/gen_task/`, but the simulation runners (`simulation/run_rm_task_*.py`) read task JSONs from `data/raw/rm_tasks/`. Regenerating a task currently means manually copying the new JSON from `gen_task/` into `rm_tasks/` afterward — this isn't automated by any script here.

## Pipeline order

1. **`01_task_gen/`** — generate the RM task JSONs (`make_rm_tasks_exp1.ipynb`, `make_rm_tasks_exp2_fb.ipynb`, `make_rm_tasks_exp2_nofb.ipynb`). Imports `psychscanner` — needs the `simulation` extra (see below).
2. **`02_data_prep/`** — wrangle raw simulation output into `data/processed/*.csv`. Base env only.
3. **`03_exp1/`**, **`04_exp2/`** — per-experiment analysis and manuscript figures, run in that order within each folder:
   - `*_sdt_analysis.ipynb`, `*_manuscript_figures.ipynb`, `exp2_analysis_v3.ipynb`* — base env.
   - `exp1_random_effects.ipynb`, `exp2_random_effects.ipynb` — mixed-models via `pymer4`/`rpy2`, needs R + the `analysis` extra.

   \* `exp2_analysis_v3.ipynb` also imports `pymer4`/`rpy2` for one section — use the analysis env for it too.
4. **`_executed.ipynb`** files (e.g. `exp1_sdt_analysis_executed.ipynb`) are pre-run copies with output baked in, used as a reference/diff target — regenerate with `jupyter nbconvert --execute`, don't hand-edit.
5. `notebooks/statsmodels/statsmodels.Rproj` is just an RStudio project file, not a notebook.
6. `_make_sdt_notebooks.py` is deprecated (see its header) — safe to ignore.

## Base env (`02_data_prep`, most of `03_exp1`/`04_exp2`)

Run these from the **`osf/` workspace root**, not from inside `LLM-RM/` — `LLM-RM/` is a workspace member, and `uv sync` run from inside it scopes to `rmllm` alone and silently uninstalls the sibling `psychscanner` package (and its `langchain`/`pydantic` deps) from the shared `.venv`.

```sh
uv sync
uv run jupyter lab
```

For `01_task_gen/` (needs `psychscanner`, via `rmllm`'s `simulation` extra):

```sh
uv sync --package rmllm --extra simulation
uv run jupyter lab
```

(`uv sync --extra simulation` alone, without `--package rmllm`, errors — the workspace root project doesn't define that extra itself.)

## Analysis env (`*_random_effects.ipynb`, `exp2_analysis_v3.ipynb`)

Needs R installed (https://cran.r-project.org/) first. One-time setup, from `LLM-RM/`:

```sh
bash scripts/setup_analysis_env.sh
```

This builds a standalone `.venv_analysis`, installs the `analysis` extra (`pymer4`, `rpy2`, `pingouin`) plus the R packages via `scripts/install_r_packages.R`, and registers a `Python (pymer4)` Jupyter kernel. Then either:

```sh
source .venv_analysis/bin/activate && jupyter lab
```

or launch `jupyter lab` from the base env and pick the **Python (pymer4)** kernel for these notebooks.
