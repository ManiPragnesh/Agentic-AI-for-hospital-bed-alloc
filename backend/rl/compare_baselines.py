import gymnasium as gym
from stable_baselines3 import PPO
import numpy as np
import os
import sys

# Path Hack
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from backend.rl.gym_env import HospitalGymEnv

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
    stats = env.sim.monitor.stats
    logs = env.sim.monitor.logs
    
    # Calculate Avg Wait Time
    # (Simplified from logs)
    return total_reward, env.sim.monitor.stats

def compare():
    print("📊 Running Baseline Comparison...")
    
    # 1. Baseline Run
    # We need to ensure Env runs in Rule Mode? 
    # Actually, GymEnv forces RL mode in reset(). 
    # We will use the 'heuristic action' logic in the loop above.
    
    r_base, stats_base = run_episode('baseline')
    print(f"Baseline: Reward={r_base}, Stats={stats_base}")

    # 2. RL Run
    print("🤖 Loading PPO Model...")
    model_path = "backend/rl/models/ppo_hospital_v1.zip"
    if not os.path.exists(model_path):
         print("❌ Model not found! Train first.")
         return

    model = PPO.load(model_path)
    r_rl, stats_rl = run_episode('rl', model)
    print(f"RL Agent: Reward={r_rl}, Stats={stats_rl}")

    print("\n--- Results ---")
    print(f"Reward Improvement: {r_rl - r_base}")
    # print(f"Wait Time Improvement: ...")

if __name__ == "__main__":
    compare()
