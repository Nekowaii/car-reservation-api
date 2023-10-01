import math


def total_minutes(transfer_time):
    return math.ceil(transfer_time.total_seconds() / 60)
