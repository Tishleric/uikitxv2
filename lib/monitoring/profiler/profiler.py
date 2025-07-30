"""Comprehensive profiling system with start/end tracking."""
import cProfile
import pstats
import io
import time
import threading
import os
import json
from typing import Dict, Optional, Any, List
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ProfileData:
    """Container for profile data with timing information."""
    def __init__(self, task_id: str, function_name: str):
        self.task_id = task_id
        self.function_name = function_name
        self.start_time = time.perf_counter()
        self.end_time: Optional[float] = None
        self.profile_stats: Optional[str] = None
        self.profiler: Optional[cProfile.Profile] = None
        self.call_count = 0
        self.total_time_ms = 0.0
        
    def duration_ms(self) -> float:
        """Get duration in milliseconds."""
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0.0


class ProfileManager:
    """Manages profiling data across the application."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.profiles: Dict[str, ProfileData] = {}
        self.profile_lock = threading.Lock()
        self.output_dir = Path("logs/profiling")
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.enabled = os.environ.get("MONITOR_PROFILING") == "1"
        
        logger.info(f"ProfileManager initialized. Profiling {'ENABLED' if self.enabled else 'DISABLED'}")
        
    def start_profile(self, task_id: str, function_name: str) -> Optional[cProfile.Profile]:
        """Start profiling for a task."""
        if not self.enabled:
            return None
            
        with self.profile_lock:
            if task_id in self.profiles:
                logger.warning(f"Profile already exists for {task_id}")
                return None
                
            profile_data = ProfileData(task_id, function_name)
            
            try:
                profile_data.profiler = cProfile.Profile()
                profile_data.profiler.enable()
                self.profiles[task_id] = profile_data
                
                logger.debug(f"[PROFILE START] {task_id} - {function_name}")
                return profile_data.profiler
                
            except ValueError as e:
                # Another profiler might be active
                logger.debug(f"Could not start profiler for {task_id}: {e}")
                return None
    
    def end_profile(self, task_id: str) -> Optional[ProfileData]:
        """End profiling for a task and capture stats."""
        if not self.enabled:
            return None
            
        with self.profile_lock:
            profile_data = self.profiles.get(task_id)
            if not profile_data:
                logger.warning(f"No profile found for {task_id}")
                return None
                
            profile_data.end_time = time.perf_counter()
            
            if profile_data.profiler:
                profile_data.profiler.disable()
                
                # Capture stats
                s = io.StringIO()
                ps = pstats.Stats(profile_data.profiler, stream=s)
                ps.sort_stats('cumulative')
                ps.print_stats(30)  # Top 30 functions
                profile_data.profile_stats = s.getvalue()
                
                # Calculate summary stats
                stats_dict = ps.stats
                profile_data.call_count = sum(data[0] for data in stats_dict.values())
                profile_data.total_time_ms = ps.total_tt * 1000
                
            logger.debug(f"[PROFILE END] {task_id} - Duration: {profile_data.duration_ms():.2f}ms")
            
            # Save to file
            self._save_profile(profile_data)
            
            return profile_data
    
    def _save_profile(self, profile_data: ProfileData):
        """Save profile data to a file."""
        filename = self.output_dir / f"profile_{self.session_id}_{profile_data.task_id}.json"
        
        data = {
            "task_id": profile_data.task_id,
            "function_name": profile_data.function_name,
            "start_time": profile_data.start_time,
            "end_time": profile_data.end_time,
            "duration_ms": profile_data.duration_ms(),
            "call_count": profile_data.call_count,
            "total_time_ms": profile_data.total_time_ms,
            "profile_stats": profile_data.profile_stats
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save profile data: {e}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all profiles."""
        with self.profile_lock:
            summary = {
                "session_id": self.session_id,
                "total_profiles": len(self.profiles),
                "profiles": []
            }
            
            for task_id, profile_data in self.profiles.items():
                summary["profiles"].append({
                    "task_id": task_id,
                    "function": profile_data.function_name,
                    "duration_ms": profile_data.duration_ms(),
                    "call_count": profile_data.call_count,
                    "status": "completed" if profile_data.end_time else "running"
                })
            
            return summary
    
    def save_summary(self):
        """Save a summary of all profiles."""
        summary_file = self.output_dir / f"summary_{self.session_id}.json"
        
        try:
            with open(summary_file, 'w') as f:
                json.dump(self.get_summary(), f, indent=2)
            logger.info(f"Profile summary saved to {summary_file}")
        except Exception as e:
            logger.error(f"Failed to save profile summary: {e}")


# Global instance
_profile_manager = ProfileManager()


@contextmanager
def profile_context(task_id: str, function_name: str):
    """Context manager for profiling a code block."""
    profiler = _profile_manager.start_profile(task_id, function_name)
    try:
        yield profiler
    finally:
        _profile_manager.end_profile(task_id)


def get_profile_manager() -> ProfileManager:
    """Get the global profile manager instance."""
    return _profile_manager 