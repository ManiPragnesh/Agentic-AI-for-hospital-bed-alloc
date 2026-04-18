# Agentic AI for Hospital Bed & Resource Optimization

## Overview
This project implements an **Agentic AI Decision Support System** using Reinforcement Learning to optimize hospital resource allocation. It models hospital dynamics (Emergency, ICU, General Wards) using a Discrete Event Simulation (`simpy`) and trains an autonomous agent using Proximal Policy Optimization (`stable-baselines3`).

The agent is trained to minimize patient wait times, maximize bed utilization, and execute dynamic strategies like early discharge and dynamic staff scaling to balance stochastic patient inflows.

## Key Features
*   **High-Fidelity Simulation (`simpy`)**: Models Poisson-distributed patient arrivals, stochastic severity scores, and capacity constrained resource allocation.
*   **Reinforcement Learning (`stable-baselines3`)**: Utilizes Proximal Policy Optimization (PPO) to learn optimal behaviors across 10,000+ timesteps.
*   **Multi-Objective MDP formulation**: Balances wait times, bed constraints, and staffing requirements.
*   **Baseline Benchmarking**: Fully automated evaluation script to compare RL learned policies against deterministic First-Come-First-Serve (FCFS) heuristics.

## Installation

### Prerequisites
*   Python 3.9+
*   Virtual environment (recommended)

```bash
# Clone the repository and navigate to the project root
cd hospital-optimization-ai

# Install dependencies
pip install -r requirements.txt
```

## Usage

The primary entry point is `main.py`.

### 1. Train the Agent
To start the PPO training loop:

```bash
# Ensure you are running from the project root so Python can resolve imports
set PYTHONPATH=. 
python main.py --train
```

*This will initialize the Stable-Baselines3 agent, execute the PPO learning loop across simulated environments, and save the final model to `results/ppo_hospital_admin_final.zip`.*

### 2. Evaluate the Agent
To evaluate the trained model against the FCFS baseline:

```bash
set PYTHONPATH=.
python main.py --eval
```

*This script produces numerical benchmarking output in the console and generates comparative charts for wait times and utilization inside the `results/graphs/` directory.*

## Architecture
The project is strictly separated into modular components:
*   `/config`: Global constants and simulation hyperparameters.
*   `/environment`: `simpy` process logic and `Gymnasium` interface wrapping.
*   `/agents`: Wrappers for SB3 model loading and execution.
*   `/simulation`: The core discrete event orchestrator.
*   `/evaluation`: Benchmarking and metric extraction.
*   `/docs`: Final academic report outlining methodology and results.
