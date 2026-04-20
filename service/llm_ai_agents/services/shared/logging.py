import os


def bootstrap_langsmith():
    api_key = os.getenv("LANGCHAIN_API_KEY", "")
    if not api_key:
        return
    os.environ.setdefault("LANGCHAIN_TRACING_V2", os.getenv("LANGCHAIN_TRACING_V2", "true"))
    os.environ.setdefault("LANGCHAIN_ENDPOINT", os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com"))
    os.environ.setdefault("LANGCHAIN_PROJECT", os.getenv("LANGCHAIN_PROJECT", "llm-observability-platform"))
    os.environ["LANGCHAIN_API_KEY"] = api_key


setup_tracing = bootstrap_langsmith
