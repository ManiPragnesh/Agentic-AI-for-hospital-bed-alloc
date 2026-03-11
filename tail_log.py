import os

fn = "backend/logs/simulation_run_1770805821.json"
size = os.path.getsize(fn)
with open(fn, "rb") as f:
    f.seek(max(0, size - 1000))
    print(f.read().decode('utf-8', errors='ignore'))
