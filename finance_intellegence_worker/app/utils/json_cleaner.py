import math

import numpy as np
import pandas as pd


def clean_json(obj):
    if obj is None:
        return None

    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj

    if isinstance(obj, np.integer):
        return int(obj)

    if isinstance(obj, np.floating):
        value = float(obj)
        if math.isnan(value) or math.isinf(value):
            return None
        return value

    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()

    if isinstance(obj, dict):
        return {
            str(key): clean_json(value)
            for key, value in obj.items()
        }

    if isinstance(obj, list):
        return [
            clean_json(item)
            for item in obj
        ]

    return obj