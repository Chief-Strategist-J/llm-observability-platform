# Event Schema Definitions

## User Request Event
```json
{
  "event_type": "user_request",
  "user_id": "string",
  "message": "string",
  "session_id": "string",
  "timestamp": "ISO8601",
  "metadata": {
    "service": "ai-proxy-service",
    "version": "1.0.0"
  }
}
```

## Knowledge Graph Enhancement Event
```json
{
  "event_type": "kg_enhancement",
  "user_id": "string",
  "session_id": "string",
  "context": {
    "entities": [],
    "relationships": []
  },
  "timestamp": "ISO8601"
}
```

## RAG Search Result Event
```json
{
  "event_type": "rag_result",
  "user_id": "string",
  "session_id": "string",
  "documents": [
    {
      "id": "string",
      "content": "string",
      "score": "float"
    }
  ],
  "timestamp": "ISO8601"
}
```

## Workflow Trigger Event
```json
{
  "event_type": "workflow_trigger",
  "workflow_name": "string",
  "trigger_data": {},
  "user_id": "string",
  "timestamp": "ISO8601"
}
```
