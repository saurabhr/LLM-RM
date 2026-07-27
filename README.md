# LLM-RM

This package is installable with `uv` and is intended to be published separately.

Archived version of [psychscanner](https://github.com/saurabhr/psychscanner) 0.1.0 can be found here: https://github.com/saurabhr/psyschscanner_v_0_1_0

## Create the package virtual environment

From the package root:

```sh
uv sync
```

This creates `.venv` (Python 3.11.14, pinned via `.python-version`), resolves `uv.lock`, and installs the package editably in one step. `uv venv` does not seed `pip` into the venv, so avoid `python -m pip install` here — use `uv sync` or `uv pip install` instead.

Keep this README and `uv.lock` for package distribution. Do not include a nested `.venv` folder when publishing.

## Directory layout

```
LLM-RM/
├── pyproject.toml                    # package metadata: dependencies + `simulation`/`analysis` extras
├── uv.lock                           # pinned dependency versions, resolved by `uv sync`
├── LICENSE                           # MIT
├── Makefile                          # `make requirements` / `make clean` / `make lint`
├── rmllm/                            # installable package: stats/analysis helpers + shared config
│   ├── __init__.py                   #   loads config on import
│   ├── config.py                     #   paths (e.g. INTERIM_DATA_DIR) and env loading, imported by everything else
│   ├── gamma.py                      #   Goodman-Kruskal gamma (accuracy/confidence association)
│   ├── auto_anova.py                 #   automated ANOVA / ordinal-model model selection
│   └── utils/                        #   apa.py — APA-style table/figure formatting helpers
├── simulation/                       # HPC (SLURM) simulation runs
│   ├── setup_env.sh                   #   one-time env setup, shared by local + HPC job scripts
│   ├── setup_env.local.sh             #   gitignored, machine-specific copy (fills in psychscanner path)
│   ├── hpg_job_rm.sh                  #   SLURM job: episodic no-feedback task
│   ├── hpg_job_rm_with_fb.sh          #   SLURM job: episodic with-feedback task
│   ├── run_rm_task_*.py               #   task runners: episodic fb / episodic no-fb / single-turn trial chain
│   ├── rm_msg_injection.py            #   shared message-injection logic used by the task runners
│   ├── llmmodels_test_remote.txt      #   model list for HPC runs
│   ├── taskrmllm_*.txt                #   task lists consumed by the runners
│   └── local/                         #   self-contained copy of the above for running on this laptop (local_job_rm*.sh, its own run_rm_task_*.py, llmmodels_test_local.txt)
├── data/                             #   Available upon publication on OSF.
│   ├── raw/                          #   source task/persona defs: persona_data/, prepare_task/, rm_tasks/, gen_task/
│   ├── interim/                      #   scratch output psychscanner writes to during a run; safe to wipe (sim_data_hpc/ for HPC, local/ for local)
│   ├── processed/                    #   cleaned/wrangled CSVs consumed by the analysis notebooks (exp1_*.csv, exp2_*.csv)
│   └── external/                     #   curated, permanent results manually downloaded from HPC (exp2/, exp_2_r/, rm_2op*/)
├── notebooks/
│   ├── README.md                     #   which conda/uv env each notebook needs + pipeline run order
│   ├── 01_task_gen/                  #   notebooks that generate the RM task sets (exp1, exp2 fb/no-fb)
│   ├── 02_data_prep/                 #   wrangle raw sim output into processed/ CSVs (exp1, exp2, exp2_r)
│   ├── 03_exp1/                      #   experiment 1 analysis, SDT, random effects, manuscript figures
│   ├── 04_exp2/                      #   experiment 2 analysis, SDT, random effects, manuscript figures
│   ├── statsmodels/                  #   R project scratch space for statsmodels comparisons
│   └── _make_sdt_notebooks.py        #   deprecated generator; SDT notebooks are now maintained in place
├── scripts/
│   ├── exp1_gamma_z_analysis.py      #   standalone gamma/z-score analysis for exp1
│   ├── generate_task_description.py  #   builds task description text from task JSONs
│   ├── install_r_packages.R          #   installs R deps for the `analysis` extra
│   ├── run_and_compare_notebook.sh   #   re-executes a notebook and diffs against a prior run
│   └── setup_analysis_env.sh         #   one-time setup for the R-backed analysis extra
├── reports/
│   ├── figures/                      #   generated plots: manuscript/ (Fig1-FigS11), supplemental/, loose diagnostic *.png
│   └── logs/                         #   captured stdout from R/Python analysis runs
└── tests/
    └── test_apa_formatting.py        #   unit tests for rmllm/utils/apa.py
```

`psyscan/` (the simulation venv, built by `setup_env.sh`) and `.venv`/`.venv_analysis` (built by `uv sync` / `setup_analysis_env.sh`) are generated at setup time and intentionally left out of this tree — see "Simulations: one-time environment setup" and the notebooks `analysis` env section below.

## Optional extras

- `analysis` — mixed-models stack (`pymer4`, `rpy2`, `pingouin`) needed for the exp1/exp2 R-backed analyses.
- `simulation` — `psychscanner`, `langchain-core`, `pydantic`, needed to run the scripts in `simulation/` (`run_rm_task_*.py`).

```sh
uv sync --extra simulation      # or --extra analysis, or --all-extras
```

## Quickstart: run one simulation locally

With `ollama serve` already running, one-time setup then a single task+model run:

```sh
bash simulation/setup_env.sh   # one-time: builds the psyscan venv (see "Simulations: one-time environment setup" below)

cd simulation/local
source ../../psyscan/bin/activate
python run_rm_task_episodic_no_fb.py --taskjson rm_2op_convo.json --modelname gemma3:12b-it-qat --familyname ollama --nsim 2
```

`psyscan/` is a real venv directory inside the project — no symlink indirection.

This pulls no model itself (`ollama pull gemma3:12b-it-qat` first if you don't already have it), runs 2 simulated participants through the `rm_2op_convo.json` task, and writes output to `data/interim/local/rm_2op_convo/...` — one `.psyscan` file per participant, each a full trial-by-trial record. `--nsim` defaults to 100; pass a small number like this for a quick smoke test before committing to a full run.

To instead run the *full* production sweep (every task in a list, every model in a list, looped), use the job scripts directly:

```sh
bash simulation/local/local_job_rm.sh            # episodic, no feedback (default; edit the script to switch task lists)
bash simulation/local/local_job_rm_with_fb.sh    # episodic, with feedback
```

See "Job scripts" in `simulation/local/README.md` for what each one runs, and `simulation/README.md` for the HPC (SLURM) equivalent.

## Simulations layout

- `simulation/` — `setup_env*.sh` (shared environment setup, see below), HPC (SLURM) job scripts (`hpg_job_rm*.sh`), and the `run_rm_task_*.py` / `rm_msg_injection.py` / task+model `.txt` files the HPC scripts use.
- `simulation/local/` — a **self-contained** copy of everything else needed to run locally: `local_job_rm*.sh`, its own copies of `run_rm_task_*.py` and `rm_msg_injection.py`, and its own task/model `.txt` files. This means the two flavors (local vs. HPC) can diverge — e.g. patch a bug in `simulation/local/run_rm_task_episodic_no_fb.py` — without touching the HPC copy, and vice versa.

  `simulation/local/` job scripts activate the same `psyscan/` venv as the HPC scripts, at the same relative path.

**Output directories are deliberately kept separate.** `llmmodels_test_local.txt` and `llmmodels_test_remote.txt` both include `gemma3:12b-it-qat`/`gemma3:27b-it-qat`, and all `run_rm_task_*.py` scripts resolve output paths via `rmllm.config.INTERIM_DATA_DIR` — an absolute path independent of which copy of the script runs it. If both copies used the same output segment, a local run of an overlapping model+task would land in the exact same tunnel file as an HPC run and **resume into it** (`psychscanner`'s tunnel logic picks up from the last logged index — see `scanner_model.py`), silently mixing local test data into real experiment output. To prevent that, `simulation/local/run_rm_task_*.py` write to `data/interim/local/...` while `simulation/run_rm_task_*.py` (HPC) write to `data/interim/sim_data_hpc/...` — a different top-level folder (`local` vs `sim_data_hpc`). Keep this top-level folder name different if you fork either copy further.

## Data flow: interim vs. external

- **`data/interim/`** is scratch space psychscanner writes to directly during a run (`sim_data_hpc/<task>/<projectname>/<task>/ollama_<model>_<memory>/` for HPC, `local/<task>/<projectname>/<task>/ollama_<model>_<memory>/` for local). Safe to wipe/regenerate; it's per-machine and never manually curated.
  - Local runs (`simulation/local/`) write here directly, on this laptop, under `local/`.
  - HPC runs (`simulation/hpg_job_rm*.sh`) write here too, but on the **cluster's own filesystem** (`<YOUR_LLM_RM_DIR>` on HPC, a separate checkout from this OneDrive folder), directly under `sim_data_hpc`. It never touches this machine's `data/interim` directly.
- **`data/external/`** is where finished HPC results get manually downloaded and reorganized into a curated, permanent structure (e.g. `exp2/10t_fb_100/ollama_gemma3_12b_Convo/`, often alongside a `.zip`) — this is a manual step after an HPC run completes, not something any script here automates.

Because HPC's `data/interim` lives on a different machine and its results only ever land in `data/external` on this laptop (never merged back into local `data/interim`), local and HPC output stay isolated even with overlapping model names — the `local` / `sim_data_hpc` top-level split is an extra safety net for the case where an HPC checkout gets copied here before being archived into `data/external`.

## Simulations: one-time environment setup

Before running any script in `simulation/local/` (`local_job_rm*.sh`) or `simulation/` (`hpg_job_rm*.sh`), run `simulation/setup_env.sh` once. It installs `uv` via conda if not already on the system, then runs `uv sync --extra simulation` with `UV_PROJECT_ENVIRONMENT` set to the absolute path of `psyscan` within this project, so the venv directory is named `psyscan` and lives directly inside the `LLM-RM` folder instead of uv's default `.venv` or the workspace root. `setup_env*.sh` lives at `simulation/` (not nested under `local/`) because both flavors' job scripts are meant to share this one setup mechanism.

**Known tradeoff:** if this checkout sits inside a cloud-synced folder (OneDrive, Dropbox, iCloud Drive, etc.), importing packages from `psyscan/` can occasionally stall for minutes at a time — the sync client mediates every file access, even to files already fully downloaded. Keeping the venv genuinely inside the project (rather than symlinking to a venv stored outside sync scope) is a deliberate choice; if the stall becomes a real problem, the fix is to build `psyscan`'s real files at, e.g., `~/.cache/llm-rm/psyscan` and `ln -sfn` it in as `./psyscan` — every job script's `source ./psyscan/bin/activate` keeps working unchanged either way.

```sh
bash simulation/setup_env.sh
```

It can be run from the package root or from `simulation/` — it resolves its own location either way.

**Note on this checkout:** Although `LLM-RM` is currently a member of a uv workspace defined one level up (`../pyproject.toml`, `[tool.uv.workspace]`, alongside `psyschscanner_v_0_1_0`), `setup_env.sh` forces the virtual environment to be built directly inside the `LLM-RM` project folder by using an absolute path for `UV_PROJECT_ENVIRONMENT`. The job scripts activate this project-level `psyscan` venv.

### Installing `psychscanner` — editing `setup_env.sh` for a full install

`simulation/setup_env.sh` (checked in, shareable, contains no personal paths) only runs `uv sync --extra simulation` — it installs `rmllm` and the simulation extras, but **not** `psychscanner`, unless your `LLM-RM` checkout happens to sit inside a uv workspace that lists `psychscanner` as a member (as is the case in this repo's dev checkout).

If you have your own local copy of `psyschscanner_v_0_1_0` and are not using a workspace, edit the bottom of `setup_env.sh`:

```sh
source ./psyscan/bin/activate
PSYCHSCANNER_DIR=<YOUR_PSYCHSCANNER_DIR>
uv pip install -e "$PSYCHSCANNER_DIR"
```

Fill in `PSYCHSCANNER_DIR` with the absolute path to your `psyschscanner_v_0_1_0` checkout and uncomment both lines. (`uv pip install -e` is used instead of plain `pip install -e .` since the venv has no seeded `pip` — see note above.)

For personal machines, keep your filled-in copy as `simulation/setup_env.local.sh` instead of editing `setup_env.sh` directly — it's gitignored, so your local paths never get committed. See `simulation/setup_env.local.sh` on this machine for a working example.
