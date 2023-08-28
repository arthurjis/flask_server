
def get_int_value(payload, key, default_value):
    value = payload.get(key, default_value)
    try:
        return int(value)
    except ValueError:
        return default_value
    
def get_float_value(payload, key, default_value):
    value = payload.get(key, default_value)
    try:
        return float(value)
    except ValueError:
        return default_value

