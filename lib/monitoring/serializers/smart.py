"""Smart serializer for observability data - Phase 1 stub"""


class SmartSerializer:
    """
    Serializes various data types for observability storage.
    
    Phase 1: Empty stub implementation
    """
    
    def __init__(self, max_repr: int = 1000, sensitive_fields: tuple = ()):
        self.max_repr = max_repr
        self.sensitive_fields = sensitive_fields
    
    def serialize(self, value):
        """Serialize a value - Phase 1 stub"""
        return str(value)  # Simple stub for now 