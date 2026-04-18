from stable_baselines3 import PPO
from backend.src.rl.gym_env import HospitalGymEnv
import os

def train():
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    env = HospitalGymEnv()
    
    # Check Env
    from stable_baselines3.common.env_checker import check_env
    # check_env(env) # Helper to verify Gym compliance
    
    model = PPO("MlpPolicy", env, verbose=1)
    
    print("Starting Training...")
    model.learn(total_timesteps=5000) # Short run for verification
    print("Training Complete.")
    
    model.save("ppo_hospital_admin")

if __name__ == "__main__":
    train()
