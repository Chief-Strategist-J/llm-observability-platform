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
from core.models.knowledge_graph_store import store_conversation_as_knowledge_graph, get_conversation_context
from core.services.category_service import get_categories_and_models, get_models_for_category, get_default_model_for_category

logging.basicConfig(
    level=logging.INFO,
    format="event=%(levelname)s ts=%(asctime)s msg=%(message)s"
)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="LLM Chat", page_icon="💬", layout="wide")
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
        st.session_state.categories = categories
        st.session_state.categories_loaded = True
        
        if categories:
            first_category = list(categories.keys())[0]
            st.session_state.selected_category = first_category
            st.session_state.selected_model = get_default_model_for_category(first_category)
            logger.info("event=app_categories_loaded count=%s default_category=%s", len(categories), first_category)

st.sidebar.header("Settings")

user_name = st.sidebar.text_input("Name", "guest")

if st.sidebar.button("🔄 Refresh Models", help="Fetch latest models from Cloudflare"):
    with st.spinner("Refreshing models..."):
        logger.info("event=app_refresh_models_start")
        categories = get_categories_and_models(force_refresh=True)
        st.session_state.categories = categories
        if categories:
            if st.session_state.selected_category not in categories:
                st.session_state.selected_category = list(categories.keys())[0]
            st.session_state.selected_model = get_default_model_for_category(st.session_state.selected_category, force_refresh=True)
        logger.info("event=app_refresh_models_complete count=%s", len(categories))
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
    key="category_selector"
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
    key="model_selector"
)

if model_choice != st.session_state.selected_model:
    st.session_state.selected_model = model_choice
    logger.info("event=app_model_changed model=%s", model_choice)

st.sidebar.markdown(f"**Models in {selected_category}:** {len(models_for_category)}")
st.sidebar.markdown(f"**Total Categories:** {len(categories)}")

if st.sidebar.button("🗑️ Reset Chat"):
    st.session_state.messages = []
    st.session_state._loaded_user = None
    logger.info("event=app_reset_chat user=%s", user_name)
    st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state._loaded_user = None

if st.session_state.get("_loaded_user") != user_name:
    logger.info("event=app_loading_history user=%s", user_name)
    conv = get_conversation_context(user_name, limit=200)
    if conv:
        st.session_state.messages = conv
        logger.info("event=app_history_loaded user=%s count=%s", user_name, len(conv))
    else:
        st.session_state.messages = []
    st.session_state._loaded_user = user_name

if not st.session_state.messages:
    st.session_state.messages.append({"role": "assistant", "text": "How can I help you?"})

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["text"])

prompt = st.chat_input("Type your message...")

if prompt:
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "text": prompt})

    start = time.time()
    logger.info("event=app_chat_request model=%s user=%s category=%s prompt_len=%s", model_choice, user_name, selected_category, len(prompt))

    conversation_history = []
    for msg in st.session_state.messages[:-1]:
        role = "assistant" if msg["role"] == "assistant" else "user"
        conversation_history.append({"role": role, "content": msg["text"]})

    with st.spinner(f"Generating response with {model_choice}..."):
        res = get_ai_response(prompt, model_choice, conversation_history=conversation_history)
    
    bot_text = res.get("text", "")
    success = res.get("success", False)
    
    duration = time.time() - start
    logger.info("event=app_chat_response model=%s user=%s duration=%.4f success=%s response_len=%s", model_choice, user_name, duration, success, len(bot_text))

    with st.chat_message("assistant"):
        st.write(bot_text)

    st.session_state.messages.append({"role": "assistant", "text": bot_text})

    try:
        store_conversation_as_knowledge_graph(user_name, prompt, bot_text, model=model_choice, version="latest")
        logger.info("event=app_conversation_saved user=%s model=%s", user_name, model_choice)
    except Exception as e:
        logger.error("event=app_conversation_save_failed user=%s model=%s error=%s", user_name, model_choice, str(e))