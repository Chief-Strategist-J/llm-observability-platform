import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama, OllamaEmbeddings

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_LLM = os.getenv("OLLAMA_LLM", "tinyllama:1b")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "all-minilm")


llm = ChatOllama(
    base_url=OLLAMA_BASE_URL,
    model=OLLAMA_LLM,
    temperature=0.2,
)


embeddings = OllamaEmbeddings(
    base_url=OLLAMA_BASE_URL,
    model=OLLAMA_EMBED_MODEL,
)