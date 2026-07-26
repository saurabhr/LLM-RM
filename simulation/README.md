# simulation

Runs the RM (reality-monitoring) task against LLMs served by Ollama, via `psychscanner`, on the HPC cluster (SLURM). For the same tasks run on this laptop instead, see [`local/README.md`](local/README.md) — that folder is a self-contained copy of everything below.

**Before submitting a job script**, fill in the `<...>` placeholders inside `hpg_job_rm.sh` / `hpg_job_rm_with_fb.sh` — HPC account, Ollama env/models directories, and your `LLM-RM` checkout path on the cluster. They're intentionally left as templates rather than hardcoded to one machine (see "Why this order" below for the full list).

## Inputs

- **Task JSONs** — `data/raw/rm_tasks/*.json` (one file per task variant, e.g. `rm_2op_convo.json`). Which ones run is selected by the `taskrmllm_*.txt` list files (one filename per line), not by scanning the directory.
- **Model list** — `llmmodels_test_remote.txt`, one Ollama model tag per line (e.g. `gemma3:12b`), pulled on demand and removed after use.
- **Persona/population files** — `data/raw/persona_data/persona_rm.json` and `population_rm.json`, shared across all tasks.

Task JSONs are produced by the `notebooks/01_task_gen/` notebooks — regenerate a task variant there first if you need to change one (see `notebooks/README.md`).

## Job scripts

| Job script | Task list | Runner | Condition |
|---|---|---|---|
| `hpg_job_rm.sh` | `taskrmllm_episodic_chain_all.txt` | `run_rm_task_episodic_no_fb.py` | episodic conversation, no feedback (default). Comment/uncomment inside the script to switch to `taskrmllm_single_turn_train_chain_all.txt` + `run_rm_task_single_turn_trial_chain.py` instead. |
| `hpg_job_rm_with_fb.sh` | `taskrmllm_episodic_chain_fb_all.txt` | `run_rm_task_episodic_fb.py` | episodic conversation, with feedback injected via `rm_msg_injection.py` |

Each runner takes `--taskjson`, `--modelname`, `--familyname`, and an optional `--nsim` (default 100) to override how many simulated participants run for that task+model pair — builds a `psychscanner` `ExpCard` and runs it through `ScannerModel`. The job scripts above don't pass `--nsim` themselves, so they always use the default 100.

## Output

- **Simulation data**: `data/interim/sim_data_hpc/<task_stem>/...` — written directly by `psychscanner` (`ExpCard.proj_dir`). This lives on the **HPC's own filesystem**, not this laptop, and is scratch space (safe to wipe). See the top-level README's "Data flow" section for how it later becomes a curated `data/external/` folder on this laptop.
- **Per-run logs**: `simulation/runouts/out_rmtask_<task>_<model>.txt` (created on first run, gitignored) — stdout/stderr of each task+model invocation.
- **SLURM logs**: `out_<jobname>_%j.log` / `err_<jobname>_%j.log` from the `#SBATCH --output`/`--error` directives.

## Why this order

1. Run `simulation/setup_env.sh` once, to build the shared `psyscan` venv (see top-level README).
2. Submit a job script (`sbatch simulation/hpg_job_rm.sh` or `hpg_job_rm_with_fb.sh`). Each loops **models on the outside, tasks on the inside**: pull a model once, run every task in the list against it, then `ollama rm` the model before moving to the next model. This keeps only one model's weights resident at a time instead of needing disk/GPU space for all of them.
3. The `sleep` calls between tasks and models give Ollama time to fully release GPU memory before the next pull/run — without them, back-to-back loads on the same GPU can collide.

Fill in the `<...>` placeholders in each job script (HPC account, Ollama env/models dirs, `LLM-RM` checkout path) before submitting — they're intentionally left as templates rather than hardcoded to one machine.
