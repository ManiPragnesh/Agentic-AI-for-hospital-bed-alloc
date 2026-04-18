# Configuration and Constants for Hospital Simulation

# Simulation Timing
SIMULATION_DAYS = 30
SIMULATION_HOURS = SIMULATION_DAYS * 24
EVALUATION_DAYS = 30

# Arrival Rates (Poisson lambda - patients per hour)
BASE_ARRIVAL_RATE = 0.5

# Ward Capacities
GENERAL_BEDS = 50
ICU_BEDS = 10
SURGERY_BEDS = 5

# Staffing
BASE_STAFF = 20
STAFF_TO_PATIENT_RATIO_MAX = 4.0 # Maximum safe ratio

# Durations (in hours)
STAY_DURATION_MEAN_GENERAL = 24.0
STAY_DURATION_MEAN_ICU = 72.0
STAY_DURATION_MEAN_SURGERY = 12.0

# Rewards (Multi-objective)
REWARD_TIMELY_DISCHARGE = 1.0
PENALTY_WAIT_TIME_THRESHOLD_EXCEEDED = -10.0 # e.g. Wait > 4 hours
PENALTY_CRITICAL_FAILURE = -100.0 # e.g. Death/Risk/Rejected from ICU when needed

WAIT_TIME_THRESHOLD = 4.0 # hours

# Patient Distributions (Probabilities)
PROB_ICU_REQUIRED = 0.10
PROB_EMERGENCY_REQUIRED = 0.20
PROB_GENERAL_REQUIRED = 0.70 # Remaining

# RL Training
TOTAL_TIMESTEPS = 10000
