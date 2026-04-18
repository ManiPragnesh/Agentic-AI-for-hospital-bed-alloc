import sys
import os
# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from backend.src.api import sim_state, get_metrics

try:
    print("Resetting simulation...")
    sim_state.reset()
    print("Simulation reset.")
    
    print("Fetching metrics...")
    m = get_metrics()
    print("Metrics fetched successfully.")
    print(m)
except Exception as e:
    print("CRASHED:")
    import traceback
    traceback.print_exc()
