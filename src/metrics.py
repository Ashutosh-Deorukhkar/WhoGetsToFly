# src/metrics.py
import numpy as np
from .models import AirlineType

def adj_pairs(slot_indices: np.ndarray) -> int:
    """
    slot_indices: sorted array of slot indices (0..m-1) for one airline.
    AdjPairs(S) = count of consecutive pairs in S.
    """
    if slot_indices.size <= 1:
        return 0
    return int(np.sum(slot_indices[1:] == slot_indices[:-1] + 1))

def value_of_bundle(t: AirlineType, slot_idx_set: np.ndarray) -> float:
    """
    v_i(S) = sum_{s in S} a_i(s) + beta_i * AdjPairs(S) - lam_i * max(0, |S|-k_i)^2
    """
    if slot_idx_set.size == 0:
        return 0.0

    s = np.array(slot_idx_set, dtype=int)
    s.sort()

    base = float(np.sum(t.a[s]))
    bonus = float(t.beta * adj_pairs(s))
    excess = max(0, int(s.size) - int(t.k))
    penalty = float(t.lam * (excess ** 2))
    return base + bonus - penalty

def total_welfare(types: list[AirlineType], alloc_sets: list[np.ndarray]) -> float:
    return float(sum(value_of_bundle(types[i], alloc_sets[i]) for i in range(len(types))))

def airline_utilities(types: list[AirlineType], alloc_sets: list[np.ndarray], payments: np.ndarray) -> np.ndarray:
    u = np.zeros(len(types), dtype=float)
    for i in range(len(types)):
        u[i] = value_of_bundle(types[i], alloc_sets[i]) - float(payments[i])
    return u

def alloc_hhi(alloc_sets: list[np.ndarray]) -> float:
    counts = np.array([len(s) for s in alloc_sets], dtype=float)
    total = float(np.sum(counts))
    if total <= 0:
        return 0.0
    shares = counts / total
    return float(np.sum(shares ** 2))

def fairness_1_minus_hhi(alloc_sets: list[np.ndarray]) -> float:
    return 1.0 - alloc_hhi(alloc_sets)