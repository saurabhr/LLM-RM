#!/bin/bash
# Run RM episodic (with-feedback) simulations locally on laptop.
# Requires: `ollama serve` already running, and setup_env.sh already run once (see README).

source "$(dirname "$0")/../../psyscan/bin/activate"

taskname_file=./taskrmllm_episodic_chain_fb_all.txt
modelname_file=./llmmodels_test_local.txt
run_script=./run_rm_task_episodic_fb.py

while IFS= read -r modelname
do
	while IFS= read -r taskname
	do
        echo "Simulation task and model"
        echo $modelname
        echo $taskname
        echo "========================="

        # Pull model if not present
        ollama pull $modelname || echo "Model already exists"

        python "$run_script" --taskjson "$taskname" --modelname "$modelname" --familyname ollama

        sleep 200

    done < "$taskname_file"
    sleep 200
    ollama rm $modelname
done < "$modelname_file"
sleep 500
