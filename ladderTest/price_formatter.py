def decimal_to_tt_bond_format(decimal_price):
    """
    Converts a decimal price to the TT bond style string format (e.g., 110.015625 -> "110'005").
    This format represents prices in terms of whole points and 32nds, with a final digit
    indicating a half of a 32nd (i.e., 64ths of a point).

    Args:
        decimal_price (float): The price as a decimal number.

    Returns:
        str: The price formatted as a TT bond style string.
    """
    if not isinstance(decimal_price, (int, float)):
        raise TypeError("Input price must be a number.")

    whole_part = int(decimal_price)
    
    # Calculate total sixty-fourths for the fractional part
    # Add a small epsilon to handle potential floating point representation issues before rounding
    # E.g., if decimal_price = 110.01562499999, fractional_value might be slightly less than 0.015625.
    # Multiplying by 64 and then rounding handles this robustly.
    fractional_value = decimal_price - whole_part
    
    # Total number of 1/64ths in the fractional part of the price
    # E.g., if price is 110.015625 (110 and 1/64), num_sixty_fourths = 1
    # E.g., if price is 110.03125 (110 and 2/64 or 1/32), num_sixty_fourths = 2
    # E.g., if price is 110.046875 (110 and 3/64), num_sixty_fourths = 3
    num_sixty_fourths = round(fractional_value * 64.0)

    # Number of full 32nds
    # E.g., 1/64 -> 0 full 32nds. 2/64 -> 1 full 32nd. 3/64 -> 1 full 32nd.
    num_full_32nds = int(num_sixty_fourths // 2)
    
    # Check if there is an extra half of a 32nd (i.e., an odd number of 64ths)
    # E.g., 1/64 -> has_half_32nd_extra = 1. 2/64 -> has_half_32nd_extra = 0. 3/64 -> has_half_32nd_extra = 1.
    has_half_32nd_extra = int(num_sixty_fourths % 2)
    
    # Format: WHOLE'XXY where XX is num_full_32nds (0-padded) and Y is 0 or 5
    # Example: 110 and 1/64 -> 110, num_full_32nds=0, has_half=1 -> "110'005"
    # Example: 110 and 2/64 (1/32) -> 110, num_full_32nds=1, has_half=0 -> "110'010"
    # Example: 110 and 3/64 -> 110, num_full_32nds=1, has_half=1 -> "110'015"
    return f"{whole_part}'{num_full_32nds:02d}{5 if has_half_32nd_extra else 0}"

if __name__ == '__main__':
    # Test cases
    test_prices = {
        110.0: "110'000",
        110.015625: "110'005",  # 1/64
        110.03125:  "110'010",  # 2/64 or 1/32
        110.046875: "110'015",  # 3/64
        110.078125: "110'025",  # 5/64 (2.5 / 32)
        110.140625: "110'045",  # 9/64 (4.5 / 32)
        110.171875: "110'055",  # 11/64 (5.5 / 32)
        110.296875: "110'095",  # 19/64 (9.5 / 32)
        110.3125:   "110'100",  # 20/64 (10 / 32)
        109.984375: "109'315",  # 109 + 63/64 (31.5 / 32)
        109.875:    "109'280",  # 109 + 56/64 (28 / 32)
        0.0: "0'000",
        0.015625: "0'005",
        1.0: "1'000",
        1.5: "1'160", # 1 + 32/64
        1.515625: "1'165" # 1 + 33/64
    }
    
    all_tests_passed = True
    for decimal, expected_str in test_prices.items():
        result = decimal_to_tt_bond_format(decimal)
        if result == expected_str:
            print(f"PASSED: {decimal} -> {result}")
        else:
            print(f"FAILED: {decimal} -> {result} (Expected: {expected_str})")
            all_tests_passed = False
    
    if all_tests_passed:
        print("\nAll test cases passed!")
    else:
        print("\nSome test cases failed.") 