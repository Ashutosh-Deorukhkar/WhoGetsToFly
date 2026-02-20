import numpy as np

from .models import sample_marginal_values, truthful_bids_from_values
from .mechanisms import (
    uniform_price_auction,
    discriminatory_price_auction,
    welfare_maximizing_allocation,
)
from .metrics import total_value, fairness_1_minus_hhi
from .equilibrium import solve_symmetric_alpha_per_unit


def run_one_scenario(
    n_airlines: int,
    m_slots: int,
    max_demand: int,
    seed: int = 0,
    bidding_mode: str = "truthful", 
    n_mc: int = 12,
    n_passes: int = 3,
):
    rng = np.random.default_rng(seed)
    values = sample_marginal_values(n_airlines, max_demand, rng)

    # Bidding 
    if bidding_mode == "truthful":
        bids_u = truthful_bids_from_values(values)
        bids_d = truthful_bids_from_values(values)

        uniform_alpha_vec = np.ones(max_demand, dtype=float)
        disc_alpha_vec = np.ones(max_demand, dtype=float)
        uniform_eq_gap = 0.0
        disc_eq_gap = 0.0

    elif bidding_mode == "strategic":
        uniform_alpha_vec, uniform_eq_gap = solve_symmetric_alpha_per_unit(
            mechanism_fn=uniform_price_auction,
            n_airlines=n_airlines,
            m_slots=m_slots,
            max_demand=max_demand,
            rng=rng,
            n_mc=n_mc,
            n_passes=n_passes,
        )

        disc_alpha_vec, disc_eq_gap = solve_symmetric_alpha_per_unit(
            mechanism_fn=discriminatory_price_auction,
            n_airlines=n_airlines,
            m_slots=m_slots,
            max_demand=max_demand,
            rng=rng,
            n_mc=n_mc,
            n_passes=n_passes,
        )

        # Apply per-unit shading: bids[i,j] = alpha_j * values[i,j]
        bids_u = values * uniform_alpha_vec[None, :]
        bids_d = values * disc_alpha_vec[None, :]

    else:
        raise ValueError(f"Unknown bidding_mode={bidding_mode}. Use 'truthful' or 'strategic'.")

    # Mechanisms 
    alloc_u, pay_u, info_u = uniform_price_auction(bids_u, m_slots)
    alloc_d, pay_d, info_d = discriminatory_price_auction(bids_d, m_slots)
    alloc_w, winners_w = welfare_maximizing_allocation(values, m_slots)

    # Metrics
    out = {
        "n_airlines": n_airlines,
        "m_slots": m_slots,
        "max_demand": max_demand,
        "bidding_mode": bidding_mode,

        "uniform_eff": total_value(values, alloc_u),
        "uniform_rev": float(pay_u.sum()),
        "uniform_price": info_u["clearing_price"],
        "uniform_fair": fairness_1_minus_hhi(alloc_u),

        "disc_eff": total_value(values, alloc_d),
        "disc_rev": float(pay_d.sum()),
        "disc_price": info_d["clearing_price"],
        "disc_fair": fairness_1_minus_hhi(alloc_d),

        "welfare_eff": total_value(values, alloc_w),
        "welfare_fair": fairness_1_minus_hhi(alloc_w),
    }

    out["uniform_alpha"] = float(np.mean(uniform_alpha_vec))
    out["disc_alpha"] = float(np.mean(disc_alpha_vec))
    out["uniform_eq_gap"] = float(uniform_eq_gap)
    out["disc_eq_gap"] = float(disc_eq_gap)

    # Add per-unit alphas for debugging/analysis (alpha0..alpha4)
    for j in range(max_demand):
        out[f"uniform_alpha{j}"] = float(uniform_alpha_vec[j])
        out[f"disc_alpha{j}"] = float(disc_alpha_vec[j])

    return out