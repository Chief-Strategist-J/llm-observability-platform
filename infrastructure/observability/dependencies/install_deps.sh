#!/bin/bash
command -v python3 >/dev/null 2>&1 || { echo >&2 "python3 required but not found. Aborting."; exit 1; }
VENV_DIR="$(dirname "$0")/venv"

create_venv() {
    python3 -m venv "$VENV_DIR" 2>/dev/null || \
    virtualenv "$VENV_DIR" 2>/dev/null || \
    {
        python3 -m pip install --user virtualenv >/dev/null 2>&1
        python3 -m virtualenv "$VENV_DIR" 2>/dev/null
    }
}

if [ ! -d "$VENV_DIR" ]; then
    create_venv
fi

# Ensure pip exists inside the venv
if [ ! -f "$VENV_DIR/bin/pip" ]; then
    curl -sS https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    "$VENV_DIR/bin/python3" get-pip.py >/dev/null 2>&1
    rm get-pip.py
fi

if [ -f "$VENV_DIR/bin/pip" ]; then
    "$VENV_DIR/bin/pip" install --upgrade pip
    "$VENV_DIR/bin/pip" install -r "$(dirname "$0")/requirements.txt"
else
    python3 -m pip install --user -r "$(dirname "$0")/requirements.txt"
fi
