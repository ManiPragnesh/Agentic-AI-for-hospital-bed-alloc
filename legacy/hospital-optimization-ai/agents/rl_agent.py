import os
from stable_baselines3 import PPO

class HospitalAdminAgent:
    """Wrapper class to initialize, save, and load the Agentic RL Brain"""
    
    def __init__(self, env):
        self.env = env
        self.model = None
        
    def build_model(self):
        """Initialize PPO agent with optimized hyperparameters"""
        self.model = PPO(
            "MlpPolicy", 
            self.env, 
            verbose=1,
            learning_rate=3e-4,
            gamma=0.99,   # Long-horizon discount due to long simulation times
            ent_coef=0.01 # Encourage exploration of the discrete actions
        )
        return self.model
        
    def train(self, total_timesteps=10000):
        if not self.model:
            self.build_model()
        print(f"🧠 Training Agent for {total_timesteps} timesteps...")
        self.model.learn(total_timesteps=total_timesteps)
        
    def save(self, path="pp0_hospital_admin"):
        if self.model:
            self.model.save(path)
            
    def load(self, path="pp0_hospital_admin"):
        if os.path.exists(path + ".zip"):
            self.model = PPO.load(path, env=self.env)
        else:
            raise FileNotFoundError(f"Model {path}.zip not found.")
            
    def predict(self, observation):
        """Return action given current state"""
        if not self.model:
            raise RuntimeError("Model not trained or loaded.")
        action, _states = self.model.predict(observation, deterministic=True)
        return action
