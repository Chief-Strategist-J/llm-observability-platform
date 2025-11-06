from temporalio import activity
from ingest.container_logs.agents.agent_manager import manager_instance

@activity.defn
async def push_and_reload_activity(config_str):
    manager_instance.push(config_str)
    manager_instance.reload()
    return True

@activity.defn
async def start_agent_activity():
    return manager_instance.start()

@activity.defn
async def stop_agent_activity():
    return manager_instance.stop()

if __name__ == "__main__":
    print(push_and_reload_activity.__name__)
