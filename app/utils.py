
from datetime import datetime, date
import decimal

def serialize_data(data):
    """
    Recursively serializes data to be JSON compatible.
    Handles:
    - datetime/date -> ISO format string
    - decimal.Decimal -> float
    - list/dict -> recursion
    """
    if isinstance(data, list):
        return [serialize_data(x) for x in data]
    if isinstance(data, dict):
        return {k: serialize_data(v) for k, v in data.items()}
    if isinstance(data, (datetime, date)):
        return data.isoformat()
    if isinstance(data, decimal.Decimal):
        return float(data)
    return data
