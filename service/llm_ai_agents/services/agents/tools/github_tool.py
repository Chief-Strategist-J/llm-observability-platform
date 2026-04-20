from langchain_core.tools import tool


@tool
def search_github(query: str) -> str:
    """Search GitHub repositories and return relevant results."""
    return f"[github_tool] stub result for: {query}"
