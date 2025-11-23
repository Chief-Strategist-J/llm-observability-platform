import sys
from pathlib import Path

root = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(root))

from infrastructure.orchestrator.base.base_trigger import BaseTrigger
from infrastructure.tests.units.config_tests.workflows.test_workflow import TestWorkflow
from infrastructure.tests.units.config_tests.activity.test_activity import test_activity

class TestTrigger(BaseTrigger):
    def get_workflows(self):
        return [TestWorkflow]

    def get_activities(self):
        return [test_activity]

if __name__ == "__main__":
    trigger = TestTrigger(
        host="localhost:7233",
        namespace="default",
        task_queue="test-queue",
        service_name="test-service",
        workflow_name="TestWorkflow",
        params={"name": "example"},
    )
    wid = trigger.run_as_trigger({"name": "dinesh"})
    print("Workflow started with ID:", wid)
