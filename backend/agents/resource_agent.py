class ResourceAgent:
    def __init__(self, env):
        self.env = env

    def select_patient(self, queue, hospital_state):
        """
        Scans the waiting queue and selects the best patient for admission.
        Args:
            queue: List of Patient objects waiting.
            hospital_state: Dict with current bed counts.
        Returns:
            (Patient, bed_type) or (None, None)
        """
        if not queue:
            return None, None
            
        # 1. Filter candidates based on bed availability
        icu_free = hospital_state['icu_beds_free'] > 0
        gen_free = hospital_state['general_beds_free'] > 0
        
        candidates = []
        for p in queue:
            if p.care_type == 'ICU' and icu_free:
                candidates.append((p, 'ICU'))
            elif p.care_type == 'ICU' and not icu_free:
                # Optional: Critical logic (overflow to Gen?) - Phase 2: strict no
                pass
            elif p.care_type != 'ICU' and gen_free:
                candidates.append((p, 'GENERAL'))
        
        if not candidates:
            return None, None
            
        # 2. Sort candidates by Priority (Severity Descending, then Arrival Time Ascending)
        # Severity: 5 is Critical, 1 is Low.
        # We want higher severity first.
        candidates.sort(key=lambda x: (-x[0].severity, x[0].arrival_time))
        
        best_patient, bed_type = candidates[0]
        return best_patient, bed_type
