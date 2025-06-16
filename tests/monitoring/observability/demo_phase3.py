"""Demo script for Phase 3: SmartSerializer functionality"""

import numpy as np
import pandas as pd
from lib.monitoring.serializers import SmartSerializer


def demo_serializer():
    """Demonstrate SmartSerializer capabilities"""
    print("=== Phase 3: SmartSerializer Demo ===\n")
    
    # Create serializer with default settings
    serializer = SmartSerializer()
    
    # 1. Primitive types
    print("1. Primitive Types:")
    print(f"   String: {serializer.serialize('hello world')}")
    print(f"   Integer: {serializer.serialize(42)}")
    print(f"   Float: {serializer.serialize(3.14159)}")
    print(f"   Boolean: {serializer.serialize(True)}")
    print(f"   None: {serializer.serialize(None)}")
    print()
    
    # 2. Collections
    print("2. Collections:")
    print(f"   List: {serializer.serialize([1, 2, 3, 4, 5])}")
    print(f"   Large list: {serializer.serialize(list(range(100)))}")
    print(f"   Dict: {serializer.serialize({'name': 'John', 'age': 30, 'city': 'NYC'})}")
    print(f"   Set: {serializer.serialize({1, 2, 3})}")
    print()
    
    # 3. NumPy arrays
    print("3. NumPy Arrays:")
    arr1d = np.array([1, 2, 3, 4, 5])
    arr2d = np.random.rand(10, 20)
    arr3d = np.ones((5, 10, 15))
    print(f"   1D array: {serializer.serialize(arr1d)}")
    print(f"   2D array: {serializer.serialize(arr2d)}")
    print(f"   3D array: {serializer.serialize(arr3d)}")
    print()
    
    # 4. Pandas DataFrames
    print("4. Pandas DataFrames:")
    df = pd.DataFrame({
        'A': [1, 2, 3, 4, 5],
        'B': ['a', 'b', 'c', 'd', 'e'],
        'C': [1.1, 2.2, 3.3, 4.4, 5.5]
    })
    series = pd.Series([10, 20, 30, 40, 50])
    print(f"   DataFrame: {serializer.serialize(df)}")
    print(f"   Series: {serializer.serialize(series)}")
    print()
    
    # 5. Nested structures
    print("5. Nested Structures:")
    nested = {
        'data': [1, 2, {'inner': [3, 4, 5]}],
        'array': np.array([1, 2, 3]),
        'df': df,
        'metadata': {
            'version': '1.0',
            'created': '2025-01-01'
        }
    }
    print(f"   Nested: {serializer.serialize(nested)}")
    print()
    
    # 6. Circular references
    print("6. Circular References:")
    circular_list = [1, 2, 3]
    circular_list.append(circular_list)
    print(f"   Circular list: {serializer.serialize(circular_list)}")
    print()
    
    # 7. Sensitive data masking
    print("7. Sensitive Data Masking:")
    sensitive_serializer = SmartSerializer(sensitive_fields=('password', 'api_key', 'secret'))
    user_data = {
        'username': 'john_doe',
        'password': 'super_secret_123',
        'email': 'john@example.com',
        'api_key': 'sk-1234567890abcdef',
        'profile': {
            'name': 'John Doe',
            'secret_token': 'xyz789'
        }
    }
    print(f"   User data: {sensitive_serializer.serialize(user_data)}")
    print()
    
    # 8. Truncation
    print("8. Truncation (max_repr=50):")
    truncate_serializer = SmartSerializer(max_repr=50)
    long_string = "This is a very long string that will be truncated because it exceeds the maximum representation length"
    print(f"   Long string: {truncate_serializer.serialize(long_string)}")
    print()
    
    # 9. Custom objects
    print("9. Custom Objects:")
    class Person:
        def __init__(self, name, age):
            self.name = name
            self.age = age
        
        def __repr__(self):
            return f"Person(name={self.name!r}, age={self.age})"
    
    person = Person("Alice", 25)
    print(f"   Custom object: {serializer.serialize(person)}")
    
    class SimpleClass:
        pass
    
    simple = SimpleClass()
    print(f"   Simple object: {serializer.serialize(simple)}")
    print()
    
    # 10. Edge cases
    print("10. Edge Cases:")
    print(f"   Empty list: {serializer.serialize([])}")
    print(f"   Empty dict: {serializer.serialize({})}")
    print(f"   Bytes: {serializer.serialize(b'binary data')}")
    print(f"   Unicode: {serializer.serialize('Hello 世界 🌍')}")
    print()
    
    print("=== SmartSerializer Demo Complete ===")


if __name__ == "__main__":
    demo_serializer() 

import numpy as np
import pandas as pd
from lib.monitoring.serializers import SmartSerializer


def demo_serializer():
    """Demonstrate SmartSerializer capabilities"""
    print("=== Phase 3: SmartSerializer Demo ===\n")
    
    # Create serializer with default settings
    serializer = SmartSerializer()
    
    # 1. Primitive types
    print("1. Primitive Types:")
    print(f"   String: {serializer.serialize('hello world')}")
    print(f"   Integer: {serializer.serialize(42)}")
    print(f"   Float: {serializer.serialize(3.14159)}")
    print(f"   Boolean: {serializer.serialize(True)}")
    print(f"   None: {serializer.serialize(None)}")
    print()
    
    # 2. Collections
    print("2. Collections:")
    print(f"   List: {serializer.serialize([1, 2, 3, 4, 5])}")
    print(f"   Large list: {serializer.serialize(list(range(100)))}")
    print(f"   Dict: {serializer.serialize({'name': 'John', 'age': 30, 'city': 'NYC'})}")
    print(f"   Set: {serializer.serialize({1, 2, 3})}")
    print()
    
    # 3. NumPy arrays
    print("3. NumPy Arrays:")
    arr1d = np.array([1, 2, 3, 4, 5])
    arr2d = np.random.rand(10, 20)
    arr3d = np.ones((5, 10, 15))
    print(f"   1D array: {serializer.serialize(arr1d)}")
    print(f"   2D array: {serializer.serialize(arr2d)}")
    print(f"   3D array: {serializer.serialize(arr3d)}")
    print()
    
    # 4. Pandas DataFrames
    print("4. Pandas DataFrames:")
    df = pd.DataFrame({
        'A': [1, 2, 3, 4, 5],
        'B': ['a', 'b', 'c', 'd', 'e'],
        'C': [1.1, 2.2, 3.3, 4.4, 5.5]
    })
    series = pd.Series([10, 20, 30, 40, 50])
    print(f"   DataFrame: {serializer.serialize(df)}")
    print(f"   Series: {serializer.serialize(series)}")
    print()
    
    # 5. Nested structures
    print("5. Nested Structures:")
    nested = {
        'data': [1, 2, {'inner': [3, 4, 5]}],
        'array': np.array([1, 2, 3]),
        'df': df,
        'metadata': {
            'version': '1.0',
            'created': '2025-01-01'
        }
    }
    print(f"   Nested: {serializer.serialize(nested)}")
    print()
    
    # 6. Circular references
    print("6. Circular References:")
    circular_list = [1, 2, 3]
    circular_list.append(circular_list)
    print(f"   Circular list: {serializer.serialize(circular_list)}")
    print()
    
    # 7. Sensitive data masking
    print("7. Sensitive Data Masking:")
    sensitive_serializer = SmartSerializer(sensitive_fields=('password', 'api_key', 'secret'))
    user_data = {
        'username': 'john_doe',
        'password': 'super_secret_123',
        'email': 'john@example.com',
        'api_key': 'sk-1234567890abcdef',
        'profile': {
            'name': 'John Doe',
            'secret_token': 'xyz789'
        }
    }
    print(f"   User data: {sensitive_serializer.serialize(user_data)}")
    print()
    
    # 8. Truncation
    print("8. Truncation (max_repr=50):")
    truncate_serializer = SmartSerializer(max_repr=50)
    long_string = "This is a very long string that will be truncated because it exceeds the maximum representation length"
    print(f"   Long string: {truncate_serializer.serialize(long_string)}")
    print()
    
    # 9. Custom objects
    print("9. Custom Objects:")
    class Person:
        def __init__(self, name, age):
            self.name = name
            self.age = age
        
        def __repr__(self):
            return f"Person(name={self.name!r}, age={self.age})"
    
    person = Person("Alice", 25)
    print(f"   Custom object: {serializer.serialize(person)}")
    
    class SimpleClass:
        pass
    
    simple = SimpleClass()
    print(f"   Simple object: {serializer.serialize(simple)}")
    print()
    
    # 10. Edge cases
    print("10. Edge Cases:")
    print(f"   Empty list: {serializer.serialize([])}")
    print(f"   Empty dict: {serializer.serialize({})}")
    print(f"   Bytes: {serializer.serialize(b'binary data')}")
    print(f"   Unicode: {serializer.serialize('Hello 世界 🌍')}")
    print()
    
    print("=== SmartSerializer Demo Complete ===")


if __name__ == "__main__":
    demo_serializer() 