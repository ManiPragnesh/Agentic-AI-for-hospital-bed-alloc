import requests
import time

BASE_URL = "http://localhost:8000/api"

def run_simple():
    print("🚀 Starting Simple Run (No RL)...")
    requests.post(f"{BASE_URL}/simulation/reset", json={
        "scenario": "NORMAL", 
        "use_rl": False 
    })
    
    start_t = time.time()
    requests.post(f"{BASE_URL}/simulation/step", json={"hours": 24})
    print(f"✅ Stepped 24h in {time.time() - start_t:.2f}s")
    
    res = requests.get(f"{BASE_URL}/metrics")
    print(f"Metrics: {res.json()['global']}")

if __name__ == "__main__":
    run_simple()
