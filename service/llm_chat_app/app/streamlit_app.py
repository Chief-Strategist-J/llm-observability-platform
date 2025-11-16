import sys
import logging
from pathlib import Path
import time
import streamlit as st
from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parents[1] / ".env.llm_chat_app"
load_dotenv(_env_path, override=True)

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.client.ai_client import get_ai_response
from core.models.knowledge_graph_store import (
    store_conversation_as_knowledge_graph,
    get_conversation_context,
)
from core.services.category_service import (
    get_categories_and_models,
    get_models_for_category,
    get_default_model_for_category,
)
from core.services.auth_service import (
    sign_in,
    sign_out,
    register_user,
    validate_session,
    request_password_reset,
    reset_password,
    change_password,
    get_user_info,
)
from core.services.collaboration_service import CollaborationService
from core.services.intelligent_agent import IntelligentAgent
from core.services.emotional_intelligence_engine import EmotionalIntelligenceEngine
from core.client.streaming_client import StreamingClient
from core.client.web_search_tools import WebSearchTools
import asyncio

logging.basicConfig(
    level=logging.INFO, format="event=%(levelname)s ts=%(asctime)s msg=%(message)s"
)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="LLM Chat", page_icon="💬", layout="wide")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.session_token = None
    st.session_state.username = None
    st.session_state.auth_page = "signin"

def show_signin_page():
    st.title("🔐 Sign In")

    with st.form("signin_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Sign In")

        if submit:
            if not username or not password:
                st.error("Please enter both username and password")
            else:
                result = sign_in(username, password)
                if result["success"]:
                    st.session_state.authenticated = True
                    st.session_state.session_token = result["session_token"]
                    st.session_state.username = result["username"]
                    st.success("Sign in successful!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error(result["message"])

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Create Account"):
            st.session_state.auth_page = "signup"
            st.rerun()
    with col2:
        if st.button("Forgot Password?"):
            st.session_state.auth_page = "forgot"
            st.rerun()

def show_signup_page():
    st.title("📝 Create Account")

    with st.form("signup_form"):
        username = st.text_input("Username (min 3 characters)")
        email = st.text_input("Email")
        password = st.text_input("Password (min 6 characters)", type="password")
        password_confirm = st.text_input("Confirm Password", type="password")
        submit = st.form_submit_button("Register")

        if submit:
            if not username or not email or not password:
                st.error("All fields are required")
            elif password != password_confirm:
                st.error("Passwords do not match")
            else:
                result = register_user(username, password, email)
                if result["success"]:
                    st.success("Registration successful! Please sign in.")
                    time.sleep(1)
                    st.session_state.auth_page = "signin"
                    st.rerun()
                else:
                    st.error(result["message"])

    if st.button("← Back to Sign In"):
        st.session_state.auth_page = "signin"
        st.rerun()

def show_forgot_password_page():
    st.title("🔑 Reset Password")

    if "reset_stage" not in st.session_state:
        st.session_state.reset_stage = "request"
        st.session_state.reset_token = None

    if st.session_state.reset_stage == "request":
        st.write("Enter your email to receive a password reset token.")

        with st.form("forgot_password_form"):
            email = st.text_input("Email")
            submit = st.form_submit_button("Request Reset Token")

            if submit:
                if not email:
                    st.error("Please enter your email")
                else:
                    result = request_password_reset(email)
                    if result["success"]:
                        st.success("Reset token generated!")
                        if "reset_token" in result:
                            st.info(f"**Reset Token:** `{result['reset_token']}`")
                            st.warning("⚠️ In production, this would be sent to your email. Copy it now!")
                            st.session_state.reset_token = result["reset_token"]
                        st.session_state.reset_stage = "reset"
                    else:
                        st.error(result["message"])

        if st.button("← Back to Sign In"):
            st.session_state.auth_page = "signin"
            st.session_state.reset_stage = "request"
            st.rerun()
    else:
        st.write("Enter your reset token and new password.")

        with st.form("reset_password_form"):
            token = st.text_input("Reset Token", value=st.session_state.reset_token or "")
            new_password = st.text_input("New Password (min 6 characters)", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            submit = st.form_submit_button("Reset Password")

            if submit:
                if not token or not new_password:
                    st.error("All fields are required")
                elif new_password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    result = reset_password(token, new_password)
                    if result["success"]:
                        st.success("Password reset successful! Please sign in.")
                        time.sleep(1)
                        st.session_state.auth_page = "signin"
                        st.session_state.reset_stage = "request"
                        st.session_state.reset_token = None
                        st.rerun()
                    else:
                        st.error(result["message"])

        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Request New Token"):
                st.session_state.reset_stage = "request"
                st.rerun()
        with col2:
            if st.button("← Back to Sign In"):
                st.session_state.auth_page = "signin"
                st.session_state.reset_stage = "request"
                st.rerun()

if not st.session_state.authenticated:
    if st.session_state.session_token:
        username = validate_session(st.session_state.session_token)
        if username:
            st.session_state.authenticated = True
            st.session_state.username = username

    if not st.session_state.authenticated:
        if st.session_state.auth_page == "signin":
            show_signin_page()
        elif st.session_state.auth_page == "signup":
            show_signup_page()
        elif st.session_state.auth_page == "forgot":
            show_forgot_password_page()
        st.stop()

st.title("💬 LLM Chat")

if "categories_loaded" not in st.session_state:
    st.session_state.categories_loaded = False
    st.session_state.categories = {}
    st.session_state.selected_category = ""
    st.session_state.selected_model = ""

if not st.session_state.categories_loaded:
    with st.spinner("Loading models from Cloudflare..."):
        logger.info("event=app_loading_categories")
        categories = get_categories_and_models(force_refresh=False)
        st.session_state.categories = categories or {}
        st.session_state.categories_loaded = True

        if st.session_state.categories:
            first_category = list(st.session_state.categories.keys())[0]
            st.session_state.selected_category = first_category
            st.session_state.selected_model = get_default_model_for_category(first_category)
            logger.info(
                "event=app_categories_loaded count=%s default_category=%s",
                len(st.session_state.categories),
                first_category,
            )

st.sidebar.header("Settings")

user_info = get_user_info(st.session_state.username)
if user_info:
    st.sidebar.write(f"👤 **{user_info['username']}**")
    st.sidebar.write(f"📧 {user_info['email']}")

if st.sidebar.button("🚪 Sign Out"):
    sign_out(st.session_state.session_token)
    logger.info("event=user_signout username=%s", st.session_state.username)
    st.session_state.authenticated = False
    st.session_state.session_token = None
    st.session_state.username = None
    st.session_state.messages = []
    st.rerun()

st.sidebar.divider()

with st.sidebar.expander("🔒 Change Password"):
    with st.form("change_password_form"):
        old_pwd = st.text_input("Current Password", type="password", key="old_pwd")
        new_pwd = st.text_input("New Password", type="password", key="new_pwd")
        confirm_pwd = st.text_input("Confirm New Password", type="password", key="confirm_pwd")
        change_submit = st.form_submit_button("Change Password")

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

st.sidebar.divider()

with st.sidebar.expander("🤝 Collaboration"):
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ New Session"):
            session = CollaborationService.create_session(
                name=f"Chat - {st.session_state.username}",
                created_by=st.session_state.username,
                settings={"model": st.session_state.selected_model}
            )
            st.session_state.collab_session_id = session["session_id"]
            st.success(f"Session created: {session['session_id'][:8]}...")
    
    with col2:
        if st.button("📋 My Sessions"):
            sessions = CollaborationService.list_sessions(st.session_state.username)
            if sessions["sessions"]:
                for s in sessions["sessions"]:
                    st.write(f"• {s['name']} ({len(s['participants'])} users)")
            else:
                st.info("No sessions yet")
    
    if "collab_session_id" in st.session_state:
        st.write(f"**Active:** {st.session_state.collab_session_id[:8]}...")
        join_code = st.text_input("Share code with others:")
        if join_code:
            CollaborationService.join_session(join_code, st.session_state.username)
            st.success("Joined session!")

with st.sidebar.expander("🔍 Web Search & Real-Time Data"):
    enable_agent = st.checkbox("Enable Internet Search for Real-Time Data", value=True, 
                               help="When enabled, chat will search the internet for current information")
    if enable_agent:
        st.session_state.enable_agent = True
        agent_mode = st.radio("Search Mode", 
                             ["Search", "Research", "Normal"],
                             help="Search: Quick web lookup | Research: Deep analysis | Normal: No web search")
        st.session_state.agent_mode = agent_mode
    else:
        st.session_state.enable_agent = False
        st.session_state.agent_mode = "Normal"

with st.sidebar.expander("⚡ Streaming"):
    enable_streaming = st.checkbox("Enable Streaming Responses", value=False)
    st.session_state.enable_streaming = enable_streaming

st.sidebar.divider()

if st.sidebar.button("🔄 Refresh Models", help="Fetch latest models from Cloudflare"):
    with st.spinner("Refreshing models..."):
        logger.info("event=app_refresh_models_start")
        categories = get_categories_and_models(force_refresh=True) or {}
        st.session_state.categories = categories
        if st.session_state.categories:
            if st.session_state.selected_category not in st.session_state.categories:
                st.session_state.selected_category = list(st.session_state.categories.keys())[0]
            st.session_state.selected_model = get_default_model_for_category(
                st.session_state.selected_category, force_refresh=True
            )
        logger.info("event=app_refresh_models_complete count=%s", len(st.session_state.categories))
        st.rerun()

categories = st.session_state.categories

if not categories:
    st.error("Failed to load models from Cloudflare. Check your API credentials and network connection.")
    st.stop()

category_list = list(categories.keys())

if st.session_state.selected_category not in category_list:
    st.session_state.selected_category = category_list[0]

selected_category = st.sidebar.selectbox(
    "Category",
    category_list,
    index=category_list.index(st.session_state.selected_category) if st.session_state.selected_category in category_list else 0,
    key="category_selector",
)

if selected_category != st.session_state.selected_category:
    st.session_state.selected_category = selected_category
    st.session_state.selected_model = get_default_model_for_category(selected_category)
    logger.info("event=app_category_changed category=%s model=%s", selected_category, st.session_state.selected_model)

models_for_category = get_models_for_category(selected_category)

if not models_for_category:
    st.sidebar.warning(f"No models available for {selected_category}")
    st.stop()

if st.session_state.selected_model not in models_for_category:
    st.session_state.selected_model = models_for_category[0]

model_choice = st.sidebar.selectbox(
    "Model",
    models_for_category,
    index=models_for_category.index(st.session_state.selected_model) if st.session_state.selected_model in models_for_category else 0,
    key="model_selector",
)

if model_choice != st.session_state.selected_model:
    st.session_state.selected_model = model_choice
    logger.info("event=app_model_changed model=%s", model_choice)

st.sidebar.markdown(f"**Models in {selected_category}:** {len(models_for_category)}")
st.sidebar.markdown(f"**Total Categories:** {len(categories)}")

if st.sidebar.button("🗑️ Reset Chat"):
    st.session_state.messages = []
    st.session_state._loaded_user = None
    logger.info("event=app_reset_chat user=%s", st.session_state.username)
    st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state._loaded_user = None

if st.session_state.get("_loaded_user") != st.session_state.username:
    logger.info("event=app_loading_history user=%s", st.session_state.username)
    conv = get_conversation_context(st.session_state.username, limit=200)
    if conv:
        st.session_state.messages = conv
        logger.info("event=app_history_loaded user=%s count=%s", st.session_state.username, len(conv))
    else:
        st.session_state.messages = []
    st.session_state._loaded_user = st.session_state.username

if not st.session_state.messages:
    st.session_state.messages.append({"role": "assistant", "text": "How can I help you?"})

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["text"])

prompt = st.chat_input("Type your message...")

if prompt:
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "text": prompt})

    if "collab_session_id" in st.session_state:
        CollaborationService.add_message(
            st.session_state.collab_session_id,
            st.session_state.username,
            "user",
            prompt
        )

    start = time.time()
    logger.info(
        "event=app_chat_request model=%s user=%s category=%s prompt_len=%s",
        st.session_state.selected_model,
        st.session_state.username,
        selected_category,
        len(prompt),
    )

    conversation_history = []
    for msg in st.session_state.messages[:-1]:
        role = "assistant" if msg["role"] == "assistant" else "user"
        conversation_history.append({"role": role, "content": msg["text"]})

    # Determine if web search should be enabled
    enable_web_search = st.session_state.get("enable_agent", False)
    agent_mode = st.session_state.get("agent_mode", "Normal")
    
    bot_text = ""
    success = False
    deep_analysis = None
    
    # Process with intelligent agent and web search
    if enable_web_search and agent_mode in ["Search", "Research"]:
        with st.spinner("🔍 Searching web for real-time data..."):
            logger.info("event=agent_mode_activated mode=%s", agent_mode)
            agent_result = IntelligentAgent.process_with_tools(
                prompt,
                st.session_state.selected_model,
                conversation_history=conversation_history,
                enable_web_search=True,
                max_iterations=3
            )
            if agent_result.get("success"):
                bot_text = agent_result.get("response", "")
                success = True
                if agent_result.get("tool_results"):
                    st.info(f"✅ Used {len(agent_result['tool_results'])} web tools for real-time data")
                    logger.info("event=agent_tools_used count=%s", len(agent_result['tool_results']))
            else:
                bot_text = f"Error: {agent_result.get('error')}"
                success = False
                logger.error("event=agent_failed error=%s", agent_result.get('error'))
    else:
        # Standard AI response without web search
        with st.spinner("💭 Thinking..."):
            ai_result = get_ai_response(
                prompt,
                st.session_state.selected_model,
                conversation_history=conversation_history,
                enable_deep_analysis=True
            )
            if ai_result.get("success"):
                bot_text = ai_result.get("text", "")
                success = True
                deep_analysis = ai_result.get("deep_analysis")
            else:
                bot_text = ai_result.get("text", "Error generating response")
                success = False

    duration = time.time() - start
    
    # Extract emotional insights using Emotional Intelligence Engine
    emotion = "neutral"
    intensity = 5
    meta_core = "No specific insight"
    emotional_state = None
    
    if deep_analysis and isinstance(deep_analysis, dict):
        # Use the Emotional Intelligence Engine for deeper analysis
        emotional_state = EmotionalIntelligenceEngine.extract_emotional_layers(deep_analysis)
        
        emotion = emotional_state.get("primary_emotion", "neutral")
        intensity = emotional_state.get("intensity", 5)
        meta_core = emotional_state.get("meta_questions", {}).get("meta_5_core", "No specific insight")
        
        # Log comprehensive emotional analysis
        logger.info(
            "event=app_chat_response model=%s user=%s duration=%.4f success=%s response_len=%s emotion=%s intensity=%s meta_core=%s",
            st.session_state.selected_model,
            st.session_state.username,
            duration,
            success,
            len(bot_text),
            emotion,
            intensity,
            meta_core,
        )
        
        # Log additional emotional intelligence
        logger.info(
            "event=app_emotional_intelligence user=%s trauma_present=%s dark_patterns=%s readiness_for_change=%s",
            st.session_state.username,
            emotional_state.get("trauma_indicators", {}).get("present", False),
            any(emotional_state.get("dark_patterns", {}).values()),
            emotional_state.get("transformation_potential", {}).get("readiness_for_change", 5),
        )
    else:
        logger.info(
            "event=app_chat_response model=%s user=%s duration=%.4f success=%s response_len=%s",
            st.session_state.selected_model,
            st.session_state.username,
            duration,
            success,
            len(bot_text),
        )

    if not st.session_state.get("enable_streaming"):
        with st.chat_message("assistant"):
            st.write(bot_text)

    st.session_state.messages.append({"role": "assistant", "text": bot_text})

    if "collab_session_id" in st.session_state:
        CollaborationService.add_message(
            st.session_state.collab_session_id,
            "assistant",
            "assistant",
            bot_text
        )

    try:
        store_conversation_as_knowledge_graph(
            st.session_state.username,
            prompt,
            bot_text,
            model=st.session_state.selected_model,
            version="latest",
            metadata={"deep_analysis": deep_analysis} if deep_analysis else None,
        )
        logger.info(
            "event=app_conversation_saved user=%s model=%s has_deep_analysis=%s",
            st.session_state.username,
            st.session_state.selected_model,
            bool(deep_analysis),
        )
    except Exception as e:
        logger.error(
            "event=app_conversation_save_failed user=%s model=%s error=%s",
            st.session_state.username,
            st.session_state.selected_model,
            str(e),
        )
