"""Smart serializer for observatory data - Phase 3 implementation"""

import re
from typing import Any, Tuple, Set
from collections.abc import Mapping, Sequence


class SmartSerializer:
    """
    Serializes various data types for observatory storage.
    
    Phase 3: Full implementation with all data types and edge cases
    """
    
    def __init__(self, max_repr: int = 1000, sensitive_fields: tuple = ()):
        self.max_repr = max_repr
        self.sensitive_fields = tuple(field.lower() for field in sensitive_fields)
        self._seen = set()  # For circular reference detection
    
    def serialize(self, value: Any, name: str = "") -> str:
        """
        Serialize a value to string representation.
        
        Args:
            value: The value to serialize
            name: Optional name/key for sensitive field checking
            
        Returns:
            String representation of the value
        """
        # Reset circular reference tracking for each top-level call
        if not hasattr(self, '_in_serialize'):
            self._seen.clear()
            self._in_serialize = True
            try:
                return self._serialize_internal(value, name)
            finally:
                self._in_serialize = False
                self._seen.clear()
        else:
            return self._serialize_internal(value, name)
    
    def _serialize_internal(self, value: Any, name: str = "") -> str:
        """Internal serialization logic"""
        # Check for sensitive fields
        if name and self._is_sensitive_field(name):
            return "***"
        
        # Handle None
        if value is None:
            return "None"
        
        # Handle primitives
        if isinstance(value, (str, int, float, bool)):
            result = repr(value)
            return self._truncate(result)
        
        # Handle bytes
        if isinstance(value, (bytes, bytearray)):
            return f"<{type(value).__name__} len={len(value)}>"
        
        # Check for circular references
        obj_id = id(value)
        if obj_id in self._seen:
            return f"<Circular reference: {type(value).__name__}>"
        
        # Try Pandas DataFrames/Series first (before numpy check)
        type_name = type(value).__name__
        if hasattr(value, '__module__') and 'pandas' in value.__module__:
            if type_name == 'DataFrame':
                return f"[DataFrame {value.shape[0]}×{value.shape[1]}]"
            elif type_name == 'Series':
                return f"[Series len={len(value)}]"
        
        # Try NumPy arrays
        if hasattr(value, 'shape') and hasattr(value, 'dtype'):
            # NumPy array
            return self._serialize_numpy(value)
        
        # Add to seen set for collections
        self._seen.add(obj_id)
        
        try:
            # Handle dictionaries
            if isinstance(value, Mapping):
                return self._serialize_dict(value)
            
            # Handle sequences (list, tuple, set)
            if isinstance(value, (list, tuple)):
                return self._serialize_sequence(value)
            
            if isinstance(value, set):
                return self._serialize_set(value)
            
            # Handle custom objects
            return self._serialize_object(value)
            
        finally:
            # Remove from seen set
            self._seen.discard(obj_id)
    
    def _is_sensitive_field(self, name: str) -> bool:
        """Check if field name indicates sensitive data"""
        name_lower = name.lower()
        return any(sensitive in name_lower for sensitive in self.sensitive_fields)
    
    def _truncate(self, text: str) -> str:
        """Truncate text if it exceeds max_repr"""
        if len(text) <= self.max_repr:
            return text
        return text[:self.max_repr - 3] + "..."
    
    def _serialize_numpy(self, arr) -> str:
        """Serialize NumPy array"""
        try:
            shape_str = "×".join(str(d) for d in arr.shape) if arr.shape else "scalar"
            dtype_str = str(arr.dtype)
            return f"[ndarray {dtype_str} ({shape_str})]"
        except:
            return f"<numpy.ndarray at {hex(id(arr))}>"
    
    def _serialize_dict(self, d: Mapping) -> str:
        """Serialize dictionary with smart key handling"""
        if not d:
            return "{}"
        
        items = []
        remaining = 0
        
        # For sensitive field detection, process all items but only show first few
        all_items = []
        for key, value in d.items():
            key_str = str(key)
            val_str = self._serialize_internal(value, key_str)
            all_items.append(f"'{key_str}': {val_str}")
        
        # If it's small enough, show everything
        full_repr = "{" + ", ".join(all_items) + "}"
        if len(full_repr) <= self.max_repr:
            return full_repr
        
        # Otherwise, show first 3 items
        items = all_items[:3]
        remaining = len(d) - 3
        
        result = "{" + ", ".join(items)
        if remaining > 0:
            result += f", +{remaining} more"
        result += "}"
        
        return self._truncate(result)
    
    def _serialize_sequence(self, seq: Sequence) -> str:
        """Serialize list or tuple"""
        if not seq:
            return "[]" if isinstance(seq, list) else "()"
        
        type_name = type(seq).__name__
        length = len(seq)
        
        if length <= 3:
            # Show all items for small sequences
            items = [self._serialize_internal(item) for item in seq]
            if isinstance(seq, list):
                return "[" + ", ".join(items) + "]"
            else:
                return "(" + ", ".join(items) + ("," if length == 1 else "") + ")"
        else:
            # Show first 3 items for large sequences
            items = [self._serialize_internal(seq[i]) for i in range(3)]
            result = f"[{type_name}] len={length} 1st3=[{', '.join(items)}]"
            return self._truncate(result)
    
    def _serialize_set(self, s: set) -> str:
        """Serialize set"""
        if not s:
            return "set()"
        
        if len(s) <= 3:
            items = [self._serialize_internal(item) for item in s]
            return "{" + ", ".join(items) + "}"
        else:
            items = [self._serialize_internal(item) for i, item in enumerate(s) if i < 3]
            return f"[set] len={len(s)} sample={{{', '.join(items)}}}"
    
    def _serialize_object(self, obj: Any) -> str:
        """Serialize custom object"""
        try:
            # Try to use repr if it's defined and safe
            if hasattr(obj, '__repr__'):
                obj_repr = repr(obj)
                # Check if repr looks custom (not default object repr)
                if not re.match(r'<.*at 0x[0-9a-fA-F]+>', obj_repr):
                    return self._truncate(obj_repr)
        except:
            pass
        
        # Fallback to class name and id
        class_name = type(obj).__name__
        # Don't include module path for test compatibility
        return f"<{class_name} at {hex(id(obj))}>" 
        self._seen = set()  # For circular reference detection
    
    def serialize(self, value: Any, name: str = "") -> str:
        """
        Serialize a value to string representation.
        
        Args:
            value: The value to serialize
            name: Optional name/key for sensitive field checking
            
        Returns:
            String representation of the value
        """
        # Reset circular reference tracking for each top-level call
        if not hasattr(self, '_in_serialize'):
            self._seen.clear()
            self._in_serialize = True
            try:
                return self._serialize_internal(value, name)
            finally:
                self._in_serialize = False
                self._seen.clear()
        else:
            return self._serialize_internal(value, name)
    
    def _serialize_internal(self, value: Any, name: str = "") -> str:
        """Internal serialization logic"""
        # Check for sensitive fields
        if name and self._is_sensitive_field(name):
            return "***"
        
        # Handle None
        if value is None:
            return "None"
        
        # Handle primitives
        if isinstance(value, (str, int, float, bool)):
            result = repr(value)
            return self._truncate(result)
        
        # Handle bytes
        if isinstance(value, (bytes, bytearray)):
            return f"<{type(value).__name__} len={len(value)}>"
        
        # Check for circular references
        obj_id = id(value)
        if obj_id in self._seen:
            return f"<Circular reference: {type(value).__name__}>"
        
        # Try Pandas DataFrames/Series first (before numpy check)
        type_name = type(value).__name__
        if hasattr(value, '__module__') and 'pandas' in value.__module__:
            if type_name == 'DataFrame':
                return f"[DataFrame {value.shape[0]}×{value.shape[1]}]"
            elif type_name == 'Series':
                return f"[Series len={len(value)}]"
        
        # Try NumPy arrays
        if hasattr(value, 'shape') and hasattr(value, 'dtype'):
            # NumPy array
            return self._serialize_numpy(value)
        
        # Add to seen set for collections
        self._seen.add(obj_id)
        
        try:
            # Handle dictionaries
            if isinstance(value, Mapping):
                return self._serialize_dict(value)
            
            # Handle sequences (list, tuple, set)
            if isinstance(value, (list, tuple)):
                return self._serialize_sequence(value)
            
            if isinstance(value, set):
                return self._serialize_set(value)
            
            # Handle custom objects
            return self._serialize_object(value)
            
        finally:
            # Remove from seen set
            self._seen.discard(obj_id)
    
    def _is_sensitive_field(self, name: str) -> bool:
        """Check if field name indicates sensitive data"""
        name_lower = name.lower()
        return any(sensitive in name_lower for sensitive in self.sensitive_fields)
    
    def _truncate(self, text: str) -> str:
        """Truncate text if it exceeds max_repr"""
        if len(text) <= self.max_repr:
            return text
        return text[:self.max_repr - 3] + "..."
    
    def _serialize_numpy(self, arr) -> str:
        """Serialize NumPy array"""
        try:
            shape_str = "×".join(str(d) for d in arr.shape) if arr.shape else "scalar"
            dtype_str = str(arr.dtype)
            return f"[ndarray {dtype_str} ({shape_str})]"
        except:
            return f"<numpy.ndarray at {hex(id(arr))}>"
    
    def _serialize_dict(self, d: Mapping) -> str:
        """Serialize dictionary with smart key handling"""
        if not d:
            return "{}"
        
        items = []
        remaining = 0
        
        # For sensitive field detection, process all items but only show first few
        all_items = []
        for key, value in d.items():
            key_str = str(key)
            val_str = self._serialize_internal(value, key_str)
            all_items.append(f"'{key_str}': {val_str}")
        
        # If it's small enough, show everything
        full_repr = "{" + ", ".join(all_items) + "}"
        if len(full_repr) <= self.max_repr:
            return full_repr
        
        # Otherwise, show first 3 items
        items = all_items[:3]
        remaining = len(d) - 3
        
        result = "{" + ", ".join(items)
        if remaining > 0:
            result += f", +{remaining} more"
        result += "}"
        
        return self._truncate(result)
    
    def _serialize_sequence(self, seq: Sequence) -> str:
        """Serialize list or tuple"""
        if not seq:
            return "[]" if isinstance(seq, list) else "()"
        
        type_name = type(seq).__name__
        length = len(seq)
        
        if length <= 3:
            # Show all items for small sequences
            items = [self._serialize_internal(item) for item in seq]
            if isinstance(seq, list):
                return "[" + ", ".join(items) + "]"
            else:
                return "(" + ", ".join(items) + ("," if length == 1 else "") + ")"
        else:
            # Show first 3 items for large sequences
            items = [self._serialize_internal(seq[i]) for i in range(3)]
            result = f"[{type_name}] len={length} 1st3=[{', '.join(items)}]"
            return self._truncate(result)
    
    def _serialize_set(self, s: set) -> str:
        """Serialize set"""
        if not s:
            return "set()"
        
        if len(s) <= 3:
            items = [self._serialize_internal(item) for item in s]
            return "{" + ", ".join(items) + "}"
        else:
            items = [self._serialize_internal(item) for i, item in enumerate(s) if i < 3]
            return f"[set] len={len(s)} sample={{{', '.join(items)}}}"
    
    def _serialize_object(self, obj: Any) -> str:
        """Serialize custom object"""
        try:
            # Try to use repr if it's defined and safe
            if hasattr(obj, '__repr__'):
                obj_repr = repr(obj)
                # Check if repr looks custom (not default object repr)
                if not re.match(r'<.*at 0x[0-9a-fA-F]+>', obj_repr):
                    return self._truncate(obj_repr)
        except:
            pass
        
        # Fallback to class name and id
        class_name = type(obj).__name__
        # Don't include module path for test compatibility
        return f"<{class_name} at {hex(id(obj))}>" 