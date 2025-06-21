"""Test script for variable-level tracking in Observatory Dashboard"""

import time
from typing import Tuple, NamedTuple
from dataclasses import dataclass
from collections import namedtuple

from lib.monitoring.decorators import monitor, start_observatory_writer, stop_observatory_writer


# Test 1: Simple function with positional args
@monitor()
def add(x: int, y: int) -> int:
    """Add two numbers"""
    return x + y


# Test 2: Function with default values
@monitor()
def greet(name: str, greeting: str = "Hello") -> str:
    """Greet someone"""
    return f"{greeting}, {name}!"


# Test 3: Function with multiple return values
@monitor()
def divmod_custom(dividend: int, divisor: int) -> Tuple[int, int]:
    """Divide and return quotient and remainder"""
    quotient = dividend // divisor
    remainder = dividend % divisor
    return quotient, remainder


# Test 4: Named tuple return
Point = namedtuple('Point', ['x', 'y'])

@monitor()
def get_point(x_val: int, y_val: int) -> Point:
    """Return a Point named tuple"""
    return Point(x=x_val, y=y_val)


# Test 5: Dataclass return
@dataclass
class User:
    name: str
    age: int
    email: str


@monitor()
def create_user(name: str, age: int, email: str) -> User:
    """Create a User dataclass"""
    return User(name=name, age=age, email=email)


# Test 6: Dictionary return
@monitor()
def get_stats(numbers: list) -> dict:
    """Calculate statistics"""
    return {
        'count': len(numbers),
        'sum': sum(numbers),
        'mean': sum(numbers) / len(numbers) if numbers else 0,
        'min': min(numbers) if numbers else None,
        'max': max(numbers) if numbers else None
    }


# Test 7: Variable args
@monitor()
def sum_all(*numbers: int) -> int:
    """Sum all numbers"""
    return sum(numbers)


# Test 8: Keyword args
@monitor()
def config_server(**settings) -> dict:
    """Configure server with settings"""
    defaults = {'host': 'localhost', 'port': 8080}
    defaults.update(settings)
    return defaults


# Test 9: Class method
class Calculator:
    def __init__(self, precision: int = 2):
        self.precision = precision
    
    @monitor()
    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers"""
        return round(a * b, self.precision)


# Test 10: Error case
@monitor()
def divide(a: int, b: int) -> float:
    """Divide a by b (may raise ZeroDivisionError)"""
    return a / b


# Test 11: Mixed args and kwargs
@monitor()
def mixed_params(required: str, *args, optional: str = "default", **kwargs) -> dict:
    """Function with mixed parameter types"""
    return {
        'required': required,
        'args': args,
        'optional': optional,
        'kwargs': kwargs
    }


# Test 12: Lambda function (via decorator)
square = monitor()(lambda x: x ** 2)


def run_tests():
    """Run all test functions and display results"""
    print("Starting variable-level tracking tests...")
    print("=" * 60)
    
    # Start the observatory writer
    start_observatory_writer("logs/test_variable_tracking.db")
    time.sleep(0.2)  # Give writer time to start
    
    try:
        # Test 1: Simple function
        print("\n1. Simple function:")
        result = add(5, 3)
        print(f"   add(5, 3) = {result}")
        
        # Test 2: Function with defaults
        print("\n2. Function with defaults:")
        result = greet("Alice")
        print(f"   greet('Alice') = {result}")
        result = greet("Bob", "Hi")
        print(f"   greet('Bob', 'Hi') = {result}")
        
        # Test 3: Multiple return values
        print("\n3. Multiple return values:")
        result = divmod_custom(17, 5)
        print(f"   divmod_custom(17, 5) = {result}")
        
        # Test 4: Named tuple return
        print("\n4. Named tuple return:")
        result = get_point(10, 20)
        print(f"   get_point(10, 20) = {result}")
        
        # Test 5: Dataclass return
        print("\n5. Dataclass return:")
        result = create_user("John Doe", 30, "john@example.com")
        print(f"   create_user(...) = {result}")
        
        # Test 6: Dictionary return
        print("\n6. Dictionary return:")
        result = get_stats([1, 2, 3, 4, 5])
        print(f"   get_stats([1, 2, 3, 4, 5]) = {result}")
        
        # Test 7: Variable args
        print("\n7. Variable args:")
        result = sum_all(1, 2, 3, 4, 5)
        print(f"   sum_all(1, 2, 3, 4, 5) = {result}")
        
        # Test 8: Keyword args
        print("\n8. Keyword args:")
        result = config_server(host='192.168.1.1', port=9000, debug=True)
        print(f"   config_server(host='192.168.1.1', ...) = {result}")
        
        # Test 9: Class method
        print("\n9. Class method:")
        calc = Calculator(precision=3)
        result = calc.multiply(3.14159, 2.71828)
        print(f"   calc.multiply(3.14159, 2.71828) = {result}")
        
        # Test 10: Error case
        print("\n10. Error case:")
        try:
            result = divide(10, 0)
        except ZeroDivisionError:
            print("   divide(10, 0) raised ZeroDivisionError (as expected)")
        
        # Test 11: Mixed parameters
        print("\n11. Mixed parameters:")
        result = mixed_params("required_value", 1, 2, 3, optional="custom", key1="val1", key2="val2")
        print(f"   mixed_params(...) = {result}")
        
        # Test 12: Lambda function
        print("\n12. Lambda function:")
        result = square(7)
        print(f"   square(7) = {result}")
        
    finally:
        # Give writer time to flush
        time.sleep(0.5)
        
        # Stop the writer
        stop_observatory_writer()
        
        print("\n" + "=" * 60)
        print("Tests completed! Check logs/test_variable_tracking.db")
        print("\nExpected behavior:")
        print("- Each parameter should have its own row in data_trace table")
        print("- Parameters should show actual names (x, y) not generic (arg_0, arg_1)")
        print("- Return values should be properly named based on their type")
        print("- Named tuples should show field names")
        print("- Dataclasses should show attribute names")
        print("- Dictionaries should show key names")


if __name__ == "__main__":
    run_tests() 