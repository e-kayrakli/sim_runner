import math

def list_stddev(lst):
    if len(lst) == 0:
        return None
    average = list_average(lst)
    diff_sum = sum([(i - average)**2 for i in lst])
    return math.sqrt(diff_sum / len(lst))


def list_average(lst):
    if len(lst) == 0:
        return None

    return float(sum(lst)) / len(lst)

def list_median(lst):
    l = len(lst)
    if l == 0:
        return None
    else:
        lst.sort()
        return lst[int(l/2)]

def list_max(lst):
    if lst:
        return max(lst)
    return None

def list_min(lst):
    if lst:
        return min(lst)
    return None

