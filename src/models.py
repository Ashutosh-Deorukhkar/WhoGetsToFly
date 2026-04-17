# src/models.py
# defines: ai(s), betai, ki,

import numpy as np
from dataclasses import dataclass

@dataclass(frozen=True)
class AirlineType:
    a: np.ndarray          # a_i(s) for each slot index s=0..m-1
    beta: float            # beta_i
    k: int                 # k_i
    lam: float             # lambda_i
    kind: str              # "hub" or "p2p" (for reporting)

def generate_slots(start_hour: int = 8, end_hour: int = 18) -> np.ndarray:
    """
    Returns an array of slot 'times' (integers). Example: 8..17 for 8am-6pm (10 slots).
    """
    return np.arange(start_hour, end_hour, dtype=int)

def sample_airline_types(
    n_airlines: int,
    slots: np.ndarray,
    rng: np.random.Generator,
    base_dist: str = "normal",        # "normal" or "uniform"
    base_scale: float = 100.0,
    hub_frac: float = 0.5,
    eta_range=(0.1, 0.5),
):
    """
    Generates airline private parameters:
      - a_i(s): base per-slot values
      - beta_i = rho_i * mean(a_i)
      - k_i chosen by airline size class
      - lambda_i = eta_i * mean(a_i)
    """
    m = len(slots)
    types = []

    # assign hub vs p2p
    is_hub = rng.random(n_airlines) < hub_frac

    # size classes determine k_i
    # (simple and defendable; not per-day/peak)
    def sample_k():
        r = rng.random()
        if r < 0.34:
            return int(rng.choice([1, 2]))  # small
        elif r < 0.67:
            return int(rng.choice([2, 3]))  # medium
        else:
            return int(rng.choice([3, 4]))  # large

    for i in range(n_airlines):
        # base per-slot values a_i(s)
        if base_dist == "uniform":
            a = rng.uniform(0.0, base_scale, size=m)
        else:
            # normal with truncation at 0
            a = rng.normal(loc=0.6 * base_scale, scale=0.25 * base_scale, size=m)
            a = np.maximum(a, 0.0)

        a_bar = float(np.mean(a))

        # rho depends on hub vs p2p
        if is_hub[i]:
            rho = float(rng.uniform(0.6, 1.0))
            kind = "hub"
        else:
            rho = float(rng.uniform(0.0, 0.4))
            kind = "p2p"

        beta = rho * a_bar

        k = sample_k()

        eta = float(rng.uniform(*eta_range))
        lam = eta * a_bar

        types.append(AirlineType(a=a, beta=beta, k=k, lam=lam, kind=kind))

    return types