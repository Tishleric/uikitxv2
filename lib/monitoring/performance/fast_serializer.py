"""Fast serialization paths for common data types."""

import json
from typing import Any, Dict, List, Union
from ..serializers.smart import SmartSerializer


class FastSerializer:
    """Optimized serializer with fast paths for common types."""
    
    # Types that can be serialized directly
    FAST_TYPES = (str, int, float, bool, type(None))
    
    def __init__(self):
        """Initialize with fallback to SmartSerializer."""
        self._smart_serializer = SmartSerializer()
        self._type_cache = {}
    
    def serialize(self, obj: Any) -> Any:
        """
        Serialize object with fast paths for common types.
        
        Fast paths for:
        - Primitives: str, int, float, bool, None
        - Simple lists/tuples of primitives
        - Simple dicts with string keys and primitive values
        
        Falls back to SmartSerializer for complex types.
        """
        # Fast path 1: Direct primitives
        if type(obj) in self.FAST_TYPES:
            return obj
        
        # Fast path 2: Simple lists/tuples
        if isinstance(obj, (list, tuple)):
            if len(obj) == 0:
                return list(obj)
            
            # Check if all elements are fast types
            if all(type(item) in self.FAST_TYPES for item in obj):
                return list(obj)
        
        # Fast path 3: Simple dicts
        if isinstance(obj, dict):
            if len(obj) == 0:
                return obj
            
            # Check if all keys are strings and values are fast types
            if all(isinstance(k, str) and type(v) in self.FAST_TYPES 
                   for k, v in obj.items()):
                return obj
        
        # Fallback to SmartSerializer for complex types
        return self._smart_serializer.serialize(obj)
    
    def lazy_serialize(self, obj: Any) -> Union[Any, Dict[str, str]]:
        """
        Lazy serialization for large objects.
        
        Returns a placeholder for large objects that can be
        serialized on-demand if needed.
        """
        # Check size estimate first
        try:
            # Quick size check for strings
            if isinstance(obj, str) and len(obj) > 10000:
                return {
                    "__lazy__": True,
                    "__type__": "str",
                    "__size__": len(obj),
                    "__preview__": obj[:100] + "..."
                }
            
            # For collections, check length
            if isinstance(obj, (list, dict, tuple, set)):
                if len(obj) > 1000:
                    return {
                        "__lazy__": True,
                        "__type__": type(obj).__name__,
                        "__size__": len(obj),
                        "__preview__": f"{type(obj).__name__} with {len(obj)} items"
                    }
        except:
            pass
        
        # Fast types go through immediately (after size check)
        if type(obj) in self.FAST_TYPES:
            return obj
        
        # Otherwise serialize normally
        return self.serialize(obj)
    
    def batch_serialize(self, objects: List[Any]) -> List[Any]:
        """
        Serialize multiple objects efficiently.
        
        Useful for batch writing to reduce overhead.
        """
        return [self.serialize(obj) for obj in objects] 