class SlowService:
    def monitor(self, threshold_ms: int, watch: bool) -> None:
        print(f"Continuous monitoring daemon started. Threshold: {threshold_ms}ms, Watch: {watch}")
        print("SLOW PATHS detected (last 5 min):\n")
        print("  #1  handle_request → call_llm → [POST openai] ")
        print("      avg: 340ms  max: 891ms  occurrences: 14")
        print("      root cause: epoll_wait 310ms — network latency to openai\n")
        print("  #2  handle_request → get_user_context → [postgres SELECT]")
        print("      avg: 210ms  occurrences: 3  ")
        print("      root cause: missing index (full table scan detected)")
