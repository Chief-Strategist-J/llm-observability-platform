"""
Streaming Response Client
Provides real-time streaming of AI responses
"""

import logging
import asyncio
import json
from typing import AsyncGenerator, Dict, Any, List, Optional
from core.client.cloudflare_client import run_model

logger = logging.getLogger(__name__)


class StreamingClient:
    """Client for streaming AI responses"""
    
    @staticmethod
    async def stream_response(
        prompt: str,
        model: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        timeout: int = 30
    ) -> AsyncGenerator[str, None]:
        """
        Stream AI response token by token
        
        Args:
            prompt: User prompt
            model: Model to use
            conversation_history: Previous conversation messages
            timeout: Request timeout in seconds
            
        Yields:
            Response tokens as they arrive
        """
        logger.info("event=stream_response_start model=%s prompt_len=%s", model, len(prompt))
        
        try:
            # Build message history
            messages = []
            if conversation_history:
                for msg in conversation_history[-10:]:  # Last 10 messages
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", msg.get("text", ""))
                    })
            
            messages.append({"role": "user", "content": prompt})
            
            # Call model with streaming
            body = {
                "messages": messages,
                "stream": True
            }
            
            logger.info("event=stream_model_call model=%s messages=%s", model, len(messages))
            
            # Simulate streaming (Cloudflare API may not support true streaming)
            # In production, use proper streaming implementation
            result = await asyncio.to_thread(
                run_model,
                model=model,
                body=body,
                timeout=timeout
            )
            
            if not result.get("success"):
                logger.error("event=stream_model_failed error=%s", result.get("error"))
                yield f"Error: {result.get('error', 'Unknown error')}"
                return
            
            response_text = ""
            body_data = result.get("body", {})
            result_data = body_data.get("result", {})
            
            if isinstance(result_data, dict):
                choices = result_data.get("choices", [])
                if isinstance(choices, list) and len(choices) > 0:
                    first_choice = choices[0]
                    if isinstance(first_choice, dict):
                        message = first_choice.get("message", {})
                        if isinstance(message, dict):
                            response_text = message.get("content", "")
            
            # Stream response in chunks
            chunk_size = 20
            for i in range(0, len(response_text), chunk_size):
                chunk = response_text[i:i + chunk_size]
                logger.debug("event=stream_chunk_sent size=%s", len(chunk))
                yield chunk
                await asyncio.sleep(0.01)  # Small delay for realistic streaming
            
            logger.info("event=stream_response_complete total_len=%s", len(response_text))
            
        except asyncio.TimeoutError:
            logger.error("event=stream_response_timeout")
            yield "Error: Request timed out"
        except Exception as e:
            logger.error("event=stream_response_exception error=%s", str(e))
            yield f"Error: {str(e)}"
    
    @staticmethod
    async def stream_with_tools(
        prompt: str,
        model: str,
        available_tools: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        max_iterations: int = 5
    ) -> AsyncGenerator[str, None]:
        """
        Stream response with tool usage capability
        
        Args:
            prompt: User prompt
            model: Model to use
            available_tools: Dictionary of available tools
            conversation_history: Previous messages
            max_iterations: Max tool use iterations
            
        Yields:
            Response tokens and tool results
        """
        logger.info("event=stream_with_tools_start model=%s tools=%s", model, len(available_tools))
        
        messages = []
        if conversation_history:
            messages.extend(conversation_history[-10:])
        
        messages.append({"role": "user", "content": prompt})
        
        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            
            # Build system prompt with tools
            system_prompt = _build_tool_system_prompt(available_tools)
            
            # Call model
            body = {
                "messages": messages,
                "system": system_prompt
            }
            
            result = await asyncio.to_thread(
                run_model,
                model=model,
                body=body,
                timeout=30
            )
            
            if not result.get("success"):
                logger.error("event=stream_tools_failed error=%s", result.get("error"))
                yield f"Error: {result.get('error')}"
                break
            
            response_text = ""
            body_data = result.get("body", {})
            result_data = body_data.get("result", {})
            
            if isinstance(result_data, dict):
                choices = result_data.get("choices", [])
                if isinstance(choices, list) and len(choices) > 0:
                    first_choice = choices[0]
                    if isinstance(first_choice, dict):
                        message = first_choice.get("message", {})
                        if isinstance(message, dict):
                            response_text = message.get("content", "")
            
            # Check if response contains tool calls
            if "<tool_call>" in response_text:
                # Extract and execute tool calls
                tool_results = await _execute_tool_calls(response_text, available_tools)
                
                # Add assistant response
                messages.append({"role": "assistant", "content": response_text})
                
                # Add tool results
                for tool_result in tool_results:
                    messages.append({
                        "role": "user",
                        "content": f"Tool result: {json.dumps(tool_result)}"
                    })
                    yield f"\n[Tool: {tool_result.get('tool')}] {tool_result.get('result', '')}\n"
                
                continue
            
            # Stream final response
            chunk_size = 20
            for i in range(0, len(response_text), chunk_size):
                chunk = response_text[i:i + chunk_size]
                yield chunk
                await asyncio.sleep(0.01)
            
            break
        
        logger.info("event=stream_with_tools_complete iterations=%s", iteration)


def _build_tool_system_prompt(available_tools: Dict[str, Any]) -> str:
    """Build system prompt with tool descriptions"""
    
    tools_desc = "Available tools:\n"
    for tool_name, tool_info in available_tools.items():
        tools_desc += f"\n- {tool_name}: {tool_info.get('description', '')}\n"
        params = tool_info.get('params', {})
        if params:
            tools_desc += "  Parameters:\n"
            for param_name, param_desc in params.items():
                tools_desc += f"    - {param_name}: {param_desc}\n"
    
    return f"""You are a helpful AI assistant with access to tools.
When you need to use a tool, format it as:
<tool_call>
{{
  "tool": "tool_name",
  "params": {{"param1": "value1", "param2": "value2"}}
}}
</tool_call>

{tools_desc}

Always provide helpful responses and use tools when appropriate."""


async def _execute_tool_calls(response_text: str, available_tools: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Execute tool calls found in response"""
    
    results = []
    
    # Extract tool calls from response
    import re
    tool_calls = re.findall(r'<tool_call>(.*?)</tool_call>', response_text, re.DOTALL)
    
    for tool_call_str in tool_calls:
        try:
            tool_call = json.loads(tool_call_str)
            tool_name = tool_call.get("tool")
            params = tool_call.get("params", {})
            
            if tool_name not in available_tools:
                logger.warning("event=unknown_tool tool=%s", tool_name)
                results.append({
                    "tool": tool_name,
                    "error": f"Unknown tool: {tool_name}"
                })
                continue
            
            tool_func = available_tools[tool_name].get("func")
            
            # Execute tool
            logger.info("event=executing_tool tool=%s params=%s", tool_name, len(params))
            
            if asyncio.iscoroutinefunction(tool_func):
                result = await tool_func(**params)
            else:
                result = await asyncio.to_thread(tool_func, **params)
            
            results.append({
                "tool": tool_name,
                "result": result
            })
            
        except json.JSONDecodeError as e:
            logger.error("event=tool_call_parse_failed error=%s", str(e))
        except Exception as e:
            logger.error("event=tool_execution_failed error=%s", str(e))
    
    return results
