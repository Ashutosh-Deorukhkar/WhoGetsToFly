# # # # # src/simulator.py
# # # # import numpy as np
# # # # from .models import generate_slots, sample_airline_types
# # # # from .mechanisms import sequential_first_price, interval_pay_as_bid, vcg_interval
# # # # from .metrics import total_welfare, fairness_1_minus_hhi, value_of_bundle
# # # # from .equilibrium import solve_alpha_sequential_fp, solve_alpha_interval

# # # # def run_one_scenario(
# # # #     n_airlines: int,
# # # #     start_hour: int = 8,
# # # #     end_hour: int = 18,
# # # #     cap_per_airline: int = 3,
# # # #     seed: int = 0,
# # # #     bidding_mode: str = "truthful",
# # # #     max_interval_len: int = 3,
# # # # ):
# # # #     rng = np.random.default_rng(seed)
# # # #     slots = generate_slots(start_hour, end_hour)
# # # #     m_slots = len(slots)

# # # #     types = sample_airline_types(n_airlines, slots=np.arange(m_slots), rng=rng)

# # # #     # --- Sequential FP ---
# # # #     if bidding_mode == "truthful":
# # # #         alpha_seq, eq_gap_seq = 1.0, 0.0
# # # #     else:
# # # #         alpha_seq, eq_gap_seq = solve_alpha_sequential_fp(
# # # #             n_airlines=n_airlines, m_slots=m_slots, rng=rng, cap_per_airline=cap_per_airline
# # # #         )
# # # #     bids_seq = np.vstack([alpha_seq * t.a for t in types])
# # # #     alloc_seq, pay_seq, _ = sequential_first_price(bids_seq, cap_per_airline=cap_per_airline)

# # # #     # --- Interval bids (same for pay-as-bid and VCG) ---
# # # #     if bidding_mode == "truthful":
# # # #         alpha_int, eq_gap_int = 1.0, 0.0
# # # #     else:
# # # #         alpha_int, eq_gap_int = solve_alpha_interval(
# # # #             n_airlines=n_airlines, m_slots=m_slots, rng=rng, cap_per_airline=cap_per_airline,
# # # #             max_interval_len=max_interval_len
# # # #         )

# # # #     intervals = [(l, r) for l in range(m_slots) for r in range(l, min(m_slots, l + max_interval_len))]
# # # #     bids_for_intervals = []
# # # #     for i in range(n_airlines):
# # # #         d = {}
# # # #         for (l, r) in intervals:
# # # #             bundle = np.arange(l, r + 1, dtype=int)
# # # #             d[(l, r)] = float(alpha_int) * float(value_of_bundle(types[i], bundle))
# # # #         bids_for_intervals.append(d)

# # # #     alloc_int, pay_int, _ = interval_pay_as_bid(
# # # #         types=types,
# # # #         bids_for_intervals=bids_for_intervals,
# # # #         m_slots=m_slots,
# # # #         max_interval_len=max_interval_len,
# # # #         cap_per_airline=cap_per_airline,
# # # #     )

# # # #     alloc_vcg, pay_vcg, _ = vcg_interval(
# # # #         types=types,
# # # #         bids_for_intervals=bids_for_intervals,
# # # #         m_slots=m_slots,
# # # #         max_interval_len=max_interval_len,
# # # #         cap_per_airline=cap_per_airline,
# # # #     )

# # # #     out = {
# # # #         "n_airlines": n_airlines,
# # # #         "m_slots": m_slots,
# # # #         "cap_per_airline": cap_per_airline,
# # # #         "bidding_mode": bidding_mode,

# # # #         "seq_eff": total_welfare(types, alloc_seq),
# # # #         "seq_rev": float(np.sum(pay_seq)),
# # # #         "seq_fair": fairness_1_minus_hhi(alloc_seq),
# # # #         "seq_alpha": float(alpha_seq),
# # # #         "seq_eq_gap": float(eq_gap_seq),

# # # #         "int_eff": total_welfare(types, alloc_int),
# # # #         "int_rev": float(np.sum(pay_int)),
# # # #         "int_fair": fairness_1_minus_hhi(alloc_int),
# # # #         "int_alpha": float(alpha_int),
# # # #         "int_eq_gap": float(eq_gap_int),

# # # #         "vcg_eff": total_welfare(types, alloc_vcg),
# # # #         "vcg_rev": float(np.sum(pay_vcg)),
# # # #         "vcg_fair": fairness_1_minus_hhi(alloc_vcg),
# # # #     }
# # # #     return out






# # # # src/simulator.py
# # # import numpy as np
# # # from .models import generate_slots, sample_airline_types
# # # from .mechanisms import sequential_first_price, interval_pay_as_bid, vcg_interval
# # # from .metrics import total_welfare, fairness_1_minus_hhi, value_of_bundle
# # # from .equilibrium import solve_alpha_sequential_fp_groups, solve_alpha_interval_by_length



# # # def _slot_group(s: int) -> int:
# # #     """
# # #     Map slot index s to a coarse time group.
# # #     For m_slots = 10 (8am..6pm): [0..2]=early, [3..6]=mid, [7..9]=late.

# # #     This implements the parametric strategy class:
# # #         b_i(s) = alpha_group(s) * a_i(s)
# # #     """
# # #     if s <= 2:
# # #         return 0
# # #     elif s <= 6:
# # #         return 1
# # #     else:
# # #         return 2


# # # def run_one_scenario(
# # #     n_airlines: int,
# # #     start_hour: int = 8,
# # #     end_hour: int = 18,
# # #     cap_per_airline: int = 3,
# # #     seed: int = 0,
# # #     bidding_mode: str = "truthful",
# # #     max_interval_len: int = 3,
# # # ):
# # #     """
# # #     Environment:
# # #       - m_slots = end_hour - start_hour (default 10)
# # #       - airline i has private type parameters (a_i(s), beta_i, k_i, lambda_i)

# # #     Value model (in metrics.value_of_bundle):
# # #         v_i(S) = sum_{s in S} a_i(s) + beta_i * AdjPairs(S) - lambda_i * max(0, |S|-k_i)^2

# # #     Mechanisms evaluated:
# # #       1) Sequential First-Price (per slot, in order)
# # #       2) Restricted Interval Pay-As-Bid (contiguous bundles length <= max_interval_len)
# # #       3) Restricted Interval VCG benchmark (same bundle space as #2)

# # #     Strategic layer (approx BNE in restricted strategy class):
# # #       - Sequential: alpha over 3 time groups
# # #       - Interval: alpha by bundle length (1..max_interval_len)
# # #     """
# # #     rng = np.random.default_rng(seed)
# # #     slots = generate_slots(start_hour, end_hour)
# # #     m_slots = len(slots)

# # #     types = sample_airline_types(n_airlines, slots=np.arange(m_slots), rng=rng)

# # #     # =========================
# # #     # 1) Sequential First-Price
# # #     # =========================
# # #     if bidding_mode == "truthful":
# # #         alpha_seq = np.ones(3, dtype=float)     # [alpha_early, alpha_mid, alpha_late]
# # #         eq_gap_seq = 0.0
# # #     else:
# # #         alpha_seq, eq_gap_seq = solve_alpha_sequential_fp_groups(
# # #             n_airlines=n_airlines,
# # #             m_slots=m_slots,
# # #             rng=rng,
# # #             cap_per_airline=cap_per_airline,
# # #         )

# # #     bids_seq = np.zeros((n_airlines, m_slots), dtype=float)
# # #     for i, t in enumerate(types):
# # #         for s in range(m_slots):
# # #             bids_seq[i, s] = float(alpha_seq[_slot_group(s)]) * float(t.a[s])

# # #     alloc_seq, pay_seq, _ = sequential_first_price(bids_seq, cap_per_airline=cap_per_airline)

# # #     # ============================================
# # #     # 2) Interval bids (Pay-As-Bid + Interval VCG)
# # #     # ============================================
# # #     if bidding_mode == "truthful":
# # #         alpha_int = np.ones(max_interval_len, dtype=float)  # [alpha_len1, alpha_len2, alpha_len3]
# # #         eq_gap_int = 0.0
# # #     else:
# # #         alpha_int, eq_gap_int = solve_alpha_interval_by_length(
# # #             n_airlines=n_airlines,
# # #             m_slots=m_slots,
# # #             rng=rng,
# # #             cap_per_airline=cap_per_airline,
# # #             max_interval_len=max_interval_len,
# # #         )

# # #     intervals = [
# # #         (l, r)
# # #         for l in range(m_slots)
# # #         for r in range(l, min(m_slots, l + max_interval_len))
# # #     ]

# # #     bids_for_intervals = []
# # #     for i in range(n_airlines):
# # #         d = {}
# # #         for (l, r) in intervals:
# # #             bundle = np.arange(l, r + 1, dtype=int)
# # #             length = (r - l + 1)  # 1..max_interval_len

# # #             d[(l, r)] = float(alpha_int[length - 1]) * float(value_of_bundle(types[i], bundle))
# # #         bids_for_intervals.append(d)

# # #     alloc_int, pay_int, _ = interval_pay_as_bid(
# # #         types=types,
# # #         bids_for_intervals=bids_for_intervals,
# # #         m_slots=m_slots,
# # #         max_interval_len=max_interval_len,
# # #         cap_per_airline=cap_per_airline,
# # #     )

# # #     alloc_vcg, pay_vcg, _ = vcg_interval(
# # #         types=types,
# # #         bids_for_intervals=bids_for_intervals,
# # #         m_slots=m_slots,
# # #         max_interval_len=max_interval_len,
# # #         cap_per_airline=cap_per_airline,
# # #     )

# # #     # =========
# # #     # Metrics
# # #     # =========
# # #     out = {
# # #         "n_airlines": n_airlines,
# # #         "m_slots": m_slots,
# # #         "cap_per_airline": cap_per_airline,
# # #         "bidding_mode": bidding_mode,

# # #         "seq_eff": total_welfare(types, alloc_seq),
# # #         "seq_rev": float(np.sum(pay_seq)),
# # #         "seq_fair": fairness_1_minus_hhi(alloc_seq),
# # #         "seq_alpha_mean": float(np.mean(alpha_seq)),
# # #         "seq_eq_gap": float(eq_gap_seq),

# # #         "int_eff": total_welfare(types, alloc_int),
# # #         "int_rev": float(np.sum(pay_int)),
# # #         "int_fair": fairness_1_minus_hhi(alloc_int),
# # #         "int_alpha_mean": float(np.mean(alpha_int)),
# # #         "int_eq_gap": float(eq_gap_int),

# # #         "vcg_eff": total_welfare(types, alloc_vcg),
# # #         "vcg_rev": float(np.sum(pay_vcg)),
# # #         "vcg_fair": fairness_1_minus_hhi(alloc_vcg),
# # #     }

# # #     # Log alpha components for plots/debug
# # #     out["seq_alpha_early"] = float(alpha_seq[0])
# # #     out["seq_alpha_mid"]   = float(alpha_seq[1])
# # #     out["seq_alpha_late"]  = float(alpha_seq[2])

# # #     for L in range(max_interval_len):
# # #         out[f"int_alpha_len{L+1}"] = float(alpha_int[L])

# # #     return out




# # # src/simulator.py
# # import numpy as np
# # from .models import generate_slots, sample_airline_types
# # from .mechanisms import sequential_first_price, interval_pay_as_bid, vcg_interval
# # from .metrics import total_welfare, fairness_1_minus_hhi, value_of_bundle
# # from .equilibrium import (
# #     solve_alpha_sequential_fp_by_kind_groups,
# #     solve_alpha_interval_by_kind_length,
# # )


# # def _slot_group(s: int) -> int:
# #     if s <= 2:
# #         return 0
# #     elif s <= 6:
# #         return 1
# #     else:
# #         return 2


# # def _kind_idx(kind: str) -> int:
# #     return 0 if kind == "hub" else 1


# # def run_one_scenario(
# #     n_airlines: int,
# #     start_hour: int = 8,
# #     end_hour: int = 18,
# #     cap_per_airline: int = 3,
# #     seed: int = 0,
# #     bidding_mode: str = "truthful",
# #     max_interval_len: int = 3,
# # ):
# #     rng = np.random.default_rng(seed)
# #     slots = generate_slots(start_hour, end_hour)
# #     m_slots = len(slots)

# #     types = sample_airline_types(n_airlines, slots=np.arange(m_slots), rng=rng)

# #     # --- Sequential FP ---
# #     if bidding_mode == "truthful":
# #         alpha_seq = np.ones((2, 3), dtype=float)  # kind x group
# #         eq_gap_seq = 0.0
# #     else:
# #         alpha_seq, eq_gap_seq = solve_alpha_sequential_fp_by_kind_groups(
# #             n_airlines=n_airlines,
# #             m_slots=m_slots,
# #             rng=rng,
# #             cap_per_airline=cap_per_airline,
# #         )

# #     bids_seq = np.zeros((n_airlines, m_slots), dtype=float)
# #     for i, t in enumerate(types):
# #         k = _kind_idx(t.kind)
# #         for s in range(m_slots):
# #             g = _slot_group(s)
# #             bids_seq[i, s] = float(alpha_seq[k, g]) * float(t.a[s])

# #     alloc_seq, pay_seq, _ = sequential_first_price(bids_seq, cap_per_airline=cap_per_airline)

# #     # --- Interval bids (same bids used for pay-as-bid and VCG allocation) ---
# #     if bidding_mode == "truthful":
# #         alpha_int = np.ones((2, max_interval_len), dtype=float)  # kind x length
# #         eq_gap_int = 0.0
# #     else:
# #         alpha_int, eq_gap_int = solve_alpha_interval_by_kind_length(
# #             n_airlines=n_airlines,
# #             m_slots=m_slots,
# #             rng=rng,
# #             cap_per_airline=cap_per_airline,
# #             max_interval_len=max_interval_len,
# #         )

# #     intervals = [(l, r) for l in range(m_slots) for r in range(l, min(m_slots, l + max_interval_len))]

# #     bids_for_intervals = []
# #     for i in range(n_airlines):
# #         t = types[i]
# #         k = _kind_idx(t.kind)
# #         d = {}
# #         for (l, r) in intervals:
# #             bundle = np.arange(l, r + 1, dtype=int)
# #             length = (r - l + 1)  # 1..max_interval_len
# #             d[(l, r)] = float(alpha_int[k, length - 1]) * float(value_of_bundle(t, bundle))
# #         bids_for_intervals.append(d)

# #     alloc_int, pay_int, _ = interval_pay_as_bid(
# #         types=types,
# #         bids_for_intervals=bids_for_intervals,
# #         m_slots=m_slots,
# #         max_interval_len=max_interval_len,
# #         cap_per_airline=cap_per_airline,
# #     )

# #     alloc_vcg, pay_vcg, _ = vcg_interval(
# #         types=types,
# #         bids_for_intervals=bids_for_intervals,
# #         m_slots=m_slots,
# #         max_interval_len=max_interval_len,
# #         cap_per_airline=cap_per_airline,
# #     )

# #     out = {
# #         "n_airlines": n_airlines,
# #         "m_slots": m_slots,
# #         "cap_per_airline": cap_per_airline,
# #         "bidding_mode": bidding_mode,

# #         "seq_eff": total_welfare(types, alloc_seq),
# #         "seq_rev": float(np.sum(pay_seq)),
# #         "seq_fair": fairness_1_minus_hhi(alloc_seq),
# #         "seq_alpha_mean": float(np.mean(alpha_seq)),
# #         "seq_eq_gap": float(eq_gap_seq),

# #         "int_eff": total_welfare(types, alloc_int),
# #         "int_rev": float(np.sum(pay_int)),
# #         "int_fair": fairness_1_minus_hhi(alloc_int),
# #         "int_alpha_mean": float(np.mean(alpha_int)),
# #         "int_eq_gap": float(eq_gap_int),

# #         "vcg_eff": total_welfare(types, alloc_vcg),
# #         "vcg_rev": float(np.sum(pay_vcg)),
# #         "vcg_fair": fairness_1_minus_hhi(alloc_vcg),
# #     }

# #     # Log alpha components (kind-specific)
# #     out["seq_alpha_hub_early"] = float(alpha_seq[0, 0])
# #     out["seq_alpha_hub_mid"]   = float(alpha_seq[0, 1])
# #     out["seq_alpha_hub_late"]  = float(alpha_seq[0, 2])

# #     out["seq_alpha_p2p_early"] = float(alpha_seq[1, 0])
# #     out["seq_alpha_p2p_mid"]   = float(alpha_seq[1, 1])
# #     out["seq_alpha_p2p_late"]  = float(alpha_seq[1, 2])

# #     for L in range(max_interval_len):
# #         out[f"int_alpha_hub_len{L+1}"] = float(alpha_int[0, L])
# #         out[f"int_alpha_p2p_len{L+1}"] = float(alpha_int[1, L])

# #     return out

# # src/simulator.py
# import numpy as np
# from .models import generate_slots, sample_airline_types
# from .mechanisms import sequential_first_price, interval_pay_as_bid, vcg_interval
# from .metrics import total_welfare, fairness_1_minus_hhi, value_of_bundle
# from .equilibrium import solve_alpha_sequential_fp_by_kind_groups, solve_alpha_interval_by_kind_length

# def _slot_group(s: int) -> int:
#     if s <= 2:
#         return 0
#     elif s <= 6:
#         return 1
#     else:
#         return 2


# def run_one_scenario(
#     n_airlines: int,
#     start_hour: int = 8,
#     end_hour: int = 18,
#     cap_per_airline: int = 3,
#     seed: int = 0,
#     bidding_mode: str = "truthful",
#     max_interval_len: int = 3,
# ):
#     rng = np.random.default_rng(seed)
#     slots = generate_slots(start_hour, end_hour)
#     m_slots = len(slots)

#     types = sample_airline_types(n_airlines, slots=np.arange(m_slots), rng=rng)

#     # =========================
#     # 1) Sequential First-Price
#     # =========================
#     if bidding_mode == "truthful":
#         base_alpha_seq = np.ones(3, dtype=float)
#         eq_gap_seq = 0.0
#     else:
#         base_alpha_seq, eq_gap_seq = solve_alpha_sequential_fp_by_kind_groups(
#             n_airlines=n_airlines,
#             m_slots=m_slots,
#             rng=rng,
#             cap_per_airline=cap_per_airline,
#         )

#     # UNIT (airline-level) shading: scale baseline alpha by airline kind
#     # hubs shade less => multiplier closer to 1
#     # p2p shade more  => multiplier smaller
#     # (these are the only two knobs you need to make allocs move)
#     kind_mult_seq = np.array(
#         [1.00 if t.kind == "hub" else 0.85 for t in types],
#         dtype=float
#     )

#     bids_seq = np.zeros((n_airlines, m_slots), dtype=float)
#     for i, t in enumerate(types):
#         for s in range(m_slots):
#             g = _slot_group(s)
#             bids_seq[i, s] = float(kind_mult_seq[i]) * float(base_alpha_seq[g]) * float(t.a[s])

#     alloc_seq, pay_seq, _ = sequential_first_price(bids_seq, cap_per_airline=cap_per_airline)

#     # ============================================
#     # 2) Interval bids (Pay-As-Bid + Interval VCG)
#     # ============================================
#     if bidding_mode == "truthful":
#         base_alpha_int = np.ones(max_interval_len, dtype=float)
#         eq_gap_int = 0.0
#     else:
#         base_alpha_int, eq_gap_int = solve_alpha_interval_by_kind_length(
#             n_airlines=n_airlines,
#             m_slots=m_slots,
#             rng=rng,
#             cap_per_airline=cap_per_airline,
#             max_interval_len=max_interval_len,
#         )

#     # UNIT (airline-level) shading for intervals too
#     kind_mult_int = np.array(
#         [1.00 if t.kind == "hub" else 0.85 for t in types],
#         dtype=float
#     )

#     intervals = [
#         (l, r)
#         for l in range(m_slots)
#         for r in range(l, min(m_slots, l + max_interval_len))
#     ]

#     bids_for_intervals = []
#     for i in range(n_airlines):
#         t = types[i]
#         d = {}
#         for (l, r) in intervals:
#             bundle = np.arange(l, r + 1, dtype=int)
#             length = (r - l + 1)  # 1..max_interval_len
#             d[(l, r)] = (
#                 float(kind_mult_int[i])
#                 * float(base_alpha_int[length - 1])
#                 * float(value_of_bundle(t, bundle))
#             )
#         bids_for_intervals.append(d)

#     alloc_int, pay_int, _ = interval_pay_as_bid(
#         types=types,
#         bids_for_intervals=bids_for_intervals,
#         m_slots=m_slots,
#         max_interval_len=max_interval_len,
#         cap_per_airline=cap_per_airline,
#     )

#     alloc_vcg, pay_vcg, _ = vcg_interval(
#         types=types,
#         bids_for_intervals=bids_for_intervals,
#         m_slots=m_slots,
#         max_interval_len=max_interval_len,
#         cap_per_airline=cap_per_airline,
#     )

#     out = {
#         "n_airlines": n_airlines,
#         "m_slots": m_slots,
#         "cap_per_airline": cap_per_airline,
#         "bidding_mode": bidding_mode,

#         "seq_eff": total_welfare(types, alloc_seq),
#         "seq_rev": float(np.sum(pay_seq)),
#         "seq_fair": fairness_1_minus_hhi(alloc_seq),
#         "seq_alpha_mean": float(np.mean(base_alpha_seq)),
#         "seq_eq_gap": float(eq_gap_seq),

#         "int_eff": total_welfare(types, alloc_int),
#         "int_rev": float(np.sum(pay_int)),
#         "int_fair": fairness_1_minus_hhi(alloc_int),
#         "int_alpha_mean": float(np.mean(base_alpha_int)),
#         "int_eq_gap": float(eq_gap_int),

#         "vcg_eff": total_welfare(types, alloc_vcg),
#         "vcg_rev": float(np.sum(pay_vcg)),
#         "vcg_fair": fairness_1_minus_hhi(alloc_vcg),
#     }

#     # log baseline alpha components
#     out["seq_alpha_early"] = float(base_alpha_seq[0])
#     out["seq_alpha_mid"]   = float(base_alpha_seq[1])
#     out["seq_alpha_late"]  = float(base_alpha_seq[2])

#     for L in range(max_interval_len):
#         out[f"int_alpha_len{L+1}"] = float(base_alpha_int[L])

#     # log kind multipliers (so you can verify heterogeneity exists)
#     out["seq_kind_mult_mean"] = float(np.mean(kind_mult_seq))
#     out["int_kind_mult_mean"] = float(np.mean(kind_mult_int))

#     return out



# src/simulator.py
import numpy as np
from .models import generate_slots, sample_airline_types
from .mechanisms import sequential_first_price, interval_pay_as_bid, vcg_interval
from .metrics import total_welfare, fairness_1_minus_hhi, value_of_bundle
from .equilibrium import (
    solve_alpha_sequential_fp_by_kind_groups,
    solve_alpha_interval_by_kind_length,
)


def _slot_group(s: int) -> int:
    if s <= 2:
        return 0
    elif s <= 6:
        return 1
    else:
        return 2


def _kind_idx(kind: str) -> int:
    return 0 if kind == "hub" else 1


def run_one_scenario(
    n_airlines: int,
    start_hour: int = 8,
    end_hour: int = 18,
    cap_per_airline: int = 3,
    seed: int = 0,
    bidding_mode: str = "truthful",
    max_interval_len: int = 3,
):
    rng = np.random.default_rng(seed)
    slots = generate_slots(start_hour, end_hour)
    m_slots = len(slots)

    types = sample_airline_types(n_airlines, slots=np.arange(m_slots), rng=rng)

    # =========================
    # 1) Sequential First-Price
    # =========================
    if bidding_mode == "truthful":
        alpha_seq = np.ones((2, 3), dtype=float)   # kind x group
        eq_gap_seq = 0.0
    else:
        alpha_seq, eq_gap_seq = solve_alpha_sequential_fp_by_kind_groups(
            n_airlines=n_airlines,
            m_slots=m_slots,
            rng=rng,
            cap_per_airline=cap_per_airline,
        )

    bids_seq = np.zeros((n_airlines, m_slots), dtype=float)
    for i, t in enumerate(types):
        k = _kind_idx(t.kind)
        for s in range(m_slots):
            g = _slot_group(s)
            bids_seq[i, s] = float(alpha_seq[k, g]) * float(t.a[s])

    alloc_seq, pay_seq, _ = sequential_first_price(bids_seq, cap_per_airline=cap_per_airline)

    # ============================================
    # 2) Interval bids (Pay-As-Bid + Interval VCG)
    # ============================================
    if bidding_mode == "truthful":
        alpha_int = np.ones((2, max_interval_len), dtype=float)  # kind x length
        eq_gap_int = 0.0
    else:
        alpha_int, eq_gap_int = solve_alpha_interval_by_kind_length(
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
    for i, t in enumerate(types):
        k = _kind_idx(t.kind)
        d = {}
        for (l, r) in intervals:
            bundle = np.arange(l, r + 1, dtype=int)
            length = (r - l + 1)  # 1..max_interval_len
            d[(l, r)] = float(alpha_int[k, length - 1]) * float(value_of_bundle(t, bundle))
        bids_for_intervals.append(d)

    # alloc_int, pay_int, _ = interval_pay_as_bid(
    #     types=types,
    #     bids_for_intervals=bids_for_intervals,
    #     m_slots=m_slots,
    #     max_interval_len=max_interval_len,
    #     cap_per_airline=cap_per_airline,
    # )

    # alloc_vcg, pay_vcg, _ = vcg_interval(
    #     types=types,
    #     bids_for_intervals=bids_for_intervals,
    #     m_slots=m_slots,
    #     max_interval_len=max_interval_len,
    #     cap_per_airline=cap_per_airline,
    # )
    alloc_int, pay_int, _ = interval_pay_as_bid(
        types=types,
        bids_for_intervals=bids_for_intervals,
        m_slots=m_slots,
        max_interval_len=max_interval_len,
        cap_per_airline=cap_per_airline,
        solve_mode="exact",
    )

    alloc_vcg, pay_vcg, _ = vcg_interval(
        types=types,
        bids_for_intervals=bids_for_intervals,
        m_slots=m_slots,
        max_interval_len=max_interval_len,
        cap_per_airline=cap_per_airline,
        solve_mode="exact",
    )

    # =========
    # Metrics
    # =========
    out = {
        "n_airlines": n_airlines,
        "m_slots": m_slots,
        "cap_per_airline": cap_per_airline,
        "bidding_mode": bidding_mode,

        "seq_eff": total_welfare(types, alloc_seq),
        "seq_rev": float(np.sum(pay_seq)),
        "seq_fair": fairness_1_minus_hhi(alloc_seq),
        "seq_alpha_mean": float(np.mean(alpha_seq)),
        "seq_eq_gap": float(eq_gap_seq),

        "int_eff": total_welfare(types, alloc_int),
        "int_rev": float(np.sum(pay_int)),
        "int_fair": fairness_1_minus_hhi(alloc_int),
        "int_alpha_mean": float(np.mean(alpha_int)),
        "int_eq_gap": float(eq_gap_int),

        "vcg_eff": total_welfare(types, alloc_vcg),
        "vcg_rev": float(np.sum(pay_vcg)),
        "vcg_fair": fairness_1_minus_hhi(alloc_vcg),
    }

    # Log alpha components
    out["seq_alpha_hub_early"] = float(alpha_seq[0, 0])
    out["seq_alpha_hub_mid"]   = float(alpha_seq[0, 1])
    out["seq_alpha_hub_late"]  = float(alpha_seq[0, 2])
    out["seq_alpha_p2p_early"] = float(alpha_seq[1, 0])
    out["seq_alpha_p2p_mid"]   = float(alpha_seq[1, 1])
    out["seq_alpha_p2p_late"]  = float(alpha_seq[1, 2])

    for L in range(max_interval_len):
        out[f"int_alpha_hub_len{L+1}"] = float(alpha_int[0, L])
        out[f"int_alpha_p2p_len{L+1}"] = float(alpha_int[1, L])

    return out