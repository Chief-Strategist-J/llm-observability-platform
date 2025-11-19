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
from core.services.graph_visualization_service import GraphVisualizationService
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
    
    if "show_graph" not in st.session_state:
        st.session_state.show_graph = False
        st.session_state.graph_data = None
        st.session_state.cypher_query = None
    
    if "scroll_to_bottom" not in st.session_state:
        st.session_state.scroll_to_bottom = False
    
    if "graph_view_mode" not in st.session_state:
        st.session_state.graph_view_mode = "full"
    
    if "graph_time_filter" not in st.session_state:
        st.session_state.graph_time_filter = "all"
    
    if "graph_node_filters" not in st.session_state:
        st.session_state.graph_node_filters = {
            "User": True,
            "Conversation": True,
            "Topic": True,
            "Entity": True,
            "Emotion": True,
            "Model": True
        }
    
    if "selected_node_data" not in st.session_state:
        st.session_state.selected_node_data = None


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
    
    SidebarUI.graph_visualization_section()
    
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


def render_graph_controls():
    st.markdown("### 🎛️ Graph Controls")
    
    col1, col2 = st.columns(2)
    
    with col1:
        view_mode = st.selectbox(
            "View Mode",
            ["full", "conversation_flow", "topic_map", "entity_network", "emotion_trend"],
            index=["full", "conversation_flow", "topic_map", "entity_network", "emotion_trend"].index(st.session_state.graph_view_mode),
            help="Select visualization focus"
        )
        if view_mode != st.session_state.graph_view_mode:
            st.session_state.graph_view_mode = view_mode
            logger.info("event=graph_view_mode_changed mode=%s user=%s", view_mode, st.session_state.username)
    
    with col2:
        time_filter = st.selectbox(
            "Time Range",
            ["all", "24h", "7d", "30d"],
            index=["all", "24h", "7d", "30d"].index(st.session_state.graph_time_filter),
            help="Filter by time period"
        )
        if time_filter != st.session_state.graph_time_filter:
            st.session_state.graph_time_filter = time_filter
            logger.info("event=graph_time_filter_changed filter=%s user=%s", time_filter, st.session_state.username)
    
    st.markdown("#### Node Type Filters")
    filter_cols = st.columns(6)
    
    node_types = ["User", "Conversation", "Topic", "Entity", "Emotion", "Model"]
    for idx, node_type in enumerate(node_types):
        with filter_cols[idx]:
            current_value = st.session_state.graph_node_filters.get(node_type, True)
            new_value = st.checkbox(node_type, value=current_value, key=f"filter_{node_type}")
            if new_value != current_value:
                st.session_state.graph_node_filters[node_type] = new_value
                logger.info("event=graph_node_filter_changed node_type=%s enabled=%s user=%s", 
                          node_type, new_value, st.session_state.username)


def generate_view_specific_query(view_mode: str, time_filter: str, username: str) -> str:
    logger.info("event=generate_view_query view_mode=%s time_filter=%s user=%s", 
               view_mode, time_filter, username)
    
    time_clause = ""
    if time_filter == "24h":
        time_clause = "AND c.ts > datetime() - duration('P1D')"
    elif time_filter == "7d":
        time_clause = "AND c.ts > datetime() - duration('P7D')"
    elif time_filter == "30d":
        time_clause = "AND c.ts > datetime() - duration('P30D')"
    
    if view_mode == "conversation_flow":
        query = f"""
        MATCH (u:User {{name: '{username}'}})-[:ASKED]->(c:Conversation)
        WHERE 1=1 {time_clause}
        OPTIONAL MATCH (c)-[:FOLLOWED_BY]->(next:Conversation)
        OPTIONAL MATCH (c)-[:FEELS]->(em:Emotion)
        RETURN u, c, next, em
        ORDER BY c.ts DESC
        LIMIT 100
        """
    elif view_mode == "topic_map":
        query = f"""
        MATCH (u:User {{name: '{username}'}})-[:ASKED]->(c:Conversation)-[:ABOUT]->(t:Topic)
        WHERE 1=1 {time_clause}
        OPTIONAL MATCH (c)-[:MENTIONS]->(e:Entity)
        RETURN u, c, t, e
        ORDER BY c.ts DESC
        LIMIT 100
        """
    elif view_mode == "entity_network":
        query = f"""
        MATCH (u:User {{name: '{username}'}})-[:ASKED]->(c:Conversation)-[:MENTIONS]->(e:Entity)
        WHERE 1=1 {time_clause}
        OPTIONAL MATCH (c)-[:ABOUT]->(t:Topic)
        RETURN u, c, e, t
        ORDER BY c.ts DESC
        LIMIT 100
        """
    elif view_mode == "emotion_trend":
        query = f"""
        MATCH (u:User {{name: '{username}'}})-[:ASKED]->(c:Conversation)-[:FEELS]->(em:Emotion)
        WHERE 1=1 {time_clause}
        OPTIONAL MATCH (c)-[:ABOUT]->(t:Topic)
        RETURN u, c, em, t
        ORDER BY c.ts DESC
        LIMIT 100
        """
    else:
        query = f"""
        MATCH (u:User {{name: '{username}'}})-[:ASKED]->(c:Conversation)
        WHERE 1=1 {time_clause}
        OPTIONAL MATCH (c)-[:ABOUT]->(t:Topic)
        OPTIONAL MATCH (c)-[:MENTIONS]->(e:Entity)
        OPTIONAL MATCH (c)-[:FEELS]->(em:Emotion)
        OPTIONAL MATCH (m:Model)-[:RESPONDED_TO]->(c)
        RETURN u, c, t, e, em, m
        ORDER BY c.ts DESC
        LIMIT 100
        """
    
    return query.strip()


def visualize_knowledge_graph(user_query: str = None):
    logger.info("event=graph_visualization_start user=%s view_mode=%s time_filter=%s", 
               st.session_state.username, st.session_state.graph_view_mode, st.session_state.graph_time_filter)
    
    try:
        cypher_query = generate_view_specific_query(
            st.session_state.graph_view_mode,
            st.session_state.graph_time_filter,
            st.session_state.username
        )
        
        graph_data, error = GraphVisualizationService.fetch_graph_data(cypher_query)
        
        if error:
            if "Cannot resolve address" in error or "Connection failed" in error:
                st.warning("⚠️ Cannot connect to Neo4j. Please check if Neo4j is running and connection settings are correct.")
                st.info("💡 **Connection Issue**: Update your `.env.llm_chat_app` file to use `bolt://localhost:7687` instead of `bolt://neo4j-development:7687`")
            else:
                st.error(f"❌ Graph error: {error}")
            logger.warning("event=graph_fetch_failed error=%s user=%s", error, st.session_state.username)
            return
        
        if not graph_data or not graph_data.get("nodes"):
            st.info("📊 No conversations yet. Start chatting to build your knowledge graph!")
            return
        
        filtered_nodes = [
            node for node in graph_data["nodes"]
            if st.session_state.graph_node_filters.get(node.get("label", ""), True)
        ]
        
        filtered_node_ids = {node["id"] for node in filtered_nodes}
        filtered_edges = [
            edge for edge in graph_data["edges"]
            if edge["from"] in filtered_node_ids and edge["to"] in filtered_node_ids
        ]
        
        filtered_graph_data = {
            "nodes": filtered_nodes,
            "edges": filtered_edges,
            "record_count": graph_data.get("record_count", 0)
        }
        
        logger.info("event=graph_data_filtered original_nodes=%s filtered_nodes=%s original_edges=%s filtered_edges=%s", 
                   len(graph_data["nodes"]), len(filtered_nodes), len(graph_data["edges"]), len(filtered_edges))
        
        stats = GraphVisualizationService.get_graph_statistics(filtered_graph_data)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📍 Nodes", stats["total_nodes"])
        with col2:
            st.metric("🔗 Edges", stats["total_edges"])
        with col3:
            st.metric("Density", f"{stats['density']:.3f}")
        with col4:
            st.metric("Types", len(stats["node_types"]))
        
        if stats["node_types"]:
            st.markdown("#### Node Distribution")
            node_type_cols = st.columns(len(stats["node_types"]))
            for idx, (node_type, count) in enumerate(stats["node_types"].items()):
                with node_type_cols[idx % len(node_type_cols)]:
                    st.metric(node_type, count)
        
        output_file = "/tmp/graph_visualization.html"
        file_path, viz_error = GraphVisualizationService.create_visualization(
            filtered_graph_data,
            output_file=output_file,
            title=f"Knowledge Graph - {st.session_state.username}",
            view_mode=st.session_state.graph_view_mode
        )
        
        if viz_error:
            st.error(f"❌ Visualization failed: {viz_error}")
            logger.error("event=graph_visualization_failed error=%s user=%s", viz_error, st.session_state.username)
            return
        
        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        st.components.v1.html(html_content, height=800, scrolling=True)
        
        insights = GraphVisualizationService.generate_ai_insights(filtered_graph_data, st.session_state.username)
        if insights:
            st.markdown("### 🧠 AI-Generated Insights")
            for insight_type, insight_data in insights.items():
                if insight_data:
                    with st.expander(f"📊 {insight_type.replace('_', ' ').title()}", expanded=False):
                        if isinstance(insight_data, list):
                            for item in insight_data[:5]:
                                st.markdown(f"- {item}")
                        elif isinstance(insight_data, dict):
                            for key, value in list(insight_data.items())[:5]:
                                st.markdown(f"**{key}**: {value}")
                        else:
                            st.write(insight_data)
        
        logger.info("event=graph_visualization_success user=%s nodes=%s edges=%s view_mode=%s", 
                   st.session_state.username, stats["total_nodes"], stats["total_edges"], st.session_state.graph_view_mode)
        
    except Exception as e:
        st.warning("⚠️ Neo4j connection issue. Please update your `.env.llm_chat_app` file to use `bolt://localhost:7687`")
        logger.warning("event=graph_visualization_exception user=%s error=%s", 
                    st.session_state.username, str(e))


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

    if "active_tab" not in st.session_state:
        st.session_state.active_tab = "chat"
    
    tab_chat, tab_graph = st.tabs(["💬 Chat", "📊 Knowledge Graph"])
    
    with tab_chat:
        st.session_state.active_tab = "chat"
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["text"])

    if st.session_state.active_tab == "chat":
        prompt = st.chat_input("Type your message here...")
        
        if prompt:
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
            
            st.rerun()
    
    with tab_graph:
        st.session_state.active_tab = "graph"
        
        render_graph_controls()
        
        st.divider()
        
        with st.spinner("🔄 Loading knowledge graph..."):
            visualize_knowledge_graph()


if __name__ == "__main__":
    main()