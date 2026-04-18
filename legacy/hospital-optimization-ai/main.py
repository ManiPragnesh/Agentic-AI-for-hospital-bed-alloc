import argparse
import sys
import os

from training.train import train_agent
from evaluation.metrics import run_evaluation

def main():
    parser = argparse.ArgumentParser(description="Hospital Resource Optimization AI (RL Agent)")
    parser.add_argument("--train", action="store_true", help="Train the PPO RL Agent")
    parser.add_argument("--eval", action="store_true", help="Evaluate the Agent vs FCFS Baseline")
    
    args = parser.parse_args()
    
    # Setup directories
    os.makedirs("results/logs", exist_ok=True)
    os.makedirs("results/graphs", exist_ok=True)

    if args.train:
        train_agent()
    elif args.eval:
        run_evaluation()
    else:
        print("Please specify --train or --eval. Use -h for help.")
        sys.exit(1)

if __name__ == "__main__":
    main()
