# Graph Visualization Feature - Implementation Guide

## Overview
Added interactive knowledge graph visualization to the LLM Chat application. Users can now visualize their conversation history and knowledge graph directly in the Streamlit UI using PyVis.

## Features Implemented

### 1. **Graph Visualization Service** (`core/services/graph_visualization_service.py`)
   - **Cypher Query Generation**: Automatically generates Neo4j Cypher queries based on user input
   - **Graph Data Fetching**: Executes queries and retrieves graph data from Neo4j
   - **Interactive Visualization**: Creates beautiful, interactive PyVis graphs
   - **Graph Statistics**: Calculates and displays graph metrics

#### Key Methods:
- `generate_cypher_query(user_query, query_type)` - Generates intelligent Cypher queries
- `fetch_graph_data(cypher_query)` - Fetches data from Neo4j
- `create_visualization(graph_data, output_file, title)` - Creates PyVis HTML visualization
- `get_graph_statistics(graph_data)` - Calculates graph metrics

### 2. **Streamlit UI Integration** (`app/streamlit_app.py`)
   - **Graph Toggle Button**: "🔍 Visualize Graph" button in sidebar
   - **Graph Visualization Panel**: Full-width interactive graph display
   - **Graph Statistics Display**: Shows nodes, edges, density, and node types
   - **Cypher Query Inspector**: Expandable section showing the generated query

#### New Functions:
- `visualize_knowledge_graph(user_query)` - Main visualization function
- Graph state management in session state

### 3. **Enhanced UI Components** (`app/ui_components.py`)
   - **Graph Visualization Section**: New sidebar expander with controls
   - **Query Type Selection**: Radio buttons for different query types
   - **Custom Query Input**: Text input for custom Cypher queries
   - **Generate Graph Button**: Triggers graph visualization

#### Query Types:
- **General**: Comprehensive view of all conversations and relationships
- **Topics**: Filter by conversation topics
- **Entities**: Show mentioned entities and their relationships
- **Emotions**: Visualize emotional patterns across conversations
- **Conversation Chain**: Show conversation progression and sequences

### 4. **Fixed Docker Build Issue**
   - **Updated requirements.txt** with missing dependencies:
     - `pyvis==0.3.2` - Interactive graph visualization
     - `networkx==3.2.1` - Graph data structure and algorithms
     - `lxml==4.9.3` - XML parsing for BeautifulSoup
     - `certifi==2023.7.22` - SSL certificate verification

## How to Use

### For Users:
1. **Enable Graph Visualization**:
   - Click "📊 Graph Visualization" in the sidebar
   - Select a query type or enter a custom query
   - Click "Generate Graph"

2. **Interact with the Graph**:
   - Drag nodes to rearrange
   - Zoom and pan with mouse
   - Hover over nodes to see details
   - Click nodes to highlight connections

3. **View Statistics**:
   - See total nodes, edges, density, and node types
   - Breakdown of each node type count

4. **Inspect Query**:
   - Expand "📝 Cypher Query Used" to see the generated query
   - Understand what data is being visualized

### For Developers:

#### Basic Usage:
```python
from core.services.graph_visualization_service import GraphVisualizationService

# Generate Cypher query
query = GraphVisualizationService.generate_cypher_query("Show conversations about Python")

# Fetch graph data
graph_data, error = GraphVisualizationService.fetch_graph_data(query)

# Create visualization
file_path, error = GraphVisualizationService.create_visualization(
    graph_data,
    output_file="graph.html",
    title="My Knowledge Graph"
)

# Get statistics
stats = GraphVisualizationService.get_graph_statistics(graph_data)
```

#### Custom Query Types:
```python
# Topic-based
query = GraphVisualizationService.generate_cypher_query(
    "Show me all discussions about machine learning",
    query_type="topic"
)

# Entity-based
query = GraphVisualizationService.generate_cypher_query(
    "What entities are mentioned?",
    query_type="entity"
)

# Emotion-based
query = GraphVisualizationService.generate_cypher_query(
    "Show emotional patterns",
    query_type="emotion"
)

# Conversation chain
query = GraphVisualizationService.generate_cypher_query(
    "Show conversation flow",
    query_type="conversation_chain"
)
```

## Graph Data Structure

### Nodes:
- **User**: Represents a user in the system
- **Conversation**: Represents a single Q&A exchange
- **Topic**: Represents discussion topics
- **Entity**: Represents mentioned entities
- **Emotion**: Represents emotional states
- **Model**: Represents AI models used

### Edges (Relationships):
- **ASKED**: User asked a question (User → Conversation)
- **RESPONDED_TO**: Model responded (Model → Conversation)
- **ABOUT**: Conversation is about a topic (Conversation → Topic)
- **MENTIONS**: Conversation mentions an entity (Conversation → Entity)
- **FEELS**: Conversation has an emotion (Conversation → Emotion)
- **FOLLOWED_BY**: Conversation sequence (Conversation → Conversation)

## Visualization Features

### Interactive Elements:
- **Physics Simulation**: Nodes automatically arrange using force-directed layout
- **Navigation**: Zoom, pan, and drag nodes
- **Highlighting**: Click nodes to highlight connected relationships
- **Tooltips**: Hover to see node details
- **Full Screen**: Expand visualization to full screen

### Customization:
- Physics parameters (gravity, spring length, damping)
- Node colors based on type
- Edge labels showing relationship types
- Interactive navigation buttons

## Error Handling

The feature includes comprehensive error handling:
- **Neo4j Unavailable**: Falls back gracefully with informative message
- **Query Execution Errors**: Displays error details to user
- **Visualization Errors**: Shows error message and logs details
- **Empty Results**: Displays helpful message to continue chatting

## Performance Considerations

- **Query Limits**: Queries limited to 50 records by default
- **Lazy Loading**: Graph only generated when requested
- **Caching**: Graph data stored in session state
- **Async**: Uses Streamlit spinners for long operations

## Testing

To test the feature:

1. **Start the application**:
   ```bash
   cd service/llm_chat_app
   streamlit run app/streamlit_app.py
   ```

2. **Have a conversation**:
   - Ask several questions to build knowledge graph
   - Wait for conversations to be stored in Neo4j

3. **Visualize the graph**:
   - Click "📊 Graph Visualization" in sidebar
   - Select query type or enter custom query
   - Click "Generate Graph"
   - Interact with the visualization

## Dependencies Added

```
pyvis==0.3.2          # Interactive graph visualization
networkx==3.2.1       # Graph algorithms and data structures
lxml==4.9.3           # XML parsing support
certifi==2023.7.22    # SSL certificate verification
```

## Future Enhancements

- [ ] Export graph as image (PNG, SVG)
- [ ] Export graph data (JSON, GraphML)
- [ ] Advanced filtering options
- [ ] Graph comparison between users
- [ ] Real-time graph updates
- [ ] Custom node styling
- [ ] Graph search and filtering
- [ ] Community detection
- [ ] Path finding between nodes

## Troubleshooting

### Graph not showing data:
- Ensure Neo4j is running and accessible
- Check that conversations have been stored (check logs)
- Try a different query type

### Visualization is slow:
- Reduce the query limit in `generate_cypher_query()`
- Use more specific query types instead of "General"
- Check Neo4j performance

### Docker build fails:
- Ensure all dependencies in `requirements.txt` are compatible
- Check Python version (3.11 in Dockerfile)
- Clear Docker cache: `docker system prune`

## Files Modified

1. **requirements.txt** - Added graph visualization dependencies
2. **app/streamlit_app.py** - Added graph visualization integration
3. **app/ui_components.py** - Added graph visualization UI controls
4. **core/services/graph_visualization_service.py** - New service (created)

## Commit Information

All changes have been committed with timestamp:
```
Auto-commit: 2025-11-16 19:56:52
```
