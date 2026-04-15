import streamlit as st
class SettingsUI:
    def __init__(self, controller, state):
        self.controller = controller
        self.state = state
    def render(self):
        st.title("Settings")
