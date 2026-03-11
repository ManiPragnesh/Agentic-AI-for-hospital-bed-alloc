import simpy
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from stable_baselines3 import PPO

# Import simulation
import sys
sys.path.append(os.getcwd())
from backend.simulation.env import HospitalSim
from backend.simulation.patient import patient_generator

def run_simulation(mode='RULE', duration=200):
    env = simpy.Environment()
    # Standard Config
    hospital = HospitalSim(env, beds=50, icu_beds=10, staff=20)
    
    # Configure Agent
    hospital.admission_agent.mode = mode
    
    if mode == 'RL':
        model_path = "ppo_hospital_admin.zip"
        if os.path.exists(model_path):
            model = PPO.load(model_path)
            
            # Mock RL steps (Since we aren't using the full Gym Step loop here, we hook into the event)
            # This is a bit tricky headless without Gym, so we'll use a process to answer RL requests
            def rl_responder(env, hosp, model):
                while True:
                    yield hosp.gym_needs_action
                    
                    # RL Decision
                    # Construct Observation (V2)
                    depts = hosp.departments
                    patient = getattr(hosp, 'current_patient', None)
                    
                    sev = patient.severity if patient else 3
                    p_type = 0
                    if patient:
                        if patient.care_type == 'Emergency': p_type = 1
                        elif patient.care_type == 'ICU': p_type = 2

                    obs = np.array([
                        len(depts['General'].queue),
                        len(depts['ICU'].queue),
                        len(depts['Emergency'].queue),
                        depts['General'].beds.capacity - depts['General'].beds.count,
                        depts['ICU'].beds.capacity - depts['ICU'].beds.count,
                        depts['Emergency'].beds.capacity - depts['Emergency'].beds.count,
                        sev,
                        p_type
                    ], dtype=np.float32)

                    action_idx, _ = model.predict(obs)
                    action = 'ADMIT' if action_idx == 0 else 'REDIRECT'
                    
                    hosp.last_action_from_gym = action
                    hosp.gym_needs_action = env.event()
                    hosp.receive_action.succeed()
                    hosp.receive_action = env.event()
            
            env.process(rl_responder(env, hospital, model))
            
        else:
            print("RL Model not found, skipping RL run.")
            return None
            
    # Start Generator
    env.process(patient_generator(env, hospital, arrival_rate=0.8)) # High Load to test diff
    
    # Run
    env.run(until=duration)
    
    return hospital.monitor.get_logs_df()

print("Running Rule-Based Simulation...")
df_rule = run_simulation('RULE')

print("Running RL-Based Simulation...")
df_rl = run_simulation('RL')

# Analysis
def analyze(df):
    if df is None or df.empty: return {}
    
    # Wait Times
    # Filter by event type
    arrivals = df[df['Event'] == 'ARRIVAL'].set_index('PatientID')['Time']
    bed_allocs = df[df['Event'] == 'BED_ALLOC'].set_index('PatientID')['Time']
    
    # Calculate wait times (only for those who got a bed)
    # We use inner join logic via index alignment
    wait_times = (bed_allocs - arrivals).dropna()
    avg_wait = wait_times.mean() if not wait_times.empty else 0
    
    # Throughput
    discharges = len(df[df['Event'] == 'DISCHARGE'])
    redirects = len(df[df['Event'] == 'REDIRECT'])
    
    return {'avg_wait': avg_wait, 'discharges': discharges, 'redirects': redirects}

stats_rule = analyze(df_rule)
stats_rl = analyze(df_rl)

print("\n--- Results (Duration: 200h) ---")
print(f"Rule-Based: Wait={stats_rule.get('avg_wait',0):.2f}h, Discharged={stats_rule.get('discharges',0)}, Redirects={stats_rule.get('redirects',0)}")
print(f"RL-Based:   Wait={stats_rl.get('avg_wait',0):.2f}h, Discharged={stats_rl.get('discharges',0)}, Redirects={stats_rl.get('redirects',0)}")

# Plotting
labels = ['Rule-Based', 'RL-Based']
waits = [stats_rule.get('avg_wait', 0), stats_rl.get('avg_wait', 0)]
discharged = [stats_rule.get('discharges', 0), stats_rl.get('discharges', 0)]

fig, ax = plt.subplots(1, 2, figsize=(12, 5))

# Wait Time Comparison
ax[0].bar(labels, waits, color=['blue', 'green'])
ax[0].set_title('Average Waiting Time (Hours)')
ax[0].set_ylabel('Hours')

# Throughput Comparison
ax[1].bar(labels, discharged, color=['blue', 'green'])
ax[1].set_title('Total Patients Discharged')
ax[1].set_ylabel('Count')

plt.tight_layout()
plt.savefig('comparison_results.png')
print("Comparison plot saved to comparison_results.png")
