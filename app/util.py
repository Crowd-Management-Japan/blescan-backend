
from typing import List, Dict, Union
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

def compact_string_to_int_list(s: str) -> List[int]:
    """
    Decode a string of ints of form: 40,41,42-45
    where integers can either be separated by commas or a range is given.
    """
    result = []
    
    elements = s.split(',')
    
    for element in elements:
        if '-' in element:
            start, end = map(int, element.split('-'))
            result.extend(range(start, end + 1))
        else:
            result.append(int(element))
    
    return result

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

def location_dict_to_string(loc: Dict) -> str:
    """
    Create the String format for the textfield of the setup page.
    It contains one line per device, formatted like 'id: lat, lon'
    """
    return "\n".join([f"{id}: {l}" for id, l in loc.items()])

def combination_array_to_string(comb: List) -> str:
    return '\n'.join([','.join(map(str, id)) for id in comb])

def float_or_None(value: str) -> Union[float,None]:
    """
    Cast a string value to a float if possible. If not, return None
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return None
    