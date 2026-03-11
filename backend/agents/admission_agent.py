class AdmissionAgent:
    def __init__(self, env):
        self.env = env
        self.mode = 'RULE' # or 'RL'
        self.decision_event = None
        self.last_action = None # To store action from RL
        
    def decide(self, patient, hospital_state, staff_agent=None):
        """
        Rule-based decision (used when mode != RL)
        Returns: 'ADMIT', 'QUEUE', or 'REDIRECT'
        """
        # 0. Safety Check (Staff Ratio)
        if staff_agent:
            # Check if adding one more patient is safe
            current_p = hospital_state.get('current_patients', 0)
            total_s = hospital_state.get('total_staff', 1)
            # We check if CURRENT state is safe. If already unsafe, definitely don't admit.
            if not staff_agent.is_safe(current_p, total_s):
                return 'QUEUE' # Or REDIRECT? Queue keeps them waiting until staff frees up.
        
        # Logic: Check capacity -> If full, check severity.
        # If Severity > Threshold (e.g. 4) and Bed available -> Admit.
        # If Full -> Add to Queue.
        
        # Simple Logic Phase 2:
        if patient.care_type == 'ICU':
            if hospital_state['icu_beds_free'] > 0:
                return 'ADMIT'
            # If ICU full, but patient is critical (Severity > 4), maybe divert? 
            # Or just Queue?
            return 'QUEUE'
            
        else: # General or Emergency
            if hospital_state['general_beds_free'] > 0:
                return 'ADMIT'
            return 'QUEUE'
