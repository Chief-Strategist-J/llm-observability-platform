"""Temporal activity and workflow implementation for greeting composition.

This module demonstrates a basic Temporal workflow that composes personalized greetings
using activities. It includes a simple activity that combines a greeting with a name and
a workflow that orchestrates the activity execution.

"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import timedelta

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker


@dataclass
class ComposeGreetingInput:
    """Input parameters for the greeting composition activity.

    Args:
        greeting: The greeting message to use.
        name: The name of the person to greet.

    """

    greeting: str
    name: str


@activity.defn
def compose_greeting(greeting_input: ComposeGreetingInput) -> str:
    """Compose a personalized greeting message.

    Args:
        greeting_input: The input parameters containing greeting and name.

    Returns:
        str: The formatted greeting message.

    """
    activity.logger.info(f"Running activity with parameter {greeting_input}")
    return f"{greeting_input.greeting}, {greeting_input.name}!"


@workflow.defn
class GreetingWorkflow:  # pylint: disable=too-few-public-methods
    """
    Workflow for orchestrating greeting composition activities.
    """

    @workflow.run
    async def run(self, name: str) -> str:
        """Execute the greeting workflow.

        Args:
            name: The name of the person to greet.

        Returns:
            str: The final greeting message.

        """
        workflow.logger.info(f"Running workflow with parameter {name}")
        return await workflow.execute_activity(
            compose_greeting,
            ComposeGreetingInput("Hello", name),
            start_to_close_timeout=timedelta(seconds=10),
        )


async def main():
    """
    Main function to run the Temporal worker and execute the workflow.
    """
    client = await Client.connect("localhost:7233")

    async with Worker(
        client,
        task_queue="hello-activity-task-queue",
        workflows=[GreetingWorkflow],
        activities=[compose_greeting],
        activity_executor=ThreadPoolExecutor(5),
    ):
        result = await client.execute_workflow(
            GreetingWorkflow.run,
            "World",
            id="hello-activity-workflow-id",
            task_queue="hello-activity-task-queue",
        )
        print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
