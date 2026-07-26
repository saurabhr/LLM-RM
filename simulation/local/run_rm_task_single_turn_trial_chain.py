import argparse
import json

import psychscanner as psy

import rmllm

parser = argparse.ArgumentParser(prog="imagine")

parser.add_argument("--taskjson", help="<task>.json")
parser.add_argument("--modelname", help="model name")
parser.add_argument("--familyname", help="family name")
parser.add_argument("--nsim", type=int, default=100, help="simulated participants (lower for a quick demo run)")
args = parser.parse_args()

raw_data_dir = rmllm.config.RAW_DATA_DIR

task_dir = raw_data_dir / "rm_tasks"
task = task_dir / args.taskjson
data_out_dir = rmllm.config.INTERIM_DATA_DIR / "local" / task.stem
population = raw_data_dir / "persona_data" / "population_rm.json"
persona = raw_data_dir / "persona_data" / "persona_rm.json"

# trial-chain tasks (chain_type="trial") need a checkpointer to carry state
# across trials sharing a trcode; memory="SingleTurn" compiles the LangGraph
# without one, so the thread_id psychscanner passes would be a no-op.
task_chain_type = json.loads(task.read_text())["chain_type"]

# Get default experiment card and update
card_in = psy.ExpCardInit()
card_in.proj_dir = data_out_dir
card_in.persona_files = [population,persona]
card_in.projectname = "RRMCONVO100"  # ""study_rm_exp2"
card_in.tunnel_status = "1"
card_in.model = args.modelname
card_in.family = args.familyname
card_in.parser = "1"  # use the parser class the task JSON itself declares
card_in.task_file = task
card_in.cogtype = "no"
card_in.nsim = args.nsim
card_in.memory = "Convo" if task_chain_type == "trial" else "SingleTurn"

# Setup current experiment card to scan
expcard = psy.ExpCard(card_in)
# Setup and run psychscanner
scanner = psy.ScannerModel(expcard=expcard)
# get simulations
simulation = scanner.run()
