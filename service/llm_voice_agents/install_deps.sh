#!/bin/bash
cd /home/btpl-lap-22/prod/llm-observability-platform/service/llm_voice_agents/
rm -f .venv/.lock /tmp/uv-setuptools-*.lock /home/btpl-lap-22/.cache/uv/sdists-v9/pypi/aec-audio-processing/1.0.1/.lock
/home/btpl-lap-22/.local/bin/uv pip install -v -r requirements.txt > install_log.txt 2>&1
