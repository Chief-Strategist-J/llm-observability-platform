import streamlit as st
import uuid

def get_session_id() -> str:
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    return st.session_state.session_id

def write_message(role: str, content: str, save: bool = True):
    if save:
        st.session_state.messages.append({"role": role, "content": content})
    with st.chat_message(role):
        st.write(content)
