import simpy
import random
import numpy as np

class Patient:
    def __init__(self, p_id, env, monitor=None, severity=None, care_type=None):
        self.id = p_id
        self.env = env
        self.monitor = monitor
        self.arrival_time = env.now
        
        # Patient Attributes
        self.severity = severity if severity is not None else random.randint(1, 5)
        self.criticality = self.severity / 5.0 # 0.0-1.0 (Dynamic score)
        self.care_type = care_type if care_type else self._determine_care_type()
        self.expected_los = self._determine_los()
        self.tolerance = self._determine_tolerance()
        
        # State tracking
        self.admission_time = None
        self.discharge_time = None
        self.assigned_bed = None
        self.history = [] # Audit log

    def log_event(self, time, event, message):
        # Local History
        self.history.append({
            'time': time,
            'event': event,
            'message': message,
            'criticality': self.criticality
        })
        # Centralized Log
        if self.monitor:
             self.monitor.log_event(time, event, message, {'patient_id': self.id, 'criticality': self.criticality})
        
    def update_condition(self, delta_time):
        """
        Simulates condition change over time.
        """
        if self.assigned_bed == 'ICU':
            # ICU stabilizes patients
            change = random.uniform(-0.05, 0.01)
        else:
            # General ward / Queue: Condition might worsen
            change = random.uniform(-0.02, 0.05)
            
        self.criticality = max(0.0, min(1.0, self.criticality + change))

    def _determine_care_type(self):
        # 10% ICU, 20% Emergency, 70% General
        r = random.random()
        if r < 0.1: return 'ICU'
        elif r < 0.3: return 'Emergency'
        else: return 'General'

    def _determine_los(self):
        # Length of Stay based on severity
        base = 24  # hours
        return base * self.severity * random.uniform(0.8, 1.2)

    def _determine_tolerance(self):
        # How long they wait before leaving (reneging)
        # Higher severity = Lower tolerance for waiting
        return 10 / self.severity  # hours

def patient_generator(env, hospital, arrival_rate):
    p_id = 0
    print(f"DEBUG: Patient Generator Started with rate={arrival_rate}")
    while True:
        # Check for Surge Multiplier in Hospital State
        # heuristic: defaults to 1.0 if not present
        multiplier = getattr(hospital, 'surge_multiplier', 1.0)
        
        effective_rate = arrival_rate * multiplier
        
        # Inter-arrival time (exponential distribution)
        # Higher rate = Lower IAT
        if effective_rate <= 0:
             yield env.timeout(1)
             continue
             
        iat = random.expovariate(effective_rate)
        # print(f"DEBUG: Next patient in {iat:.2f} hours")
        yield env.timeout(iat)
        
        p_id += 1
        monitor = getattr(hospital, 'monitor', None)
        patient = Patient(p_id, env, monitor=monitor)
        
        print(f"DEBUG: P-{p_id} Generated at {env.now:.2f}")
        
        # Handover to Hospital Logic
        env.process(hospital.handle_patient(patient))
