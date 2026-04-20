from langchain_core.tools import tool


@tool
def query_database(query: str) -> str:
    """Execute a read-only database query and return results as text."""
    return f"[db_tool] stub result for: {query}"
