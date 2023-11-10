
from typing import List

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