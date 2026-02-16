import numpy as np

from .models import sample_marginal_values, truthful_bids_from_values
from .mechanisms import uniform_price_auction, discriminatory_price_auction, welfare_maximizing_allocation
from .metrics import total_value


def run_one_scenario(n_airlines: int, m_slots: int, max_demand: int, seed: int = 0):
    rng = np.random.default_rng(seed)
    values = sample_marginal_values(n_airlines, max_demand, rng)

    # Baseline: truthful bids
    bids = truthful_bids_from_values(values)

    # Mechanisms
    alloc_u, pay_u, info_u = uniform_price_auction(bids, m_slots)
    alloc_d, pay_d, info_d = discriminatory_price_auction(bids, m_slots)
    alloc_w, winners_w = welfare_maximizing_allocation(values, m_slots)

    # Metrics
    out = {
        "n_airlines": n_airlines,
        "m_slots": m_slots,
        "max_demand": max_demand,

        "uniform_eff": total_value(values, alloc_u),
        "uniform_rev": float(pay_u.sum()),
        "uniform_price": info_u["clearing_price"],

        "disc_eff": total_value(values, alloc_d),
        "disc_rev": float(pay_d.sum()),
        "disc_price": info_d["clearing_price"],

        "welfare_eff": total_value(values, alloc_w),  # benchmark welfare
    }
    return out