import cProfile
import pstats
from run_spot_risk_watcher import main as run_watcher

def profile_spot_risk_watcher():
    """
    Runs the Spot Risk Watcher under cProfile and saves the stats.
    """
    output_file = 'logs/producer_profile_stats.prof'
    print(f"Starting profiler. Output will be saved to {output_file}")
    
    # Run the main function from the watcher script under the profiler
    cProfile.run('run_watcher()', output_file)
    
    print("\nProfiling complete. Analyzing stats...")
    
    # Optional: Print the top 20 functions by cumulative time
    stats = pstats.Stats(output_file)
    stats.sort_stats('cumulative').print_stats(20)
    
    print(f"\nFull profiling stats saved to {output_file}")
    print("You can visualize this file with a tool like snakeviz.")

if __name__ == "__main__":
    profile_spot_risk_watcher() 