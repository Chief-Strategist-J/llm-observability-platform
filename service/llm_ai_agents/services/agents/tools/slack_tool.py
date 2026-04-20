from langchain_core.tools import tool


@tool
def send_slack_message(message: str) -> str:
    """Send a message to the configured Slack channel."""
    return f"[slack_tool] stub: message queued: {message}"
