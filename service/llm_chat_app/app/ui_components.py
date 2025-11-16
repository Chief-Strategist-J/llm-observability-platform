import streamlit as st
import time
from core.services.auth_service import (
    sign_in, sign_out, register_user, validate_session,
    request_password_reset, reset_password, change_password, get_user_info
)
from core.services.collaboration_service import CollaborationService


class AuthUI:
    @staticmethod
    def signin():
        st.title("🔐 Sign In")
        with st.form("signin_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Sign In", use_container_width=True)

            if submit:
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    result = sign_in(username, password)
                    if result["success"]:
                        st.session_state.authenticated = True
                        st.session_state.session_token = result["session_token"]
                        st.session_state.username = result["username"]
                        st.success("✓ Sign in successful!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(result["message"])

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📝 Create Account", use_container_width=True):
                st.session_state.auth_page = "signup"
                st.rerun()
        with col2:
            if st.button("🔑 Forgot Password?", use_container_width=True):
                st.session_state.auth_page = "forgot"
                st.rerun()

    @staticmethod
    def signup():
        st.title("📝 Create Account")
        with st.form("signup_form"):
            username = st.text_input("Username (min 3 characters)")
            email = st.text_input("Email")
            password = st.text_input("Password (min 6 characters)", type="password")
            password_confirm = st.text_input("Confirm Password", type="password")
            submit = st.form_submit_button("Register", use_container_width=True)

            if submit:
                if not username or not email or not password:
                    st.error("All fields are required")
                elif password != password_confirm:
                    st.error("Passwords do not match")
                else:
                    result = register_user(username, password, email)
                    if result["success"]:
                        st.success("✓ Registration successful! Please sign in.")
                        time.sleep(1)
                        st.session_state.auth_page = "signin"
                        st.rerun()
                    else:
                        st.error(result["message"])

        if st.button("← Back to Sign In", use_container_width=True):
            st.session_state.auth_page = "signin"
            st.rerun()

    @staticmethod
    def forgot_password():
        st.title("🔑 Reset Password")

        if "reset_stage" not in st.session_state:
            st.session_state.reset_stage = "request"
            st.session_state.reset_token = None

        if st.session_state.reset_stage == "request":
            st.write("Enter your email to receive a password reset token.")
            with st.form("forgot_password_form"):
                email = st.text_input("Email")
                submit = st.form_submit_button("Request Reset Token", use_container_width=True)

                if submit:
                    if not email:
                        st.error("Please enter your email")
                    else:
                        result = request_password_reset(email)
                        if result["success"]:
                            st.success("✓ Reset token generated!")
                            if "reset_token" in result:
                                st.info(f"**Reset Token:** `{result['reset_token']}`")
                                st.warning("⚠️ Copy this token now (sent to email in production)")
                                st.session_state.reset_token = result["reset_token"]
                            st.session_state.reset_stage = "reset"
                        else:
                            st.error(result["message"])

            if st.button("← Back to Sign In", use_container_width=True):
                st.session_state.auth_page = "signin"
                st.session_state.reset_stage = "request"
                st.rerun()
        else:
            st.write("Enter your reset token and new password.")
            with st.form("reset_password_form"):
                token = st.text_input("Reset Token", value=st.session_state.reset_token or "")
                new_password = st.text_input("New Password (min 6 characters)", type="password")
                confirm_password = st.text_input("Confirm New Password", type="password")
                submit = st.form_submit_button("Reset Password", use_container_width=True)

                if submit:
                    if not token or not new_password:
                        st.error("All fields are required")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match")
                    else:
                        result = reset_password(token, new_password)
                        if result["success"]:
                            st.success("✓ Password reset successful! Please sign in.")
                            time.sleep(1)
                            st.session_state.auth_page = "signin"
                            st.session_state.reset_stage = "request"
                            st.session_state.reset_token = None
                            st.rerun()
                        else:
                            st.error(result["message"])

            col1, col2 = st.columns(2)
            with col1:
                if st.button("← Request New Token", use_container_width=True):
                    st.session_state.reset_stage = "request"
                    st.rerun()
            with col2:
                if st.button("← Back to Sign In", use_container_width=True):
                    st.session_state.auth_page = "signin"
                    st.session_state.reset_stage = "request"
                    st.rerun()


class SidebarUI:
    @staticmethod
    def user_info(username: str):
        user_info = get_user_info(username)
        if user_info:
            st.sidebar.markdown(f"### 👤 {user_info['username']}")
            st.sidebar.markdown(f"📧 {user_info['email']}")

    @staticmethod
    def signout_button(username: str):
        if st.sidebar.button("🚪 Sign Out", use_container_width=True):
            sign_out(st.session_state.session_token)
            st.session_state.authenticated = False
            st.session_state.session_token = None
            st.session_state.username = None
            st.session_state.messages = []
            st.rerun()

    @staticmethod
    def change_password_section():
        with st.sidebar.expander("🔒 Change Password"):
            with st.form("change_password_form"):
                old_pwd = st.text_input("Current Password", type="password", key="old_pwd")
                new_pwd = st.text_input("New Password", type="password", key="new_pwd")
                confirm_pwd = st.text_input("Confirm New Password", type="password", key="confirm_pwd")
                change_submit = st.form_submit_button("Change Password", use_container_width=True)

                if change_submit:
                    if not old_pwd or not new_pwd:
                        st.error("All fields are required")
                    elif new_pwd != confirm_pwd:
                        st.error("Passwords do not match")
                    else:
                        result = change_password(st.session_state.username, old_pwd, new_pwd)
                        if result["success"]:
                            st.success(result["message"])
                        else:
                            st.error(result["message"])

    @staticmethod
    def collaboration_section():
        with st.sidebar.expander("🤝 Collaboration"):
            col1, col2 = st.columns(2)
            with col1:
                if st.button("➕ New Session", use_container_width=True):
                    session = CollaborationService.create_session(
                        name=f"Chat - {st.session_state.username}",
                        created_by=st.session_state.username,
                        settings={"model": st.session_state.selected_model}
                    )
                    st.session_state.collab_session_id = session["session_id"]
                    st.success(f"✓ Session: {session['session_id'][:8]}...")
            
            with col2:
                if st.button("📋 My Sessions", use_container_width=True):
                    sessions = CollaborationService.list_sessions(st.session_state.username)
                    if sessions["sessions"]:
                        for s in sessions["sessions"]:
                            st.write(f"• {s['name']} ({len(s['participants'])} users)")
                    else:
                        st.info("No sessions yet")
            
            if "collab_session_id" in st.session_state:
                st.write(f"**Active:** {st.session_state.collab_session_id[:8]}...")
                join_code = st.text_input("Share code:")
                if join_code:
                    CollaborationService.join_session(join_code, st.session_state.username)
                    st.success("✓ Joined session\!")

    @staticmethod
    def web_search_section():
        with st.sidebar.expander("�� Web Search"):
            enable_agent = st.checkbox("Enable Internet Search", value=True)
            if enable_agent:
                st.session_state.enable_agent = True
                agent_mode = st.radio("Mode", ["Search", "Research", "Normal"])
                st.session_state.agent_mode = agent_mode
            else:
                st.session_state.enable_agent = False
                st.session_state.agent_mode = "Normal"

    @staticmethod
    def streaming_section():
        with st.sidebar.expander("⚡ Streaming"):
            enable_streaming = st.checkbox("Enable Streaming", value=False)
            st.session_state.enable_streaming = enable_streaming

    @staticmethod
    def model_selection(categories: dict, selected_category: str, selected_model: str):
        from core.services.category_service import (
            get_models_for_category, get_default_model_for_category
        )

        category_list = list(categories.keys())
        if selected_category not in category_list:
            selected_category = category_list[0]

        selected_category = st.sidebar.selectbox(
            "Category",
            category_list,
            index=category_list.index(selected_category) if selected_category in category_list else 0,
            key="category_selector",
        )

        if selected_category != st.session_state.selected_category:
            st.session_state.selected_category = selected_category
            st.session_state.selected_model = get_default_model_for_category(selected_category)

        models_for_category = get_models_for_category(selected_category)
        if not models_for_category:
            st.sidebar.warning(f"No models for {selected_category}")
            return

        if selected_model not in models_for_category:
            selected_model = models_for_category[0]

        model_choice = st.sidebar.selectbox(
            "Model",
            models_for_category,
            index=models_for_category.index(selected_model) if selected_model in models_for_category else 0,
            key="model_selector",
        )

        if model_choice != st.session_state.selected_model:
            st.session_state.selected_model = model_choice

        st.sidebar.markdown(f"**Models:** {len(models_for_category)} | **Categories:** {len(categories)}")

    @staticmethod
    def reset_chat_button():
        if st.sidebar.button("🗑️ Reset Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state._loaded_user = None
            st.rerun()
