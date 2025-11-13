import sys
import logging
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.client.ai_client import get_ai_response
from core.models.graph_store import store_conversation
from core.models.model_store import all_models

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

st.set_page_config(page_title="LLM Chat", page_icon="💬")

st.title("LLM Chat")

if "messages" not in st.session_state:
    st.session_state.messages = []

user_name = st.text_input("Name", "guest")
model_choice = st.selectbox("Select Model", all_models())
prompt = st.text_input("Message")

if st.button("Send") and prompt:
    res = get_ai_response(prompt, model_choice)
    text = res.get("text", "")

    st.session_state.messages.append((prompt, text))

    try:
        store_conversation(
            user_name,
            prompt,
            text,
            model=model_choice,
            version="latest"
        )
    except Exception:
        logger.exception("store_conversation_failed")

for u, b in st.session_state.messages:
    st.markdown(f"**You:** {u}")
    st.markdown(f"**Bot:** {b}")
    st.markdown("---")
