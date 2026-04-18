import simpy

class HospitalResources:
    """Wrapper for SimPy resources representing hospital capacity"""
    
    def __init__(self, env: simpy.Environment, config):
        self.env = env
        
        # Beds
        self.general_ward = simpy.Resource(env, capacity=config.GENERAL_BEDS)
        self.icu_ward = simpy.Resource(env, capacity=config.ICU_BEDS)
        self.surgery_ward = simpy.Resource(env, capacity=config.SURGERY_BEDS)
        
        # Staffing (can be dynamically altered)
        self.staff_available = config.BASE_STAFF
        self.base_staff = config.BASE_STAFF
        
    def add_staff(self, amount: int):
        self.staff_available += amount
        
    def reset_staff(self):
        self.staff_available = self.base_staff
        
    @property
    def total_beds(self):
        return self.general_ward.capacity + self.icu_ward.capacity + self.surgery_ward.capacity
        
    @property
    def occupied_beds(self):
        return self.general_ward.count + self.icu_ward.count + self.surgery_ward.count
        
    @property
    def utilization_rate(self):
        if self.total_beds == 0: return 0.0
        return self.occupied_beds / float(self.total_beds)
        
    def get_ward(self, name: str) -> simpy.Resource:
        if name == "GENERAL":
            return self.general_ward
        elif name == "ICU":
            return self.icu_ward
        elif name == "EMERGENCY":
            return self.surgery_ward
        raise ValueError(f"Unknown ward: {name}")
