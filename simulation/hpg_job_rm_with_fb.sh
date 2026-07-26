#!/bin/bash
#SBATCH --job-name=job_rrrrm_llama
##SBATCH --mail-type=ALL
##SBATCH --mail-user=<YOUR_EMAIL>
#SBATCH --ntasks=1
#SBATCH --account=<YOUR_HPC_ACCOUNT>
#SBATCH --mem=320gb
#SBATCH --partition=hpg-b200
#SBATCH --gpus=1
#SBATCH --cpus-per-task=20
#SBATCH --time=200:00:00
#SBATCH --output=out_rrrrm_llama_%j.log
#SBATCH --error=err_rrrrm_llama_%j.log

pwd; hostname; date

module purge
module load ollama/0.11.6

# ADD LOCAL PATHS: replace each <...> placeholder below with wherever that
# thing actually lives on your system (they need not share a common parent dir)
export PATH=<YOUR_OLLAMA_ENV_DIR>/bin:$PATH

cd <YOUR_LLM_RM_DIR>
echo "changeing present working dir to:"
pwd
echo "activate project uv venv, python version:"
source ./psyscan/bin/activate
python -V

# Start Ollama server in the background
# <YOUR_OLLAMA_LOG_FILE>.log is relative to cwd, so it is written into <YOUR_LLM_RM_DIR> (set by the cd above)
env OLLAMA_MODELS=<YOUR_OLLAMA_MODELS_DIR> ollama serve >> <YOUR_OLLAMA_LOG_FILE>.log 2>&1 &
sleep 10  # Allow server to initialize

taskname_file=./simulation/taskrmllm_episodic_chain_fb_all.txt
modelname_file=./simulation/llmmodels_test_remote.txt
run_script=./simulation/run_rm_task_episodic_fb.py

mkdir -p ./simulation/runouts

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

        # Run Python script with given modelname and taskname
        python "$run_script" --taskjson $taskname --modelname $modelname --familyname ollama >> ./simulation/runouts/out_rmtask_"$taskname"_"$modelname".txt 2>&1
        sleep 200
    
    done < "$taskname_file"
    sleep 200    
    ollama rm $modelname
done < "$modelname_file"
sleep 500