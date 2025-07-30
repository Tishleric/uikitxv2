"""View comprehensive profiling results from the new profiling system."""
import json
import os
from pathlib import Path
from datetime import datetime
import argparse

def view_profiles(session_id=None):
    """View profiling results from logs/profiling directory."""
    
    profiling_dir = Path("logs/profiling")
    if not profiling_dir.exists():
        print("No profiling directory found. Make sure MONITOR_PROFILING=1 is set.")
        return
    
    # If no session_id provided, find the most recent
    if not session_id:
        summary_files = list(profiling_dir.glob("summary_*.json"))
        if not summary_files:
            print("No profiling summaries found.")
            profile_files = list(profiling_dir.glob("profile_*.json"))
            if profile_files:
                print(f"\nFound {len(profile_files)} individual profile files:")
                # Extract session from filename
                sessions = set()
                for f in profile_files:
                    parts = f.stem.split('_')
                    if len(parts) >= 3:
                        session = f"{parts[1]}_{parts[2]}"
                        sessions.add(session)
                
                for session in sorted(sessions, reverse=True):
                    print(f"  - Session: {session}")
                    session_files = [f for f in profile_files if session in f.name]
                    print(f"    Files: {len(session_files)}")
            return
        
        # Get most recent summary
        latest_summary = max(summary_files, key=lambda f: f.stat().st_mtime)
        session_id = latest_summary.stem.replace("summary_", "")
        print(f"Using most recent session: {session_id}")
    
    # Load summary if it exists
    summary_file = profiling_dir / f"summary_{session_id}.json"
    if summary_file.exists():
        with open(summary_file) as f:
            summary = json.load(f)
        
        print(f"\n{'='*80}")
        print(f"Session: {summary['session_id']}")
        print(f"Total Profiles: {summary['total_profiles']}")
        print(f"{'='*80}\n")
        
        if summary['profiles']:
            print(f"{'Task ID':<50} {'Function':<40} {'Duration(ms)':<12} {'Status':<10}")
            print("-" * 112)
            
            for profile in sorted(summary['profiles'], key=lambda p: p['duration_ms'], reverse=True):
                task_id = profile['task_id'][:50]
                function = profile['function'][:40]
                duration = f"{profile['duration_ms']:.2f}"
                status = profile['status']
                print(f"{task_id:<50} {function:<40} {duration:<12} {status:<10}")
    
    # Load individual profiles
    profile_files = list(profiling_dir.glob(f"profile_{session_id}_*.json"))
    
    if not profile_files:
        print(f"\nNo profile files found for session {session_id}")
        return
    
    # Sort by duration
    profiles_data = []
    for pf in profile_files:
        with open(pf) as f:
            data = json.load(f)
            profiles_data.append(data)
    
    profiles_data.sort(key=lambda p: p.get('duration_ms', 0), reverse=True)
    
    # Show top 5 detailed profiles
    print(f"\n{'='*80}")
    print("Top 5 Detailed Profiles (by duration):")
    print(f"{'='*80}\n")
    
    for i, profile in enumerate(profiles_data[:5]):
        print(f"\n--- Profile {i+1} ---")
        print(f"Task ID: {profile['task_id']}")
        print(f"Function: {profile['function_name']}")
        print(f"Duration: {profile['duration_ms']:.2f}ms")
        print(f"Call Count: {profile['call_count']}")
        print(f"Total Time in Function: {profile['total_time_ms']:.2f}ms")
        
        if profile.get('profile_stats'):
            print("\nTop Functions by Cumulative Time:")
            print("-" * 80)
            # Show first 15 lines of profile stats
            lines = profile['profile_stats'].split('\n')
            for line in lines[:15]:
                if line.strip():
                    print(line)
    
    # Show timing distribution
    print(f"\n{'='*80}")
    print("Timing Distribution:")
    print(f"{'='*80}\n")
    
    buckets = {
        "< 10ms": 0,
        "10-50ms": 0,
        "50-100ms": 0,
        "100-500ms": 0,
        "500ms-1s": 0,
        "> 1s": 0
    }
    
    for profile in profiles_data:
        duration = profile.get('duration_ms', 0)
        if duration < 10:
            buckets["< 10ms"] += 1
        elif duration < 50:
            buckets["10-50ms"] += 1
        elif duration < 100:
            buckets["50-100ms"] += 1
        elif duration < 500:
            buckets["100-500ms"] += 1
        elif duration < 1000:
            buckets["500ms-1s"] += 1
        else:
            buckets["> 1s"] += 1
    
    for bucket, count in buckets.items():
        print(f"{bucket:<15} {count:>5} tasks")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="View comprehensive profiling results")
    parser.add_argument("--session", help="Session ID to view (default: most recent)")
    args = parser.parse_args()
    
    view_profiles(args.session) 