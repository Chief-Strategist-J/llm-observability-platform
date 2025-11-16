import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class EmotionalStateBuilder:

    @staticmethod
    def build_core_emotion(data: Dict[str, Any]) -> Dict[str, Any]:
        layer_2 = data.get("layer_2_emotional_state", {})
        return {
            "primary_emotion": layer_2.get("core_emotion", "neutral"),
            "intensity": layer_2.get("intensity", 5),
            "secondary_emotions": layer_2.get("secondary_emotions", []),
            "emotional_trigger": layer_2.get("emotional_trigger", "unknown"),
            "emotional_pattern": layer_2.get("emotional_pattern", "none"),
            "coping_mechanism": layer_2.get("coping_mechanism", "unknown"),
        }

    @staticmethod
    def build_trauma_indicators(data: Dict[str, Any]) -> Dict[str, Any]:
        layer_3 = data.get("layer_3_trauma_indicators", {})
        return {
            "present": layer_3.get("trauma_present", False),
            "type": layer_3.get("trauma_type", "none"),
            "severity": layer_3.get("trauma_severity", 0),
            "defense_mechanism": layer_3.get("defense_mechanism", "unknown"),
        }

    @staticmethod
    def build_dark_patterns(data: Dict[str, Any]) -> Dict[str, Any]:
        layer_4 = data.get("layer_4_dark_patterns", {})
        return {
            "self_sabotage": layer_4.get("self_sabotage", False),
            "perfectionism": layer_4.get("perfectionism_trap", False),
            "imposter_syndrome": layer_4.get("imposter_syndrome", False),
            "learned_helplessness": layer_4.get("learned_helplessness", False),
            "catastrophizing": layer_4.get("catastrophizing", False),
            "all_or_nothing": layer_4.get("all_or_nothing_thinking", False),
        }

    @staticmethod
    def build_meta_questions(data: Dict[str, Any]) -> Dict[str, Any]:
        layer_5 = data.get("layer_5_meta_questions", {})
        return {
            "meta_1": layer_5.get("meta_1", ""),
            "meta_2": layer_5.get("meta_2", ""),
            "meta_3": layer_5.get("meta_3", ""),
            "meta_4": layer_5.get("meta_4", ""),
            "meta_5_core": layer_5.get("meta_5", "Am I fundamentally broken?"),
            "existential_concern": layer_5.get("existential_concern", "unknown"),
        }

    @staticmethod
    def build_behavioral_analysis(data: Dict[str, Any]) -> Dict[str, Any]:
        layer_6 = data.get("layer_6_behavioral_analysis", {})
        return {
            "communication_style": layer_6.get("communication_style", "unknown"),
            "power_dynamic": layer_6.get("power_dynamic", "unknown"),
            "attachment_style": layer_6.get("attachment_style", "unknown"),
            "boundary_health": layer_6.get("boundary_health", 5),
            "autonomy_level": layer_6.get("autonomy_level", 5),
            "help_seeking_pattern": layer_6.get("help_seeking_pattern", "unknown"),
        }

    @staticmethod
    def build_cognitive_state(data: Dict[str, Any]) -> Dict[str, Any]:
        layer_7 = data.get("layer_7_cognitive_state", {})
        return {
            "cognitive_distortion": layer_7.get("cognitive_distortion", "none"),
            "cognitive_load": layer_7.get("cognitive_load", 5),
            "decision_paralysis": layer_7.get("decision_paralysis", False),
            "clarity_level": layer_7.get("clarity_level", 5),
            "executive_function": layer_7.get("executive_function", "functional"),
        }

    @staticmethod
    def build_identity_struggle(data: Dict[str, Any]) -> Dict[str, Any]:
        layer_8 = data.get("layer_8_identity_struggle", {})
        return {
            "self_worth": layer_8.get("self_worth", 5),
            "competence_belief": layer_8.get("competence_belief", 5),
            "belonging_need": layer_8.get("belonging_need", 5),
            "purpose_clarity": layer_8.get("purpose_clarity", 5),
        }

    @staticmethod
    def build_transformation_potential(data: Dict[str, Any]) -> Dict[str, Any]:
        layer_12 = data.get("layer_12_transformation_potential", {})
        return {
            "readiness_for_change": layer_12.get("readiness_for_change", 5),
            "resistance_level": layer_12.get("resistance_level", 5),
            "insight_capacity": layer_12.get("insight_capacity", 5),
            "hope_level": layer_12.get("hope_level", 5),
            "breakthrough_proximity": layer_12.get("breakthrough_proximity", "far"),
        }

    @staticmethod
    def build_actionable_intelligence(data: Dict[str, Any]) -> Dict[str, Any]:
        intel = data.get("actionable_intelligence", {})
        return {
            "immediate_need": intel.get("immediate_need", "unknown"),
            "intervention_type": intel.get("intervention_type", "support"),
            "communication_strategy": intel.get("communication_strategy", "empathize"),
            "danger_signs": intel.get("danger_signs", []),
        }


class EmotionalIntelligenceEngine:

    @staticmethod
    def extract_emotional_layers(deep_analysis: Dict[str, Any]) -> Dict[str, Any]:
        if not deep_analysis or not isinstance(deep_analysis, dict):
            logger.warning("event=emotional_extract_invalid_input")
            return EmotionalIntelligenceEngine._default_state()

        logger.info("event=emotional_extract_start")

        emotional_state = {
            "timestamp": datetime.now().isoformat(),
            **EmotionalStateBuilder.build_core_emotion(deep_analysis),
            "trauma_indicators": EmotionalStateBuilder.build_trauma_indicators(deep_analysis),
            "dark_patterns": EmotionalStateBuilder.build_dark_patterns(deep_analysis),
            "meta_questions": EmotionalStateBuilder.build_meta_questions(deep_analysis),
            "behavioral_analysis": EmotionalStateBuilder.build_behavioral_analysis(deep_analysis),
            "cognitive_state": EmotionalStateBuilder.build_cognitive_state(deep_analysis),
            "identity_struggle": EmotionalStateBuilder.build_identity_struggle(deep_analysis),
            "transformation_potential": EmotionalStateBuilder.build_transformation_potential(deep_analysis),
            "actionable_intelligence": EmotionalStateBuilder.build_actionable_intelligence(deep_analysis),
        }

        logger.info("event=emotional_extract_complete emotion=%s intensity=%s",
                   emotional_state["primary_emotion"], emotional_state["intensity"])

        return emotional_state

    @staticmethod
    def detect_emotional_patterns(current_state: Dict[str, Any], 
                                 previous_states: List[Dict[str, Any]]) -> Dict[str, Any]:
        logger.info("event=pattern_detection_start history_count=%s", len(previous_states))

        if not previous_states:
            return {"pattern_detected": False, "trend": "baseline", "volatility": 0}

        emotions = [s.get("primary_emotion", "neutral") for s in previous_states]
        intensities = [s.get("intensity", 5) for s in previous_states]

        emotions.append(current_state.get("primary_emotion", "neutral"))
        intensities.append(current_state.get("intensity", 5))

        intensity_changes = [abs(intensities[i] - intensities[i-1]) 
                           for i in range(1, len(intensities))]
        avg_volatility = sum(intensity_changes) / len(intensity_changes) if intensity_changes else 0

        if len(intensities) >= 3:
            recent = intensities[-3:]
            trend = "escalating" if recent[-1] > recent[0] else "de-escalating" if recent[-1] < recent[0] else "stable"
        else:
            trend = "insufficient_data"

        emotion_counts = {}
        for emotion in emotions:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

        repeating = max(emotion_counts, key=emotion_counts.get) if emotion_counts else "none"
        repeat_count = emotion_counts.get(repeating, 0)

        pattern = {
            "pattern_detected": repeat_count >= 3,
            "repeating_emotion": repeating,
            "emotion_trajectory": emotions[-5:],
            "intensity_trajectory": intensities[-5:],
            "volatility": round(avg_volatility, 2),
            "trend": trend,
            "emotional_stability": "stable" if avg_volatility < 2 else "volatile",
        }

        logger.info("event=pattern_detection_complete trend=%s volatility=%s", 
                   pattern["trend"], pattern["volatility"])

        return pattern

    @staticmethod
    def _default_state() -> Dict[str, Any]:
        return {
            "timestamp": datetime.now().isoformat(),
            "primary_emotion": "neutral",
            "intensity": 5,
            "secondary_emotions": [],
            "emotional_trigger": "unknown",
            "emotional_pattern": "none",
            "coping_mechanism": "unknown",
            "trauma_indicators": {"present": False, "type": "none", "severity": 0},
            "dark_patterns": {k: False for k in ["self_sabotage", "perfectionism", "imposter_syndrome",
                                                 "learned_helplessness", "catastrophizing", "all_or_nothing"]},
            "meta_questions": {"meta_1": "", "meta_2": "", "meta_3": "", "meta_4": "", 
                             "meta_5_core": "Am I fundamentally broken?", "existential_concern": "unknown"},
            "behavioral_analysis": {"communication_style": "unknown", "power_dynamic": "unknown",
                                  "attachment_style": "unknown", "boundary_health": 5, "autonomy_level": 5},
            "cognitive_state": {"cognitive_distortion": "none", "cognitive_load": 5, 
                              "decision_paralysis": False, "clarity_level": 5},
            "identity_struggle": {"self_worth": 5, "competence_belief": 5, "belonging_need": 5},
            "transformation_potential": {"readiness_for_change": 5, "resistance_level": 5, 
                                       "hope_level": 5, "breakthrough_proximity": "far"},
            "actionable_intelligence": {"immediate_need": "unknown", "intervention_type": "support",
                                      "communication_strategy": "empathize", "danger_signs": []},
        }
