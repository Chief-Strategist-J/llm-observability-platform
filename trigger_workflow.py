#!/usr/bin/env python3
"""
Simple script to trigger a Temporal workflow for testing.
"""

import asyncio

from temporalio.client import Client


async def main():
    # Connect to Temporal server
    client = await Client.connect("localhost:7233")

    # Start the LoggingPipelineWorkflow
    result = await client.start_workflow(
        "LoggingPipelineWorkflow",
        "ai-proxy-service",
        id="test-workflow-" + str(int(asyncio.get_event_loop().time())),
        task_queue="logging-pipeline",
    )

    print(f"Started workflow with ID: {result.id}")
    print("Check Temporal UI at http://localhost:8233 to see it running!")


if __name__ == "__main__":
    asyncio.run(main())
