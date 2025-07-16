def decimal_to_32nds(price: float) -> str:
    whole = int(price)
    fraction = (price - whole) * 32
    return f"{whole}-{int(fraction):02d}"

def price_to_decimal(price_str: str) -> float:
    if isinstance(price_str, (int, float)):
        return float(price_str)
    price_str = str(price_str).strip()
    if '.' in price_str and '-' not in price_str:
        return float(price_str)
    if '-' in price_str:
        parts = price_str.split('-')
        if len(parts) != 2:
            raise ValueError(f"Invalid 32nds format: {price_str}")
        return float(parts[0]) + float(parts[1]) / 32
    return float(price_str)
