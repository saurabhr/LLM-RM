# simulation/local

Runs the same RM task simulations as [`simulation/`](../README.md), but on this laptop instead of the HPC cluster. This folder is a **self-contained copy**: its own job scripts, task runners, injection logic, and model/task lists. Nothing here depends on files outside this folder other than the shared `psyscan` venv and `../setup_env*.sh` one level up. That means a local-only bugfix (e.g. patching `run_rm_task_episodic_no_fb.py`) can be made here without touching the HPC copy, and vice versa.

## Inputs

- **Task JSONs** — `data/raw/rm_tasks/*.json`, same files as the HPC side, selected via the local copies of `taskrmllm_*.txt`.
- **Model list** — `llmmodels_test_local.txt` — deliberately a short list (`gemma3:12b-it-qat`, `gemma3:27b-it-qat`) since this runs on a laptop, not a cluster GPU.
- **Persona/population files** — `data/raw/persona_data/persona_rm.json` / `population_rm.json` (shared, same as HPC).
- Requires `ollama serve` already running locally, and `simulation/setup_env.sh` already run once.

## Job scripts

| Job script | Task list | Runner |
|---|---|---|
| `local_job_rm.sh` | `taskrmllm_episodic_chain_all.txt` | `run_rm_task_episodic_no_fb.py` (episodic, no feedback, default. Comment/uncomment inside the script to switch to `taskrmllm_single_turn_train_chain_all.txt` + `run_rm_task_single_turn_trial_chain.py` instead.) |
| `local_job_rm_with_fb.sh` | `taskrmllm_episodic_chain_fb_all.txt` | `run_rm_task_episodic_fb.py` (episodic, with feedback) |

Run from inside this folder (`cd simulation/local && bash local_job_rm.sh`) — the list/script paths in each job script are relative (`./taskrmllm_...txt`), unlike the HPC versions which use `./simulation/...` paths from the repo root.

Each runner takes `--taskjson`, `--modelname`, `--familyname`, and an optional `--nsim` (default 100, matching the HPC side) to override how many simulated participants run for that task+model pair — useful for a quick local smoke test with a small `nsim` before committing to a full run. The job scripts above don't pass `--nsim` themselves, so they always use the default 100 unless you edit the `python "$run_script" ...` line to add it.

## Output

`data/interim/local/<task_stem>/...` — **not** `sim_data_hpc/` (that's what the HPC copy writes to). The top-level folder name (`local` vs `sim_data_hpc`) is what keeps the two copies from colliding: `psychscanner`'s tunnel logic resumes from the last logged index in a project dir, so if a local run and an HPC run ever shared the same output path, a local test run of an overlapping model+task could silently resume into — and corrupt — real experiment data. Keep that top-level segment different if you fork either copy further. See the top-level README's "Data flow" section for the full explanation.

Relatedly: if you rerun the same task+model+memory combination against an output directory that already finished (tunnel log shows an `END` checkpoint), `ScannerModel` raises `ValueError: Session already has ended. Delete old files to run.` rather than silently resuming or overwriting — this is deliberate, not a bug. Delete that specific `ollama_<model>_<memory>/` output folder under `data/interim/local/<task_stem>/RRMCONVO100/<taskname>/` to rerun it.

## Why this order

Same reasoning as `simulation/`: `setup_env.sh` once, then a job script loops models outside / tasks inside so only one model's weights are resident at a time, with `sleep` calls to let Ollama release memory between runs. The local list is short and models are `-it-qat` (quantized) variants specifically so this is feasible to run on laptop hardware rather than requiring the cluster.
