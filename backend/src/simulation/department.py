import simpy
from collections import deque

class Department:
    def __init__(self, env, name, capacity, staff_count, acuity_threshold=0.0):
        """
        Args:
            env: SimPy environment
            name: Department Name (e.g., 'ICU', 'General')
            capacity: Number of beds
            staff_count: Assigned nurses/doctors
            acuity_threshold: Minimum criticality to be here (0.0 - 1.0)
        """
        self.env = env
        self.name = name
        self.capacity = capacity
        self.beds = simpy.Resource(env, capacity=capacity)
        self.staff_count = staff_count
        self.acuity_threshold = acuity_threshold
        
        self.queue = deque() # Waiting buffer for this specific department
        self.patients = []   # Currently treated patients
        
    def add_to_queue(self, patient, high_priority=False):
        if high_priority:
            self.queue.appendleft(patient)
            patient.log_event(self.env.now, 'QUEUED_URGENT', f"Joined {self.name} queue (Front)")
        else:
            self.queue.append(patient)
            patient.log_event(self.env.now, 'QUEUED', f"Joined {self.name} queue")

    def admit_patient(self, patient):
        """
        Moves patient from Queue -> Bed
        """
        if patient in self.queue:
            self.queue.remove(patient)
            
        wait_time = self.env.now - patient.arrival_time
        self.patients.append(patient)
        patient.log_event(self.env.now, 'ADMIT', f"Admitted to {self.name}", {'wait_time': wait_time})
        
    def discharge_patient(self, patient):
        if patient in self.patients:
            self.patients.remove(patient)
            patient.log_event(self.env.now, 'DISCHARGED', f"Left {self.name}")
            
    def get_occupancy(self):
        return self.beds.count
        
    def get_queue_length(self):
        return len(self.queue)
        
    def is_full(self):
        return self.beds.count >= self.beds.capacity
    
    def get_staff_ratio(self):
        if self.staff_count == 0: return float('inf')
        return len(self.patients) / self.staff_count

    def bump_patient(self):
        """
        Emergency Override: Remove the most stable patient to free a bed.
        Returns: bumped_patient or None
        """
        if not self.patients:
            return None
            
        # Find lowest criticality
        # Note: Patient object now has 'criticality' attribute from recent update
        # We assume self.patients contains Patient objects
        self.patients.sort(key=lambda p: p.criticality)
        most_stable = self.patients[0]
        
        # Logic: Only bump if they are relatively stable (< 0.5)?
        # For now, ruthless override: Just bump the best one.
        
        # We need to signal them to leave?
        # In SimPy, we interrupting their process_stay is hard unless we stored the process.
        # But our Departments track 'patients' list separately from the SimPy resource 'beds'.
        # The 'process_stay' holds the 'req' context manager.
        # This is tricky in SimPy without interrupting the specific process.
        
        # Workaround: We can't forcefully release the SimPy resource 'req' easily from outside.
        # We will simulate the bump by artificially increasing capacity momentarily or 
        # just returning the patient and handling the 'bed' release in logic?
        
        # Simplified V2 approach:
        # Just return the patient, and we log it. The simulation might show occupancy > capacity if we force add.
        # But 'add_to_queue' waits for bed.
        
        # Correct SimPy approach: Interrupt the process!
        # But we don't store the process handle on the patient.
        # Let's add that to patient.py? Or just skip hard bumping for this iteration and use "Overcrowding" (+1 capacity).
        
        return most_stable
