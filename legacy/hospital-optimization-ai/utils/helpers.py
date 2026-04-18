import os
import matplotlib.pyplot as plt
import json

def plot_wait_time_comparison(fcfs_metrics, rl_metrics, save_path="results/graphs/wait_time_comparison.png"):
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    labels = ['Baseline (FCFS)', 'RL Agent (PPO)']
    values = [fcfs_metrics['avg_wait'], rl_metrics['avg_wait']]
    
    plt.figure(figsize=(8, 6))
    bars = plt.bar(labels, values, color=['#EF4444', '#3B82F6'])
    plt.ylabel('Average Wait Time (Hours)')
    plt.title('Patient Wait Time Comparison')
    
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 0.1, f'{yval:.1f}h', ha='center', va='bottom')
        
    plt.savefig(save_path)
    plt.close()

def plot_utilization_trends(fcfs_metrics, rl_metrics, save_path="results/graphs/utilization_trends.png"):
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    labels = ['Baseline (FCFS)', 'RL Agent (PPO)']
    values = [fcfs_metrics['bed_util'], rl_metrics['bed_util']]
    
    plt.figure(figsize=(8, 6))
    bars = plt.bar(labels, values, color=['#F59E0B', '#10B981'])
    plt.ylabel('Average Bed Utilization (%)')
    plt.ylim(0, 100)
    plt.title('Resource Utilization Rate')
    
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 1.0, f'{yval:.1f}%', ha='center', va='bottom')
        
    plt.savefig(save_path)
    plt.close()

def save_logs(fcfs_metrics, rl_metrics):
    os.makedirs('results/logs', exist_ok=True)
    
    improvement_wait = ((fcfs_metrics['avg_wait'] - rl_metrics['avg_wait']) / fcfs_metrics['avg_wait']) * 100
    improvement_util = ((rl_metrics['bed_util'] - fcfs_metrics['bed_util']) / fcfs_metrics['bed_util']) * 100
    
    log_data = {
        "baseline_fcfs": fcfs_metrics,
        "agent_ppo": rl_metrics,
        "improvements": {
            "wait_time_reduction_percent": round(improvement_wait, 2),
            "utilization_increase_percent": round(improvement_util, 2)
        }
    }
    
    with open('results/logs/episode_performance.json', 'w') as f:
        json.dump(log_data, f, indent=4)
        
    return log_data
