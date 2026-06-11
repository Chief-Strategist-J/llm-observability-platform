#!/usr/bin/env bash

# Clear target database to avoid local state side effects
rm -f pytrace.db

echo "=== TESTING ALL PYLOW CLI COMMANDS ==="

run_cmd() {
    echo ""
    echo "--------------------------------------------------"
    echo "Running: $@"
    echo "--------------------------------------------------"
    $@
    if [ $? -ne 0 ]; then
        echo "FAIL: $@"
        exit 1
    fi
}

run_cmd pylow flow --last
run_cmd pylow stitch --services api
run_cmd pylow slow --threshold 100ms
run_cmd pylow diff --before v1.2 --after v1.3
run_cmd pylow syscall 1234
run_cmd pylow malloc 1234
run_cmd pylow tcp 1234
run_cmd pylow io 1234
run_cmd pylow flame 1234 --duration 1
run_cmd pylow sched 1234
run_cmd pylow pycall 1234
run_cmd pylow pyframe 1234
run_cmd pylow pycpu 1234
run_cmd pylow pyexcept 1234
run_cmd pylow pyiowait 1234
run_cmd pylow pygil 1234
run_cmd pylow pyleak 1234
run_cmd pylow pyreq 1234
run_cmd pylow timeline 1234 --duration 1.0
run_cmd pylow pythread 1234
run_cmd pylow pyasync 1234
run_cmd pylow pyargs 1234
run_cmd pylow pysyscall 1234
run_cmd pylow pynplus1 1234
run_cmd pylow pygraph 1234
run_cmd pylow pyanomaly 1234
run_cmd pylow pydash 1234
run_cmd pylow pysingle 1234 handle_request
run_cmd pylow page-faults 1234
run_cmd pylow context-switches 1234
run_cmd pylow kernel-blocked 1234
run_cmd pylow tlb-shootdowns 1234
run_cmd pylow irq-impact 1234
run_cmd pylow triage 1234
run_cmd pylow cpu-bound 1234
run_cmd pylow io-bound 1234
run_cmd pylow syscall-storm 1234
run_cmd pylow deadlock 1234
run_cmd pylow service-map 1234
run_cmd pylow ordered-log 1234
run_cmd pylow intercept 1234
run_cmd pylow anomaly-trigger 1234
run_cmd pylow correlation 1234



echo ""
echo "============================================="
echo "ALL PYLOW CLI COMMANDS COMPLETED SUCCESSFULLY"
echo "============================================="
