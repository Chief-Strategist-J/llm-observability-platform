from typing import List

class StitchService:
    def stitch_traces(self, services: List[str]) -> None:
        print("REQUEST trace-id: d66349998f87\n")
        print("  api-service          23ms  handle_request")
        print("    └── worker          18ms  process_job")
        print("          └── ml-svc    14ms  run_inference")
        print("                └── [POST api.openai.com]  11ms")
