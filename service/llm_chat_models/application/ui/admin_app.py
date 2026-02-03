import streamlit as st
import requests
import json
import logging
from typing import Dict, Any, List, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

API_BASE_URL = "http://localhost:8100"

st.set_page_config(
    page_title="LLM Admin Panel",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
    }
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #b0b0b0;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #1a1f2e 0%, #252b3d 100%);
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #2d3548;
    }
    .success-box {
        background-color: #1a3d2a;
        border: 1px solid #2d8b46;
        border-radius: 8px;
        padding: 1rem;
        color: #4ade80;
    }
    .error-box {
        background-color: #3d1a1a;
        border: 1px solid #8b2d2d;
        border-radius: 8px;
        padding: 1rem;
        color: #f87171;
    }
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
    }
</style>
""", unsafe_allow_html=True)


def api_request(method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
    logger.info("event=api_request method=%s endpoint=%s", method, endpoint)
    url = f"{API_BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=60)
        elif method == "PUT":
            response = requests.put(url, json=data, timeout=30)
        elif method == "DELETE":
            response = requests.delete(url, timeout=30)
        else:
            return {"error": f"Unsupported method: {method}"}
        if response.status_code in [200, 201]:
            logger.info("event=api_request_success endpoint=%s status=%d", endpoint, response.status_code)
            return response.json()
        logger.error("event=api_request_error endpoint=%s status=%d", endpoint, response.status_code)
        return {"error": f"Request failed: {response.status_code} - {response.text}"}
    except requests.exceptions.ConnectionError:
        logger.error("event=api_request_connection_error endpoint=%s", endpoint)
        return {"error": "Connection error - is the API server running?"}
    except Exception as e:
        logger.error("event=api_request_exception endpoint=%s error=%s", endpoint, str(e))
        return {"error": str(e)}


def render_sidebar():
    st.sidebar.markdown("## 🤖 LLM Admin Panel")
    st.sidebar.markdown("---")
    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Models", "Endpoints", "Schemas", "Test"],
        index=0
    )
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Quick Stats")
    models_result = api_request("GET", "/admin/models?limit=1000")
    endpoints_result = api_request("GET", "/admin/endpoints?limit=1000")
    if "error" not in models_result:
        st.sidebar.metric("Total Models", models_result.get("total_count", 0))
    if "error" not in endpoints_result:
        st.sidebar.metric("Total Endpoints", endpoints_result.get("total_count", 0))
    return page


def render_dashboard():
    st.markdown('<p class="main-header">📊 Dashboard</p>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    models_result = api_request("GET", "/admin/models?limit=1000")
    endpoints_result = api_request("GET", "/admin/endpoints?limit=1000")
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        if "error" not in models_result:
            total = models_result.get("total_count", 0)
            active = len([m for m in models_result.get("items", []) if m.get("is_active")])
            st.metric("Total Models", total)
            st.metric("Active Models", active)
        else:
            st.error(models_result.get("error"))
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        if "error" not in endpoints_result:
            total = endpoints_result.get("total_count", 0)
            active = len([e for e in endpoints_result.get("items", []) if e.get("is_active")])
            st.metric("Total Endpoints", total)
            st.metric("Active Endpoints", active)
        else:
            st.error(endpoints_result.get("error"))
        st.markdown('</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        health_result = api_request("GET", "/health")
        if "error" not in health_result:
            st.metric("API Status", "🟢 Healthy")
            st.caption(f"Version: {health_result.get('version', 'N/A')}")
        else:
            st.metric("API Status", "🔴 Unhealthy")
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown('<p class="sub-header">Recent Models</p>', unsafe_allow_html=True)
    if "error" not in models_result and models_result.get("items"):
        for model in models_result.get("items", [])[:5]:
            with st.expander(f"🤖 {model.get('display_name', model.get('name'))}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Provider:** {model.get('provider')}")
                    st.write(f"**Model ID:** {model.get('model_id')}")
                with col2:
                    st.write(f"**Status:** {'🟢 Active' if model.get('is_active') else '🔴 Inactive'}")
                    st.write(f"**Temperature:** {model.get('temperature')}")


def render_models():
    st.markdown('<p class="main-header">🤖 Model Management</p>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📋 List Models", "➕ Add Model"])
    with tab1:
        models_result = api_request("GET", "/admin/models?limit=100")
        if "error" in models_result:
            st.error(models_result.get("error"))
        else:
            models = models_result.get("items", [])
            if not models:
                st.info("No models configured yet. Add your first model!")
            else:
                for model in models:
                    with st.expander(f"{'🟢' if model.get('is_active') else '🔴'} {model.get('display_name', model.get('name'))}"):
                        col1, col2, col3 = st.columns([2, 2, 1])
                        with col1:
                            st.write(f"**Name:** {model.get('name')}")
                            st.write(f"**Provider:** {model.get('provider')}")
                            st.write(f"**Model ID:** {model.get('model_id')}")
                            st.write(f"**Base URL:** {model.get('base_url')}")
                        with col2:
                            st.write(f"**Temperature:** {model.get('temperature')}")
                            st.write(f"**Max Tokens:** {model.get('max_tokens')}")
                            st.write(f"**Context Length:** {model.get('context_length')}")
                            st.write(f"**Status:** {'Active' if model.get('is_active') else 'Inactive'}")
                        with col3:
                            if st.button("🗑️ Delete", key=f"del_model_{model.get('_id')}"):
                                result = api_request("DELETE", f"/admin/models/{model.get('_id')}")
                                if result.get("success"):
                                    st.success("Model deleted!")
                                    st.rerun()
                                else:
                                    st.error(result.get("error", result.get("message")))
    with tab2:
        st.markdown('<p class="sub-header">Add New Model</p>', unsafe_allow_html=True)
        with st.form("add_model_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Name (unique identifier)", placeholder="my-model")
                display_name = st.text_input("Display Name", placeholder="My Model")
                description = st.text_area("Description", placeholder="Model description...")
                provider = st.selectbox("Provider", ["ollama", "openai", "anthropic", "custom"])
            with col2:
                base_url = st.text_input("Base URL", placeholder="http://ollama:11434")
                model_id = st.text_input("Model ID", placeholder="llama3")
                api_key = st.text_input("API Key (optional)", type="password")
                temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
            col3, col4 = st.columns(2)
            with col3:
                max_tokens = st.number_input("Max Tokens", min_value=1, max_value=128000, value=2048)
            with col4:
                context_length = st.number_input("Context Length", min_value=1, max_value=200000, value=4096)
            is_active = st.checkbox("Active", value=True)
            submitted = st.form_submit_button("➕ Add Model")
            if submitted:
                if not name or not display_name or not base_url or not model_id:
                    st.error("Please fill in all required fields")
                else:
                    model_data = {
                        "name": name,
                        "display_name": display_name,
                        "description": description,
                        "provider": provider,
                        "base_url": base_url,
                        "model_id": model_id,
                        "api_key": api_key if api_key else None,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "context_length": context_length,
                        "is_active": is_active,
                        "headers": {}
                    }
                    result = api_request("POST", "/admin/models", model_data)
                    if result.get("success"):
                        st.success(f"Model '{name}' created successfully!")
                        st.rerun()
                    else:
                        st.error(result.get("error", result.get("detail", "Failed to create model")))


def render_endpoints():
    st.markdown('<p class="main-header">🔗 Endpoint Management</p>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📋 List Endpoints", "➕ Add Endpoint"])
    with tab1:
        endpoints_result = api_request("GET", "/admin/endpoints?limit=100")
        if "error" in endpoints_result:
            st.error(endpoints_result.get("error"))
        else:
            endpoints = endpoints_result.get("items", [])
            if not endpoints:
                st.info("No endpoints configured yet. Add your first endpoint!")
            else:
                for endpoint in endpoints:
                    with st.expander(f"{'🟢' if endpoint.get('is_active') else '🔴'} {endpoint.get('name')} ({endpoint.get('endpoint_path')})"):
                        col1, col2, col3 = st.columns([2, 2, 1])
                        with col1:
                            st.write(f"**Name:** {endpoint.get('name')}")
                            st.write(f"**Path:** /api/v1/{endpoint.get('endpoint_path')}")
                            st.write(f"**Method:** {endpoint.get('method')}")
                            st.write(f"**Model ID:** {endpoint.get('model_id')}")
                        with col2:
                            st.write(f"**Rate Limit:** {endpoint.get('rate_limit')} req/min")
                            st.write(f"**Status:** {'Active' if endpoint.get('is_active') else 'Inactive'}")
                            st.write(f"**Description:** {endpoint.get('description', 'N/A')}")
                        with col3:
                            if st.button("🗑️ Delete", key=f"del_ep_{endpoint.get('_id')}"):
                                result = api_request("DELETE", f"/admin/endpoints/{endpoint.get('_id')}")
                                if result.get("success"):
                                    st.success("Endpoint deleted!")
                                    st.rerun()
                                else:
                                    st.error(result.get("error", result.get("message")))
    with tab2:
        st.markdown('<p class="sub-header">Add New Endpoint</p>', unsafe_allow_html=True)
        models_result = api_request("GET", "/admin/models?limit=100")
        models = models_result.get("items", []) if "error" not in models_result else []
        if not models:
            st.warning("No models available. Please add a model first.")
        else:
            with st.form("add_endpoint_form"):
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("Name (unique identifier)", placeholder="chat-endpoint")
                    endpoint_path = st.text_input("Endpoint Path", placeholder="chat/v1")
                    description = st.text_area("Description", placeholder="Endpoint description...")
                with col2:
                    model_options = {f"{m.get('display_name', m.get('name'))} ({m.get('provider')})": m.get('_id') for m in models}
                    selected_model = st.selectbox("Select Model", list(model_options.keys()))
                    model_id = model_options.get(selected_model, "")
                    method = st.selectbox("HTTP Method", ["POST", "GET"])
                    rate_limit = st.number_input("Rate Limit (req/min)", min_value=1, max_value=10000, value=60)
                st.markdown("**Request Template**")
                col3, col4 = st.columns(2)
                with col3:
                    prompt_field = st.text_input("Prompt Field", value="prompt")
                with col4:
                    system_prompt = st.text_input("Default System Prompt (optional)")
                st.markdown("**Response Mapping**")
                content_field = st.text_input("Content Field", value="response")
                is_active = st.checkbox("Active", value=True)
                submitted = st.form_submit_button("➕ Add Endpoint")
                if submitted:
                    if not name or not endpoint_path or not model_id:
                        st.error("Please fill in all required fields")
                    else:
                        endpoint_data = {
                            "name": name,
                            "description": description,
                            "model_id": model_id,
                            "endpoint_path": endpoint_path,
                            "method": method,
                            "request_template": {
                                "prompt_field": prompt_field,
                                "system_prompt": system_prompt if system_prompt else None,
                                "include_fields": []
                            },
                            "response_mapping": {
                                "content_field": content_field
                            },
                            "rate_limit": rate_limit,
                            "is_active": is_active
                        }
                        result = api_request("POST", "/admin/endpoints", endpoint_data)
                        if result.get("success"):
                            st.success(f"Endpoint '{name}' created successfully!")
                            st.rerun()
                        else:
                            st.error(result.get("error", result.get("detail", "Failed to create endpoint")))


def render_schemas():
    st.markdown('<p class="main-header">📄 Schema Registry</p>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📋 List Schemas", "➕ Add Schema"])
    with tab1:
        schemas_result = api_request("GET", "/admin/schemas")
        if "error" in schemas_result:
            st.warning(f"Schema registry unavailable: {schemas_result.get('error')}")
            st.info("Make sure Apicurio Registry is running.")
        else:
            artifacts = schemas_result.get("artifacts", [])
            if not artifacts:
                st.info("No schemas registered yet.")
            else:
                for artifact in artifacts:
                    with st.expander(f"📄 {artifact.get('id', artifact.get('artifactId', 'Unknown'))}"):
                        st.write(f"**Type:** {artifact.get('type', artifact.get('artifactType', 'N/A'))}")
                        st.write(f"**State:** {artifact.get('state', 'N/A')}")
                        if st.button("🗑️ Delete", key=f"del_schema_{artifact.get('id', artifact.get('artifactId'))}"):
                            result = api_request("DELETE", f"/admin/schemas/{artifact.get('id', artifact.get('artifactId'))}")
                            if result.get("success"):
                                st.success("Schema deleted!")
                                st.rerun()
                            else:
                                st.error(result.get("error"))
    with tab2:
        st.markdown('<p class="sub-header">Register New Schema</p>', unsafe_allow_html=True)
        with st.form("add_schema_form"):
            artifact_id = st.text_input("Artifact ID", placeholder="my-schema")
            group_id = st.text_input("Group ID", value="llm-admin")
            artifact_type = st.selectbox("Schema Type", ["JSON", "AVRO", "PROTOBUF", "OPENAPI"])
            name = st.text_input("Name (optional)")
            description = st.text_input("Description (optional)")
            content = st.text_area("Schema Content", height=200, placeholder='{"type": "object", "properties": {...}}')
            submitted = st.form_submit_button("📄 Register Schema")
            if submitted:
                if not artifact_id or not content:
                    st.error("Please provide artifact ID and content")
                else:
                    schema_data = {
                        "artifact_id": artifact_id,
                        "group_id": group_id,
                        "artifact_type": artifact_type,
                        "name": name if name else None,
                        "description": description if description else None,
                        "content": content
                    }
                    result = api_request("POST", "/admin/schemas", schema_data)
                    if result.get("success"):
                        st.success(f"Schema '{artifact_id}' registered!")
                        st.rerun()
                    else:
                        st.error(result.get("error"))


def render_test():
    st.markdown('<p class="main-header">🧪 Test Models</p>', unsafe_allow_html=True)
    models_result = api_request("GET", "/admin/models?is_active=true&limit=100")
    models = models_result.get("items", []) if "error" not in models_result else []
    if not models:
        st.warning("No active models available for testing.")
        return
    model_options = {f"{m.get('display_name', m.get('name'))} ({m.get('provider')})": m.get('_id') for m in models}
    selected_model = st.selectbox("Select Model to Test", list(model_options.keys()))
    model_id = model_options.get(selected_model, "")
    with st.form("test_model_form"):
        system_prompt = st.text_input("System Prompt (optional)", placeholder="You are a helpful assistant...")
        prompt = st.text_area("Prompt", height=150, placeholder="Enter your prompt here...")
        col1, col2 = st.columns(2)
        with col1:
            temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
        with col2:
            max_tokens = st.number_input("Max Tokens", min_value=1, max_value=128000, value=2048)
        submitted = st.form_submit_button("🚀 Test Model")
        if submitted:
            if not prompt:
                st.error("Please enter a prompt")
            else:
                with st.spinner("Testing model..."):
                    test_data = {
                        "prompt": prompt,
                        "system_prompt": system_prompt if system_prompt else None,
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    }
                    result = api_request("POST", f"/admin/models/{model_id}/test", test_data)
                if result.get("success"):
                    st.markdown('<div class="success-box">', unsafe_allow_html=True)
                    st.markdown("### ✅ Test Successful")
                    st.write(f"**Model:** {result.get('model_name')}")
                    st.write(f"**Latency:** {result.get('latency_ms', 0):.2f} ms")
                    st.markdown("**Response:**")
                    st.write(result.get("response", "No response"))
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="error-box">', unsafe_allow_html=True)
                    st.markdown("### ❌ Test Failed")
                    st.write(f"**Error:** {result.get('error', 'Unknown error')}")
                    st.markdown('</div>', unsafe_allow_html=True)


def main():
    logger.info("event=admin_app_render")
    page = render_sidebar()
    if page == "Dashboard":
        render_dashboard()
    elif page == "Models":
        render_models()
    elif page == "Endpoints":
        render_endpoints()
    elif page == "Schemas":
        render_schemas()
    elif page == "Test":
        render_test()


if __name__ == "__main__":
    main()
