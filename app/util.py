
from typing import List, Dict
import logging

def compact_int_list_string(lst: List[int]) -> str:
    if not lst:
        return ""

    lst.sort()
    result = []
    start = end = lst[0]

    for i in range(1, len(lst)):
        if lst[i] == end + 1:
            # Continue the current interval
            end = lst[i]
        else:
            # Add the interval or single number to the result
            result.append(f"{start}-{end}" if start != end else str(start))
            start = end = lst[i]

    # Add the last interval or single number to the result
    result.append(f"{start}-{end}" if start != end else str(start))

    return ','.join(result)

def dict_strict_deep_update(d1: Dict, d2: Dict):
    """
    Use the dict.update method for updating nested dicts.
    If a field in dict 1 is a dict itself, it will be updated deeply.

    This method will not add any fields!
    It just updates existing fields
    """
    cpy = {}
    for k, v in d1.items():
        # only add fields to cpy, that are not a dict, and present in d1
        # we don't want to add fields of d2
        if type(v) == type({}):
            dict_strict_deep_update(v, d2.get(k, {}))
        else:
            cpy[k] = d2.get(k, d1[k])

    d1.update(cpy)