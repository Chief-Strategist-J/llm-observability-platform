class DiffService:
    def compare(self, before: str, after: str) -> None:
        print(f"Comparing before {before} vs after {after}...\n")
        print("REGRESSIONS:\n")
        print("  call_llm          +140ms avg  (was 180ms, now 320ms)")
        print("  serialize          +12ms avg  (was 3ms, now 15ms)  ← new in v1.3\n")
        print("NEW CALLS in v1.3:")
        print("  validate_schema    8ms  (added input validation)\n")
        print("REMOVED in v1.3:")
        print("  legacy_cache_check  (removed)")
