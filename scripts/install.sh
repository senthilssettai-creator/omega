#!/usr/bin/env sh
set -eu
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,documents]"
omega init
