from stable_baselines3.common.callbacks import EvalCallback
from environment.hospital_env import HospitalGymEnv
from simulation.simulator import Simulator
from agents.rl_agent import HospitalAdminAgent
import config.settings as cfg

def train_agent():
    """Initializes environment, simulator, and runs PPO training."""
    # 1. Setup Eval Environment
    eval_env = HospitalGymEnv(cfg)
    eval_sim = Simulator(cfg, eval_env, baseline_mode=False)
    
    # Needs to reset per episode
    # Stable-baselines handles reset() calls, so we wrap the constructor logic
    
    class WrappedEnv(HospitalGymEnv):
        def reset(self, seed=None, options=None):
            # Pure RL: Rebuild simulator per episode
            sim = Simulator(cfg, self, baseline_mode=False)
            self.set_simulator(sim)
            return super().reset(seed=seed, options=options)

    train_env = WrappedEnv(cfg)
    eval_env_wrapped = WrappedEnv(cfg)
    
    # 2. Callbacks for saving best model during training
    eval_callback = EvalCallback(
        eval_env_wrapped, 
        best_model_save_path='./results/logs/',
        log_path='./results/logs/', 
        eval_freq=1000,
        deterministic=True, 
        render=False
    )
    
    # 3. Setup Agent
    agent = HospitalAdminAgent(train_env)
    agent.build_model()
    
    # 4. Train
    print("Starting PPO Training...")
    agent.model.learn(total_timesteps=cfg.TOTAL_TIMESTEPS, callback=eval_callback)
    
    # 5. Save Final Option
    agent.save("results/ppo_hospital_admin_final")
    print("Training complete. Model saved.")

if __name__ == "__main__":
    train_agent()
