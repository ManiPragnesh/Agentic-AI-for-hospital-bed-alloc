class DischargeAgent:
    def __init__(self, env):
        self.env = env
    
    def check_discharge(self, patient):
        """
        Checks if patient is ready for discharge.
        Returns: True/False
        """
        # Rule: Discharge if stay >= expected_los
        time_spent = self.env.now - patient.admission_time
        if time_spent >= patient.expected_los:
            return True
        return False
