import argparse

import psychscanner as psy

from rm_msg_injection import *
import rmllm
import nltk

nltk.download('words')

parser = argparse.ArgumentParser(prog="rmproject", description="Run RM task with feedback")

parser.add_argument("--taskjson", help="<task>.json")
parser.add_argument("--modelname", help="model name")
parser.add_argument("--familyname", help="family name")
parser.add_argument("--nsim", type=int, default=100, help="simulated participants (lower for a quick demo run)")
args = parser.parse_args()

raw_data_dir = rmllm.config.RAW_DATA_DIR

task_dir = raw_data_dir / "rm_tasks"
task = task_dir / args.taskjson
data_out_dir = rmllm.config.INTERIM_DATA_DIR / "sim_data_hpc" / task.stem
population = raw_data_dir / "persona_data" / "population_rm.json"
persona = raw_data_dir / "persona_data" / "persona_rm.json"

# Get default experiment card and update
card_in = psy.ExpCardInit()
card_in.proj_dir = data_out_dir
print(data_out_dir)
card_in.persona_files = [population,persona]
card_in.projectname = "RRMCONVO100"  # ""study_rm_exp2"
card_in.tunnel_status = "1"
card_in.model = args.modelname
card_in.family = args.familyname
card_in.parser = "dynamic"
card_in.task_file = task
card_in.cogtype = "no"
card_in.nsim = args.nsim
card_in.chain_type = "task"
card_in.memory = "Convo"
card_in.feedback = '1'
card_in.feedback_fn = Stim_Trial_Injection

# Setup current experiment card to scan
expcard = psy.ExpCard(card_in)
# Setup and run psychscanner
scanner = psy.ScannerModel(expcard=expcard)
# get simulations
simulation = scanner.run()
