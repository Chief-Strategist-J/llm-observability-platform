import streamlit as st
class SettingsState:
    def __init__(self):
        if "settings" not in st.session_state:
            st.session_state.settings = {}
