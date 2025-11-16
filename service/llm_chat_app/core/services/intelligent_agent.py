import logging
import json
import re
from typing import Dict, List, Any, Optional
from core.client.web_search_tools import WebSearchTools, AVAILABLE_TOOLS
from core.client.cloudflare_client import run_model

logger = logging.getLogger(__name__)

class IntelligentAgent:
    
    @staticmethod
    def process_with_tools(
        prompt: str,
        model: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        max_iterations: int = 3,
        enable_web_search: bool = True
    ) -> Dict[str, Any]:
        
        if not prompt or not isinstance(prompt, str):
            return {"success": False, "error": "Invalid prompt"}
        
        if not model or not isinstance(model, str):
            return {"success": False, "error": "Invalid model"}
        
        logger.info("event=agent_process_start prompt_len=%s model=%s enable_web_search=%s", 
                   len(prompt), model, enable_web_search)
        
        messages = []
        if conversation_history and isinstance(conversation_history, list):
            messages.extend(conversation_history[-10:])
        
        messages.append({"role": "user", "content": prompt})
        
        tools_available = AVAILABLE_TOOLS if enable_web_search else {}
        system_prompt = _build_agent_system_prompt(tools_available)
        
        iteration = 0
        tool_results = []
        final_response = ""
        
        while iteration < max_iterations:
            iteration += 1
            logger.info("event=agent_iteration iteration=%s", iteration)
            
            body = {
                "messages": messages,
                "system": system_prompt
            }
            
            result = run_model(model_name=model, prompt="", params=body, timeout=30)
            
            if not result or not result.get("success"):
                error_msg = result.get("error", "Unknown error") if result else "No response"
                logger.error("event=agent_model_failed error=%s", error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "iterations": iteration
                }
            
            response_text = _extract_response_text(result)
            
            if not response_text:
                logger.warning("event=agent_empty_response")
                return {
                    "success": False,
                    "error": "Empty response",
                    "iterations": iteration
                }
            
            tool_calls = _extract_tool_calls(response_text)
            
            if tool_calls:
                logger.info("event=agent_tool_calls count=%s", len(tool_calls))
                
                messages.append({"role": "assistant", "content": response_text})
                
                for tool_call in tool_calls:
                    tool_name = tool_call.get("tool")
                    params = tool_call.get("params", {})
                    
                    logger.info("event=agent_executing_tool tool=%s", tool_name)
                    
                    tool_result = _execute_tool(tool_name, params)
                    tool_results.append({
                        "tool": tool_name,
                        "params": params,
                        "result": tool_result
                    })
                    
                    messages.append({
                        "role": "user",
                        "content": f"Tool result from {tool_name}:\n{json.dumps(tool_result)}"
                    })
                
                continue
            
            final_response = response_text
            break
        
        logger.info("event=agent_process_complete iterations=%s tool_calls=%s", 
                   iteration, len(tool_results))
        
        return {
            "success": True,
            "response": final_response,
            "iterations": iteration,
            "tool_results": tool_results,
            "tool_count": len(tool_results)
        }
    
    @staticmethod
    def analyze_with_research(
        topic: str,
        model: str,
        depth: str = "standard"
    ) -> Dict[str, Any]:
        
        if not topic or not isinstance(topic, str):
            return {"success": False, "error": "Invalid topic"}
        
        if not model or not isinstance(model, str):
            return {"success": False, "error": "Invalid model"}
        
        logger.info("event=agent_analyze_start topic=%s depth=%s", topic, depth)
        
        search_count = {"quick": 1, "standard": 3, "deep": 5}.get(depth, 3)
        
        search_results = []
        search_queries = [
            topic,
            f"{topic} latest",
            f"{topic} best practices",
            f"{topic} trends",
            f"{topic} guide"
        ][:search_count]
        
        for query in search_queries:
            logger.info("event=agent_searching query=%s", query)
            result = WebSearchTools.web_search(query, count=5)
            if result and result.get("success"):
                search_results.extend(result.get("results", []))
        
        if not search_results:
            logger.warning("event=agent_no_search_results topic=%s", topic)
            return {"success": False, "error": "No search results found"}
        
        content_snippets = []
        for result in search_results[:5]:
            url = result.get("url")
            if url and isinstance(url, str):
                content = WebSearchTools.visit_url(url)
                if content and content.get("success"):
                    content_snippets.append({
                        "url": url,
                        "title": content.get("title"),
                        "content": content.get("content", "")[:500]
                    })
        
        if not content_snippets:
            logger.warning("event=agent_no_content_extracted topic=%s", topic)
            return {"success": False, "error": "Could not extract content"}
        
        analysis_prompt = f"""Based on the following research about "{topic}", provide a comprehensive analysis:

Research Results:
{json.dumps(content_snippets, indent=2)}

Please provide:
1. Key findings
2. Important trends
3. Best practices
4. Recommendations
5. Future outlook"""
        
        body = {
            "messages": [{"role": "user", "content": analysis_prompt}]
        }
        
        result = run_model(model=model, body=body, timeout=30)
        
        if not result or not result.get("success"):
            error_msg = result.get("error", "Unknown error") if result else "No response"
            logger.error("event=agent_analyze_failed error=%s", error_msg)
            return {
                "success": False,
                "error": error_msg
            }
        
        analysis_text = _extract_response_text(result)
        
        if not analysis_text:
            logger.warning("event=agent_empty_analysis topic=%s", topic)
            return {"success": False, "error": "Empty analysis"}
        
        logger.info("event=agent_analyze_complete topic=%s sources=%s", topic, len(content_snippets))
        
        return {
            "success": True,
            "topic": topic,
            "analysis": analysis_text,
            "sources": len(content_snippets),
            "research_results": content_snippets
        }

def _build_agent_system_prompt(tools: Dict[str, Any]) -> str:
    
    tools_desc = ""
    if tools and isinstance(tools, dict):
        tools_desc = "\nAvailable Tools:\n"
        for tool_name, tool_info in tools.items():
            if isinstance(tool_info, dict):
                tools_desc += f"\n- {tool_name}: {tool_info.get('description', '')}\n"
                params = tool_info.get('params', {})
                if params and isinstance(params, dict):
                    tools_desc += "  Parameters:\n"
                    for param_name, param_desc in params.items():
                        tools_desc += f"    - {param_name}: {param_desc}\n"
    
    return f"""You are an intelligent AI assistant with reasoning and tool usage capabilities.

When you need to search the web or gather information, use tools in this format:
<tool_call>
{{
  "tool": "tool_name",
  "params": {{"param1": "value1", "param2": "value2"}}
}}
</tool_call>

{tools_desc}

Instructions:
1. Analyze the user's request carefully
2. Use tools when you need current information, web search, or external data
3. Provide clear, well-reasoned responses
4. Cite sources when using tool results
5. If you use tools, continue reasoning until you have enough information to answer

Always be helpful, accurate, and thorough."""

def _extract_response_text(result: Dict[str, Any]) -> str:
    
    if not result or not isinstance(result, dict):
        return ""
    
    body_data = result.get("body", {})
    result_data = body_data.get("result", {})
    
    if isinstance(result_data, dict):
        choices = result_data.get("choices", [])
        if isinstance(choices, list) and len(choices) > 0:
            first_choice = choices[0]
            if isinstance(first_choice, dict):
                message = first_choice.get("message", {})
                if isinstance(message, dict):
                    return message.get("content", "")
    
    return ""

def _extract_tool_calls(response_text: str) -> List[Dict[str, Any]]:
    
    tool_calls = []
    
    if not response_text or not isinstance(response_text, str):
        return tool_calls
    
    matches = re.findall(r'<tool_call>(.*?)</tool_call>', response_text, re.DOTALL)
    
    for match in matches:
        try:
            tool_call = json.loads(match)
            if isinstance(tool_call, dict):
                tool_calls.append(tool_call)
        except json.JSONDecodeError as e:
            logger.warning("event=tool_call_parse_failed error=%s", str(e))
    
    return tool_calls

def _execute_tool(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    
    if not tool_name or not isinstance(tool_name, str):
        return {"error": "Invalid tool name"}
    
    if tool_name not in AVAILABLE_TOOLS:
        logger.error("event=unknown_tool tool=%s", tool_name)
        return {"error": f"Unknown tool: {tool_name}"}
    
    try:
        tool_info = AVAILABLE_TOOLS[tool_name]
        if not isinstance(tool_info, dict):
            return {"error": "Invalid tool info"}
        
        tool_func = tool_info.get("func")
        if not tool_func or not callable(tool_func):
            return {"error": f"Tool not callable: {tool_name}"}
        
        if not isinstance(params, dict):
            params = {}
        
        result = tool_func(**params)
        logger.info("event=tool_executed tool=%s success=%s", tool_name, result.get("success", False) if isinstance(result, dict) else False)
        return result
        
    except TypeError as e:
        logger.error("event=tool_param_error tool=%s error=%s", tool_name, str(e))
        return {"error": f"Parameter error: {str(e)}", "tool": tool_name}
    except Exception as e:
        logger.error("event=tool_execution_failed tool=%s error=%s", tool_name, str(e))
        return {"error": str(e), "tool": tool_name}
