import subprocess
import time
import requests
import sys
import os

def test_api():
    # Start Server
    print("Starting Uvicorn Server...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.server.main:app", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    try:
        # Wait for startup
        print("Waiting for startup...")
        time.sleep(10)
        
        # Test Root
        try:
            resp = requests.get("http://localhost:8000/")
            print(f"Root: {resp.status_code} {resp.json()}")
            assert resp.status_code == 200
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to server.")
            raise

        # Test Reset
        resp = requests.post("http://localhost:8000/simulation/reset")
        print(f"Reset: {resp.status_code} {resp.json()}")
        assert resp.status_code == 200
        
        # Test Step
        initial_metrics = requests.get("http://localhost:8000/metrics").json()
        print(f"Initial Time: {initial_metrics['time']}")
        
        print("Stepping sim...")
        resp = requests.post("http://localhost:8000/simulation/step", json={"hours": 1})
        print(f"Step: {resp.status_code} {resp.json()}")
        assert resp.status_code == 200
        
        # Test Metrics again
        resp = requests.get("http://localhost:8000/metrics")
        data = resp.json()
        print(f"Metrics Time: {data['time']}")
        assert data['time'] > initial_metrics['time']
        
        print("✅ API Test Passed")
        
    except Exception as e:
        print(f"❌ API Test Failed: {e}")
        outs, errs = proc.communicate(timeout=1)
        print("Server Output:", outs.decode())
        print("Server Error:", errs.decode())
        
    finally:
        print("Terminating server...")
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    test_api()
