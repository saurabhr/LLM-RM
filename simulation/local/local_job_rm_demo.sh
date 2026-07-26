#!/bin/bash
# Quick local smoke test: small demo tasks (notebooks/01_task_gen/demo_output/,
# structurally identical to the real tasks, just 2-8 trials instead of 40-144)
# against an already-installed model, nsim kept low since this is only for
# checking the pipeline runs. Each run_rm_task_*.py in this folder has its
# rm_tasks task_dir line swapped for demo_output (see the commented line
# above task_dir in each script) -- revert that to point back at rm_tasks/
# for real runs.
# Requires: `ollama serve` already running, and setup_env.sh already run once (see README).

source "$(dirname "$0")/../../psyscan/bin/activate"

modelname=gemma3:1b-it-qat
nsim=2

# stdout/stderr logged separately per task, in this script's own directory.
log_dir="$(dirname "$0")/logs"
mkdir -p "$log_dir"
run_ts=$(date +%Y%m%d_%H%M%S)

# (run_script, taskjson) pairs -- demo tasks span all three runner scripts,
# unlike the production task lists which are one runner per .txt file.
demo_runs=(
    "run_rm_task_single_turn_trial_chain.py demo_rm_2op.json"
    "run_rm_task_single_turn_trial_chain.py demo_rm_2op_tc.json"
    "run_rm_task_episodic_no_fb.py demo_rm_2op_convo.json"
    "run_rm_task_episodic_fb.py demo_rm_2op_convo_fb.json"
)

for entry in "${demo_runs[@]}"; do
    read -r run_script taskname <<< "$entry"
    task_id="${taskname%.json}"
    stdout_log="$log_dir/${run_ts}_${task_id}.stdout.log"
    stderr_log="$log_dir/${run_ts}_${task_id}.stderr.log"
    echo "=== $run_script  $taskname  (stdout: $stdout_log, stderr: $stderr_log) ==="
    python -u "./$run_script" --taskjson "$taskname" --modelname "$modelname" --familyname ollama --nsim "$nsim" \
        >"$stdout_log" 2>"$stderr_log"
done
