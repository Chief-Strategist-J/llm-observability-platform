# Advanced Features Documentation

## Overview

This document describes the advanced features added to the LLM Chatbot:
1. **Real-time Streaming Responses**
2. **Real-time Collaboration** (Multiple users, shared sessions)
3. **Intelligent Agent with Internet Tools**

---

## 1. Real-time Streaming Responses

### Overview
Stream AI responses token-by-token for a more interactive user experience.

### Module
`core/client/streaming_client.py`

### Usage

```python
from core.client.streaming_client import StreamingClient
import asyncio

async def stream_chat():
    async for chunk in StreamingClient.stream_response(
        prompt="What is Python?",
        model="@cf/meta/llama-3.2-1b-instruct",
        conversation_history=[]
    ):
        print(chunk, end="", flush=True)

asyncio.run(stream_chat())
```

### Features
- **Token-by-token streaming**: Responses appear as they're generated
- **Tool-aware streaming**: Supports streaming with tool usage
- **Async/await support**: Non-blocking streaming operations
- **Timeout handling**: Configurable request timeouts

### API

#### `StreamingClient.stream_response()`
Stream a response from the AI model.

**Parameters:**
- `prompt` (str): User prompt
- `model` (str): Model identifier
- `conversation_history` (List[Dict], optional): Previous messages
- `timeout` (int): Request timeout in seconds (default: 30)

**Yields:**
- Response tokens as strings

#### `StreamingClient.stream_with_tools()`
Stream response with tool usage capability.

**Parameters:**
- `prompt` (str): User prompt
- `model` (str): Model identifier
- `available_tools` (Dict): Available tools
- `conversation_history` (List[Dict], optional): Previous messages
- `max_iterations` (int): Max tool use iterations (default: 5)

**Yields:**
- Response tokens and tool results

---

## 2. Real-time Collaboration

### Overview
Enable multiple users to share chat sessions and collaborate in real-time.

### Module
`core/services/collaboration_service.py`

### Usage

```python
from core.services.collaboration_service import CollaborationService

# Create a session
session = CollaborationService.create_session(
    name="Team Discussion",
    created_by="user1",
    settings={"model": "@cf/meta/llama-3.2-1b-instruct"}
)
session_id = session["session_id"]

# Join the session
CollaborationService.join_session(session_id, "user2")

# Add messages
CollaborationService.add_message(
    session_id=session_id,
    user="user1",
    role="user",
    content="What's the best way to learn Python?",
    metadata={"source": "streamlit"}
)

# Get session info
session_info = CollaborationService.get_session(session_id)

# List user's sessions
sessions = CollaborationService.list_sessions("user1")

# Leave session
CollaborationService.leave_session(session_id, "user1")
```

### Features
- **Session creation**: Create collaborative chat sessions
- **Multi-user support**: Multiple users can join and participate
- **Message history**: Full message history with metadata
- **Persistence**: Sessions saved to disk
- **Real-time updates**: In-memory session tracking
- **Participant management**: Track who's in each session

### API

#### `CollaborationService.create_session()`
Create a new collaborative session.

**Parameters:**
- `name` (str): Session name
- `created_by` (str): User creating the session
- `settings` (Dict, optional): Session settings

**Returns:**
```json
{
  "success": true,
  "session_id": "uuid",
  "session": {
    "session_id": "uuid",
    "name": "Team Discussion",
    "created_by": "user1",
    "participants": ["user1"],
    "message_count": 0,
    "is_active": true
  }
}
```

#### `CollaborationService.join_session()`
Join an existing session.

**Parameters:**
- `session_id` (str): Session to join
- `user` (str): User joining

**Returns:**
- Session info and all messages

#### `CollaborationService.add_message()`
Add a message to a session.

**Parameters:**
- `session_id` (str): Session ID
- `user` (str): User sending message
- `role` (str): "user" or "assistant"
- `content` (str): Message content
- `metadata` (Dict, optional): Additional data

**Returns:**
- Message info with ID and timestamp

#### `CollaborationService.get_session()`
Get session information.

#### `CollaborationService.list_sessions()`
List all sessions for a user.

#### `CollaborationService.leave_session()`
Leave a session.

#### `CollaborationService.get_participants()`
Get list of participants in a session.

---

## 3. Intelligent Agent with Internet Tools

### Overview
Enable the AI to use web search and information extraction tools for intelligent reasoning.

### Modules
- `core/client/web_search_tools.py`: Web search and extraction tools
- `core/services/intelligent_agent.py`: Agent with reasoning and tool usage

### Usage

```python
from core.services.intelligent_agent import IntelligentAgent

# Process with tools
result = IntelligentAgent.process_with_tools(
    prompt="What are the latest trends in AI?",
    model="@cf/meta/llama-3.2-1b-instruct",
    enable_web_search=True,
    max_iterations=3
)

# Analyze with research
analysis = IntelligentAgent.analyze_with_research(
    topic="Machine Learning",
    model="@cf/meta/llama-3.2-1b-instruct",
    depth="deep"  # quick, standard, or deep
)
```

### Available Tools

#### 1. `web_search(query, count=10)`
Search the web using Brave Search API.

**Parameters:**
- `query` (str): Search query
- `count` (int): Number of results (max 20)

**Returns:**
```json
{
  "success": true,
  "query": "Python tutorials",
  "results": [
    {
      "title": "...",
      "url": "...",
      "description": "...",
      "type": "web"
    }
  ],
  "count": 10
}
```

#### 2. `visit_url(url)`
Visit a URL and extract text content.

**Parameters:**
- `url` (str): URL to visit

**Returns:**
```json
{
  "success": true,
  "url": "...",
  "title": "...",
  "content": "...",
  "length": 5000
}
```

#### 3. `extract_text(url, selector=None)`
Extract specific text from a URL using CSS selector.

**Parameters:**
- `url` (str): URL to extract from
- `selector` (str, optional): CSS selector

**Returns:**
```json
{
  "success": true,
  "url": "...",
  "selector": "...",
  "content": "...",
  "length": 3000
}
```

#### 4. `crawl_site(domain, max_pages=5)`
Crawl a website and extract links.

**Parameters:**
- `domain` (str): Domain to crawl
- `max_pages` (int): Maximum pages to crawl

**Returns:**
```json
{
  "success": true,
  "domain": "...",
  "pages_crawled": 5,
  "results": [
    {
      "url": "...",
      "title": "...",
      "links_found": 15
    }
  ]
}
```

#### 5. `get_news(topic, count=10)`
Get news articles about a topic.

**Parameters:**
- `topic` (str): Topic to search
- `count` (int): Number of results

**Returns:**
```json
{
  "success": true,
  "topic": "AI",
  "results": [
    {
      "title": "...",
      "url": "...",
      "description": "...",
      "source": "...",
      "published": "...",
      "type": "news"
    }
  ],
  "count": 10
}
```

### Configuration

Set the Brave Search API key:

```bash
export BRAVE_API_KEY="your_api_key_here"
```

Get your API key from: https://api.search.brave.com/

### Agent Reasoning

The intelligent agent:
1. Analyzes the user's request
2. Determines if tools are needed
3. Executes tools to gather information
4. Synthesizes results into a coherent response
5. Iterates if more information is needed (up to max_iterations)

Tool calls are formatted as:
```json
<tool_call>
{
  "tool": "web_search",
  "params": {"query": "Python tutorials", "count": 5}
}
</tool_call>
```

---

## Knowledge Graph Fixes

### Issue
The knowledge graph was not building properly because entities and topics were not being extracted correctly.

### Solution
Fixed `knowledge_graph_store.py` to properly extract entities and topics from the deep analysis results:

```python
# Extract entities and topics from deep_analysis
entities = deep_analysis.get("entities", [])
topics = deep_analysis.get("topics", [])

# Ensure they're lists
if not isinstance(entities, list):
    entities = [entities] if entities else []
if not isinstance(topics, list):
    topics = [topics] if topics else []
```

### Result
- Knowledge graph now properly stores conversation entities and topics
- Neo4j relationships are correctly created
- Fallback file storage works as expected

---

## Integration Examples

### Streamlit Integration

```python
import streamlit as st
from core.services.collaboration_service import CollaborationService
from core.services.intelligent_agent import IntelligentAgent
from core.client.streaming_client import StreamingClient
import asyncio

# Collaboration
if st.button("Create Shared Session"):
    session = CollaborationService.create_session(
        name="Team Chat",
        created_by=st.session_state.user
    )
    st.session_state.session_id = session["session_id"]

# Agent with tools
if st.button("Search and Analyze"):
    result = IntelligentAgent.process_with_tools(
        prompt=st.text_input("Your question"),
        model=st.session_state.model,
        enable_web_search=True
    )
    st.write(result["response"])

# Streaming
async def stream_response():
    async for chunk in StreamingClient.stream_response(
        prompt=st.text_input("Ask something"),
        model=st.session_state.model
    ):
        st.write(chunk, end="")

if st.button("Stream Response"):
    asyncio.run(stream_response())
```

---

## Performance Considerations

1. **Streaming**: Reduces perceived latency by showing responses as they arrive
2. **Collaboration**: Uses in-memory caching with disk persistence for scalability
3. **Web Tools**: Implements timeouts and error handling for reliability
4. **Agent**: Limits iterations to prevent infinite loops

---

## Security Notes

1. **API Keys**: Store BRAVE_API_KEY in environment variables, never hardcode
2. **Web Crawling**: Respects robots.txt and implements rate limiting
3. **User Isolation**: Collaboration sessions are user-specific
4. **Input Validation**: All tool parameters are validated before execution

---

## Troubleshooting

### Web Search Not Working
- Verify BRAVE_API_KEY is set
- Check API key is valid at https://api.search.brave.com/
- Ensure network connectivity

### Collaboration Session Not Found
- Session may have expired (check is_active flag)
- Verify session_id is correct
- Check collaboration_sessions directory exists

### Streaming Timeout
- Increase timeout parameter
- Check model availability
- Verify network connectivity

---

## Future Enhancements

1. WebSocket support for real-time streaming
2. Redis integration for distributed collaboration
3. Additional tools (email, calendar, database queries)
4. Advanced reasoning with chain-of-thought
5. Multi-modal support (images, documents)
