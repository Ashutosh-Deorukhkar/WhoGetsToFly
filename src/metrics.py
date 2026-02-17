import numpy as np

def total_value(values: np.ndarray, alloc: np.ndarray):
    tv = 0.0
    for i, a in enumerate(alloc):
        if a > 0:
            tv += float(values[i, :a].sum())
    return tv

def airline_utilities(values: np.ndarray, alloc: np.ndarray, payments: np.ndarray):
    utils = np.zeros_like(payments, dtype=float)
    for i, a in enumerate(alloc):
        v = float(values[i, :a].sum()) if a > 0 else 0.0
        utils[i] = v - float(payments[i])
    return utils

def alloc_hhi(alloc: np.ndarray) -> float:
    total = float(np.sum(alloc))
    if total <= 0:
        return 0.0
    shares = alloc.astype(float) / total
    return float(np.sum(shares ** 2))

def fairness_1_minus_hhi(alloc: np.ndarray) -> float:
    """
    Fairness score in [0, 1 - 1/n] (when total allocation > 0).
    Higher = more equal allocation across airlines.
    """
    return 1.0 - alloc_hhi(alloc)