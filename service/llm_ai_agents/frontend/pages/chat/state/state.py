import streamlit as st

class ChatState:
    DEFAULT_MODEL_CONFIG = "configs/models/local/gemma/v2/cpu/2b.yaml"

    def __init__(self):
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "model_config_path" not in st.session_state:
            st.session_state.model_config_path = self.DEFAULT_MODEL_CONFIG

    @property
    def messages(self):
        return st.session_state.messages

    def add_message(self, role, content):
        st.session_state.messages.append({"role": role, "content": content})

    def clear_history(self):
        st.session_state.messages = []
        st.rerun()
