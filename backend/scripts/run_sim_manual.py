from backend.src.simulation.env import run_simulation

if __name__ == "__main__":
    print("Starting Hospital Simulation...")
    df = run_simulation(duration=200)
    print("\nSimulation Complete. Logs:")
    print(df.head(20))
    print(f"\nTotal Patients Processed: {len(df)}")
    
    # Save to CSV for inspection
    df.to_csv("sim_logs.csv", index=False)
