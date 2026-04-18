import gymnasium as gym
from gymnasium import spaces
import numpy as np
import simpy
from backend.src.simulation.env import HospitalSim
from backend.src.simulation.patient import patient_generator

class HospitalGymEnv(gym.Env):
    def __init__(self):
        super(HospitalGymEnv, self).__init__()
        
        # Define Action Space:
        # 0: ADMIT_GENERAL
        # 1: ADMIT_ICU
        # 2: ADMIT_EMERGENCY
        # 3: TRANSFER (Redirect)
        # 4: DISCHARGE (New: Force early discharge of stable patient)
        # 5: CALL_STAFF (New: Request extra shift)
        self.action_space = spaces.Discrete(6)
        
        # Define Observation Space:
        # [
        #   Total_Waiting, Bed_Occupancy_Rate, Staff_Availability,
        #   Gen_Queue, ICU_Queue, Emer_Queue,
        #   Pt_Severity, Pt_Criticality
        # ]
        self.observation_space = spaces.Box(low=0, high=9999, shape=(8,), dtype=np.float32)
        
        self.sim = None
        self.sim_env = None

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        # Init SimPy
        self.sim_env = simpy.Environment()
        self.sim = HospitalSim(self.sim_env)
        
        # Enable RL Mode for Admission
        self.sim.admission_agent.mode = 'RL'
        
        # Start Patient Gen
        self.sim_env.process(patient_generator(self.sim_env, self.sim, arrival_rate=0.5))
        
        # Run until first decision needed
        self.sim_env.run(until=self.sim.gym_needs_action)
        self.sim.gym_needs_action = self.sim_env.event() # Reset for next
        
        obs = self._get_obs()
        return obs, {}

    def step(self, action):
        # 1. Map Action
        action_map = {
            0: 'ADMIT_General',
            1: 'ADMIT_ICU',
            2: 'ADMIT_Emergency',
            3: 'TRANSFER',
            4: 'DISCHARGE',
            5: 'CALL_STAFF'
        }
        action_str = action_map.get(action, 'TRANSFER')
        
        # 2. Resign action to Sim
        self.sim.last_action_from_gym = action_str
        self.sim.receive_action.succeed() 
        self.sim.receive_action = self.sim_env.event() # Reset
        
        # 3. Run Sim until next decision or timeout
        try:
            # We must wait for either a new decision or the end of the simulation
            remaining = 168 - self.sim_env.now
            if remaining > 0:
                timeout = self.sim_env.timeout(remaining)
                self.sim_env.run(until=simpy.AnyOf(self.sim_env, [self.sim.gym_needs_action, timeout]))
                
            if self.sim.gym_needs_action.triggered:
                self.sim.gym_needs_action = self.sim_env.event()
                done = False
            else:
                done = True
        except Exception: 
            done = True
        
        if self.sim_env.now >= 168: 
             done = True
        
        # 4. Obs & Reward
        obs = self._get_obs()
        reward = self._calculate_reward(action_str)
        
        return obs, reward, done, False, {}

    def _get_obs(self):
        depts = self.sim.departments
        
        gen_q = len(depts['General'].queue)
        icu_q = len(depts['ICU'].queue)
        emer_q = len(depts['Emergency'].queue)
        total_waiting = gen_q + icu_q + emer_q
        
        # Bed Occupancy %
        total_beds = sum(d.beds.capacity for d in depts.values())
        occupied_beds = sum(d.beds.count for d in depts.values())
        occ_rate = occupied_beds / max(1, total_beds)
        
        # Staff Availability
        staff_avail = self.sim.state.get('total_staff', 0)
        
        # Current Patient Details
        patient = getattr(self.sim, 'current_patient', None)
        sev = patient.severity if patient else 0
        crit = patient.criticality if patient else 0
            
        return np.array([
            total_waiting, occ_rate, staff_avail,
            gen_q, icu_q, emer_q,
            sev, crit
        ], dtype=np.float32)

    def _calculate_reward(self, action_str):
        # Align with Project Methodology:
        # +$1 for timely discharge
        # -$10 for wait time > 4 hours
        # -$100 for patient death/risk
        
        reward = 0
        
        # 1. Check for recent discharges (Tracked in monitor)
        # We look at events since last check
        recent_events = self.sim.monitor.get_recent_events(count=10)
        for event in recent_events:
            if event['Event'] == 'DISCHARGE':
                reward += 1.0
            if 'DEATH' in event['Event'] or 'CRITICAL_FAIL' in event['Event']:
                reward -= 100.0
                
        # 2. Check current queues for wait time violations
        for dept in self.sim.departments.values():
            for p in dept.queue:
                wait_time = self.sim_env.now - p.arrival_time
                if wait_time > 4:
                    reward -= 10.0
                    
        # 3. Risk Penalty for full critical departments
        if self.sim.departments['ICU'].is_full() and action_str == 'ADMIT_ICU':
            reward -= 50.0 # High risk of refusal
            
        return reward
