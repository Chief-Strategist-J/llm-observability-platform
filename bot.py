import streamlit as st
from utils import write_message
from agent import generate_response

st.set_page_config("Ebert", page_icon=":movie_camera:")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi, I'm the GraphAcademy Chatbot! Ask me about movies 🎬"},
    ]

def handle_submit(message: str):
    with st.spinner("Thinking..."):
        response = generate_response(message)
        write_message("assistant", response)

for m in st.session_state.messages:
    write_message(m["role"], m["content"], save=False)

if prompt := st.chat_input("Ask me about movies…"):
    write_message("user", prompt)
    handle_submit(prompt)
