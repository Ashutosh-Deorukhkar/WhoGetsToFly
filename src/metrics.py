import numpy as np

def total_value(values: np.ndarray, alloc: np.ndarray):
    # values are marginal values; alloc[i] slots => sum first alloc[i] marginals
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
