def time_in_range(start, end, x):
    if start <= end:
        return start <= x <= end
    else:
        return start <= x or x <= end
