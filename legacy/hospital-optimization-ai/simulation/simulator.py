import simpy
import random
import numpy as np
from uuid import uuid4

from config.settings import (
    BASE_ARRIVAL_RATE, 
    PROB_ICU_REQUIRED, 
    PROB_EMERGENCY_REQUIRED,
    STAY_DURATION_MEAN_GENERAL,
    STAY_DURATION_MEAN_ICU,
    STAY_DURATION_MEAN_SURGERY
)
from environment.patient import Patient, CareType
from environment.resources import HospitalResources

class Simulator:
    """
    SimPy Discrete Event Simulation manager.
    Can be run autonomously (Baseline FCFS) or driven by the RL Env step-by-step.
    """
    
    def __init__(self, config, env_wrapper, baseline_mode=False):
        self.config = config
        self.env = simpy.Environment()
        self.max_time = config.SIMULATION_HOURS
        
        self.resources = HospitalResources(self.env, config)
        self.rl_env = env_wrapper
        self.baseline_mode = baseline_mode
        
        self.patient_queue = []
        
        # Metrics
        self.generated_patients = 0
        self.admitted_patients = 0
        self.discharged_patients = 0
        self.rejected_patients = 0
        self.total_reward = 0.0
        
        # Bind back to wrapper
        if self.rl_env:
            self.rl_env.set_simulator(self)
        
        # Start processes
        self.env.process(self.patient_generator())
        
        if self.baseline_mode:
            self.env.process(self.fcfs_agent())
            
    def generate_patient(self) -> Patient:
        """Stochastic generation of a patient"""
        choice = random.random()
        if choice < PROB_ICU_REQUIRED:
            ct = CareType.ICU
            sev = random.randint(4, 5)
            stay = np.random.exponential(STAY_DURATION_MEAN_ICU)
        elif choice < PROB_ICU_REQUIRED + PROB_EMERGENCY_REQUIRED:
            ct = CareType.EMERGENCY
            sev = random.randint(3, 5)
            stay = np.random.exponential(STAY_DURATION_MEAN_SURGERY)
        else:
            ct = CareType.GENERAL
            sev = random.randint(1, 4)
            stay = np.random.exponential(STAY_DURATION_MEAN_GENERAL)
            
        self.generated_patients += 1
        return Patient(
            id=f"P_{uuid4().hex[:6]}",
            arrival_time=self.env.now,
            severity=sev,
            care_type=ct,
            expected_stay_duration=stay
        )
        
    def patient_generator(self):
        """Simulate arrivals over time"""
        while True:
            # Inter-arrival time exponential
            delay = random.expovariate(BASE_ARRIVAL_RATE)
            yield self.env.timeout(delay)
            
            p = self.generate_patient()
            self.patient_queue.append(p)
            
    def fcfs_agent(self):
        """Baseline Heuristic: Process queue strictly in order as beds open"""
        while True:
            yield self.env.timeout(0.5) # Check every 30 mins
            
            # Reset staff to default periodically in FCFS
            if self.env.now % 24 == 0:
                self.resources.reset_staff()
            
            if len(self.patient_queue) == 0:
                continue
                
            p = self.patient_queue[0]
            
            target = None
            if p.care_type == CareType.GENERAL and self.resources.general_ward.count < self.resources.general_ward.capacity:
                target = self.resources.general_ward
            elif p.care_type == CareType.ICU and self.resources.icu_ward.count < self.resources.icu_ward.capacity:
                target = self.resources.icu_ward
            elif p.care_type == CareType.EMERGENCY and self.resources.surgery_ward.count < self.resources.surgery_ward.capacity:
                target = self.resources.surgery_ward
                
            if target:
                self.patient_queue.pop(0)
                p.admitted_time = self.env.now
                self.admitted_patients += 1
                
                req = target.request()
                def stay_process(req, patient, ward):
                    yield self.env.timeout(patient.expected_stay_duration)
                    ward.release(req)
                    patient.discharged_time = self.env.now
                    self.discharged_patients += 1
                    
                self.env.process(stay_process(req, p, target))
                
    def run(self):
        """Run the simulation to completion (useful for baseline)"""
        self.env.run(until=self.max_time)
