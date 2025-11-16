"""
Enhanced Emotional Intelligence Engine for deeper human emotion understanding.
Optimizes knowledge graph with multi-layered emotional context and patterns.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class EmotionalIntelligenceEngine:
    """
    Analyzes and tracks emotional patterns across conversations.
    Provides deeper understanding of user emotional states without assumptions.
    """

    @staticmethod
    def extract_emotional_layers(deep_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and organize emotional layers from deep psychological analysis.
        
        Args:
            deep_analysis: Output from analyze_deep_psychology()
            
        Returns:
            Structured emotional intelligence data
        """
        if not deep_analysis or not isinstance(deep_analysis, dict):
            logger.warning("event=emotional_extract_invalid_input")
            return EmotionalIntelligenceEngine._default_emotional_state()

        logger.info("event=emotional_extract_start")

        emotional_state = {
            "timestamp": datetime.now().isoformat(),
            "primary_emotion": deep_analysis.get("layer_2_emotional_state", {}).get(
                "core_emotion", "neutral"
            ),
            "intensity": deep_analysis.get("layer_2_emotional_state", {}).get(
                "intensity", 5
            ),
            "secondary_emotions": deep_analysis.get("layer_2_emotional_state", {}).get(
                "secondary_emotions", []
            ),
            "emotional_trigger": deep_analysis.get("layer_2_emotional_state", {}).get(
                "emotional_trigger", "unknown"
            ),
            "emotional_pattern": deep_analysis.get("layer_2_emotional_state", {}).get(
                "emotional_pattern", "none"
            ),
            "coping_mechanism": deep_analysis.get("layer_2_emotional_state", {}).get(
                "coping_mechanism", "unknown"
            ),
            "trauma_indicators": {
                "present": deep_analysis.get("layer_3_trauma_indicators", {}).get(
                    "trauma_present", False
                ),
                "type": deep_analysis.get("layer_3_trauma_indicators", {}).get(
                    "trauma_type", "none"
                ),
                "severity": deep_analysis.get("layer_3_trauma_indicators", {}).get(
                    "trauma_severity", 0
                ),
                "defense_mechanism": deep_analysis.get(
                    "layer_3_trauma_indicators", {}
                ).get("defense_mechanism", "unknown"),
            },
            "dark_patterns": {
                "self_sabotage": deep_analysis.get("layer_4_dark_patterns", {}).get(
                    "self_sabotage", False
                ),
                "perfectionism": deep_analysis.get("layer_4_dark_patterns", {}).get(
                    "perfectionism_trap", False
                ),
                "imposter_syndrome": deep_analysis.get("layer_4_dark_patterns", {}).get(
                    "imposter_syndrome", False
                ),
                "learned_helplessness": deep_analysis.get(
                    "layer_4_dark_patterns", {}
                ).get("learned_helplessness", False),
                "catastrophizing": deep_analysis.get("layer_4_dark_patterns", {}).get(
                    "catastrophizing", False
                ),
                "all_or_nothing": deep_analysis.get("layer_4_dark_patterns", {}).get(
                    "all_or_nothing_thinking", False
                ),
                "description": deep_analysis.get("layer_4_dark_patterns", {}).get(
                    "pattern_description", "none"
                ),
            },
            "meta_questions": {
                "meta_1": deep_analysis.get("layer_5_meta_questions", {}).get(
                    "meta_1", ""
                ),
                "meta_2": deep_analysis.get("layer_5_meta_questions", {}).get(
                    "meta_2", ""
                ),
                "meta_3": deep_analysis.get("layer_5_meta_questions", {}).get(
                    "meta_3", ""
                ),
                "meta_4": deep_analysis.get("layer_5_meta_questions", {}).get(
                    "meta_4", ""
                ),
                "meta_5_core": deep_analysis.get("layer_5_meta_questions", {}).get(
                    "meta_5", "Am I fundamentally broken?"
                ),
                "existential_concern": deep_analysis.get(
                    "layer_5_meta_questions", {}
                ).get("existential_concern", "unknown"),
            },
            "behavioral_analysis": {
                "communication_style": deep_analysis.get(
                    "layer_6_behavioral_analysis", {}
                ).get("communication_style", "unknown"),
                "power_dynamic": deep_analysis.get("layer_6_behavioral_analysis", {}).get(
                    "power_dynamic", "unknown"
                ),
                "attachment_style": deep_analysis.get(
                    "layer_6_behavioral_analysis", {}
                ).get("attachment_style", "unknown"),
                "boundary_health": deep_analysis.get("layer_6_behavioral_analysis", {}).get(
                    "boundary_health", 5
                ),
                "autonomy_level": deep_analysis.get("layer_6_behavioral_analysis", {}).get(
                    "autonomy_level", 5
                ),
                "help_seeking_pattern": deep_analysis.get(
                    "layer_6_behavioral_analysis", {}
                ).get("help_seeking_pattern", "unknown"),
            },
            "cognitive_state": {
                "cognitive_distortion": deep_analysis.get("layer_7_cognitive_state", {}).get(
                    "cognitive_distortion", "none"
                ),
                "cognitive_load": deep_analysis.get("layer_7_cognitive_state", {}).get(
                    "cognitive_load", 5
                ),
                "decision_paralysis": deep_analysis.get("layer_7_cognitive_state", {}).get(
                    "decision_paralysis", False
                ),
                "information_overload": deep_analysis.get(
                    "layer_7_cognitive_state", {}
                ).get("information_overload", False),
                "clarity_level": deep_analysis.get("layer_7_cognitive_state", {}).get(
                    "clarity_level", 5
                ),
                "executive_function": deep_analysis.get("layer_7_cognitive_state", {}).get(
                    "executive_function", "functional"
                ),
            },
            "identity_struggle": {
                "identity_crisis": deep_analysis.get("layer_8_identity_struggle", {}).get(
                    "identity_crisis", False
                ),
                "self_worth": deep_analysis.get("layer_8_identity_struggle", {}).get(
                    "self_worth", 5
                ),
                "competence_belief": deep_analysis.get(
                    "layer_8_identity_struggle", {}
                ).get("competence_belief", 5),
                "belonging_need": deep_analysis.get("layer_8_identity_struggle", {}).get(
                    "belonging_need", 5
                ),
                "purpose_clarity": deep_analysis.get("layer_8_identity_struggle", {}).get(
                    "purpose_clarity", 5
                ),
                "role_confusion": deep_analysis.get("layer_8_identity_struggle", {}).get(
                    "role_confusion", "none"
                ),
                "comparison_trap": deep_analysis.get("layer_8_identity_struggle", {}).get(
                    "comparison_trap", "none"
                ),
            },
            "systemic_context": {
                "external_pressure": deep_analysis.get("layer_9_systemic_context", {}).get(
                    "external_pressure", "none"
                ),
                "support_system": deep_analysis.get("layer_9_systemic_context", {}).get(
                    "support_system", "weak"
                ),
                "resource_scarcity": deep_analysis.get("layer_9_systemic_context", {}).get(
                    "resource_scarcity", "unknown"
                ),
                "systemic_barrier": deep_analysis.get("layer_9_systemic_context", {}).get(
                    "systemic_barrier", "none"
                ),
                "power_imbalance": deep_analysis.get("layer_9_systemic_context", {}).get(
                    "power_imbalance", "none"
                ),
            },
            "temporal_dimension": {
                "stuck_in_past": deep_analysis.get("layer_10_temporal_dimension", {}).get(
                    "stuck_in_past", False
                ),
                "anxious_about_future": deep_analysis.get(
                    "layer_10_temporal_dimension", {}
                ).get("anxious_about_future", False),
                "present_awareness": deep_analysis.get("layer_10_temporal_dimension", {}).get(
                    "present_awareness", 5
                ),
                "time_pressure": deep_analysis.get("layer_10_temporal_dimension", {}).get(
                    "time_pressure", 5
                ),
                "urgency_real": deep_analysis.get("layer_10_temporal_dimension", {}).get(
                    "urgency_real", False
                ),
                "urgency_perceived": deep_analysis.get(
                    "layer_10_temporal_dimension", {}
                ).get("urgency_perceived", False),
                "patience_level": deep_analysis.get("layer_10_temporal_dimension", {}).get(
                    "patience_level", 5
                ),
            },
            "relational_dynamics": {
                "trust_level": deep_analysis.get("layer_11_relational_dynamics", {}).get(
                    "trust_level", 5
                ),
                "vulnerability_shown": deep_analysis.get(
                    "layer_11_relational_dynamics", {}
                ).get("vulnerability_shown", 5),
                "defensiveness": deep_analysis.get("layer_11_relational_dynamics", {}).get(
                    "defensiveness", 5
                ),
                "connection_seeking": deep_analysis.get(
                    "layer_11_relational_dynamics", {}
                ).get("connection_seeking", 5),
                "isolation_level": deep_analysis.get("layer_11_relational_dynamics", {}).get(
                    "isolation_level", 5
                ),
                "projection": deep_analysis.get("layer_11_relational_dynamics", {}).get(
                    "projection", "none"
                ),
                "transference": deep_analysis.get("layer_11_relational_dynamics", {}).get(
                    "transference", "none"
                ),
            },
            "transformation_potential": {
                "readiness_for_change": deep_analysis.get(
                    "layer_12_transformation_potential", {}
                ).get("readiness_for_change", 5),
                "resistance_level": deep_analysis.get(
                    "layer_12_transformation_potential", {}
                ).get("resistance_level", 5),
                "insight_capacity": deep_analysis.get(
                    "layer_12_transformation_potential", {}
                ).get("insight_capacity", 5),
                "agency_belief": deep_analysis.get("layer_12_transformation_potential", {}).get(
                    "agency_belief", 5
                ),
                "hope_level": deep_analysis.get("layer_12_transformation_potential", {}).get(
                    "hope_level", 5
                ),
                "breakthrough_proximity": deep_analysis.get(
                    "layer_12_transformation_potential", {}
                ).get("breakthrough_proximity", "far"),
                "growth_edge": deep_analysis.get("layer_12_transformation_potential", {}).get(
                    "growth_edge", "unknown"
                ),
            },
            "actionable_intelligence": {
                "immediate_need": deep_analysis.get("actionable_intelligence", {}).get(
                    "immediate_need", "unknown"
                ),
                "intervention_type": deep_analysis.get("actionable_intelligence", {}).get(
                    "intervention_type", "support"
                ),
                "communication_strategy": deep_analysis.get(
                    "actionable_intelligence", {}
                ).get("communication_strategy", "empathize"),
                "danger_signs": deep_analysis.get("actionable_intelligence", {}).get(
                    "danger_signs", []
                ),
                "green_lights": deep_analysis.get("actionable_intelligence", {}).get(
                    "green_lights", []
                ),
                "next_conversation_approach": deep_analysis.get(
                    "actionable_intelligence", {}
                ).get("next_conversation_approach", "standard"),
            },
        }

        logger.info(
            "event=emotional_extract_complete emotion=%s intensity=%s",
            emotional_state["primary_emotion"],
            emotional_state["intensity"],
        )

        return emotional_state

    @staticmethod
    def detect_emotional_patterns(
        current_state: Dict[str, Any], previous_states: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect patterns in emotional evolution across conversations.
        
        Args:
            current_state: Current emotional state
            previous_states: List of previous emotional states
            
        Returns:
            Pattern analysis
        """
        logger.info("event=pattern_detection_start current_state_count=1 history_count=%s", len(previous_states))

        if not previous_states:
            logger.info("event=pattern_detection_no_history")
            return {
                "pattern_detected": False,
                "emotion_trajectory": "baseline",
                "volatility": "unknown",
                "trend": "neutral",
            }

        emotions = [state.get("primary_emotion", "neutral") for state in previous_states]
        intensities = [state.get("intensity", 5) for state in previous_states]

        current_emotion = current_state.get("primary_emotion", "neutral")
        current_intensity = current_state.get("intensity", 5)

        emotions.append(current_emotion)
        intensities.append(current_intensity)

        # Calculate volatility
        intensity_changes = [
            abs(intensities[i] - intensities[i - 1]) for i in range(1, len(intensities))
        ]
        avg_volatility = sum(intensity_changes) / len(intensity_changes) if intensity_changes else 0

        # Detect trend
        if len(intensities) >= 3:
            recent_trend = intensities[-3:]
            if recent_trend[-1] > recent_trend[0]:
                trend = "escalating"
            elif recent_trend[-1] < recent_trend[0]:
                trend = "de-escalating"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        # Detect repeating emotions
        emotion_counts = {}
        for emotion in emotions:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

        repeating_emotion = max(emotion_counts, key=emotion_counts.get) if emotion_counts else "none"
        repeat_count = emotion_counts.get(repeating_emotion, 0)

        pattern = {
            "pattern_detected": repeat_count >= 3,
            "repeating_emotion": repeating_emotion,
            "repeat_frequency": repeat_count,
            "emotion_trajectory": emotions[-5:],  # Last 5 emotions
            "intensity_trajectory": intensities[-5:],  # Last 5 intensities
            "volatility": round(avg_volatility, 2),
            "trend": trend,
            "emotional_stability": "stable" if avg_volatility < 2 else "volatile",
        }

        logger.info(
            "event=pattern_detection_complete pattern_detected=%s trend=%s volatility=%s",
            pattern["pattern_detected"],
            pattern["trend"],
            pattern["volatility"],
        )

        return pattern

    @staticmethod
    def _default_emotional_state() -> Dict[str, Any]:
        """Return default emotional state structure."""
        return {
            "timestamp": datetime.now().isoformat(),
            "primary_emotion": "neutral",
            "intensity": 5,
            "secondary_emotions": [],
            "emotional_trigger": "unknown",
            "emotional_pattern": "none",
            "coping_mechanism": "unknown",
            "trauma_indicators": {
                "present": False,
                "type": "none",
                "severity": 0,
                "defense_mechanism": "unknown",
            },
            "dark_patterns": {
                "self_sabotage": False,
                "perfectionism": False,
                "imposter_syndrome": False,
                "learned_helplessness": False,
                "catastrophizing": False,
                "all_or_nothing": False,
                "description": "none",
            },
            "meta_questions": {
                "meta_1": "",
                "meta_2": "",
                "meta_3": "",
                "meta_4": "",
                "meta_5_core": "Am I fundamentally broken?",
                "existential_concern": "unknown",
            },
            "behavioral_analysis": {
                "communication_style": "unknown",
                "power_dynamic": "unknown",
                "attachment_style": "unknown",
                "boundary_health": 5,
                "autonomy_level": 5,
                "help_seeking_pattern": "unknown",
            },
            "cognitive_state": {
                "cognitive_distortion": "none",
                "cognitive_load": 5,
                "decision_paralysis": False,
                "information_overload": False,
                "clarity_level": 5,
                "executive_function": "functional",
            },
            "identity_struggle": {
                "identity_crisis": False,
                "self_worth": 5,
                "competence_belief": 5,
                "belonging_need": 5,
                "purpose_clarity": 5,
                "role_confusion": "none",
                "comparison_trap": "none",
            },
            "systemic_context": {
                "external_pressure": "none",
                "support_system": "weak",
                "resource_scarcity": "unknown",
                "systemic_barrier": "none",
                "power_imbalance": "none",
            },
            "temporal_dimension": {
                "stuck_in_past": False,
                "anxious_about_future": False,
                "present_awareness": 5,
                "time_pressure": 5,
                "urgency_real": False,
                "urgency_perceived": False,
                "patience_level": 5,
            },
            "relational_dynamics": {
                "trust_level": 5,
                "vulnerability_shown": 5,
                "defensiveness": 5,
                "connection_seeking": 5,
                "isolation_level": 5,
                "projection": "none",
                "transference": "none",
            },
            "transformation_potential": {
                "readiness_for_change": 5,
                "resistance_level": 5,
                "insight_capacity": 5,
                "agency_belief": 5,
                "hope_level": 5,
                "breakthrough_proximity": "far",
                "growth_edge": "unknown",
            },
            "actionable_intelligence": {
                "immediate_need": "unknown",
                "intervention_type": "support",
                "communication_strategy": "empathize",
                "danger_signs": [],
                "green_lights": [],
                "next_conversation_approach": "standard",
            },
        }
