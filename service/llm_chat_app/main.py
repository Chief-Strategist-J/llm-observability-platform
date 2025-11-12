import streamlit as st
import logging
from client.ai_client import get_ai_response
from models.graph_store import store_conversation
from config.config import DEFAULT_CONTAINER_NAME

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

st.set_page_config(page_title="LLM Chat", page_icon="💬")
st.title("LLM Chat")

if "messages" not in st.session_state:
    st.session_state.messages = []

user_name = st.text_input("Enter your name", "guest")
prompt = st.text_input("Message")

if st.button("Send") and prompt:
    logger.info("ui send user=%s prompt_len=%d", user_name, len(prompt))
    res = get_ai_response(prompt)
    text = res.get("text", "")
    st.session_state.messages.append((prompt, text, res.get("raw", {})))
    try:
        store_conversation(user_name, prompt, text, model=res.get("raw", {}).get("model", "unknown"), version=res.get("raw", {}).get("version", "unknown"))
    except Exception:
        logger.exception("failed to store conversation")
for u_msg, bot_msg, meta in st.session_state.messages:
    st.markdown(f"**You:** {u_msg}")
    st.markdown(f"**Bot:** {bot_msg}")
    st.markdown("---")
