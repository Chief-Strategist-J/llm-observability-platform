"""
Examples of using advanced features
- Real-time streaming
- Collaboration
- Intelligent agent with tools
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.services.collaboration_service import CollaborationService
from core.services.intelligent_agent import IntelligentAgent
from core.client.streaming_client import StreamingClient
from core.client.web_search_tools import WebSearchTools


def example_1_web_search():
    """Example 1: Web Search"""
    print("\n=== Example 1: Web Search ===\n")
    
    result = WebSearchTools.web_search("Python programming", count=5)
    
    if result.get("success"):
        print(f"Found {result['count']} results for: {result['query']}\n")
        for i, res in enumerate(result["results"], 1):
            print(f"{i}. {res['title']}")
            print(f"   URL: {res['url']}")
            print(f"   {res['description'][:100]}...\n")
    else:
        print(f"Error: {result.get('error')}")


def example_2_visit_url():
    """Example 2: Visit URL and Extract Content"""
    print("\n=== Example 2: Visit URL ===\n")
    
    url = "https://www.python.org"
    result = WebSearchTools.visit_url(url)
    
    if result.get("success"):
        print(f"Title: {result['title']}")
        print(f"Content length: {result['length']} characters")
        print(f"\nFirst 500 characters:\n{result['content'][:500]}...")
    else:
        print(f"Error: {result.get('error')}")


def example_3_collaboration():
    """Example 3: Collaboration Session"""
    print("\n=== Example 3: Collaboration ===\n")
    
    # Create session
    print("Creating session...")
    session = CollaborationService.create_session(
        name="Team AI Discussion",
        created_by="alice",
        settings={"model": "@cf/meta/llama-3.2-1b-instruct"}
    )
    
    session_id = session["session_id"]
    print(f"Session created: {session_id}\n")
    
    # Join session
    print("User 'bob' joining session...")
    CollaborationService.join_session(session_id, "bob")
    
    # Add messages
    print("Adding messages...\n")
    CollaborationService.add_message(
        session_id=session_id,
        user="alice",
        role="user",
        content="What's the best way to learn Python?",
        metadata={"source": "streamlit"}
    )
    
    CollaborationService.add_message(
        session_id=session_id,
        user="bob",
        role="user",
        content="I agree, let's discuss learning strategies"
    )
    
    # Get session info
    session_info = CollaborationService.get_session(session_id)
    print(f"Session: {session_info['session']['name']}")
    print(f"Participants: {session_info['session']['participants']}")
    print(f"Messages: {len(session_info['messages'])}\n")
    
    # List sessions
    print("Alice's sessions:")
    sessions = CollaborationService.list_sessions("alice")
    for s in sessions["sessions"]:
        print(f"  - {s['name']} ({s['session_id']})")


def example_4_intelligent_agent():
    """Example 4: Intelligent Agent with Tools"""
    print("\n=== Example 4: Intelligent Agent ===\n")
    
    # Process with tools
    print("Processing request with web search tools...\n")
    
    result = IntelligentAgent.process_with_tools(
        prompt="What are the latest trends in artificial intelligence?",
        model="@cf/meta/llama-3.2-1b-instruct",
        enable_web_search=True,
        max_iterations=2
    )
    
    if result.get("success"):
        print(f"Response:\n{result['response']}\n")
        print(f"Iterations: {result['iterations']}")
        print(f"Tools used: {result['tool_count']}")
        
        if result["tool_results"]:
            print("\nTool Results:")
            for tool_result in result["tool_results"]:
                print(f"  Tool: {tool_result['tool']}")
                print(f"  Params: {tool_result['params']}")
    else:
        print(f"Error: {result.get('error')}")


def example_5_research_analysis():
    """Example 5: Research Analysis"""
    print("\n=== Example 5: Research Analysis ===\n")
    
    print("Analyzing topic with research...\n")
    
    result = IntelligentAgent.analyze_with_research(
        topic="Machine Learning",
        model="@cf/meta/llama-3.2-1b-instruct",
        depth="standard"
    )
    
    if result.get("success"):
        print(f"Topic: {result['topic']}")
        print(f"Sources: {result['sources']}")
        print(f"\nAnalysis:\n{result['analysis'][:500]}...\n")
        
        if result["research_results"]:
            print("Research Sources:")
            for source in result["research_results"][:3]:
                print(f"  - {source['title']}")
                print(f"    {source['url']}")
    else:
        print(f"Error: {result.get('error')}")


async def example_6_streaming():
    """Example 6: Streaming Response"""
    print("\n=== Example 6: Streaming Response ===\n")
    
    print("Streaming response:\n")
    
    async for chunk in StreamingClient.stream_response(
        prompt="Explain quantum computing in simple terms",
        model="@cf/meta/llama-3.2-1b-instruct"
    ):
        print(chunk, end="", flush=True)
    
    print("\n")


def main():
    """Run all examples"""
    
    print("=" * 60)
    print("Advanced Features Examples")
    print("=" * 60)
    
    try:
        # Example 1: Web Search
        example_1_web_search()
        
        # Example 2: Visit URL
        # example_2_visit_url()  # Commented out to avoid network calls
        
        # Example 3: Collaboration
        example_3_collaboration()
        
        # Example 4: Intelligent Agent
        # example_4_intelligent_agent()  # Commented out - requires API key
        
        # Example 5: Research Analysis
        # example_5_research_analysis()  # Commented out - requires API key
        
        # Example 6: Streaming (async)
        # asyncio.run(example_6_streaming())  # Commented out - requires API key
        
        print("\n" + "=" * 60)
        print("Examples completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
