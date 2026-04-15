import streamlit as st
class AuthState:
    def __init__(self):
        if "user" not in st.session_state:
            st.session_state.user = None
    def set_user(self, user):
        st.session_state.user = user
