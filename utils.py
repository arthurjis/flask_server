import json
from bson.objectid import ObjectId
from datetime import datetime
 


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

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime):
            return o.isoformat() 
        return json.JSONEncoder.default(self, o)
