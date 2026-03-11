import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
import os
import sys

# Path Hack
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from backend.rl.gym_env import HospitalGymEnv

def train():
    # Create Environment
    env = HospitalGymEnv()
    
    # Initialize PPO Agent
    model = PPO("MlpPolicy", env, verbose=1, learning_rate=0.0003)
    
    print("🚀 Starting PPO Training...")
    
    # Train
    model.learn(total_timesteps=10000)
    
    print("✅ Training Complete.")
    
    # Save Model
    os.makedirs("backend/rl/models", exist_ok=True)
    model.save("backend/rl/models/ppo_hospital_v1")
    print("💾 Model Saved to backend/rl/models/ppo_hospital_v1.zip")

if __name__ == "__main__":
    train()
