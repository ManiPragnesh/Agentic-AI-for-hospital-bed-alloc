import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
import os
import sys

# Path Hack
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from backend.src.rl.gym_env import HospitalGymEnv

def train():
    # Create Environment
    env = HospitalGymEnv()
    
    # Initialize PPO Agent
    model = PPO("MlpPolicy", env, verbose=1, learning_rate=0.0003)
    
    print("🚀 Starting PPO Training...")
    
    # Train
    # 12,000 steps roughly corresponds to 1000 days of arrivals at 0.5 rate
    model.learn(total_timesteps=12000)
    
    print("✅ Training Complete.")
    
    # Save Model
    os.makedirs("backend/src/rl/models", exist_ok=True)
    model.save("backend/src/rl/models/ppo_hospital_v1")
    print("💾 Model Saved to backend/src/rl/models/ppo_hospital_v1.zip")

if __name__ == "__main__":
    train()
