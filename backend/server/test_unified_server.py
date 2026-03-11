import subprocess
import time
import requests
import sys
import os

def test_unified():
    env = os.environ.copy()
    env.pop("DEV_PROXY", None)
    print("Building frontend for unified package...")
    subprocess.check_call([sys.executable, os.path.join("scripts", "build_unified.py")])

    print("Starting unified server...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.server.main:app", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    try:
        time.sleep(3)
        # Frontend root should serve HTML
        r = requests.get("http://localhost:8000/")
        assert r.status_code == 200
        assert "<html" in r.text.lower()

        # API endpoint should work under /api
        r2 = requests.post("http://localhost:8000/api/simulation/reset")
        assert r2.status_code == 200
        r3 = requests.get("http://localhost:8000/api/metrics")
        assert r3.status_code == 200
        data = r3.json()
        assert "time" in data
        print("✅ Unified server test passed")
    finally:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    test_unified()
