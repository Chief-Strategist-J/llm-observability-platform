import os
from dotenv import load_dotenv
from langchain_neo4j import Neo4jGraph

load_dotenv()

def get_graph():
    uri = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
    auth = os.getenv("NEO4J_AUTH", "neo4j/Scaibu@123")

    try:
        user, password = auth.split("/", 1)
    except ValueError:
        raise RuntimeError("Invalid NEO4J_AUTH format. Use 'username/password'.")

    try:
        g = Neo4jGraph(url=uri, username=user, password=password)
        _ = g.query("RETURN 1 AS ok")
        return g
    except Exception as e:
        raise RuntimeError(f"Neo4j connection failed: {e}")

graph = get_graph()
