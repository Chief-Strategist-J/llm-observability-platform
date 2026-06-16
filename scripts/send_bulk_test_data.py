#!/usr/bin/env python3
import json
import random
import time
import urllib.request
import uuid
import subprocess
from datetime import datetime, timezone

MODELS = ["gpt-4o", "claude-3-5-sonnet", "llama-3.1-70b", "gemini-1.5-pro"]
PROVIDERS = ["openai", "anthropic", "meta", "google"]
ENDPOINTS = ["/v1/chat/completions", "/v1/messages", "/v1/completions", "/v1/generate"]
LANGUAGES = ["en", "en", "en", "es", "fr", "de"]
USERS = ["user_9823", "user_1102", "user_4920", "user_6672", "user_0911"]

def send_span(span_id, trace_id, model, provider, endpoint, user_id, latency, prompt_toks, comp_toks, cost):
    payload = {
        "span_id": span_id,
        "trace_id": trace_id,
        "user_id": user_id,
        "schema_version": 1,
        "model": model,
        "provider": provider,
        "service_name": "test-service",
        "endpoint": endpoint,
        "environment": "dev",
        "prompt_tokens": prompt_toks,
        "completion_tokens": comp_toks,
        "latency_ms_total": latency,
        "finish_reason": "stop" if random.random() > 0.05 else "content_filter",
        "cost_usd_micro": cost,
        "price_version": "v1",
        "token_count_method": "tiktoken",
        "is_sampled": True,
        "timestamp_utc": datetime.now(timezone.utc).isoformat()
    }
    
    req = urllib.request.Request(
        "http://localhost:8002/v1/spans",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            resp.read()
    except Exception as e:
        print(f"Failed to send span: {e}")

def send_score(span_id, trace_id, model, endpoint, user_id, prompt_type, lang, scores, flags=[]):
    payload = {
        "span_id": span_id,
        "trace_id": trace_id,
        "model": model,
        "endpoint": endpoint,
        "prompt_type": prompt_type,
        "response_language": lang,
        "scores": scores,
        "quality_flags": flags,
        "scored_at": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id
    }
    
    # Write directly via docker-kafka-1 kafka-console-producer
    proc = subprocess.Popen(
        ["docker", "exec", "-i", "docker-kafka-1", "kafka-console-producer", "--topic", "llm.quality.scores", "--bootstrap-server", "kafka:29092"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    proc.communicate(input=json.dumps(payload).encode() + b"\n")

def main():
    print("🚀 Pushing bulk test data to populate dashboard metrics...")
    
    for i in range(30):
        span_id = str(uuid.uuid4())
        trace_id = str(uuid.uuid4())
        
        idx = random.randint(0, len(MODELS) - 1)
        model = MODELS[idx]
        provider = PROVIDERS[idx]
        endpoint = ENDPOINTS[idx]
        user_id = random.choice(USERS)
        
        latency = random.randint(150, 1800)
        prompt_toks = random.randint(10, 200)
        comp_toks = random.randint(15, 500)
        cost = int(prompt_toks * 0.015 + comp_toks * 0.06)
        
        # 1. Send the span to instrumentation SDK
        send_span(span_id, trace_id, model, provider, endpoint, user_id, latency, prompt_toks, comp_toks, cost)
        
        # Determine score variables
        is_toxic = random.random() < 0.15
        toxicity = random.uniform(0.55, 0.98) if is_toxic else random.uniform(0.01, 0.25)
        
        is_coherent = random.random() > 0.10
        coherence = random.uniform(0.65, 0.99) if is_coherent else random.uniform(0.05, 0.25)
        
        faithfulness = random.uniform(0.75, 1.0) if random.random() > 0.10 else random.uniform(0.20, 0.65)
        perplexity = random.uniform(1.2, 5.0) if random.random() > 0.05 else random.uniform(25.0, 95.0)
        
        scores = {
            "coherence": coherence,
            "toxicity": toxicity,
            "faithfulness": faithfulness,
            "perplexity": perplexity
        }
        
        prompt_type = random.choice(["chat", "rag", "code", "classification"])
        lang = random.choice(LANGUAGES)
        
        flags = []
        if faithfulness < 0.70:
            flags.append("HALLUCINATION_RISK")
        if coherence < 0.30:
            flags.append("LOW_COHERENCE")
            
        # 2. Send the score
        send_score(span_id, trace_id, model, endpoint, user_id, prompt_type, lang, scores, flags)
        
        # Emit a simulated invariant violation metric periodically
        if i % 10 == 0:
            subprocess.run(["docker", "exec", "quality-engine", "python", "-c", 
                            "from prometheus_client import CollectorRegistry, Counter, push_to_gateway; "
                            "reg = CollectorRegistry(); "
                            f"c = Counter('invariant_violation_total', 'Violations', ['invariant_id'], registry=reg); "
                            f"c.labels(invariant_id='INV-Q-0{random.randint(1,7)}').inc(); "
                            "push_to_gateway('quality-observability-stack:9091', job='quality-engine', registry=reg)"], 
                            capture_output=True)
            
        time.sleep(0.1)
        
    print("✅ Successfully generated and pushed 30 simulated spans and quality scores!")

if __name__ == "__main__":
    main()
