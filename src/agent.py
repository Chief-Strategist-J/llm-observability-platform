from typing import Iterator, List, Tuple
from llm_client import llm
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser

chat_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a movie expert. Always answer short, clear, and to the point."),
    ("human", "{input}")
])
movie_chat = chat_prompt | llm | StrOutputParser()

def generate_response(user_input: str) -> str:
    return movie_chat.invoke({"input": user_input})

def stream_response(user_input: str) -> Iterator[str]:
    messages: List[Tuple[str, str]] = [
        ("system", "You are a movie expert. Always answer short, clear, and to the point."),
        ("human", user_input),
    ]
    for chunk in llm.stream(messages):
        text = ""
        msg = getattr(chunk, "message", None)
        if msg is not None:
            text = getattr(msg, "content", "") or ""
        if not text:
            text = getattr(chunk, "content", "") or ""
        if not text:
            t = getattr(chunk, "text", None)
            if callable(t):
                text = t() or ""
            elif isinstance(t, str):
                text = t
        if text:
            yield text
