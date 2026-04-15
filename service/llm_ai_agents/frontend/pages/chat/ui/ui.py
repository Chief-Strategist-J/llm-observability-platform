import streamlit as st

class ChatUI:
    def __init__(self, controller, state):
        self.controller = controller
        self.state = state

    def render_page_config(self):
        st.set_page_config(
            page_title="LLM Observability Platform",
            page_icon="robot",
            layout="wide"
        )

    def render_sidebar(self):
        st.sidebar.title("Configuration")
        st.sidebar.header("Model Settings")
        model_config_path = st.sidebar.text_input(
            "Model Config Path",
            value=self.state.DEFAULT_MODEL_CONFIG,
            help="Path to the model configuration file"
        )
        st.sidebar.header("Generation Parameters")
        st.sidebar.info("Note: CPU generation is slower than GPU. Reducing Max Tokens will improve response time.")
        temperature = st.sidebar.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
        top_p = st.sidebar.slider("Top P", 0.0, 1.0, 0.95, 0.05)
        max_tokens = st.sidebar.slider("Max Tokens", 128, 2048, 128, 128)
        
        return {
            "model_config_path": model_config_path,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens
        }

    def render_header(self):
        st.title("LLM Chat Interface")
        st.markdown("---")

    def render_health_checks(self):
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Check Health"):
                result = self.controller.check_health()
                if result["success"]:
                    st.success(f"API Status: {result['data'].get('status')}")
                    st.info(f"Model: {result['data'].get('model')}")
                else:
                    st.error(f"Error: {result['error']}")

        with col2:
            if st.button("Check Download Progress"):
                result = self.controller.get_download_progress()
                if result["success"]:
                    st.info(f"Downloaded: {result['size_gb']:.2f} GB")
                elif "message" in result:
                    st.warning(f"Warning: {result['message']}")
                else:
                    st.error(f"Error: {result['error']}")

        with col3:
            if st.button("Restart API"):
                st.warning("Warning: Restart functionality requires server access")

        st.markdown("---")

    def render_chat_history(self):
        for message in self.state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    def render_chat_input(self, params):
        if prompt := st.chat_input("Type your message here..."):
            self.state.add_message("user", prompt)
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                full_response = st.write_stream(self.controller.stream_message(prompt, params))
                self.state.add_message("assistant", full_response)

    def render_footer(self, model_config_path):
        if st.button("Clear Chat History"):
            self.state.clear_history()

        st.markdown("---")
        st.subheader("System Information")
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**API URL:** {self.controller.api_base_url}")
        with col2:
            st.info(f"**Model Config:** {model_config_path}")
