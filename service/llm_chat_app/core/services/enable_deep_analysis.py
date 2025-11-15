import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from core.client.cloudflare_client import run_model

logger = logging.getLogger(__name__)

def analyze_deep_psychology(
    prompt: str,
    response: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    session_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    
    logger.info("event=deep_psych_start prompt_len=%s history_len=%s", 
                len(prompt), len(conversation_history) if conversation_history else 0)
    
    history_text = ""
    if conversation_history and len(conversation_history) > 0:
        recent = conversation_history[-6:] if len(conversation_history) > 6 else conversation_history
        history_text = "\n".join([f"{msg.get('role', 'unknown')}: {msg.get('content', msg.get('text', ''))}" for msg in recent])
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    analysis_prompt = f"""You are a ruthless psychological profiler analyzing human behavior at the deepest levels. Extract EVERYTHING hidden beneath the surface.

CURRENT TIME: {current_time}
CURRENT CONVERSATION:
User: {prompt}
Assistant: {response}

CONVERSATION HISTORY:
{history_text if history_text else "First interaction"}

ANALYZE ACROSS 12 DIMENSIONS. Output ONLY valid JSON (no markdown, no preamble):

{{
  "timestamp": "{current_time}",
  "surface_analysis": {{
    "explicit_question": "what they literally asked",
    "stated_goal": "what they claim to want",
    "obvious_emotion": "visible emotion"
  }},
  "layer_1_immediate_subtext": {{
    "real_question": "what they're actually asking",
    "hidden_need": "what they really need",
    "unspoken_assumption": "what they assume you know",
    "fear": "what they're afraid of"
  }},
  "layer_2_emotional_state": {{
    "core_emotion": "primary emotion (frustrated/desperate/overwhelmed/excited/scared/angry/lost/hopeful)",
    "intensity": 1-10,
    "secondary_emotions": ["emotion1", "emotion2"],
    "emotional_trigger": "what triggered this state",
    "emotional_pattern": "repeating pattern detected",
    "coping_mechanism": "how they're dealing with it"
  }},
  "layer_3_trauma_indicators": {{
    "trauma_present": true/false,
    "trauma_type": "abandonment/failure/rejection/betrayal/loss/inadequacy/control/trust",
    "trauma_severity": 1-10,
    "triggered_by": "what in conversation triggered it",
    "defense_mechanism": "how they're protecting themselves",
    "avoidance_pattern": "what they're avoiding",
    "hypervigilance": "what they're watching for"
  }},
  "layer_4_dark_patterns": {{
    "self_sabotage": true/false,
    "perfectionism_trap": true/false,
    "imposter_syndrome": true/false,
    "learned_helplessness": true/false,
    "catastrophizing": true/false,
    "all_or_nothing_thinking": true/false,
    "self_punishment": true/false,
    "pattern_description": "specific pattern observed"
  }},
  "layer_5_meta_questions": {{
    "meta_1": "question behind the question",
    "meta_2": "question behind meta_1",
    "meta_3": "question behind meta_2",
    "meta_4": "question behind meta_3",
    "meta_5": "ultimate core question",
    "existential_concern": "deepest fear/need"
  }},
  "layer_6_behavioral_analysis": {{
    "communication_style": "direct/indirect/defensive/pleading/aggressive/passive",
    "power_dynamic": "seeking_control/surrendering_control/challenging_authority/seeking_validation",
    "attachment_style": "anxious/avoidant/secure/disorganized",
    "boundary_health": 1-10,
    "autonomy_level": 1-10,
    "help_seeking_pattern": "chronic/new/resistant/open"
  }},
  "layer_7_cognitive_state": {{
    "cognitive_distortion": "overgeneralization/black-white/mental_filter/jumping_conclusions/catastrophizing/personalization/should_statements/labeling/none",
    "cognitive_load": 1-10,
    "decision_paralysis": true/false,
    "information_overload": true/false,
    "clarity_level": 1-10,
    "executive_function": "impaired/struggling/functional/optimal"
  }},
  "layer_8_identity_struggle": {{
    "identity_crisis": true/false,
    "self_worth": 1-10,
    "competence_belief": 1-10,
    "belonging_need": 1-10,
    "purpose_clarity": 1-10,
    "role_confusion": "what role they're struggling with",
    "comparison_trap": "who they're comparing to"
  }},
  "layer_9_systemic_context": {{
    "external_pressure": "work/family/financial/social/health/time/none",
    "support_system": "strong/weak/absent/toxic",
    "resource_scarcity": "time/money/knowledge/energy/connections",
    "systemic_barrier": "what's blocking them externally",
    "power_imbalance": "who has power over them"
  }},
  "layer_10_temporal_dimension": {{
    "stuck_in_past": true/false,
    "anxious_about_future": true/false,
    "present_awareness": 1-10,
    "time_pressure": 1-10,
    "urgency_real": true/false,
    "urgency_perceived": true/false,
    "patience_level": 1-10
  }},
  "layer_11_relational_dynamics": {{
    "trust_level": 1-10,
    "vulnerability_shown": 1-10,
    "defensiveness": 1-10,
    "connection_seeking": 1-10,
    "isolation_level": 1-10,
    "projection": "what they're projecting onto you",
    "transference": "who you represent to them"
  }},
  "layer_12_transformation_potential": {{
    "readiness_for_change": 1-10,
    "resistance_level": 1-10,
    "insight_capacity": 1-10,
    "agency_belief": 1-10,
    "hope_level": 1-10,
    "breakthrough_proximity": "far/approaching/imminent/happening",
    "growth_edge": "what they need to confront next"
  }},
  "ruthless_truth": {{
    "what_they_wont_admit": "what they're hiding from themselves",
    "real_barrier": "the actual thing stopping them",
    "necessary_confrontation": "what needs to be said",
    "harsh_reality": "truth they need to hear",
    "enabling_pattern": "how we might enable their dysfunction",
    "tough_love": "direct intervention needed"
  }},
  "actionable_intelligence": {{
    "immediate_need": "what they need right now",
    "intervention_type": "support/challenge/information/validation/boundary/redirection",
    "communication_strategy": "how to speak to them effectively",
    "danger_signs": ["red_flag_1", "red_flag_2"],
    "green_lights": ["positive_indicator_1", "positive_indicator_2"],
    "next_conversation_approach": "how to approach next interaction"
  }},
  "data_to_remember": {{
    "emotional_signature": "unique pattern identifier",
    "progress_marker": "where they are in journey",
    "recurring_theme": "pattern that keeps appearing",
    "breakthrough_indicator": "sign they're ready to shift"
  }},
  "data_to_forget": {{
    "sensitive_details": "DO NOT STORE: specific trauma details",
    "identifying_info": "DO NOT STORE: personal identifiers",
    "vulnerable_moments": "DO NOT STORE: specific vulnerable disclosures"
  }}
}}

BE RUTHLESSLY HONEST. EXTRACT EVERYTHING. NO SUGAR COATING."""

    logger.info("event=deep_psych_llm_call model=@cf/qwen/qwen2.5-72b-instruct")
    
    try:
        result = run_model(
            "@cf/qwen/qwen2.5-72b-instruct",
            analysis_prompt,
            timeout=45
        )
        
        if not result.get("success"):
            logger.error("event=deep_psych_llm_failed error=%s", result.get("error"))
            return _emergency_fallback_analysis(prompt, response, history_text)
        
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
            logger.warning("event=deep_psych_empty_response")
            return _emergency_fallback_analysis(prompt, response, history_text)
        
        logger.info("event=deep_psych_llm_success response_len=%s", len(response_text))
        
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
            
            logger.info("event=deep_psych_parsed emotion=%s trauma=%s meta_core=%s", 
                       analysis.get("layer_2_emotional_state", {}).get("core_emotion"),
                       analysis.get("layer_3_trauma_indicators", {}).get("trauma_type"),
                       analysis.get("layer_5_meta_questions", {}).get("meta_5"))
            
            sanitized = _sanitize_for_storage(analysis)
            
            logger.info("event=deep_psych_sanitized removed_sensitive=%s", 
                       len(analysis.get("data_to_forget", {})))
            
            return sanitized
            
        except json.JSONDecodeError as e:
            logger.error("event=deep_psych_json_failed error=%s response=%s", 
                        str(e), response_text[:300])
            return _emergency_fallback_analysis(prompt, response, history_text)
            
    except Exception as e:
        logger.exception("event=deep_psych_exception error=%s", str(e))
        return _emergency_fallback_analysis(prompt, response, history_text)

def _sanitize_for_storage(analysis: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("event=sanitize_start")
    
    sanitized = {}
    
    for key, value in analysis.items():
        if key == "data_to_forget":
            logger.info("event=sanitize_removed section=data_to_forget")
            continue
        
        if key in ["layer_3_trauma_indicators", "ruthless_truth"]:
            if isinstance(value, dict):
                sanitized_section = {}
                for k, v in value.items():
                    if k in ["trauma_type", "defense_mechanism", "pattern_description", "real_barrier", "necessary_confrontation"]:
                        sanitized_section[k] = v
                    else:
                        sanitized_section[k] = "REDACTED"
                sanitized[key] = sanitized_section
                logger.info("event=sanitize_redacted section=%s", key)
        else:
            sanitized[key] = value
    
    logger.info("event=sanitize_complete")
    return sanitized

def _emergency_fallback_analysis(prompt: str, response: str, history: str) -> Dict[str, Any]:
    logger.info("event=deep_psych_fallback_start")
    
    prompt_lower = prompt.lower()
    
    emotion = "neutral"
    intensity = 5
    trauma_present = False
    trauma_type = "none"
    
    distress_words = ["help", "stuck", "can't", "won't", "always", "never", "impossible", "failed", "error", "wrong"]
    distress_count = sum(1 for word in distress_words if word in prompt_lower)
    
    if distress_count >= 3:
        emotion = "overwhelmed"
        intensity = 8
        trauma_present = True
        trauma_type = "inadequacy"
    elif "error" in prompt_lower or "not working" in prompt_lower:
        emotion = "frustrated"
        intensity = 7
    elif "?" in prompt and len(prompt) > 50:
        emotion = "confused"
        intensity = 6
    elif "!" in prompt:
        emotion = "desperate" if distress_count > 0 else "excited"
        intensity = 7
    
    meta_1 = f"How to actually solve: {prompt[:50]}"
    meta_2 = "Am I capable of solving this?"
    meta_3 = "Will I ever be good enough?"
    meta_4 = "Do I deserve success?"
    meta_5 = "Am I fundamentally broken?"
    
    fallback = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "surface_analysis": {
            "explicit_question": prompt[:100],
            "stated_goal": "solve problem",
            "obvious_emotion": emotion
        },
        "layer_1_immediate_subtext": {
            "real_question": meta_1,
            "hidden_need": "validation and competence",
            "unspoken_assumption": "I should already know this",
            "fear": "being judged as incompetent"
        },
        "layer_2_emotional_state": {
            "core_emotion": emotion,
            "intensity": intensity,
            "secondary_emotions": ["anxious", "uncertain"],
            "emotional_trigger": "technical challenge",
            "emotional_pattern": "performance anxiety",
            "coping_mechanism": "seeking external validation"
        },
        "layer_3_trauma_indicators": {
            "trauma_present": trauma_present,
            "trauma_type": trauma_type,
            "trauma_severity": intensity if trauma_present else 0,
            "triggered_by": "challenge to competence",
            "defense_mechanism": "intellectualization",
            "avoidance_pattern": "avoiding autonomous problem-solving",
            "hypervigilance": "monitoring for mistakes"
        },
        "layer_4_dark_patterns": {
            "self_sabotage": False,
            "perfectionism_trap": distress_count > 2,
            "imposter_syndrome": True,
            "learned_helplessness": distress_count > 3,
            "catastrophizing": "always" in prompt_lower or "never" in prompt_lower,
            "all_or_nothing_thinking": distress_count > 2,
            "self_punishment": False,
            "pattern_description": "seeking external rescue rather than building confidence"
        },
        "layer_5_meta_questions": {
            "meta_1": meta_1,
            "meta_2": meta_2,
            "meta_3": meta_3,
            "meta_4": meta_4,
            "meta_5": meta_5,
            "existential_concern": "fundamental worth and capability"
        },
        "layer_6_behavioral_analysis": {
            "communication_style": "pleading" if distress_count > 2 else "questioning",
            "power_dynamic": "surrendering_control",
            "attachment_style": "anxious",
            "boundary_health": 5,
            "autonomy_level": 4,
            "help_seeking_pattern": "chronic" if distress_count > 3 else "new"
        },
        "layer_7_cognitive_state": {
            "cognitive_distortion": "catastrophizing" if distress_count > 2 else "none",
            "cognitive_load": 7,
            "decision_paralysis": distress_count > 2,
            "information_overload": len(prompt) > 100,
            "clarity_level": 4,
            "executive_function": "struggling"
        },
        "layer_8_identity_struggle": {
            "identity_crisis": False,
            "self_worth": 5,
            "competence_belief": 4,
            "belonging_need": 6,
            "purpose_clarity": 6,
            "role_confusion": "learner vs expert",
            "comparison_trap": "comparing to others who seem to know"
        },
        "layer_9_systemic_context": {
            "external_pressure": "time",
            "support_system": "weak",
            "resource_scarcity": "knowledge",
            "systemic_barrier": "information access",
            "power_imbalance": "none detected"
        },
        "layer_10_temporal_dimension": {
            "stuck_in_past": False,
            "anxious_about_future": True,
            "present_awareness": 5,
            "time_pressure": 6,
            "urgency_real": False,
            "urgency_perceived": True,
            "patience_level": 4
        },
        "layer_11_relational_dynamics": {
            "trust_level": 6,
            "vulnerability_shown": 5,
            "defensiveness": 4,
            "connection_seeking": 7,
            "isolation_level": 5,
            "projection": "all-knowing expert",
            "transference": "parent/teacher figure"
        },
        "layer_12_transformation_potential": {
            "readiness_for_change": 6,
            "resistance_level": 5,
            "insight_capacity": 6,
            "agency_belief": 4,
            "hope_level": 6,
            "breakthrough_proximity": "approaching",
            "growth_edge": "building autonomous problem-solving confidence"
        },
        "ruthless_truth": {
            "what_they_wont_admit": "afraid of being incompetent",
            "real_barrier": "self-doubt more than technical challenge",
            "necessary_confrontation": "need to try independently first",
            "harsh_reality": "confidence comes from struggling through, not avoiding struggle",
            "enabling_pattern": "REDACTED",
            "tough_love": "REDACTED"
        },
        "actionable_intelligence": {
            "immediate_need": "clear next step",
            "intervention_type": "support with challenge",
            "communication_strategy": "empathize then empower",
            "danger_signs": ["learned helplessness", "chronic help-seeking"],
            "green_lights": ["asking questions", "engaging"],
            "next_conversation_approach": "encourage independent exploration"
        },
        "data_to_remember": {
            "emotional_signature": f"{emotion}_{intensity}",
            "progress_marker": "early_dependency",
            "recurring_theme": "competence_anxiety",
            "breakthrough_indicator": "asking how rather than asking to do"
        }
    }
    
    logger.info("event=deep_psych_fallback_complete emotion=%s trauma=%s", emotion, trauma_type)
    
    return fallback

def get_conversation_intelligence(analysis: Dict[str, Any]) -> str:
    logger.info("event=intelligence_summary_start")
    
    if not analysis:
        return "No analysis available"
    
    emotion = analysis.get("layer_2_emotional_state", {}).get("core_emotion", "unknown")
    intensity = analysis.get("layer_2_emotional_state", {}).get("intensity", 0)
    meta_core = analysis.get("layer_5_meta_questions", {}).get("meta_5", "unknown")
    real_barrier = analysis.get("ruthless_truth", {}).get("real_barrier", "unknown")
    immediate_need = analysis.get("actionable_intelligence", {}).get("immediate_need", "unknown")
    
    summary = f"""PSYCHOLOGICAL INTELLIGENCE:
Emotional State: {emotion} (intensity: {intensity}/10)
Core Question: {meta_core}
Real Barrier: {real_barrier}
Immediate Need: {immediate_need}"""
    
    logger.info("event=intelligence_summary_complete")
    
    return summary