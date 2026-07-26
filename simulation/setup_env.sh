#!/bin/bash
# Run this once before any other job script in this directory or in local/ (local_job_rm*.sh, hpg_job_rm*.sh).
# Installs uv via conda if not already on the system, then creates the venv "psyscan" inside LLM-RM.
#
# ponytail: if this checkout lives inside a cloud-synced folder (OneDrive, Dropbox,
# iCloud Drive, etc.), importing a venv's packages from inside it can stall for
# minutes at a time -- the sync client mediates every file access, even to files
# already fully downloaded. Building ./psyscan for real here anyway is a deliberate
# tradeoff for a genuinely in-project venv; if that stall ever bites, the fix is to
# build the venv outside the synced folder and symlink it in as ./psyscan instead.
#
# EDIT FOR YOUR SETUP: this only installs the rmllm package + simulation extras. It does NOT
# install psychscanner unless your LLM-RM checkout sits inside a uv workspace that lists it as
# a member (see README). If you have a separate local checkout of psyschscanner_v_0_1_0, set
# PSYCHSCANNER_DIR below and uncomment the install line — see README for details.

command -v uv >/dev/null 2>&1 || conda install -y -c conda-forge uv
cd "$(dirname "$0")/.."

UV_PROJECT_ENVIRONMENT="$(pwd)/psyscan" uv sync --extra simulation

# source ./psyscan/bin/activate
# PSYCHSCANNER_DIR=<YOUR_PSYCHSCANNER_DIR>
# uv pip install --python ./psyscan/bin/python -e "$PSYCHSCANNER_DIR"
