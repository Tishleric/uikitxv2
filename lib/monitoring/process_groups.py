"""Intelligent process group assignment strategies for the monitoring system"""

import re
import inspect
from typing import Optional, List, Callable, Dict, Any
from functools import lru_cache


class ProcessGroupStrategy:
    """Base class for process group assignment strategies"""
    
    def assign(self, func: Callable) -> str:
        """Assign a process group to a function"""
        raise NotImplementedError


class ModuleBasedStrategy(ProcessGroupStrategy):
    """Assign groups based on module hierarchy"""
    
    def __init__(self, depth: int = 2):
        self.depth = depth
    
    def assign(self, func: Callable) -> str:
        """Use module path up to specified depth"""
        module = func.__module__
        parts = module.split('.')
        return '.'.join(parts[:self.depth])


class PatternBasedStrategy(ProcessGroupStrategy):
    """Assign groups based on function name patterns"""
    
    def __init__(self, patterns: Dict[str, str]):
        """
        Args:
            patterns: Dict mapping regex patterns to group names
                     e.g., {r'^get_.*': 'data.read', r'^save_.*': 'data.write'}
        """
        self.patterns = [(re.compile(p), g) for p, g in patterns.items()]
    
    def assign(self, func: Callable) -> str:
        """Match function name against patterns"""
        name = func.__name__
        
        for pattern, group in self.patterns:
            if pattern.match(name):
                return group
        
        # Fallback to module
        return func.__module__


class SemanticStrategy(ProcessGroupStrategy):
    """Assign groups based on semantic analysis of function"""
    
    def __init__(self):
        self.io_keywords = {'read', 'load', 'fetch', 'get', 'query', 'select'}
        self.write_keywords = {'write', 'save', 'store', 'put', 'insert', 'update', 'delete'}
        self.compute_keywords = {'calculate', 'compute', 'process', 'transform', 'analyze'}
        self.api_keywords = {'handle', 'route', 'endpoint', 'view', 'controller'}
    
    def assign(self, func: Callable) -> str:
        """Analyze function name and docstring for semantic hints"""
        name = func.__name__.lower()
        doc = (func.__doc__ or '').lower()
        
        # Check for I/O operations
        if any(kw in name for kw in self.io_keywords):
            return f"io.read.{func.__module__.split('.')[-1]}"
        if any(kw in name for kw in self.write_keywords):
            return f"io.write.{func.__module__.split('.')[-1]}"
        
        # Check for compute operations
        if any(kw in name for kw in self.compute_keywords):
            return f"compute.{func.__module__.split('.')[-1]}"
        
        # Check for API handlers
        if any(kw in name for kw in self.api_keywords):
            return f"api.{func.__module__.split('.')[-1]}"
        
        # Check docstring for hints
        if 'database' in doc or 'sql' in doc:
            return f"database.{func.__module__.split('.')[-1]}"
        if 'api' in doc or 'rest' in doc:
            return f"api.{func.__module__.split('.')[-1]}"
        
        # Fallback to module
        return func.__module__


class LayeredStrategy(ProcessGroupStrategy):
    """Assign groups based on architectural layers"""
    
    def __init__(self):
        self.layer_patterns = {
            'presentation': ['routes', 'views', 'handlers', 'api', 'endpoints'],
            'business': ['services', 'managers', 'processors', 'domain'],
            'data': ['repositories', 'dao', 'models', 'entities'],
            'infrastructure': ['utils', 'helpers', 'common', 'shared']
        }
    
    def assign(self, func: Callable) -> str:
        """Determine architectural layer from module path"""
        module_parts = func.__module__.split('.')
        
        for layer, patterns in self.layer_patterns.items():
            if any(p in module_parts for p in patterns):
                return f"{layer}.{module_parts[-1]}"
        
        # Check if it's a trading-specific module
        if 'trading' in module_parts:
            if 'actant' in module_parts:
                return f"trading.actant.{func.__name__.split('_')[0]}"
            elif 'pricing_monkey' in module_parts:
                return "trading.pricing_monkey"
            elif 'tt_api' in module_parts:
                return "trading.tt_api"
        
        return func.__module__


class CompositeStrategy(ProcessGroupStrategy):
    """Combine multiple strategies with priorities"""
    
    def __init__(self, strategies: List[tuple[ProcessGroupStrategy, float]]):
        """
        Args:
            strategies: List of (strategy, weight) tuples
        """
        self.strategies = strategies
    
    def assign(self, func: Callable) -> str:
        """Use first strategy that returns a non-default group"""
        for strategy, weight in self.strategies:
            group = strategy.assign(func)
            if group != func.__module__:  # Not the default fallback
                return group
        
        return func.__module__


# Singleton instance for global configuration
_global_strategy: Optional[ProcessGroupStrategy] = None


def set_global_strategy(strategy: ProcessGroupStrategy):
    """Set the global process group assignment strategy"""
    global _global_strategy
    _global_strategy = strategy


def get_process_group(func: Callable) -> str:
    """Get process group for a function using the global strategy"""
    if _global_strategy is None:
        # Default to module-based strategy
        return ModuleBasedStrategy().assign(func)
    return _global_strategy.assign(func)


# Pre-configured strategies for common use cases
class ProcessGroupStrategies:
    """Pre-configured strategies for different scenarios"""
    
    @staticmethod
    def for_microservices() -> ProcessGroupStrategy:
        """Strategy for microservice architectures"""
        return CompositeStrategy([
            (LayeredStrategy(), 1.0),
            (PatternBasedStrategy({
                r'^handle_.*': 'api.handlers',
                r'^.*_task$': 'async.tasks',
                r'^.*_job$': 'batch.jobs'
            }), 0.8),
            (ModuleBasedStrategy(depth=3), 0.5)
        ])
    
    @staticmethod
    def for_data_pipeline() -> ProcessGroupStrategy:
        """Strategy for data processing pipelines"""
        return PatternBasedStrategy({
            r'^extract_.*': 'pipeline.extract',
            r'^transform_.*': 'pipeline.transform',
            r'^load_.*': 'pipeline.load',
            r'^validate_.*': 'pipeline.validate',
            r'^.*_etl$': 'pipeline.orchestration'
        })
    
    @staticmethod
    def for_trading_system() -> ProcessGroupStrategy:
        """Strategy for trading systems like UIKitXv2"""
        return CompositeStrategy([
            (PatternBasedStrategy({
                # Order management
                r'^(submit|cancel|modify)_order.*': 'trading.orders.execution',
                r'^.*_order_status.*': 'trading.orders.status',
                
                # Market data
                r'^(get|fetch)_.*_price.*': 'trading.market_data.prices',
                r'^.*_market_data.*': 'trading.market_data.feed',
                
                # Risk
                r'^calculate_.*risk.*': 'trading.risk.calculation',
                r'^check_.*limit.*': 'trading.risk.limits',
                
                # P&L
                r'^.*_pnl.*': 'trading.pnl',
                r'^.*_position.*': 'trading.positions',
                
                # External APIs
                r'^tt_.*': 'external.tt_api',
                r'^pm_.*': 'external.pricing_monkey'
            }), 1.0),
            (SemanticStrategy(), 0.7),
            (ModuleBasedStrategy(depth=3), 0.5)
        ])


# Auto-grouping decorator
def auto_monitor(**kwargs):
    """Monitor decorator with automatic process group assignment"""
    def decorator(func):
        # Get process group if not specified
        if 'process_group' not in kwargs:
            kwargs['process_group'] = get_process_group(func)
        
        # Import here to avoid circular dependency
        from lib.monitoring.decorators.monitor import monitor
        return monitor(**kwargs)(func)
    
    return decorator


# Example of multi-group support (future enhancement)
class MultiGroupMonitor:
    """
    Future enhancement: Support multiple process groups per function
    
    Usage:
        @multi_monitor(groups=['trading.orders', 'critical.realtime'])
        def submit_order():
            pass
    """
    
    def __init__(self, groups: List[str], **monitor_kwargs):
        self.groups = groups
        self.monitor_kwargs = monitor_kwargs
    
    def __call__(self, func):
        # This would require changes to the monitoring system to support
        # multiple records per function call, one for each group
        raise NotImplementedError("Multi-group support not yet implemented")


# Dynamic group assignment based on runtime context
class ContextualGroupStrategy(ProcessGroupStrategy):
    """Assign groups based on runtime context (future enhancement)"""
    
    def assign_with_context(self, func: Callable, *args, **kwargs) -> str:
        """
        Assign group based on function arguments or global context
        
        Example: Different groups for different trading instruments
        """
        # Check for instrument type in arguments
        if args and hasattr(args[0], 'instrument_type'):
            instrument = args[0].instrument_type
            return f"trading.{instrument}.{func.__name__}"
        
        # Check for user role in context
        # This would need contextvars support
        # user_role = context_vars.get('user_role')
        # if user_role == 'admin':
        #     return f"admin.{func.__module__}"
        
        return self.assign(func) 