import streamlit as st
class AuthUI:
    def __init__(self, controller, state):
        self.controller = controller
        self.state = state
    def render(self):
        st.title("Authentication")
