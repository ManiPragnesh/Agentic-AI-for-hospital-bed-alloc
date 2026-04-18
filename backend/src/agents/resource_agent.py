class ResourceAgent:
    def __init__(self, env):
        self.env = env

    def allocate_bed(self, dept):
        """
        Scans a department's waiting queue and selects the best patient for admission based on priority.
        If priority is equal (or roughly equal), older arrival times get preference.
        
        Args:
            dept: Department object containing the queue.
        Returns:
            Patient object or None
        """
        if not dept.queue:
            return None
            
        # Optional: In the future, we might only check top N candidates to simulate limited triage capability
        # For now, we perfectly sort all patients in the queue
        
        # Sort candidates by Priority (Criticality Descending, then Wait Time Ascending)
        # We use a tuple: (-criticality, arrival_time) 
        # so larger criticality and earlier arrival is prioritized.
        candidates = list(dept.queue)
        candidates.sort(key=lambda p: (-p.criticality, p.arrival_time))
        
        best_patient = candidates[0]
        return best_patient
