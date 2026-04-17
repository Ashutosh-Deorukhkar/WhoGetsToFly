# src/simulator.py
import numpy as np
from .models import generate_slots, sample_airline_types
from .mechanisms import (
    sequential_first_price,
    interval_pay_as_bid,
    vcg_interval,
    vcg_combinatorial,
)
from .metrics import total_welfare, fairness_1_minus_hhi, value_of_bundle
from .equilibrium import solve_alpha_sequential_fp, solve_alpha_interval


def run_one_scenario(
    n_airlines: int,
    start_hour: int = 8,
    end_hour: int = 18,
    cap_per_airline: int = 3,
    seed: int = 0,
    bidding_mode: str = "truthful",
    max_interval_len: int = 3,
) -> dict:
    """
    Run one simulation scenario under a given bidding mode.

    Mechanisms:
      1) Sequential First-Price (SFP)
      2) Interval Pay-As-Bid (PAB)
      3) Interval VCG benchmark (restricted language)
      4) Full Combinatorial VCG benchmark (all subsets, CP-SAT)

    Bidding modes:
      truthful  - airlines bid true valuations (alpha = 1.0)
      strategic - alpha found via simulation-based best-response dynamics

    Note: Full combinatorial VCG is always truthful by design (IC mechanism).

    Returns a dict of metrics for all four mechanisms.
    """
    rng = np.random.default_rng(seed)
    slots = generate_slots(start_hour, end_hour)
    m_slots = len(slots)

    types = sample_airline_types(n_airlines, slots=np.arange(m_slots), rng=rng)

    # ─────────────────────────────
    # 1) Sequential First-Price
    # ─────────────────────────────
    if bidding_mode == "truthful":
        alpha_seq, eq_gap_seq = 1.0, 0.0
    else:
        alpha_seq, eq_gap_seq = solve_alpha_sequential_fp(
            n_airlines=n_airlines,
            m_slots=m_slots,
            rng=rng,
            cap_per_airline=cap_per_airline,
        )

    bids_seq = np.vstack([alpha_seq * t.a for t in types])
    alloc_seq, pay_seq, _ = sequential_first_price(
        bids_seq, cap_per_airline=cap_per_airline
    )

    # ─────────────────────────────────────────────
    # 2) Interval bids (shared by PAB and interval VCG)
    # ─────────────────────────────────────────────
    if bidding_mode == "truthful":
        alpha_int, eq_gap_int = 1.0, 0.0
    else:
        alpha_int, eq_gap_int = solve_alpha_interval(
            n_airlines=n_airlines,
            m_slots=m_slots,
            rng=rng,
            cap_per_airline=cap_per_airline,
            max_interval_len=max_interval_len,
        )

    intervals = [
        (l, r)
        for l in range(m_slots)
        for r in range(l, min(m_slots, l + max_interval_len))
    ]

    bids_for_intervals = []
    for t in types:
        d = {}
        for (l, r) in intervals:
            bundle = np.arange(l, r + 1, dtype=int)
            d[(l, r)] = float(alpha_int) * float(value_of_bundle(t, bundle))
        bids_for_intervals.append(d)

    alloc_int, pay_int, _ = interval_pay_as_bid(
        types=types,
        bids_for_intervals=bids_for_intervals,
        m_slots=m_slots,
        max_interval_len=max_interval_len,
        cap_per_airline=cap_per_airline,
        solve_mode="exact",
    )

    alloc_ivcg, pay_ivcg, _ = vcg_interval(
        types=types,
        bids_for_intervals=bids_for_intervals,
        m_slots=m_slots,
        max_interval_len=max_interval_len,
        cap_per_airline=cap_per_airline,
        solve_mode="exact",
    )

    # ─────────────────────────────────────────────
    # 3) Full Combinatorial VCG (always truthful)
    # ─────────────────────────────────────────────
    alloc_cvcg, pay_cvcg, _ = vcg_combinatorial(
        types=types,
        m_slots=m_slots,
        cap_per_airline=cap_per_airline,
    )

    return {
        "n_airlines":      n_airlines,
        "m_slots":         m_slots,
        "cap_per_airline": cap_per_airline,
        "bidding_mode":    bidding_mode,

        # Sequential First-Price
        "seq_eff":    total_welfare(types, alloc_seq),
        "seq_rev":    float(np.sum(pay_seq)),
        "seq_fair":   fairness_1_minus_hhi(alloc_seq),
        "seq_alpha":  float(alpha_seq),
        "seq_eq_gap": float(eq_gap_seq),

        # Interval PAB
        "int_eff":    total_welfare(types, alloc_int),
        "int_rev":    float(np.sum(pay_int)),
        "int_fair":   fairness_1_minus_hhi(alloc_int),
        "int_alpha":  float(alpha_int),
        "int_eq_gap": float(eq_gap_int),

        # Interval VCG (restricted benchmark)
        "ivcg_eff":  total_welfare(types, alloc_ivcg),
        "ivcg_rev":  float(np.sum(pay_ivcg)),
        "ivcg_fair": fairness_1_minus_hhi(alloc_ivcg),

        # Full Combinatorial VCG (new benchmark)
        "cvcg_eff":  total_welfare(types, alloc_cvcg),
        "cvcg_rev":  float(np.sum(pay_cvcg)),
        "cvcg_fair": fairness_1_minus_hhi(alloc_cvcg),
    }
