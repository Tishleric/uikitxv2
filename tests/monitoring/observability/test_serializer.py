"""Comprehensive tests for SmartSerializer - Phase 3"""

import pytest
import numpy as np
import pandas as pd
from lib.monitoring.serializers.smart import SmartSerializer


class TestSmartSerializer:
    """Test suite for SmartSerializer covering all data types and edge cases"""
    
    def test_primitives(self):
        """Test serialization of primitive types"""
        serializer = SmartSerializer()
        
        # String
        assert serializer.serialize("hello") == "'hello'"
        assert serializer.serialize("") == "''"
        
        # Integer
        assert serializer.serialize(42) == "42"
        assert serializer.serialize(0) == "0"
        assert serializer.serialize(-123) == "-123"
        
        # Float
        assert serializer.serialize(3.14) == "3.14"
        assert serializer.serialize(0.0) == "0.0"
        
        # Boolean
        assert serializer.serialize(True) == "True"
        assert serializer.serialize(False) == "False"
        
        # None
        assert serializer.serialize(None) == "None"
    
    def test_bytes(self):
        """Test serialization of bytes and bytearray"""
        serializer = SmartSerializer()
        
        assert serializer.serialize(b"hello") == "<bytes len=5>"
        assert serializer.serialize(bytearray(b"world")) == "<bytearray len=5>"
        assert serializer.serialize(b"") == "<bytes len=0>"
    
    def test_collections_small(self):
        """Test serialization of small collections"""
        serializer = SmartSerializer()
        
        # Small list
        assert serializer.serialize([1, 2, 3]) == "[1, 2, 3]"
        assert serializer.serialize([]) == "[]"
        
        # Small tuple
        assert serializer.serialize((1, 2, 3)) == "(1, 2, 3)"
        assert serializer.serialize((1,)) == "(1,)"
        assert serializer.serialize(()) == "()"
        
        # Small set
        result = serializer.serialize({1, 2, 3})
        # Sets are unordered, so check it contains the right elements
        assert result.startswith("{") and result.endswith("}")
        assert "1" in result and "2" in result and "3" in result
        assert serializer.serialize(set()) == "set()"
    
    def test_collections_large(self):
        """Test serialization of large collections"""
        serializer = SmartSerializer()
        
        # Large list
        big_list = list(range(100))
        result = serializer.serialize(big_list)
        assert result == "[list] len=100 1st3=[0, 1, 2]"
        
        # Large tuple
        big_tuple = tuple(range(50))
        result = serializer.serialize(big_tuple)
        assert result == "[tuple] len=50 1st3=[0, 1, 2]"
        
        # Large set
        big_set = set(range(20))
        result = serializer.serialize(big_set)
        assert "[set] len=20 sample={" in result
    
    def test_dict_serialization(self):
        """Test dictionary serialization"""
        serializer = SmartSerializer()
        
        # Empty dict
        assert serializer.serialize({}) == "{}"
        
        # Small dict
        assert serializer.serialize({"a": 1, "b": 2}) == "{'a': 1, 'b': 2}"
        
        # Large dict with limited max_repr to force truncation
        serializer_truncate = SmartSerializer(max_repr=100)
        big_dict = {f"key{i}": f"value_{i}" for i in range(10)}
        result = serializer_truncate.serialize(big_dict)
        assert "'key0': 'value_0'" in result
        assert "+7 more" in result
    
    def test_nested_collections(self):
        """Test nested data structures"""
        serializer = SmartSerializer()
        
        nested = {
            "list": [1, 2, {"nested": True}],
            "tuple": (3, 4, 5),
            "set": {6, 7}
        }
        result = serializer.serialize(nested)
        assert "'list': [1, 2, {'nested': True}]" in result
        assert "'tuple': (3, 4, 5)" in result
    
    def test_numpy_arrays(self):
        """Test NumPy array serialization"""
        serializer = SmartSerializer()
        
        # 1D array
        arr1d = np.array([1, 2, 3])
        assert serializer.serialize(arr1d) == "[ndarray int64 (3)]"
        
        # 2D array
        arr2d = np.array([[1, 2], [3, 4]])
        assert serializer.serialize(arr2d) == "[ndarray int64 (2×2)]"
        
        # 3D array
        arr3d = np.ones((2, 3, 4))
        assert serializer.serialize(arr3d) == "[ndarray float64 (2×3×4)]"
        
        # Scalar
        scalar = np.array(42)
        assert serializer.serialize(scalar) == "[ndarray int64 (scalar)]"
    
    def test_pandas_dataframes(self):
        """Test Pandas DataFrame and Series serialization"""
        serializer = SmartSerializer()
        
        # DataFrame
        df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        assert serializer.serialize(df) == "[DataFrame 3×2]"
        
        # Series
        series = pd.Series([1, 2, 3, 4, 5])
        assert serializer.serialize(series) == "[Series len=5]"
        
        # Empty DataFrame
        empty_df = pd.DataFrame()
        assert serializer.serialize(empty_df) == "[DataFrame 0×0]"
    
    def test_custom_objects(self):
        """Test custom object serialization"""
        serializer = SmartSerializer()
        
        class SimpleClass:
            pass
        
        class CustomRepr:
            def __repr__(self):
                return "CustomRepr(value=42)"
        
        # Simple object
        obj1 = SimpleClass()
        result1 = serializer.serialize(obj1)
        assert result1.startswith("<SimpleClass at 0x") or result1.startswith("<test_serializer.SimpleClass at 0x")
        
        # Object with custom repr
        obj2 = CustomRepr()
        assert serializer.serialize(obj2) == "CustomRepr(value=42)"
    
    def test_circular_references(self):
        """Test circular reference detection"""
        serializer = SmartSerializer()
        
        # Self-referencing list
        lst = [1, 2]
        lst.append(lst)
        result = serializer.serialize(lst)
        assert "<Circular reference: list>" in result
        
        # Circular dict
        d1 = {"a": 1}
        d2 = {"b": d1}
        d1["c"] = d2
        result = serializer.serialize(d1)
        assert "<Circular reference:" in result
    
    def test_sensitive_fields(self):
        """Test sensitive field masking"""
        serializer = SmartSerializer(sensitive_fields=("password", "api_key", "token"))
        
        data = {
            "username": "john",
            "password": "secret123",
            "api_key": "abc-123-def",
            "access_token": "bearer xyz",
            "data": "normal data"
        }
        
        result = serializer.serialize(data)
        assert "'username': 'john'" in result
        assert "'password': ***" in result
        assert "'api_key': ***" in result
        assert "'access_token': ***" in result  # 'token' is in 'access_token'
        assert "'data': 'normal data'" in result
    
    def test_truncation(self):
        """Test long string truncation"""
        serializer = SmartSerializer(max_repr=50)
        
        # Long string
        long_str = "a" * 100
        result = serializer.serialize(long_str)
        assert len(result) == 50
        assert result.endswith("...")
        
        # Long list representation
        long_list = list(range(1000))
        result = serializer.serialize(long_list)
        assert len(result) <= 50
    
    def test_edge_cases(self):
        """Test various edge cases"""
        serializer = SmartSerializer()
        
        # Recursive data structure
        recursive_dict = {}
        recursive_dict["self"] = recursive_dict
        result = serializer.serialize(recursive_dict)
        assert "Circular reference" in result
        
        # Mixed types in collections
        mixed = [1, "two", 3.0, None, True, {"nested": [4, 5]}]
        result = serializer.serialize(mixed)
        assert "[1, 'two', 3.0" in result
        
        # Unicode strings
        unicode_str = "Hello 世界 🌍"
        result = serializer.serialize(unicode_str)
        assert unicode_str in result
    
    def test_special_dict_keys(self):
        """Test dictionaries with non-string keys"""
        serializer = SmartSerializer()
        
        # Numeric keys
        numeric_dict = {1: "one", 2: "two", 3.14: "pi"}
        result = serializer.serialize(numeric_dict)
        assert "'1': 'one'" in result
        assert "'2': 'two'" in result
        assert "'3.14': 'pi'" in result
    
    def test_exception_handling(self):
        """Test serialization of objects that raise exceptions"""
        serializer = SmartSerializer()
        
        class BadRepr:
            def __repr__(self):
                raise ValueError("Bad repr")
        
        obj = BadRepr()
        result = serializer.serialize(obj)
        # Should fall back to default representation
        assert result.startswith("<BadRepr at 0x") or result.startswith("<test_serializer.BadRepr at 0x") 
        serializer = SmartSerializer()
        
        # String
        assert serializer.serialize("hello") == "'hello'"
        assert serializer.serialize("") == "''"
        
        # Integer
        assert serializer.serialize(42) == "42"
        assert serializer.serialize(0) == "0"
        assert serializer.serialize(-123) == "-123"
        
        # Float
        assert serializer.serialize(3.14) == "3.14"
        assert serializer.serialize(0.0) == "0.0"
        
        # Boolean
        assert serializer.serialize(True) == "True"
        assert serializer.serialize(False) == "False"
        
        # None
        assert serializer.serialize(None) == "None"
    
    def test_bytes(self):
        """Test serialization of bytes and bytearray"""
        serializer = SmartSerializer()
        
        assert serializer.serialize(b"hello") == "<bytes len=5>"
        assert serializer.serialize(bytearray(b"world")) == "<bytearray len=5>"
        assert serializer.serialize(b"") == "<bytes len=0>"
    
    def test_collections_small(self):
        """Test serialization of small collections"""
        serializer = SmartSerializer()
        
        # Small list
        assert serializer.serialize([1, 2, 3]) == "[1, 2, 3]"
        assert serializer.serialize([]) == "[]"
        
        # Small tuple
        assert serializer.serialize((1, 2, 3)) == "(1, 2, 3)"
        assert serializer.serialize((1,)) == "(1,)"
        assert serializer.serialize(()) == "()"
        
        # Small set
        result = serializer.serialize({1, 2, 3})
        # Sets are unordered, so check it contains the right elements
        assert result.startswith("{") and result.endswith("}")
        assert "1" in result and "2" in result and "3" in result
        assert serializer.serialize(set()) == "set()"
    
    def test_collections_large(self):
        """Test serialization of large collections"""
        serializer = SmartSerializer()
        
        # Large list
        big_list = list(range(100))
        result = serializer.serialize(big_list)
        assert result == "[list] len=100 1st3=[0, 1, 2]"
        
        # Large tuple
        big_tuple = tuple(range(50))
        result = serializer.serialize(big_tuple)
        assert result == "[tuple] len=50 1st3=[0, 1, 2]"
        
        # Large set
        big_set = set(range(20))
        result = serializer.serialize(big_set)
        assert "[set] len=20 sample={" in result
    
    def test_dict_serialization(self):
        """Test dictionary serialization"""
        serializer = SmartSerializer()
        
        # Empty dict
        assert serializer.serialize({}) == "{}"
        
        # Small dict
        assert serializer.serialize({"a": 1, "b": 2}) == "{'a': 1, 'b': 2}"
        
        # Large dict with limited max_repr to force truncation
        serializer_truncate = SmartSerializer(max_repr=100)
        big_dict = {f"key{i}": f"value_{i}" for i in range(10)}
        result = serializer_truncate.serialize(big_dict)
        assert "'key0': 'value_0'" in result
        assert "+7 more" in result
    
    def test_nested_collections(self):
        """Test nested data structures"""
        serializer = SmartSerializer()
        
        nested = {
            "list": [1, 2, {"nested": True}],
            "tuple": (3, 4, 5),
            "set": {6, 7}
        }
        result = serializer.serialize(nested)
        assert "'list': [1, 2, {'nested': True}]" in result
        assert "'tuple': (3, 4, 5)" in result
    
    def test_numpy_arrays(self):
        """Test NumPy array serialization"""
        serializer = SmartSerializer()
        
        # 1D array
        arr1d = np.array([1, 2, 3])
        assert serializer.serialize(arr1d) == "[ndarray int64 (3)]"
        
        # 2D array
        arr2d = np.array([[1, 2], [3, 4]])
        assert serializer.serialize(arr2d) == "[ndarray int64 (2×2)]"
        
        # 3D array
        arr3d = np.ones((2, 3, 4))
        assert serializer.serialize(arr3d) == "[ndarray float64 (2×3×4)]"
        
        # Scalar
        scalar = np.array(42)
        assert serializer.serialize(scalar) == "[ndarray int64 (scalar)]"
    
    def test_pandas_dataframes(self):
        """Test Pandas DataFrame and Series serialization"""
        serializer = SmartSerializer()
        
        # DataFrame
        df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        assert serializer.serialize(df) == "[DataFrame 3×2]"
        
        # Series
        series = pd.Series([1, 2, 3, 4, 5])
        assert serializer.serialize(series) == "[Series len=5]"
        
        # Empty DataFrame
        empty_df = pd.DataFrame()
        assert serializer.serialize(empty_df) == "[DataFrame 0×0]"
    
    def test_custom_objects(self):
        """Test custom object serialization"""
        serializer = SmartSerializer()
        
        class SimpleClass:
            pass
        
        class CustomRepr:
            def __repr__(self):
                return "CustomRepr(value=42)"
        
        # Simple object
        obj1 = SimpleClass()
        result1 = serializer.serialize(obj1)
        assert result1.startswith("<SimpleClass at 0x") or result1.startswith("<test_serializer.SimpleClass at 0x")
        
        # Object with custom repr
        obj2 = CustomRepr()
        assert serializer.serialize(obj2) == "CustomRepr(value=42)"
    
    def test_circular_references(self):
        """Test circular reference detection"""
        serializer = SmartSerializer()
        
        # Self-referencing list
        lst = [1, 2]
        lst.append(lst)
        result = serializer.serialize(lst)
        assert "<Circular reference: list>" in result
        
        # Circular dict
        d1 = {"a": 1}
        d2 = {"b": d1}
        d1["c"] = d2
        result = serializer.serialize(d1)
        assert "<Circular reference:" in result
    
    def test_sensitive_fields(self):
        """Test sensitive field masking"""
        serializer = SmartSerializer(sensitive_fields=("password", "api_key", "token"))
        
        data = {
            "username": "john",
            "password": "secret123",
            "api_key": "abc-123-def",
            "access_token": "bearer xyz",
            "data": "normal data"
        }
        
        result = serializer.serialize(data)
        assert "'username': 'john'" in result
        assert "'password': ***" in result
        assert "'api_key': ***" in result
        assert "'access_token': ***" in result  # 'token' is in 'access_token'
        assert "'data': 'normal data'" in result
    
    def test_truncation(self):
        """Test long string truncation"""
        serializer = SmartSerializer(max_repr=50)
        
        # Long string
        long_str = "a" * 100
        result = serializer.serialize(long_str)
        assert len(result) == 50
        assert result.endswith("...")
        
        # Long list representation
        long_list = list(range(1000))
        result = serializer.serialize(long_list)
        assert len(result) <= 50
    
    def test_edge_cases(self):
        """Test various edge cases"""
        serializer = SmartSerializer()
        
        # Recursive data structure
        recursive_dict = {}
        recursive_dict["self"] = recursive_dict
        result = serializer.serialize(recursive_dict)
        assert "Circular reference" in result
        
        # Mixed types in collections
        mixed = [1, "two", 3.0, None, True, {"nested": [4, 5]}]
        result = serializer.serialize(mixed)
        assert "[1, 'two', 3.0" in result
        
        # Unicode strings
        unicode_str = "Hello 世界 🌍"
        result = serializer.serialize(unicode_str)
        assert unicode_str in result
    
    def test_special_dict_keys(self):
        """Test dictionaries with non-string keys"""
        serializer = SmartSerializer()
        
        # Numeric keys
        numeric_dict = {1: "one", 2: "two", 3.14: "pi"}
        result = serializer.serialize(numeric_dict)
        assert "'1': 'one'" in result
        assert "'2': 'two'" in result
        assert "'3.14': 'pi'" in result
    
    def test_exception_handling(self):
        """Test serialization of objects that raise exceptions"""
        serializer = SmartSerializer()
        
        class BadRepr:
            def __repr__(self):
                raise ValueError("Bad repr")
        
        obj = BadRepr()
        result = serializer.serialize(obj)
        # Should fall back to default representation
        assert result.startswith("<BadRepr at 0x") or result.startswith("<test_serializer.BadRepr at 0x") 