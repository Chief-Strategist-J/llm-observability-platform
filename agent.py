from llm_client import llm
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser

chat_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a movie expert. Be concise, clear, and helpful."),
        ("human", "{input}"),
    ]
)


movie_chat = chat_prompt | llm | StrOutputParser()

def generate_response(user_input: str) -> str:
    try:
        return movie_chat.invoke({"input": user_input})
    except Exception as e:
        return f"⚠️ Error: {e}"
