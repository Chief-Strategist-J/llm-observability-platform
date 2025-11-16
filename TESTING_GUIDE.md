# Testing Guide - Chatbot Improvements

## Quick Test Checklist

### 1. Web Search Functionality ✅

**Test Case 1.1: Default Web Search Enabled**
```
1. Open Streamlit app
2. Check sidebar → "🔍 Web Search & Real-Time Data"
3. Verify checkbox is CHECKED by default
4. Expected: "Enable Internet Search for Real-Time Data" is checked
```

**Test Case 1.2: Web Search Returns Results**
```
1. Enable "Search" mode
2. Ask: "What is the current weather in New York?"
3. Expected: Response includes "✅ Used X web tools for real-time data"
4. Response should contain current weather information
```

**Test Case 1.3: Research Mode Works**
```
1. Select "Research" mode
2. Ask: "Latest developments in AI 2025"
3. Expected: Deep analysis with multiple sources
4. Response should cite sources and provide comprehensive info
```

**Test Case 1.4: Normal Mode (No Web Search)**
```
1. Select "Normal" mode
2. Ask: "What happened today in tech?"
3. Expected: Response based on training data only
4. No "web tools" message should appear
```

---

### 2. Emotional Intelligence Engine ✅

**Test Case 2.1: Emotional Layer Extraction**
```
1. Ask: "I'm feeling really stuck and can't figure out what to do"
2. Check logs for: event=app_emotional_intelligence
3. Expected output includes:
   - primary_emotion: (e.g., "overwhelmed", "confused", "frustrated")
   - intensity: (1-10 scale)
   - trauma_present: true/false
   - dark_patterns: (list of detected patterns)
   - readiness_for_change: (1-10 scale)
```

**Test Case 2.2: Meta Questions (Core Insight)**
```
1. Ask: "Why do I always fail at everything?"
2. Check logs for: meta_5_core
3. Expected: Deep meta-question like "Am I fundamentally broken?"
4. Verify it captures the underlying existential concern
```

**Test Case 2.3: Trauma Detection**
```
1. Ask: "I was rejected by someone I trusted deeply"
2. Check emotional_state["trauma_indicators"]
3. Expected:
   - trauma_present: true
   - trauma_type: "rejection" or "betrayal"
   - severity: (high number)
   - defense_mechanism: (e.g., "avoidance", "intellectualization")
```

**Test Case 2.4: Dark Pattern Recognition**
```
1. Ask: "I should be able to do this perfectly or not at all"
2. Check emotional_state["dark_patterns"]
3. Expected:
   - perfectionism: true
   - all_or_nothing: true
   - catastrophizing: true
```

**Test Case 2.5: Behavioral Analysis**
```
1. Ask: "Can you help me with this? I'm not sure I can do it myself"
2. Check emotional_state["behavioral_analysis"]
3. Expected:
   - communication_style: "pleading" or "questioning"
   - attachment_style: "anxious"
   - help_seeking_pattern: "chronic" or "new"
```

**Test Case 2.6: Cognitive State Assessment**
```
1. Ask a complex multi-part question
2. Check emotional_state["cognitive_state"]
3. Expected:
   - cognitive_load: (high if complex)
   - decision_paralysis: true/false
   - clarity_level: (1-10)
```

**Test Case 2.7: Transformation Potential**
```
1. Ask: "I want to change but I'm scared"
2. Check emotional_state["transformation_potential"]
3. Expected:
   - readiness_for_change: (6-8 range)
   - resistance_level: (moderate)
   - breakthrough_proximity: "approaching"
   - growth_edge: (specific area to work on)
```

---

### 3. No Assumptions Principle ✅

**Test Case 3.1: Fallback Analysis Only When Needed**
```
1. Disable LLM deep analysis (simulate failure)
2. Ask a question
3. Expected: Fallback analysis triggers
4. Check logs: event=deep_psych_fallback_start
5. Verify fallback is based on keyword detection, not assumptions
```

**Test Case 3.2: Precise Analysis From Real Data**
```
1. Ask: "I'm struggling with perfectionism"
2. Check emotional_state["dark_patterns"]["perfectionism"]
3. Expected: true (detected from actual content)
4. Should NOT assume other patterns not mentioned
```

---

### 4. Knowledge Graph Integration ✅

**Test Case 4.1: Emotional Data Stored**
```
1. Have a conversation with emotional content
2. Check Neo4j database (or JSON backup)
3. Expected: Conversation node includes:
   - emotion_primary: (detected emotion)
   - emotion_intensity: (1-10)
   - trauma_indicators: (if present)
   - dark_patterns: (if detected)
```

**Test Case 4.2: Pattern Tracking**
```
1. Have multiple conversations with similar emotional themes
2. Check Neo4j for FOLLOWED_BY relationships
3. Expected:
   - emotion_shift: "frustrated_to_neutral"
   - time_gap: (seconds between conversations)
   - Pattern detection across conversations
```

---

### 5. Logging Verification ✅

**Test Case 5.1: Web Search Logging**
```
Logs should include:
- event=agent_mode_activated mode=Search
- event=agent_tools_used count=X
- event=web_search_start query=...
- event=web_search_success total_results=X
```

**Test Case 5.2: Emotional Analysis Logging**
```
Logs should include:
- event=app_emotional_intelligence
- event=emotional_extract_start
- event=emotional_extract_complete emotion=X intensity=Y
- event=deep_psych_start/success/failed
```

---

## Manual Testing Scenarios

### Scenario 1: User Seeking Real-Time Information
```
User: "What are the latest AI models released in 2025?"
Expected:
- Web search automatically triggered
- Results from current sources
- "✅ Used X web tools for real-time data" message
- Comprehensive, up-to-date response
```

### Scenario 2: User with Emotional Struggle
```
User: "I feel like I'm not good enough and I'll never succeed"
Expected:
- Emotional analysis captures:
  - Primary emotion: "hopeless" or "inadequate"
  - Intensity: 7-8/10
  - Dark patterns: imposter_syndrome, catastrophizing
  - Meta_5: "Am I fundamentally broken?"
  - Trauma type: "inadequacy"
- Appropriate intervention strategy logged
```

### Scenario 3: Complex Technical Question with Emotional Component
```
User: "I can't figure out this code and I feel stupid"
Expected:
- Web search finds current solutions (if needed)
- Emotional analysis detects:
  - Frustration + self-doubt
  - Imposter syndrome
  - Perfectionism trap
  - Cognitive load: high
- Response addresses both technical and emotional aspects
```

### Scenario 4: Pattern Recognition Across Conversations
```
Conversation 1: "I'm overwhelmed"
Conversation 2: "I'm still stuck"
Conversation 3: "I think I'm making progress"
Expected:
- Emotion trajectory: overwhelmed → stuck → hopeful
- Pattern detected: escalation then improvement
- Volatility: moderate
- Trend: de-escalating (improving)
```

---

## Log Analysis Commands

### View Web Search Activity
```bash
grep "event=agent_mode_activated\|event=agent_tools_used\|event=web_search" logs.txt
```

### View Emotional Analysis
```bash
grep "event=app_emotional_intelligence\|event=emotional_extract\|event=deep_psych" logs.txt
```

### View Pattern Detection
```bash
grep "event=pattern_detection\|event=kg_conversation_chain" logs.txt
```

### View All Chat Events
```bash
grep "event=app_chat_response" logs.txt
```

---

## Expected Behavior Summary

| Feature | Before | After |
|---------|--------|-------|
| Web Search | Disabled by default | **Enabled by default** |
| Emotional Layers | 2 (emotion + intensity) | **12 comprehensive layers** |
| Assumptions | Made when data missing | **None - fallback only when LLM fails** |
| Pattern Tracking | None | **Across conversations** |
| Trauma Detection | Not tracked | **Detected and categorized** |
| Dark Patterns | Not identified | **All 7 patterns tracked** |
| Meta Questions | Not analyzed | **5-level deep analysis** |
| Actionable Intelligence | Generic | **Specific to user state** |

---

## Troubleshooting

### Web Search Not Working
```
Check:
1. Internet connection active
2. DuckDuckGo/Wikipedia APIs accessible
3. Logs for: event=web_search_failed
4. Fallback to Normal mode if needed
```

### Emotional Analysis Not Triggering
```
Check:
1. Deep analysis enabled (should be by default)
2. Logs for: event=deep_psych_start
3. If failed, check: event=deep_psych_fallback_start
4. Verify LLM model is responding
```

### Knowledge Graph Not Storing Data
```
Check:
1. Neo4j connection available
2. Logs for: event=kg_neo4j_success or event=kg_file_success
3. Fallback JSON storage in: chat_backups/conversations.json
4. Check file permissions
```

---

## Performance Metrics to Monitor

- Web search response time: < 5 seconds
- Emotional analysis time: < 3 seconds
- Total chat response time: < 10 seconds
- Knowledge graph storage: < 1 second
- Pattern detection: < 500ms

---

**Last Updated**: 2025-11-16 18:47:11
