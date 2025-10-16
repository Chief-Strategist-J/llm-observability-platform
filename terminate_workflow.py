#!/usr/bin/env python3
"""
Script to terminate a Temporal workflow.
"""

import asyncio

from temporalio.client import Client


async def terminate_workflow(workflow_id: str, reason: str = "Terminating workflow"):
    """
    Terminate a Temporal workflow by ID.
    """
    client = await Client.connect("localhost:7233")

    try:
        # Get the workflow handle
        handle = client.get_workflow_handle(workflow_id)

        # Terminate the workflow
        await handle.terminate(reason)
        print(f"✅ Workflow '{workflow_id}' has been terminated successfully!")
        print(f"Reason: {reason}")

    except Exception as e:
        print(f"❌ Failed to terminate workflow '{workflow_id}': {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python terminate_workflow.py <workflow_id>")
        print("Example: python terminate_workflow.py test-workflow-19407")
        sys.exit(1)

    workflow_id = sys.argv[1]
    asyncio.run(terminate_workflow(workflow_id))
