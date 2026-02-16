import numpy as np

def sample_marginal_values(n_airlines: int, max_demand: int, rng: np.random.Generator,
                           base_scale: float = 100.0, diminishing: float = 0.85):
    """
    Returns values[i, j] = airline i's marginal value for its (j+1)-th slot.
    Diminishing returns enforced by geometric decay.
    """
    base = rng.lognormal(mean=np.log(base_scale), sigma=0.4, size=(n_airlines, 1))
    steps = np.arange(max_demand)[None, :]
    values = base * (diminishing ** steps)
    noise = rng.normal(0, base_scale * 0.05, size=values.shape)
    values = np.maximum(values + noise, 0.0)
    return values

def truthful_bids_from_values(values: np.ndarray):
    """Truthful bidding for marginal values."""
    return values.copy()