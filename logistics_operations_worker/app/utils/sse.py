import json


def sse_event(event: str, data: dict):
    return {
        "event": event,
        "data": json.dumps(data, default=str),
    }