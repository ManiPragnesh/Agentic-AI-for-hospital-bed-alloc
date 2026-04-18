import gymnasium as gym
from stable_baselines3 import PPO
import numpy as np
import os
import sys

# Path Hack
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from backend.src.rl.gym_env import HospitalGymEnv

def run_episode(agent_type='baseline', model=None):
    env = HospitalGymEnv()
    
    # Configure Agent Mode
    # Configure Agent Mode
    # NOTE: We keep mode='RL' for both, but manually inject heuristic actions for baseline
    # to ensure the Gym step() loop functions correctly.
    # env.sim is init in reset(), so we don't touch it here.
        
    obs, info = env.reset()
    done = False
    total_reward = 0
    steps = 0
    
    while not done:
        if agent_type == 'baseline':
             # HEURISTIC LOGIC (Mirroring AdmissionAgent)
             patient = env.sim.current_patient
             action = 0 # Default General
             
             if patient:
                  target = patient.care_type
                  # 0: Gen, 1: ICU, 2: Emer, 3: Transfer
                  
                  if target == 'ICU':
                      # Check capacity
                      icu_free = env.sim.departments['ICU'].beds.capacity - env.sim.departments['ICU'].beds.count
                      if icu_free > 0: action = 1
                      else: action = 0 # Fallback to General (or Queue if full)
                      
                  elif target == 'Emergency':
                      action = 2
                      
                  else:
                      action = 0
             
        else:
            action, _ = model.predict(obs, deterministic=True)
            if isinstance(action, np.ndarray): action = int(action)
            
        obs, reward, done, truncated, info = env.step(action)
        total_reward += reward
        steps += 1
        
    # Collect Metrics from Monitor
    monitor = env.sim.monitor
    
    avg_wait = monitor.total_wait_time / max(1, monitor.total_admissions)
    
    avg_occ = {}
    for name, history in monitor.occupancy_history.items():
        avg_occ[name] = np.mean(history) if history else 0
        
    return total_reward, {
        'avg_wait': avg_wait,
        'avg_occupancy': avg_occ,
        'total_admissions': monitor.total_admissions,
        'total_deaths': monitor.total_deaths
    }

def compare():
    print("📊 Running Baseline Comparison...")
    
    r_base, stats_base = run_episode('baseline')
    print(f"Baseline: Reward={r_base}")
    print(f"  Avg Wait Time: {stats_base['avg_wait']:.2f} hours")
    print(f"  Avg Occupancy: {stats_base['avg_occupancy']}")

    # 2. RL Run
    print("\n🤖 Loading PPO Model...")
    model_path = "backend/src/rl/models/ppo_hospital_v1.zip"
    if not os.path.exists(model_path):
         print("❌ Model not found! Train first.")
         return

    model = PPO.load(model_path)
    r_rl, stats_rl = run_episode('rl', model)
    print(f"RL Agent: Reward={r_rl}")
    print(f"  Avg Wait Time: {stats_rl['avg_wait']:.2f} hours")
    print(f"  Avg Occupancy: {stats_rl['avg_occupancy']}")

    print("\n--- Results ---")
    wait_reduction = (stats_base['avg_wait'] - stats_rl['avg_wait']) / max(0.1, stats_base['avg_wait']) * 100
    print(f"Wait Time Reduction: {wait_reduction:.1f}%")
    
    if wait_reduction >= 20:
        print("✅ Goal Met: >20% reduction in wait time.")
    else:
        print("⚠️ Goal Not Met: Wait time reduction is below 20%. Consider more training.")

    print(f"Reward Improvement: {r_rl - r_base:.1f}")

if __name__ == "__main__":
    compare()
