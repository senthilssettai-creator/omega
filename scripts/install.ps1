$ErrorActionPreference = "Stop"
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev,documents]"
.\.venv\Scripts\omega.exe init
