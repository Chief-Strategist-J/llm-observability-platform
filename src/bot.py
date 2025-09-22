import streamlit as st
from agent import generate_response, stream_response
from graph import store_message, fetch_conversation, init_chat, enrich_message

def render_header() -> None:
    st.markdown(
        """
        <div style="background:#2B6CB0; padding:10px; border-radius:8px;
                    text-align:center; max-width:380px; margin:auto;">
            <h3 style="color:white; margin:0;">🎬 Ebert Chat</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_message(role: str, content: str) -> None:
    if role == "user":
        color, text, align = "#2B6CB0", "white", "flex-end"
    else:
        color, text, align = "#EDF2F7", "#2D3748", "flex-start"
    st.markdown(
        f"""
        <div style="display:flex; justify-content:{align}; margin:4px 0;">
            <div style="background:{color}; color:{text};
                        padding:8px 14px; border-radius:14px;
                        max-width:70%; font-size:15px; word-wrap:break-word;">
                {content}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

CHAT_ID = "demo-chat"

def handle_submit(message: str) -> None:
    # show user bubble immediately
    st.session_state.messages.append({"role": "user", "content": message})
    render_message("user", message)

    # persist + enrich (user)
    try:
        user_msg_id = store_message(CHAT_ID, "user", message)
    except Exception:
        user_msg_id = None
    if user_msg_id:
        try:
            enrich_message(user_msg_id, message)
        except Exception:
            pass

    # stream assistant reply
    placeholder = st.empty()
    partial_text = ""

    try:
        for piece in stream_response(message):
            partial_text += piece
            placeholder.markdown(
                f"""
                <div style="display:flex; justify-content:flex-start; margin:4px 0;">
                    <div style="background:#EDF2F7; color:#2D3748;
                                padding:8px 14px; border-radius:14px;
                                max-width:70%; font-size:15px; word-wrap:break-word;">
                        {partial_text}▌
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    except Exception:
        # graceful fallback (non-streaming)
        partial_text = generate_response(message)
        placeholder.markdown(
            f"""
            <div style="display:flex; justify-content:flex-start; margin:4px 0;">
                <div style="background:#EDF2F7; color:#2D3748;
                            padding:8px 14px; border-radius:14px;
                            max-width:70%; font-size:15px; word-wrap:break-word;">
                    {partial_text}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # finalize + persist + enrich (assistant)
    if partial_text:
        placeholder.markdown(
            f"""
            <div style="display:flex; justify-content:flex-start; margin:4px 0;">
                <div style="background:#EDF2F7; color:#2D3748;
                            padding:8px 14px; border-radius:14px;
                            max-width:70%; font-size:15px; word-wrap:break-word;">
                    {partial_text}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.session_state.messages.append({"role": "assistant", "content": partial_text})

        try:
            asst_msg_id = store_message(CHAT_ID, "assistant", partial_text)
        except Exception:
            asst_msg_id = None
        if asst_msg_id:
            try:
                enrich_message(asst_msg_id, partial_text)
            except Exception:
                pass

def main() -> None:
    st.set_page_config(page_title="Ebert 🎬", page_icon="🍿", layout="centered")

    st.markdown(
        """
        <style>
            .chat-wrap {max-width:380px; margin:auto;}
            .chat-scroll {max-height:60vh; overflow:auto; padding-right:6px;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ensure chat node exists
    init_chat(CHAT_ID)

    if "messages" not in st.session_state:
        # load existing history from Neo4j
        history = fetch_conversation(CHAT_ID)
        if history:
            st.session_state.messages = [
                {"role": row["role"], "content": row["content"]} for row in history
            ]
        else:
            st.session_state.messages = [
                {"role": "assistant", "content": "Hi 👋 I'm Ebert! Ask me about movies 🎥"},
            ]
            # persist the greeting
            try:
                greet_id = store_message(CHAT_ID, "assistant", "Hi 👋 I'm Ebert! Ask me about movies 🎥")
                if greet_id:
                    enrich_message(greet_id, "Hi 👋 I'm Ebert! Ask me about movies 🎥")
            except Exception:
                pass

    render_header()

    st.markdown('<div class="chat-wrap"><div class="chat-scroll">', unsafe_allow_html=True)
    for m in st.session_state.messages:
        render_message(m["role"], m["content"])
    st.markdown('</div></div>', unsafe_allow_html=True)

    if prompt := st.chat_input("Write a message..."):
        handle_submit(prompt)

if __name__ == "__main__":
    main()
