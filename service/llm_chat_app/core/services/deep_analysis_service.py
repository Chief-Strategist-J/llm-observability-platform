import logging
from typing import Dict, Any, List, Optional
from core.client.cloudflare_client import run_model

logger = logging.getLogger(__name__)

def analyze_user_intent_and_emotion(
    prompt: str, 
    response: str,
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    
    logger.info("event=deep_analysis_start prompt_len=%s response_len=%s history_len=%s", 
                len(prompt), len(response), len(conversation_history) if conversation_history else 0)
    
    history_context = ""
    if conversation_history and len(conversation_history) > 0:
        recent = conversation_history[-4:] if len(conversation_history) > 4 else conversation_history
        history_context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent])
    
    analysis_prompt = f"""Analyze this conversation deeply across 7 meta-levels:

CONVERSATION:
User: {prompt}
Assistant: {response}

PREVIOUS CONTEXT:
{history_context if history_context else "No previous context"}

Provide analysis in this EXACT JSON format (no extra text):
{{
  "emotion": {{
    "primary": "curious/frustrated/excited/confused/anxious/happy/sad/angry/neutral",
    "intensity": 0-10,
    "secondary_emotions": ["emotion1", "emotion2"],
    "emotional_trajectory": "rising/falling/stable"
  }},
  "intent": {{
    "primary": "learn/solve_problem/explore/create/debug/understand/compare",
    "urgency": 0-10,
    "specificity": 0-10,
    "goals": ["goal1", "goal2"]
  }},
  "meta_level_1_surface": {{
    "what_user_asked": "literal question",
    "explicit_topic": "stated topic",
    "keywords": ["key1", "key2", "key3"]
  }},
  "meta_level_2_implicit": {{
    "what_user_actually_wants": "deeper need",
    "hidden_concerns": ["concern1", "concern2"],
    "assumptions": ["assumption1", "assumption2"]
  }},
  "meta_level_3_context": {{
    "user_knowledge_level": "beginner/intermediate/expert",
    "project_phase": "planning/building/debugging/deploying/learning",
    "stuck_point": "where user is blocked",
    "missing_knowledge": ["gap1", "gap2"]
  }},
  "meta_level_4_patterns": {{
    "learning_style": "visual/hands-on/theoretical/example-driven",
    "problem_solving_approach": "top-down/bottom-up/trial-error/systematic",
    "communication_style": "concise/detailed/questioning/assertive",
    "confidence_level": 0-10
  }},
  "meta_level_5_psychological": {{
    "cognitive_load": 0-10,
    "frustration_indicators": ["indicator1", "indicator2"],
    "breakthrough_moments": ["moment1", "moment2"],
    "mental_model": "how user conceptualizes problem",
    "blockers": ["mental_blocker1", "mental_blocker2"]
  }},
  "meta_level_6_strategic": {{
    "long_term_goal": "ultimate objective",
    "current_strategy": "approach being used",
    "strategy_effectiveness": 0-10,
    "needed_pivot": "what needs to change",
    "success_criteria": ["criterion1", "criterion2"]
  }},
  "meta_level_7_transformative": {{
    "worldview_shift": "how this changes user's understanding",
    "capability_gained": "new skill or insight",
    "future_trajectory": "where this leads",
    "empowerment_level": 0-10,
    "autonomy_gained": "what user can now do independently"
  }},
  "entities": ["entity1", "entity2", "entity3"],
  "topics": ["topic1", "topic2", "topic3"],
  "concepts": ["concept1", "concept2"],
  "relationships": ["relates_to_previous", "builds_on", "contradicts"]
}}"""

    logger.info("event=deep_analysis_llm_start model=@cf/meta/llama-3.1-8b-instruct")
    
    try:
        result = run_model(
            "@cf/meta/llama-3.1-8b-instruct",
            analysis_prompt,
            timeout=30
        )
        
        if not result.get("success"):
            logger.error("event=deep_analysis_llm_failed error=%s", result.get("error"))
            return _fallback_analysis(prompt, response)
        
        body = result.get("body", {})
        result_data = body.get("result", {})
        
        response_text = ""
        if isinstance(result_data, dict):
            choices = result_data.get("choices", [])
            if isinstance(choices, list) and len(choices) > 0:
                first_choice = choices[0]
                if isinstance(first_choice, dict):
                    message = first_choice.get("message", {})
                    if isinstance(message, dict):
                        response_text = message.get("content", "")
        
        if not response_text:
            logger.warning("event=deep_analysis_empty_response")
            return _fallback_analysis(prompt, response)
        
        logger.info("event=deep_analysis_llm_success response_len=%s", len(response_text))
        
        import json
        
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        try:
            analysis = json.loads(response_text)
            logger.info("event=deep_analysis_parsed emotion=%s intent=%s", 
                       analysis.get("emotion", {}).get("primary"),
                       analysis.get("intent", {}).get("primary"))
            return analysis
        except json.JSONDecodeError as e:
            logger.error("event=deep_analysis_json_parse_failed error=%s response=%s", 
                        str(e), response_text[:200])
            return _fallback_analysis(prompt, response)
            
    except Exception as e:
        logger.exception("event=deep_analysis_exception error=%s", str(e))
        return _fallback_analysis(prompt, response)

def _fallback_analysis(prompt: str, response: str) -> Dict[str, Any]:
    logger.info("event=deep_analysis_fallback_start")
    
    prompt_lower = prompt.lower()
    response_lower = response.lower()
    
    emotion_primary = "neutral"
    emotion_intensity = 5
    
    if any(word in prompt_lower for word in ["help", "how", "what", "?"]):
        emotion_primary = "curious"
        emotion_intensity = 6
    if any(word in prompt_lower for word in ["error", "issue", "problem", "not working", "fail"]):
        emotion_primary = "frustrated"
        emotion_intensity = 7
    if any(word in prompt_lower for word in ["!", "amazing", "great", "thank"]):
        emotion_primary = "excited"
        emotion_intensity = 8
    if any(word in prompt_lower for word in ["confused", "don't understand", "unclear"]):
        emotion_primary = "confused"
        emotion_intensity = 6
    
    intent_primary = "learn"
    if "how" in prompt_lower or "?" in prompt:
        intent_primary = "understand"
    if "error" in prompt_lower or "fix" in prompt_lower or "debug" in prompt_lower:
        intent_primary = "solve_problem"
    if "create" in prompt_lower or "build" in prompt_lower or "make" in prompt_lower:
        intent_primary = "create"
    
    topics = []
    common_topics = {
        "python": ["python", "py"],
        "code": ["code", "coding", "program"],
        "api": ["api", "endpoint", "request"],
        "error": ["error", "exception", "bug"],
        "deploy": ["deploy", "deployment", "production"],
        "database": ["database", "db", "sql", "neo4j"],
        "docker": ["docker", "container"],
        "ai": ["ai", "model", "llm", "gpt"]
    }
    
    for topic, keywords in common_topics.items():
        if any(kw in prompt_lower or kw in response_lower for kw in keywords):
            topics.append(topic)
    
    entities = []
    words = prompt.split()
    if len(words) > 3:
        entities.append(" ".join(words[:3]))
    
    knowledge_level = "intermediate"
    if any(word in prompt_lower for word in ["basic", "beginner", "start", "first time", "new to"]):
        knowledge_level = "beginner"
    if any(word in prompt_lower for word in ["advanced", "optimize", "performance", "architecture"]):
        knowledge_level = "expert"
    
    analysis = {
        "emotion": {
            "primary": emotion_primary,
            "intensity": emotion_intensity,
            "secondary_emotions": [],
            "emotional_trajectory": "stable"
        },
        "intent": {
            "primary": intent_primary,
            "urgency": 5,
            "specificity": 5,
            "goals": [intent_primary]
        },
        "meta_level_1_surface": {
            "what_user_asked": prompt[:100],
            "explicit_topic": topics[0] if topics else "general",
            "keywords": topics
        },
        "meta_level_2_implicit": {
            "what_user_actually_wants": f"{intent_primary} about {topics[0] if topics else 'topic'}",
            "hidden_concerns": [],
            "assumptions": []
        },
        "meta_level_3_context": {
            "user_knowledge_level": knowledge_level,
            "project_phase": "building",
            "stuck_point": "unknown",
            "missing_knowledge": []
        },
        "meta_level_4_patterns": {
            "learning_style": "example-driven",
            "problem_solving_approach": "systematic",
            "communication_style": "detailed" if len(prompt) > 50 else "concise",
            "confidence_level": 5
        },
        "meta_level_5_psychological": {
            "cognitive_load": 5,
            "frustration_indicators": [],
            "breakthrough_moments": [],
            "mental_model": "sequential",
            "blockers": []
        },
        "meta_level_6_strategic": {
            "long_term_goal": "build working solution",
            "current_strategy": "asking for help",
            "strategy_effectiveness": 7,
            "needed_pivot": "none",
            "success_criteria": ["working code"]
        },
        "meta_level_7_transformative": {
            "worldview_shift": "gaining understanding",
            "capability_gained": "new knowledge",
            "future_trajectory": "continued learning",
            "empowerment_level": 6,
            "autonomy_gained": "can implement solution"
        },
        "entities": entities,
        "topics": topics,
        "concepts": topics,
        "relationships": []
    }
    
    logger.info("event=deep_analysis_fallback_complete emotion=%s intent=%s topics=%s", 
                emotion_primary, intent_primary, len(topics))
    
    return analysis