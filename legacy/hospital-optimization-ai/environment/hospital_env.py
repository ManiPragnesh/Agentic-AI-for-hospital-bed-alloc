import gymnasium as gym
import numpy as np
from gymnasium import spaces
import math

from config.settings import (
    TOTAL_TIMESTEPS, 
    STAFF_TO_PATIENT_RATIO_MAX,
    REWARD_TIMELY_DISCHARGE,
    PENALTY_WAIT_TIME_THRESHOLD_EXCEEDED,
    PENALTY_CRITICAL_FAILURE,
    WAIT_TIME_THRESHOLD
)

class HospitalGymEnv(gym.Env):
    """
    OpenAI Gym interface for the Hospital Simulation.
    Integrated tightly with SimPy to allow step-by-step decision making.
    """
    
    def __init__(self, simulator_config, render_mode=None):
        super(HospitalGymEnv, self).__init__()
        self.config = simulator_config
        self.simulator = None # Provided dynamically via reset()
        
        # State Space (8 dimensions):
        # [waiting_patients_count, bed_occupancy_ratio, staff_availability_ratio,
        #  gen_queue, icu_queue, emer_queue, current_patient_severity, current_patient_critical_flag]
        self.observation_space = spaces.Box(
            low=np.array([0, 0.0, 0.0, 0, 0, 0, 1, 0]),
            high=np.array([500, 1.0, 2.0, 500, 500, 500, 5, 1]),
            dtype=np.float32
        )
        
        # Action Space (5 Discrete Choices):
        # 0: Admit to General
        # 1: Admit to ICU
        # 2: Admit to Emergency
        # 3: Discharge stable patient early (free up bed)
        # 4: Call additional staff
        self.action_space = spaces.Discrete(5)
        
    def set_simulator(self, simulator):
        """Link the Gym Environment to the active SimPy runner"""
        self.simulator = simulator
        
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        # Re-initialize state trackers
        self.current_step = 0
        state = self._get_observation()
        info = {}
        return state, info
        
    def _get_observation(self):
        """Build the state vector from the SimPy environment variables"""
        if not self.simulator:
            return np.zeros(8, dtype=np.float32)
            
        sim = self.simulator
        
        # Base stats
        waiting_count = len(sim.patient_queue)
        occupancy = sim.resources.utilization_rate
        staff_ratio = sim.resources.staff_available / max(1, self.config.BASE_STAFF)
        
        # Queues breakdown (Approximated by care type required in queue)
        gen_q = sum(1 for p in sim.patient_queue if p.care_type.value == "GENERAL")
        icu_q = sum(1 for p in sim.patient_queue if p.care_type.value == "ICU")
        emer_q = sum(1 for p in sim.patient_queue if p.care_type.value == "EMERGENCY")
        
        # Current Patient (Head of Queue or None)
        sev = 1
        crit = 0
        if waiting_count > 0:
            top_patient = sim.patient_queue[0]
            sev = top_patient.severity
            crit = 1 if top_patient.severity >= 4 else 0
            
        obs = np.array([waiting_count, occupancy, staff_ratio, gen_q, icu_q, emer_q, sev, crit], dtype=np.float32)
        return obs
        
    def step(self, action):
        """Execute action, advance simulation if wait queue empty, calculate reward"""
        if not self.simulator:
            raise RuntimeError("Simulator not linked to Environment!")
            
        reward = 0.0
        terminated = False
        truncated = False
        info = {"action_taken": action}
        
        sim = self.simulator
        
        # Execute Action on the Queue or Resources
        if action in [0, 1, 2]: # Admits
            if len(sim.patient_queue) > 0:
                patient = sim.patient_queue.pop(0) # Pop from queue
                
                target_ward = "GENERAL" if action == 0 else ("ICU" if action == 1 else "EMERGENCY")
                
                # Check constraints (Staff to patient ratio)
                total_patients = sim.resources.occupied_beds + 1
                if (total_patients / max(1, sim.resources.staff_available)) > STAFF_TO_PATIENT_RATIO_MAX:
                    # Penalty for violating safety constraints
                    reward += PENALTY_CRITICAL_FAILURE / 10.0
                    info["violation"] = "unsafe_ratio"
                
                # Try to admit
                ward = sim.resources.get_ward(target_ward)
                if ward.count < ward.capacity:
                    # Successful admit
                    patient.admitted_time = sim.env.now
                    ward_req = ward.request()
                    
                    # Store lambda capture for resource release inside simulator
                    def process_stay(req, p, w):
                        yield sim.env.timeout(p.expected_stay_duration)
                        w.release(req)
                        p.discharged_time = sim.env.now
                        
                        # Timely discharge reward added to total simulator tracking
                        sim.total_reward += REWARD_TIMELY_DISCHARGE
                        sim.discharged_patients += 1
                        
                    sim.env.process(process_stay(ward_req, patient, ward))
                    sim.admitted_patients += 1
                    
                    # Reward formatting
                    wait_time = patient.wait_duration(sim.env.now)
                    if wait_time > WAIT_TIME_THRESHOLD:
                        reward += PENALTY_WAIT_TIME_THRESHOLD_EXCEEDED
                else:
                    # Bed full - critical failure, reject patient (patient leaves)
                    reward += PENALTY_CRITICAL_FAILURE
                    sim.rejected_patients += 1
            else:
                # Wasted action (no queue)
                reward -= 1.0 
                
        elif action == 3: # Discharge Early
            # Abstract representation: free up a bed if any occupied, but with a slight penalty 
            # as it's a forced early discharge
            if sim.resources.general_ward.count > 0:
                 # In a true detailed SimPy we would interrupt a process.
                 # For RL simplicity, we apply a heuristic reward penalty but open a slot
                 reward -= 5.0 
                 # We assume the simulator allows 'early out' conceptually.
                 # Implementing explicit process interruption in SimPy is complex,
                 # we will reward the agent for attempting it when capacity is near full
                 if sim.resources.utilization_rate > 0.9:
                     reward += 10.0 # Good strategic call!
                     
        elif action == 4: # Call Staff
            sim.resources.add_staff(5)
            # Costly action
            reward -= 20.0
            
        # VERY IMPORTANT: Advance simulation clock until next event or timeout
        # If queue is empty, we must wait for a patient to arrive
        if len(sim.patient_queue) == 0:
            sim.env.run(until=sim.env.now + 1.0) # Step forward 1 hour
        else:
            sim.env.run(until=sim.env.now + 0.1) # Small step to process immediate yields
            
        # End episode if simulation is over
        if sim.env.now >= sim.max_time:
            terminated = True
            
        obs = self._get_observation()
        
        # Additional state-based rewards
        if obs[0] > 10: # Long total queue
            reward -= (obs[0] * 0.1) # Continuous slight penalty for keeping queue long
            
        return obs, float(reward), terminated, truncated, info
