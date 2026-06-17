migration/phases/phase-0-audit/checklist.md

[ ] Every service has a CONTRACT.md
[ ] Every port in use is documented
[ ] Every service-to-service call is documented
[ ] Every external egress endpoint is documented
[ ] DNS TTL set to 60s for all internal records
[ ] Current error rates recorded (p50, p95, p99 latency)
[ ] Current connection counts recorded per service pair
[ ] Load balancer access logs enabled and retained (min 30 days)
[ ] All hardcoded IPs found and ticketed for replacement
[ ] Circular dependencies identified (these block migration order)
