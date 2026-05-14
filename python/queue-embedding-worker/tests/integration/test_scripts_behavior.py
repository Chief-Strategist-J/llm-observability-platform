import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_health_check_script_runs_successfully():
    proc = subprocess.run(["bash", str(ROOT / "scripts" / "health-check.sh")], cwd=ROOT, capture_output=True, text=True)
    assert proc.returncode == 0
    assert "ok" in proc.stdout


def test_migrate_script_runs_successfully():
    proc = subprocess.run(["bash", str(ROOT / "scripts" / "migrate.sh")], cwd=ROOT, capture_output=True, text=True)
    assert proc.returncode == 0
    assert "Apply SQL migrations" in proc.stdout
