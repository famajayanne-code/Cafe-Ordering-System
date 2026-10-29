def merge_sort(items, key="name"):
    """Return a new list sorted by key, using a manually implemented merge sort."""
    if len(items) <= 1:
        return list(items)
    middle = len(items) // 2
    left = merge_sort(items[:middle], key)
    right = merge_sort(items[middle:], key)
    return _merge(left, right, key)

def _merge(left, right, key):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i][key] <= right[j][key]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result

def binary_search_by_id(sorted_items, target_id):
    """Binary search over items sorted by ascending numeric ID."""
    low, high = 0, len(sorted_items) - 1
    while low <= high:
        middle = (low + high) // 2
        current_id = sorted_items[middle]["id"]
        if current_id == target_id:
            return sorted_items[middle]
        if current_id < target_id:
            low = middle + 1
        else:
            high = middle - 1
    return None
