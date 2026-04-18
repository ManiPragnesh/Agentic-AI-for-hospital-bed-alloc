import os
import sys
import numpy as np
from stable_baselines3 import PPO
import builtins

# Path Hack
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.src.rl.gym_env import HospitalGymEnv

# Global to keep original print
original_print = builtins.print

def silent_print(*args, **kwargs):
    if args and isinstance(args[0], str):
        msg = args[0]
        if msg.startswith("DEBUG:") or msg.startswith("🚀") or msg.startswith("✅") or msg.startswith("💾") or msg.startswith("[INFO]") or msg.startswith("[WARN]"):
            return
    original_print(*args, **kwargs)

def run_research_episode(run_num, policy_type, model=None):
    env = HospitalGymEnv()
    obs, info = env.reset()
    done = False
    total_reward = 0
    
    hourly_stats = []
    
    # We'll track our own history to avoid issues with monitor flushing
    history_occ = {'General': [], 'ICU': [], 'Emergency': []}
    
    while not done:
        if policy_type == 'FCFS':
            patient = env.sim.current_patient
            action = 0 
            if patient:
                target = patient.care_type
                if target == 'ICU':
                    icu_free = env.sim.departments['ICU'].beds.capacity - env.sim.departments['ICU'].beds.count
                    action = 1 if icu_free > 0 else 0
                elif target == 'Emergency':
                    action = 2
                else:
                    action = 0
        else:
            action, _ = model.predict(obs, deterministic=True)
            if isinstance(action, np.ndarray): action = int(action)
            
        obs, reward, done, truncated, info = env.step(action)
        total_reward += reward
        
        # Record current occupancy
        for name, dept in env.sim.departments.items():
            history_occ[name].append(dept.beds.count / max(1, dept.beds.capacity))
        
        current_hour = int(env.sim_env.now)
        if current_hour > 0 and len(hourly_stats) < current_hour:
            # Hourly snapshot
            total_occupied = sum(d.beds.count for d in env.sim.departments.values())
            total_capacity = sum(d.beds.capacity for d in env.sim.departments.values())
            util = total_occupied / max(1, total_capacity)
            
            all_waiting = []
            for dept in env.sim.departments.values():
                all_waiting.extend(list(dept.queue))
            
            avg_wait_min = 0
            if all_waiting:
                avg_wait_min = np.mean([env.sim_env.now - p.arrival_time for p in all_waiting]) * 60
            
            # Fill in any missing hours (if the sim jumped ahead)
            while len(hourly_stats) < current_hour:
                hour_to_add = len(hourly_stats) + 1
                hourly_stats.append((hour_to_add, avg_wait_min, util))

    monitor = env.sim.monitor
    total_patients = max(1, monitor.total_patients)
    avg_wait_time = monitor.total_wait_time / max(1, monitor.total_admissions)
    
    # Global Utilization from our history
    global_utils = []
    for g, i, e in zip(history_occ['General'], history_occ['ICU'], history_occ['Emergency']):
        global_utils.append((g*50 + i*10 + e*10) / 70)
    
    bed_util_rate = np.mean(global_utils) if global_utils else 0
    failure_rate = monitor.total_deaths / total_patients
    
    dept_utils = {
        'ICU': np.mean(history_occ['ICU']) if history_occ['ICU'] else 0,
        'Emergency': np.mean(history_occ['Emergency']) if history_occ['Emergency'] else 0,
        'General': np.mean(history_occ['General']) if history_occ['General'] else 0
    }

    original_print("==============================")
    original_print(f"RUN: {run_num}")
    original_print(f"POLICY: {policy_type}")
    original_print(f"Average_Wait_Time: {avg_wait_time:.2f}")
    original_print(f"Bed_Utilization_Rate: {bed_util_rate:.2f}")
    original_print(f"Critical_Failure_Rate: {failure_rate:.4f}")
    original_print(f"Total_Patients: {monitor.total_patients}")
    original_print("--- TIME SERIES (Hourly) ---")
    original_print("Format:")
    original_print("Hour | Avg_Wait_Time | Bed_Utilization")
    for h, w, u in hourly_stats:
        original_print(f"{h} | {int(w)} | {u:.2f}")
    original_print("--- DEPARTMENT UTILIZATION ---")
    original_print(f"ICU_Utilization: {dept_utils['ICU']:.2f}")
    original_print(f"Emergency_Utilization: {dept_utils['Emergency']:.2f}")
    original_print(f"General_Utilization: {dept_utils['General']:.2f}")
    if policy_type == 'RL':
        original_print("--- OPTIONAL (if RL) ---")
        original_print(f"Total_Reward: {total_reward:.1f}")
    original_print("==============================")

    return {
        'avg_wait': avg_wait_time,
        'bed_util': bed_util_rate,
        'failure_rate': failure_rate
    }

def run_all():
    builtins.print = silent_print
    
    model_path = "backend/src/rl/models/ppo_hospital_v1.zip"
    model = PPO.load(model_path) if os.path.exists(model_path) else None
    
    all_fcfs = []
    all_rl = []
    
    for i in range(1, 2):
        all_fcfs.append(run_research_episode(i, 'FCFS'))
        
    for i in range(1, 2):
        all_rl.append(run_research_episode(i, 'RL', model))
        
    original_print("==============================")
    original_print("FINAL SUMMARY (AVERAGE OVER 1 RUNS)")
    original_print("FCFS:")
    original_print(f"Avg_Wait_Time: {np.mean([r['avg_wait'] for r in all_fcfs]):.2f}")
    original_print(f"Bed_Utilization: {np.mean([r['bed_util'] for r in all_fcfs]):.2f}")
    original_print(f"Failure_Rate: {np.mean([r['failure_rate'] for r in all_fcfs]):.4f}")
    original_print("RL:")
    original_print(f"Avg_Wait_Time: {np.mean([r['avg_wait'] for r in all_rl]):.2f}")
    original_print(f"Bed_Utilization: {np.mean([r['bed_util'] for r in all_rl]):.2f}")
    original_print(f"Failure_Rate: {np.mean([r['failure_rate'] for r in all_rl]):.4f}")
    original_print("==============================")

if __name__ == "__main__":
    run_all()
