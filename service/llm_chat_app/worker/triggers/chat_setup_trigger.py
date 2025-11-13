import asyncio
import logging
import sys
from pathlib import Path
from uuid import uuid4
from temporalio.client import Client

project_root = Path(__file__).resolve().parents[4]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from service.llm_chat_app.worker.workflows.chat_setup_workflow import ChatSetupWorkflow

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("chat_setup_trigger")

async def main():
    client = await Client.connect("localhost:7233")
    params = {"service_name": "chat-setup"}
    run_id = f"chat-setup-{uuid4().hex}"
    handle = await client.start_workflow(
        ChatSetupWorkflow.run,
        params,
        id=run_id,
        task_queue="chat-service-queue",
    )
    logger.info("started workflow id=%s run=%s", handle.id, handle.run_id)
    await handle.result()

if __name__ == "__main__":
    asyncio.run(main())
