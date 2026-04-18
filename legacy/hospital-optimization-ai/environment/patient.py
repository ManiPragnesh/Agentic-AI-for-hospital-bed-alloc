import dataclasses
from enum import Enum

class CareType(Enum):
    GENERAL = "GENERAL"
    ICU = "ICU"
    EMERGENCY = "EMERGENCY" # Represents immediate high-priority triage/surgery
    
@dataclasses.dataclass
class Patient:
    id: str
    arrival_time: float
    severity: int # 1 (Lowest) to 5 (Critical)
    care_type: CareType
    expected_stay_duration: float
    wait_start_time: float = 0.0
    admitted_time: float = -1.0
    discharged_time: float = -1.0
    
    @property
    def is_admitted(self) -> bool:
        return self.admitted_time >= 0

    def wait_duration(self, current_time: float = None) -> float:
        if current_time is None:
            return 0.0
        if self.is_admitted:
            return self.admitted_time - self.arrival_time
        return current_time - self.arrival_time
