import simpy
from backend.simulation.patient import patient_generator
from backend.simulation.monitor import Monitor
from backend.agents.admission_agent import AdmissionAgent
from backend.agents.resource_agent import ResourceAgent
from backend.agents.discharge_agent import DischargeAgent

from backend.agents.staff_agent import StaffAgent

from backend.agents.staff_agent import StaffAgent
from backend.simulation.department import Department

class HospitalSim:
    def __init__(self, env, beds=50, icu_beds=10, staff=20):
        self.env = env
        self.total_staff = staff
        
        # V2: Department-Based Structure
        # We divide total staff among depts (Simple heuristic for now: 20% ICU, 30% ER, 50% General)
        self.departments = {
            'Emergency': Department(env, 'Emergency', capacity=10, staff_count=int(staff*0.3), acuity_threshold=0.0),
            'ICU':       Department(env, 'ICU',       capacity=icu_beds, staff_count=int(staff*0.2), acuity_threshold=0.8),
            'General':   Department(env, 'General',   capacity=beds,     staff_count=int(staff*0.5), acuity_threshold=0.2),
        }
        
        # Legacy Resource Mapping (for compatibility with existing Agents/Tests)
        # We proxy these to the Department resources
        self.sem_general_beds = self.departments['General'].beds
        self.sem_icu_beds = self.departments['ICU'].beds
        
        # State tracking for Agents (Agent Knowledge)
        self.state = {
            'general_beds_free': beds,
            'icu_beds_free': icu_beds,
            'total_staff': staff,
            'current_patients': 0 # New: Track active patients for ratio
        }

        # Waiting Queue (Global Entry Queue - Triage Area)
        self.waiting_queue = []
        
        # Triggers
        self.trigger_allocation = env.event()
        
        # RL Synchronization Triggers
        self.gym_needs_action = env.event() 
        self.receive_action = env.event()   
        self.last_action_from_gym = None
        
        # Agents
        self.admission_agent = AdmissionAgent(env)
        self.resource_agent = ResourceAgent(env)
        self.discharge_agent = DischargeAgent(env)
        self.staff_agent = StaffAgent(env, max_ratio=4) # New Agent
        
        # Monitor
        self.monitor = Monitor(self) # Pass self for state access
        
        # Scenario State
        self.surge_multiplier = 1.0
        
        # Start Allocation Process
        # Start Allocation Processes (One per Department)
        for name in self.departments:
            self.env.process(self.department_allocation_loop(name))
            
        # Start Triage Logic
        self.env.process(self.triage_control_loop())
        
        # Start Shift Rotation Logic
        self.env.process(self.shift_rotation_loop())
        
        # Start Monitoring Logic (New)
        self.env.process(self.monitoring_loop())
        
    def monitoring_loop(self):
        """
        Ticks the monitor every simulation unit (1 hour? or 1 minute?).
        Arrival rate is per hour. Let's tick every 0.5 hours for resolution.
        """
        try:
            while True:
                self.monitor.tick(self.env.now)
                yield self.env.timeout(0.5)
        except Exception as e:
            import traceback
            with open("backend/logs/monitor_error.log", "w") as f:
                f.write(traceback.format_exc())
            print(f"❌ Monitoring Loop Crahed: {e}")

    def shift_rotation_loop(self):
        """
        Updates staff counts based on shift changes (Day/Night).
        """
        while True:
            # Calculate Shift Strength
            modifier = self.staff_agent.get_shift_modifier()
            
            # Apply to Departments
            # Base distribution: ICU(20%), ER(30%), General(50%)
            # We recalculate based on Total Staff * Modifier
            current_active_staff = int(self.total_staff * modifier)
            
            self.departments['Emergency'].staff_count = max(1, int(current_active_staff * 0.3))
            self.departments['ICU'].staff_count       = max(1, int(current_active_staff * 0.2))
            self.departments['General'].staff_count   = max(1, int(current_active_staff * 0.5))
            
            # Update Global State
            self.state['total_staff'] = current_active_staff
            
            # Log Shift Change
            if self.env.now > 0: # Skip initial log if preferred, or log it
                 shift_name = "Day" if modifier == 1.0 else "Night"
                 self.monitor.log_event(self.env.now, 'SHIFT_CHANGE', f"{shift_name} Shift Started (Active Staff: {current_active_staff})")
            
            # Wait for next check (e.g., every hour to catch the transition)
            yield self.env.timeout(1)
        
    def triage_control_loop(self):
        """
        Periodically re-evaluates waiting patients.
        Escalates priority if condition worsens.
        """
        while True:
            yield self.env.timeout(0.5) # Every 30 mins
            
            # Check General Queue for deterioration
            gen_dept = self.departments['General']
            escalated_patients = []
            
            for patient in list(gen_dept.queue):
                # Update condition artificially for simulation
                patient.update_condition(0.5)
                
                # Logic: If Criticality > 0.8 (High) -> Move to ICU
                if patient.criticality > 0.8:
                    escalated_patients.append(patient)
            
            # Execute Moves (Escalation)
            for p in escalated_patients:
                self.monitor.log_event(self.env.now, 'TRIAGE_ESCALATE', f"Patient {p.id} escalated to ICU (Crit {p.criticality:.2f})", {'patient_id': p.id})
                gen_dept.queue.remove(p)
                self.departments['ICU'].add_to_queue(p)
                p.care_type = 'ICU' # Update record
        
    def trigger_scenario(self, name):
        """
        Triggers a predefined scenario.
        """
        if name == 'mass_casualty':
            self.env.process(self._scenario_process(5.0, 4)) # 5x patients for 4 hours
        elif name == 'bus_accident':
            self.env.process(self._scenario_process(10.0, 1)) # 10x patients for 1 hour
            
    def _scenario_process(self, multiplier, duration):
        self.monitor.log_event(self.env.now, 'SCENARIO_START', f"Surge x{multiplier} started")
        self.surge_multiplier = multiplier
        yield self.env.timeout(duration)
        self.surge_multiplier = 1.0
        self.monitor.log_event(self.env.now, 'SCENARIO_END', "Surge ended")

    def handle_patient(self, patient):
        """
        Process patient arrival, admission decision, and queuing.
        """
        self.monitor.log_event(self.env.now, 'ARRIVAL', f"Patient {patient.id} arrived (Severity {patient.severity}, Type {patient.care_type})", {'patient_id': patient.id})
        
        # 1. Determine Target Department
        if patient.care_type == 'ICU':
            target_dept = 'ICU'
        elif patient.care_type == 'Emergency':
            target_dept = 'Emergency' 
        else:
            target_dept = 'General'

        # 2. Admission Decision
        while True: # Loop for management actions
            if self.admission_agent.mode == 'RL':
                self.current_patient = patient # Expose for Gym Obs
                self.gym_needs_action.succeed() 
                self.gym_needs_action = self.env.event() 
                yield self.receive_action
                decision = self.last_action_from_gym
                self.current_patient = None # Cleanup
            else:
                 decision = self.admission_agent.decide(patient, self.state, self.staff_agent)
            
            # Handle Management Actions
            if decision == 'DISCHARGE':
                # Force discharge of most stable patient in General Ward
                gen_dept = self.departments['General']
                if len(gen_dept.patients) > 0:
                    # Sort by criticality ascending (lowest first)
                    gen_dept.patients.sort(key=lambda x: x.criticality)
                    stable_p = gen_dept.patients[0]
                    self.monitor.log_event(self.env.now, 'FORCE_DISCHARGE', f"Agent forced discharge of P-{stable_p.id} to free space")
                    # We can't easily 'kill' a process in SimPy, but we can set a flag
                    stable_p.discharge_time = self.env.now 
                    # The process_stay will handle it in its next tick or we can just remove them
                continue # Decision loop again for the current patient
                
            elif decision == 'CALL_STAFF':
                self.monitor.log_event(self.env.now, 'CALL_STAFF', "Agent called extra staff (+5)")
                self.total_staff += 5
                self.state['total_staff'] = self.total_staff
                continue # Decision loop again for the current patient
            
            break # Exit loop for ADMIT or TRANSFER

        if decision.startswith('ADMIT'):
            # Parse Target from Decision (e.g., "ADMIT_ICU") or fallback to default
            if '_' in decision:
                target_dept = decision.split('_')[1].capitalize() # "ADMIT_ICU" -> "ICU"
            
            # Emergency Override Check
            is_critical = patient.criticality > 0.9
            
            # Add to specific Department Queue
            if target_dept in self.departments:
                dept = self.departments[target_dept]
                dept.add_to_queue(patient, high_priority=is_critical)
                
                if is_critical:
                     self.monitor.log_event(self.env.now, 'OVERRIDE_TRIGGER', f"Critical Patient {patient.id} jumped queue", {'patient_id': patient.id})
                     self.monitor.record_transaction(target_dept, cost=200, type='penalty') # Cost of override chaos
                
                # Legacy: Keep in global queue for stats/dashboard for now
                self.waiting_queue.append(patient)
            else:
                 # Fallback if invalid dept
                 self.monitor.log_event(self.env.now, 'ERROR', f"Invalid Target Dept {target_dept}", {'patient_id': patient.id})

        else:
            self.monitor.log_event(self.env.now, 'REDIRECT', f"Patient {patient.id} redirected/transferred", {'patient_id': patient.id})

    def department_allocation_loop(self, dept_name):
        """
        Process queue for a specific department.
        """
        dept = self.departments[dept_name]
        while True:
            # Check if anyone is waiting AND we have beds
            if len(dept.queue) > 0 and not dept.is_full():
                # FIFO for now (or Priority sort)
                patient = dept.queue[0] # Peek
                
                # Check Staffing Ratio for this Dept
                if dept.get_staff_ratio() < 4.0: 
                    # Allocate
                    with dept.beds.request() as req:
                        yield req
                        
                        # Verify patient still there
                        if patient in dept.queue:
                            dept.admit_patient(patient) # Moves from queue to patients list
                            
                            # Update Legacy Global State (for dashboard compatibility)
                            if patient in self.waiting_queue:
                                self.waiting_queue.remove(patient)
                            self.state['current_patients'] += 1
                            if dept_name == 'ICU': self.state['icu_beds_free'] = self.departments['ICU'].beds.capacity - self.departments['ICU'].beds.count
                            elif dept_name == 'General': self.state['general_beds_free'] = self.departments['General'].beds.capacity - self.departments['General'].beds.count
                            
                            # Start Treatment
                            self.env.process(self.process_stay(patient, dept))
                else:
                    # Staff saturated
                    yield self.env.timeout(1)
            else:
                # Idle
                yield self.env.timeout(1)

    def process_stay(self, patient, dept):
        """
        Simulate treatment duration.
        """
        patient.admission_time = self.env.now
        
        # Treatment / Stay Loop
        while True:
            yield self.env.timeout(1) # Check every hour
            
            # Check for early discharge flag from RL Agent
            if patient.discharge_time is not None and self.env.now >= patient.discharge_time:
                self.monitor.log_event(self.env.now, 'EARLY_DISCHARGE', f"Patient {patient.id} discharged early by RL Agent", {'patient_id': patient.id})
                break
                
            if self.discharge_agent.check_discharge(patient):
                break
        
        # Discharge
        dept.discharge_patient(patient)
        self.monitor.log_event(self.env.now, 'DISCHARGE', f"Patient {patient.id} discharged from {dept.name}", {'patient_id': patient.id})
        
        # Release Legacy State
        self.state['current_patients'] -= 1
        if dept.name == 'ICU': self.state['icu_beds_free'] = self.departments['ICU'].beds.capacity - self.departments['ICU'].beds.count
        elif dept.name == 'General': self.state['general_beds_free'] = self.departments['General'].beds.capacity - self.departments['General'].beds.count

def run_simulation(duration=100):
    env = simpy.Environment()
    hospital = HospitalSim(env)
    
    # Start Patient Generator
    env.process(patient_generator(env, hospital, arrival_rate=0.5))
    
    env.run(until=duration)
    return hospital.monitor.get_logs_df()
