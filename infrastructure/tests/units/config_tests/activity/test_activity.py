from temporalio import activity
import asyncio

@activity.defn
async def test_activity(name: str) -> str:
    await asyncio.sleep(1)
    return f"Activity executed for: {name}"
