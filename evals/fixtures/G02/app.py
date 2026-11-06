def request(payload):
    try: return perform(payload)
    except Exception: return None

def perform(payload):
    return payload
