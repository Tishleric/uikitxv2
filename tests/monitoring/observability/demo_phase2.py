"""Demo script for Phase 2 monitor decorator functionality"""

import time
from lib.monitoring.decorators import monitor


@monitor(process_group="demo.calculations")
def calculate_sum(numbers):
    """Calculate sum of numbers"""
    return sum(numbers)


@monitor(process_group="demo.calculations")
def calculate_average(numbers):
    """Calculate average with sum reuse"""
    total = calculate_sum(numbers)
    return total / len(numbers) if numbers else 0


@monitor(process_group="demo.api")
def simulate_api_call(endpoint, delay=0.1):
    """Simulate an API call with configurable delay"""
    time.sleep(delay)
    return f"Response from {endpoint}"


@monitor(process_group="demo.errors")
def risky_operation(value):
    """Demonstrate error handling"""
    if value < 0:
        raise ValueError("Value must be non-negative")
    return value ** 0.5


def main():
    print("=== Phase 2 Monitor Decorator Demo ===\n")
    
    # Demo 1: Simple function monitoring
    print("1. Simple calculation:")
    numbers = [1, 2, 3, 4, 5]
    result = calculate_sum(numbers)
    print(f"   Result: {result}\n")
    
    # Demo 2: Nested function calls
    print("2. Nested function calls:")
    avg = calculate_average(numbers)
    print(f"   Average: {avg}\n")
    
    # Demo 3: Timing measurement
    print("3. API simulation with timing:")
    response = simulate_api_call("/users", delay=0.25)
    print(f"   {response}\n")
    
    # Demo 4: Error handling
    print("4. Error handling:")
    try:
        result = risky_operation(16)
        print(f"   Success: sqrt(16) = {result}")
    except:
        pass
    
    try:
        result = risky_operation(-4)
    except ValueError:
        print("   Error was handled correctly\n")
    
    # Demo 5: Multiple quick calls
    print("5. Performance test with multiple calls:")
    for i in range(3):
        calculate_sum(list(range(i * 10, (i + 1) * 10)))
    
    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    main() 

import time
from lib.monitoring.decorators import monitor


@monitor(process_group="demo.calculations")
def calculate_sum(numbers):
    """Calculate sum of numbers"""
    return sum(numbers)


@monitor(process_group="demo.calculations")
def calculate_average(numbers):
    """Calculate average with sum reuse"""
    total = calculate_sum(numbers)
    return total / len(numbers) if numbers else 0


@monitor(process_group="demo.api")
def simulate_api_call(endpoint, delay=0.1):
    """Simulate an API call with configurable delay"""
    time.sleep(delay)
    return f"Response from {endpoint}"


@monitor(process_group="demo.errors")
def risky_operation(value):
    """Demonstrate error handling"""
    if value < 0:
        raise ValueError("Value must be non-negative")
    return value ** 0.5


def main():
    print("=== Phase 2 Monitor Decorator Demo ===\n")
    
    # Demo 1: Simple function monitoring
    print("1. Simple calculation:")
    numbers = [1, 2, 3, 4, 5]
    result = calculate_sum(numbers)
    print(f"   Result: {result}\n")
    
    # Demo 2: Nested function calls
    print("2. Nested function calls:")
    avg = calculate_average(numbers)
    print(f"   Average: {avg}\n")
    
    # Demo 3: Timing measurement
    print("3. API simulation with timing:")
    response = simulate_api_call("/users", delay=0.25)
    print(f"   {response}\n")
    
    # Demo 4: Error handling
    print("4. Error handling:")
    try:
        result = risky_operation(16)
        print(f"   Success: sqrt(16) = {result}")
    except:
        pass
    
    try:
        result = risky_operation(-4)
    except ValueError:
        print("   Error was handled correctly\n")
    
    # Demo 5: Multiple quick calls
    print("5. Performance test with multiple calls:")
    for i in range(3):
        calculate_sum(list(range(i * 10, (i + 1) * 10)))
    
    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    main() 