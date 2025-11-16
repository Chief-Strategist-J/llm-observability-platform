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
from core.services.intelligent_agent import IntelligentAgent
from core.services.emotional_intelligence_engine import EmotionalIntelligenceEngine
from ui_components import AuthUI, SidebarUI

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


def init_session_state():
    if "categories_loaded" not in st.session_state:
        st.session_state.categories_loaded = False
        st.session_state.categories = {}
        st.session_state.selected_category = ""
        st.session_state.selected_model = ""
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state._loaded_user = None


def load_models():
    if not st.session_state.categories_loaded:
        with st.spinner("Loading models..."):
            logger.info("event=app_loading_categories")
            categories = get_categories_and_models(force_refresh=False)
            st.session_state.categories = categories or {}
            st.session_state.categories_loaded = True

            if st.session_state.categories:
                first_category = list(st.session_state.categories.keys())[0]
                st.session_state.selected_category = first_category
                st.session_state.selected_model = get_default_model_for_category(first_category)
                logger.info("event=app_categories_loaded count=%s", len(st.session_state.categories))


def load_conversation_history():
    if st.session_state.get("_loaded_user") != st.session_state.username:
        logger.info("event=app_loading_history user=%s", st.session_state.username)
        conv = get_conversation_context(st.session_state.username, limit=200)
        st.session_state.messages = conv if conv else []
        st.session_state._loaded_user = st.session_state.username

    if not st.session_state.messages:
        st.session_state.messages.append({"role": "assistant", "text": "How can I help you today?"})


def render_sidebar():
    st.sidebar.header("⚙️ Settings")
    
    SidebarUI.user_info(st.session_state.username)
    SidebarUI.signout_button(st.session_state.username)
    st.sidebar.divider()
    
    SidebarUI.change_password_section()
    SidebarUI.collaboration_section()
    SidebarUI.web_search_section()
    SidebarUI.streaming_section()
    
    st.sidebar.divider()
    
    if st.sidebar.button("🔄 Refresh Models", use_container_width=True):
        with st.spinner("Refreshing..."):
            logger.info("event=app_refresh_models_start")
            categories = get_categories_and_models(force_refresh=True) or {}
            st.session_state.categories = categories
            if st.session_state.categories:
                if st.session_state.selected_category not in st.session_state.categories:
                    st.session_state.selected_category = list(st.session_state.categories.keys())[0]
                st.session_state.selected_model = get_default_model_for_category(
                    st.session_state.selected_category, force_refresh=True
                )
            st.rerun()
    
    SidebarUI.model_selection(
        st.session_state.categories,
        st.session_state.selected_category,
        st.session_state.selected_model
    )
    
    SidebarUI.reset_chat_button()


def process_chat_response(prompt: str, conversation_history: list):
    enable_web_search = st.session_state.get("enable_agent", False)
    agent_mode = st.session_state.get("agent_mode", "Normal")
    
    bot_text = ""
    success = False
    deep_analysis = None
    
    if enable_web_search and agent_mode in ["Search", "Research"]:
        with st.spinner("🔍 Searching web..."):
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
                    st.info(f"✅ Used {len(agent_result['tool_results'])} web tools")
                    logger.info("event=agent_tools_used count=%s", len(agent_result['tool_results']))
            else:
                bot_text = f"Error: {agent_result.get('error')}"
                success = False
                logger.error("event=agent_failed error=%s", agent_result.get('error'))
    else:
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

    return bot_text, success, deep_analysis


def extract_emotional_state(deep_analysis):
    emotion = "neutral"
    intensity = 5
    meta_core = "No specific insight"
    
    if deep_analysis and isinstance(deep_analysis, dict):
        emotional_state = EmotionalIntelligenceEngine.extract_emotional_layers(deep_analysis)
        emotion = emotional_state.get("primary_emotion", "neutral")
        intensity = emotional_state.get("intensity", 5)
        meta_core = emotional_state.get("meta_questions", {}).get("meta_5_core", "No specific insight")
        
        logger.info(
            "event=app_emotional_intelligence user=%s trauma=%s patterns=%s readiness=%s",
            st.session_state.username,
            emotional_state.get("trauma_indicators", {}).get("present", False),
            any(emotional_state.get("dark_patterns", {}).values()),
            emotional_state.get("transformation_potential", {}).get("readiness_for_change", 5),
        )
    
    return emotion, intensity, meta_core


def main():
    init_session_state()
    
    if not st.session_state.authenticated:
        if st.session_state.session_token:
            from core.services.auth_service import validate_session
            username = validate_session(st.session_state.session_token)
            if username:
                st.session_state.authenticated = True
                st.session_state.username = username

        if not st.session_state.authenticated:
            if st.session_state.auth_page == "signin":
                AuthUI.signin()
            elif st.session_state.auth_page == "signup":
                AuthUI.signup()
            elif st.session_state.auth_page == "forgot":
                AuthUI.forgot_password()
            st.stop()

    st.title("💬 LLM Chat")
    
    load_models()
    load_conversation_history()
    render_sidebar()
    
    if not st.session_state.categories:
        st.error("Failed to load models. Check your API credentials.")
        st.stop()

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["text"])

    prompt = st.chat_input("Type your message...")

    if prompt:
        st.chat_message("user").write(prompt)
        st.session_state.messages.append({"role": "user", "text": prompt})

        start = time.time()
        logger.info(
            "event=app_chat_request model=%s user=%s category=%s prompt_len=%s",
            st.session_state.selected_model,
            st.session_state.username,
            st.session_state.selected_category,
            len(prompt),
        )

        conversation_history = []
        for msg in st.session_state.messages[:-1]:
            role = "assistant" if msg["role"] == "assistant" else "user"
            conversation_history.append({"role": role, "content": msg["text"]})

        bot_text, success, deep_analysis = process_chat_response(prompt, conversation_history)
        duration = time.time() - start
        
        emotion, intensity, meta_core = extract_emotional_state(deep_analysis)

        logger.info(
            "event=app_chat_response model=%s user=%s duration=%.4f success=%s response_len=%s emotion=%s intensity=%s",
            st.session_state.selected_model,
            st.session_state.username,
            duration,
            success,
            len(bot_text),
            emotion,
            intensity,
        )

        if not st.session_state.get("enable_streaming"):
            with st.chat_message("assistant"):
                st.write(bot_text)

        st.session_state.messages.append({"role": "assistant", "text": bot_text})

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
                "event=app_conversation_save_failed user=%s error=%s",
                st.session_state.username,
                str(e),
            )


if __name__ == "__main__":
    main()
