#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import urllib.request
import urllib.parse

def load_yaml(file_path):
    # Since we don't want to rely on PyYAML if not installed globally, we can parse this simple YAML format manually
    queries = []
    current_query = {}
    feature_name = ""
    
    with open(file_path, 'r') as f:
        in_queries = False
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            
            if stripped.startswith("feature:"):
                feature_name = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("queries:"):
                in_queries = True
            elif in_queries and stripped.startswith("-"):
                if current_query:
                    queries.append(current_query)
                current_query = {}
                parts = stripped.lstrip("- ").split(":", 1)
                if len(parts) == 2:
                    current_query[parts[0].strip()] = parts[1].strip()
            elif in_queries and ":" in stripped:
                parts = stripped.split(":", 1)
                key = parts[0].strip()
                val = parts[1].strip()
                # strip surrounding quotes if any
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                current_query[key] = val
        if current_query:
            queries.append(current_query)
            
    return feature_name, queries

def execute_postgresql(query):
    cmd = ["docker", "exec", "-i", "quality-engine-postgres", "psql", "-U", "postgres", "-d", "quality_engine_db", "-c", query]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        return res.stdout
    else:
        return f"Error executing PostgreSQL: {res.stderr}"

def execute_redis(query):
    cmd = ["docker", "exec", "-i", "quality-engine-redis", "redis-cli"] + query.split()
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        return res.stdout
    } else:
        return f"Error executing Redis: {res.stderr}"

def execute_kafka(query):
    # Adjust kafka bootstrap hosts for docker command if executed from host
    adjusted_query = query.replace("kafka:29092", "localhost:9094")
    print(f"Executing Kafka: docker exec -it docker-kafka-1 {adjusted_query}")
    print("Press Ctrl+C to stop consuming...")
    cmd = ["docker", "exec", "-it", "docker-kafka-1"] + adjusted_query.split()
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nConsumer stopped.")
    return ""

def execute_promql(query):
    encoded_query = urllib.parse.urlencode({"query": query})
    url = f"http://localhost:9090/api/v1/query?{encoded_query}"
    try:
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read().decode())
            if data.get("status") == "success":
                results = data["data"]["result"]
                if not results:
                    return "No metrics matching the query currently found in Prometheus."
                out = []
                for r in results:
                    metric = r.get("metric", {})
                    val = r.get("value", [])
                    out.append(f"Metric: {metric}\nValue: {val}\n")
                return "\n".join(out)
            return f"Prometheus returned error: {data}"
    except Exception as e:
        return f"Failed to connect to Prometheus: {e}"

def execute_traceql(query):
    encoded_query = urllib.parse.urlencode({"q": query})
    # Query Tempo via the quality-observability-stack container internally
    cmd = ["docker", "exec", "quality-observability-stack", "curl", "-s", f"http://localhost:3200/api/search?{encoded_query}"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        try:
            data = json.loads(res.stdout)
            traces = data.get("traces", [])
            if not traces:
                return "No traces matched the TraceQL query."
            out = []
            for t in traces:
                out.append(f"Trace ID: {t['traceID']} | Service: {t['rootServiceName']} | Root: {t['rootTraceName']} | Duration: {t['durationMs']}ms")
            return "\n".join(out)
        except Exception as e:
            return f"Raw Response:\n{res.stdout}"
    return f"Error executing TraceQL: {res.stderr}"

def main():
    queries_root = "queries"
    if not os.path.isdir(queries_root):
        print(f"Error: {queries_root} directory not found.")
        sys.exit(1)
        
    features = [d for d in os.listdir(queries_root) if os.path.isdir(os.path.join(queries_root, d))]
    
    print("==============================================")
    # Style: bold and clean CLI interface
    print("📊 LLM Observability Platform Query Runner")
    print("==============================================")
    print("Select a feature folder:")
    for idx, f in enumerate(features, 1):
        print(f"  [{idx}] {f}")
        
    try:
        sel = int(input("Enter number: ")) - 1
        if sel < 0 or sel >= len(features):
            raise ValueError()
    except (ValueError, IndexError, KeyboardInterrupt):
        print("Invalid selection.")
        sys.exit(1)
        
    feature_dir = os.path.join(queries_root, features[sel])
    yaml_path = os.path.join(feature_dir, "queries.yaml")
    
    feature_name, queries = load_yaml(yaml_path)
    
    print("\n----------------------------------------------")
    print(f"Feature: {feature_name}")
    print("Select a query to execute:")
    for idx, q in enumerate(queries, 1):
        print(f"  [{idx}] {q.get('id')} ({q.get('type').upper()})")
        print(f"      Description: {q.get('description')}")
        print(f"      Importance:  {q.get('importance')}")
        
    try:
        sel_q = int(input("Enter number: ")) - 1
        if sel_q < 0 or sel_q >= len(queries):
            raise ValueError()
    except (ValueError, IndexError, KeyboardInterrupt):
        print("Invalid selection.")
        sys.exit(1)
        
    query_obj = queries[sel_q]
    q_type = query_obj.get("type")
    q_str = query_obj.get("query")
    
    print("\n==============================================")
    print(f"Executing: {q_str}")
    print(f"Type: {q_type.upper()}")
    print("Expected Output: " + str(query_obj.get("expected_output")))
    print("==============================================\n")
    
    result = ""
    if q_type == "postgresql":
        result = execute_postgresql(q_str)
    elif q_type == "redis":
        result = execute_redis(q_str)
    elif q_type == "kafka":
        result = execute_kafka(q_str)
    elif q_type == "promql":
        result = execute_promql(q_str)
    elif q_type == "traceql":
        result = execute_traceql(q_str)
    else:
        result = f"Unsupported query type: {q_type}"
        
    if result:
        print(result)
        
if __name__ == "__main__":
    main()
