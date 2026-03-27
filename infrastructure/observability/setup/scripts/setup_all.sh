#!/bash
echo "Starting Observability Stack Master Setup..."
echo "Step 1: Preparing Environment (Ansible)"
cd deployment/ansible && ./scripts/deploy.sh && cd ../..
echo "Step 2: Starting Temporal Worker"
python3 setup/observability_stack_setup_worker.py &
WORKER_PID=$!
sleep 5
echo "Step 3: Triggering Setup Workflow"
python3 setup/trigger_observability_stack_setup.py setup
echo "Setup triggered successfully. Monitor results in Temporal UI or logs."
