import numpy as np
from .models import sample_marginal_values
from .metrics import airline_utilities

def _sample_profiles(
    n_airlines: int,
    max_demand: int,
    rng: np.random.Generator,
    n_mc: int,
) -> np.ndarray:
    """
    Returns an array of sampled value profiles with shape:
        (n_mc, n_airlines, max_demand)
    """
    profiles = np.empty((n_mc, n_airlines, max_demand), dtype=float)
    for t in range(n_mc):
        profiles[t] = sample_marginal_values(n_airlines, max_demand, rng)
    return profiles


def _eu_deviator_per_unit_on_profiles(
    mechanism_fn,
    profiles: np.ndarray,        
    m_slots: int,
    alpha_other: np.ndarray,    
    j: int,
    alpha_j_i: float,
) -> float:
    """
    Expected utility of deviator (airline 0) when only coordinate j differs,
    evaluated on a fixed set of sampled profiles (CRN).
    """
    T, n, K = profiles.shape
    alpha_other = np.asarray(alpha_other, dtype=float)

    utils = np.empty(T, dtype=float)
    for t in range(T):
        values = profiles[t]

        bids = values * alpha_other[None, :]
        bids[0, j] = float(alpha_j_i) * values[0, j]

        alloc, payments, _info = mechanism_fn(bids, m_slots)
        u = airline_utilities(values, alloc, payments)[0]
        utils[t] = float(u)

    return float(np.mean(utils))


def solve_symmetric_alpha_per_unit(
    mechanism_fn,
    n_airlines: int,
    m_slots: int,
    max_demand: int,
    rng: np.random.Generator,
    alpha_grid: np.ndarray | None = None,
    n_mc: int = 20,        
    n_passes: int = 4,     
    tol: float = 1e-3,
    damping: float = 0.6,
    n_mc_eval: int = 80,   
):
    """
    Per-unit symmetric strategy class:
        b_{i,j} = alpha_j * v_{i,j}

    Approx equilibrium via damped coordinate best response using CRN
    (same sampled profiles for all candidate alpha_j in a step).

    Returns:
        alpha_vec: (K,)
        eq_gap: max single-coordinate profitable deviation gain at final alpha_vec
    """
    if alpha_grid is None:
        alpha_grid = np.linspace(0.4, 1.0, 13)  

    alpha_grid = np.asarray(alpha_grid, dtype=float)
    damping = float(np.clip(damping, 0.0, 1.0))

    alpha = np.ones(max_demand, dtype=float)

    for _ in range(n_passes):
        alpha_prev = alpha.copy()

        for j in range(max_demand):
            profiles = _sample_profiles(n_airlines, max_demand, rng, n_mc)

            eus = []
            for a_j in alpha_grid:
                eus.append(
                    _eu_deviator_per_unit_on_profiles(
                        mechanism_fn=mechanism_fn,
                        profiles=profiles,
                        m_slots=m_slots,
                        alpha_other=alpha,
                        j=j,
                        alpha_j_i=float(a_j),
                    )
                )

            a_br = float(alpha_grid[int(np.argmax(eus))])
            alpha[j] = (1.0 - damping) * alpha[j] + damping * a_br

        if float(np.max(np.abs(alpha - alpha_prev))) < tol:
            break

    gaps = []
    for j in range(max_demand):
        profiles_eval = _sample_profiles(n_airlines, max_demand, rng, n_mc_eval)

        eus_eval = []
        for a_j in alpha_grid:
            eus_eval.append(
                _eu_deviator_per_unit_on_profiles(
                    mechanism_fn=mechanism_fn,
                    profiles=profiles_eval,
                    m_slots=m_slots,
                    alpha_other=alpha,
                    j=j,
                    alpha_j_i=float(a_j),
                )
            )

        best_eu = float(np.max(eus_eval))
        stay_idx = int(np.argmin(np.abs(alpha_grid - alpha[j])))
        stay_eu = float(eus_eval[stay_idx])
        gaps.append(best_eu - stay_eu)

    eq_gap = float(np.max(gaps)) if gaps else 0.0
    return alpha, eq_gap