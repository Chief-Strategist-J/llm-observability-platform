# Quick Start - Graph Visualization Feature

## What Was Added?

✅ **Interactive Knowledge Graph Visualization** in your Streamlit chat app
✅ **Automatic Cypher Query Generation** based on user input
✅ **Beautiful PyVis Interactive Graphs** with physics simulation
✅ **Graph Statistics & Metrics** display
✅ **Fixed Docker Build** with missing dependencies

## How to Use It

### Step 1: Start the App
```bash
cd service/llm_chat_app
streamlit run app/streamlit_app.py
```

### Step 2: Have a Conversation
- Sign in to your account
- Ask the LLM several questions
- Your conversations are automatically stored in Neo4j

### Step 3: Visualize Your Knowledge Graph
1. Look for **"📊 Graph Visualization"** in the left sidebar
2. Choose a query type:
   - **General** - See everything
   - **Topics** - Filter by topics discussed
   - **Entities** - Show mentioned entities
   - **Emotions** - Visualize emotional patterns
   - **Conversation Chain** - Show conversation flow
3. (Optional) Enter a custom query like "Show conversations about Python"
4. Click **"Generate Graph"**

### Step 4: Interact with the Graph
- **Drag** nodes to rearrange
- **Scroll** to zoom in/out
- **Hover** over nodes to see details
- **Click** nodes to highlight connections
- Use navigation buttons in the top-left

## What You'll See

### Graph Statistics
- 📍 **Nodes**: Total number of nodes in the graph
- 🔗 **Edges**: Total connections between nodes
- **Density**: How connected the graph is (0-1)
- **Node Types**: Breakdown of different node categories

### Interactive Visualization
- **Colored nodes** by type (User, Conversation, Topic, Entity, Emotion, Model)
- **Labeled edges** showing relationship types
- **Physics simulation** for automatic layout
- **Smooth animations** when interacting

### Query Inspector
- Expand **"📝 Cypher Query Used"** to see the exact Neo4j query
- Useful for understanding what data is being visualized
- Can be used for debugging or custom queries

## Docker Build Fix

The Docker build was failing due to missing dependencies. Fixed by adding:
- `pyvis` - Graph visualization
- `networkx` - Graph algorithms
- `lxml` - XML parsing
- `certifi` - SSL certificates

To rebuild the Docker image:
```bash
cd service/llm_chat_app
docker build -t llm_chat_app:latest .
```

## File Changes

| File | Changes |
|------|---------|
| `requirements.txt` | Added 4 new dependencies |
| `app/streamlit_app.py` | Added graph visualization integration |
| `app/ui_components.py` | Added graph controls in sidebar |
| `core/services/graph_visualization_service.py` | **NEW** - Graph service |
| `GRAPH_VISUALIZATION_FEATURE.md` | **NEW** - Full documentation |

## Example Queries

### Show all conversations about a topic
```
"Show me conversations about Python"
```

### Show emotional patterns
```
"What emotions are present in my conversations?"
```

### Show conversation flow
```
"Show the sequence of my conversations"
```

### Show entities mentioned
```
"What entities have been mentioned?"
```

## Troubleshooting

### Graph shows no data
- Make sure you've had conversations (they need to be stored in Neo4j)
- Check that Neo4j is running
- Try a different query type

### Visualization is slow
- Try a more specific query type instead of "General"
- Reduce the number of conversations

### Docker build fails
- Run: `docker system prune`
- Rebuild: `docker build -t llm_chat_app:latest .`

## Next Steps

1. **Test the feature**: Have conversations and visualize the graph
2. **Customize queries**: Try different query types
3. **Export data**: (Coming soon) Export graph as image or data file
4. **Advanced features**: (Coming soon) Community detection, path finding

## Support

For issues or questions:
1. Check `GRAPH_VISUALIZATION_FEATURE.md` for detailed documentation
2. Review the logs in the terminal
3. Check Neo4j connection settings in `.env.llm_chat_app`

---

**Enjoy exploring your knowledge graph! 🎉**
