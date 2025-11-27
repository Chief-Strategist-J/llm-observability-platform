#!/bin/bash
set -e

echo "Starting CI/CD Pipeline Worker..."

cd "$(dirname "$0")/../../.."

python infrastructure/cicd/workers/cicd_pipeline_worker.py
