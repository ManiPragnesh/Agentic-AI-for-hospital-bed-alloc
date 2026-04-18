class StaffAgent:
    def __init__(self, env, max_ratio=4):
        """
        Args:
            env: SimPy environment
            max_ratio: Max patients per nurse (e.g. 4)
        """
        self.env = env
        self.max_ratio = max_ratio
        
    def get_shift_modifier(self):
        """
        Returns % of total staff available based on time of day.
        Day Shift (7am - 7pm): 100%
        Night Shift (7pm - 7am): 60%
        """
        # Simpy time is in hours? Assuming starts at 0 (Midnight? or 8am?)
        # Let's assume t=0 is 8:00 AM for simplicity.
        # Hour of day = (8 + self.env.now) % 24
        hour_of_day = (8 + self.env.now) % 24
        
        if 7 <= hour_of_day < 19:
            return 1.0 # Day Shift
        else:
            return 0.6 # Night Shift (Reduced Staff)
            
    def is_safe(self, current_patients, total_staff):
        """
        Checks if adding a patient maintains safe ratios.
        Returns: Boolean (True = Safe, False = Unsafe)
        """
        # Avoid division by zero
        if total_staff == 0:
            return False
            
        current_ratio = current_patients / total_staff
        
        if current_ratio >= self.max_ratio:
            return False
        return True
    
    def get_status(self, current_patients, total_staff):
        ratio = current_patients / total_staff if total_staff > 0 else float('inf')
        return {
            'ratio': ratio,
            'is_safe': ratio < self.max_ratio,
            'strain_level': ratio / self.max_ratio # 0.0 to 1.0+
        }
