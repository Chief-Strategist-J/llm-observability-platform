Usage
1. Ensure Temporal and Neo4j are running and reachable.
2. Build image:
   docker build -t llm_chat_app:latest .
3. Start worker (container runs worker by default):
   docker run --network temporal-network --name llm_chat_app llm_chat_app:latest
4. To run UI mode:
   docker run -p 8501:8501 --network temporal-network llm_chat_app:latest streamlit run main.py --server.port=8501 --server.address=0.0.0.0
5. Trigger setup:
   python triggers/chat_setup_trigger.py
6. Trigger cleanup:
   python triggers/chat_cleanup_trigger.py
