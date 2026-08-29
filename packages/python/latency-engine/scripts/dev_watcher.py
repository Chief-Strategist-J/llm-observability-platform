#!/usr/bin/env python3
import sys
import time
import os
import subprocess

def watch_and_run(cmd, watch_dirs=("src", "scripts"), patterns=(".py", ".yaml", ".yml")):
    proc = subprocess.Popen(cmd)
    mtimes = {}

    def get_mtimes():
        current = {}
        for wdir in watch_dirs:
            if not os.path.exists(wdir):
                continue
            for root, _, files in os.walk(wdir):
                for f in files:
                    if any(f.endswith(p) for p in patterns):
                        path = os.path.join(root, f)
                        try:
                            current[path] = os.path.getmtime(path)
                        except OSError:
                            pass
        return current

    mtimes = get_mtimes()
    print(f"[DevWatcher] Monitoring directories {watch_dirs} for changes...", flush=True)
    try:
        while True:
            time.sleep(1.0)
            new_mtimes = get_mtimes()
            if new_mtimes != mtimes:
                print("[DevWatcher] Source file change detected! Restarting service...", flush=True)
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
                proc = subprocess.Popen(cmd)
                mtimes = new_mtimes
    except KeyboardInterrupt:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    cmd = sys.argv[1:] if len(sys.argv) > 1 else ["python", "src/worker/index.py"]
    watch_and_run(cmd)
