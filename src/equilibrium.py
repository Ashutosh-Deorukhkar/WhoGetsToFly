# # # src/equilibrium.py
# # import numpy as np
# # from .metrics import airline_utilities, value_of_bundle
# # from .mechanisms import sequential_first_price, interval_pay_as_bid
# # from .models import sample_airline_types


# # _KIND_TO_IDX = {"hub": 0, "p2p": 1}


# # def solve_alpha_sequential_fp_by_kind_groups(
# #     n_airlines: int,
# #     m_slots: int,
# #     rng: np.random.Generator,
# #     cap_per_airline: int,
# #     alpha_grid=None,
# #     n_mc: int = 30,
# #     n_passes: int = 5,
# #     damping: float = 0.6,
# #     n_mc_eval: int = 80,
# # ):
# #     """
# #     Two-population, 3-group strategy class:
# #       b_i(s) = alpha[kind(i), g(s)] * a_i(s)
# #     where kind in {hub, p2p} and g(s) in {early, mid, late}.

# #     Returns:
# #       alpha_seq: shape (2,3)
# #       eq_gap: avg unilateral gain of deviating ONE coordinate (kind,group) for a single deviator
# #     """

# #     if alpha_grid is None:
# #         alpha_grid = np.linspace(0.4, 1.0, 13)
# #     alpha_grid = np.asarray(alpha_grid, dtype=float)

# #     def group_of_slot(s: int) -> int:
# #         if s <= 2:
# #             return 0
# #         elif s <= 6:
# #             return 1
# #         else:
# #             return 2

# #     K, G = 2, 3
# #     alpha = np.full((K, G), 0.8, dtype=float)

# #     def bids_from_types(types, alpha_mat, dev=None):
# #         """
# #         dev can be (dev_i, dev_kind_idx, dev_group_idx, dev_alpha)
# #         """
# #         bids = np.zeros((n_airlines, m_slots), dtype=float)
# #         for i, t in enumerate(types):
# #             k = _KIND_TO_IDX.get(t.kind, 1)
# #             for s in range(m_slots):
# #                 g = group_of_slot(s)
# #                 a = float(alpha_mat[k, g])
# #                 if dev is not None:
# #                     dev_i, dk, dg, da = dev
# #                     if i == dev_i and k == dk and g == dg:
# #                         a = float(da)
# #                 bids[i, s] = a * float(t.a[s])
# #         return bids

# #     def u_of_deviator(types, alpha_mat, dev_i: int, dk=None, dg=None, da=None):
# #         dev = None
# #         if dk is not None:
# #             dev = (dev_i, dk, dg, da)
# #         bids = bids_from_types(types, alpha_mat, dev=dev)
# #         alloc, payments, _ = sequential_first_price(bids, cap_per_airline=cap_per_airline)
# #         return float(airline_utilities(types, alloc, payments)[dev_i])

# #     # --- solve by alternating best responses over (kind,group) ---
# #     for _ in range(n_passes):
# #         prev = alpha.copy()
# #         types_mc = [sample_airline_types(n_airlines, np.arange(m_slots), rng) for _t in range(n_mc)]

# #         for dk in range(K):
# #             for dg in range(G):
# #                 eus = []
# #                 for a_candidate in alpha_grid:
# #                     u_vals = []
# #                     for types in types_mc:
# #                         # choose a deviator of this kind if possible, else skip this sample
# #                         dev_candidates = [i for i, t in enumerate(types) if _KIND_TO_IDX.get(t.kind, 1) == dk]
# #                         if not dev_candidates:
# #                             continue
# #                         dev_i = dev_candidates[0]
# #                         u_vals.append(u_of_deviator(types, alpha, dev_i, dk=dk, dg=dg, da=a_candidate))
# #                     eus.append(float(np.mean(u_vals)) if len(u_vals) else -1e18)

# #                 a_br = float(alpha_grid[int(np.argmax(eus))])
# #                 alpha[dk, dg] = (1.0 - damping) * alpha[dk, dg] + damping * a_br

# #         if float(np.max(np.abs(alpha - prev))) < 1e-3:
# #             break

# #     # --- eq gap: unilateral deviation gain averaged over random deviators (by kind availability) ---
# #     types_eval = [sample_airline_types(n_airlines, np.arange(m_slots), rng) for _t in range(n_mc_eval)]

# #     gaps = []
# #     for types in types_eval:
# #         # pick deviator as airline 0 for consistency
# #         dev_i = 0
# #         dk = _KIND_TO_IDX.get(types[dev_i].kind, 1)

# #         stay = u_of_deviator(types, alpha, dev_i)

# #         best = -1e18
# #         for dg in range(G):
# #             for a_candidate in alpha_grid:
# #                 best = max(best, u_of_deviator(types, alpha, dev_i, dk=dk, dg=dg, da=a_candidate))

# #         gaps.append(best - stay)

# #     eq_gap = float(np.mean(np.array(gaps, dtype=float)))
# #     return alpha, eq_gap


# # def solve_alpha_interval_by_kind_length(
# #     n_airlines: int,
# #     m_slots: int,
# #     rng: np.random.Generator,
# #     cap_per_airline: int,
# #     max_interval_len: int = 3,
# #     alpha_grid=None,
# #     n_mc: int = 30,
# #     n_passes: int = 4,
# #     damping: float = 0.6,
# #     n_mc_eval: int = 80,
# # ):
# #     """
# #     Two-population, per-length strategy class:
# #       b_i(B) = alpha[kind(i), |B|] * v_i(B)

# #     Returns:
# #       alpha_int: shape (2, L)
# #       eq_gap: avg unilateral gain by deviating ONE length coordinate for deviator airline 0
# #     """

# #     if alpha_grid is None:
# #         alpha_grid = np.linspace(0.4, 1.0, 13)
# #     alpha_grid = np.asarray(alpha_grid, dtype=float)

# #     L = int(max_interval_len)
# #     K = 2
# #     alpha = np.full((K, L), 0.8, dtype=float)

# #     intervals = [(l, r) for l in range(m_slots) for r in range(l, min(m_slots, l + L))]

# #     def build_bids(types, alpha_mat, dev=None):
# #         """
# #         dev can be (dev_i, dev_kind_idx, dev_len, dev_alpha)
# #         """
# #         bids_for_intervals = []
# #         for i, t in enumerate(types):
# #             k = _KIND_TO_IDX.get(t.kind, 1)
# #             d = {}
# #             for (l, r) in intervals:
# #                 bundle = np.arange(l, r + 1, dtype=int)
# #                 length = int(r - l + 1)
# #                 a = float(alpha_mat[k, length - 1])
# #                 if dev is not None:
# #                     dev_i, dk, dlen, da = dev
# #                     if i == dev_i and k == dk and length == dlen:
# #                         a = float(da)
# #                 d[(l, r)] = a * float(value_of_bundle(t, bundle))
# #             bids_for_intervals.append(d)
# #         return bids_for_intervals

# #     def u_of_deviator(types, alpha_mat, dev_i: int, dk=None, dlen=None, da=None):
# #         dev = None
# #         if dk is not None:
# #             dev = (dev_i, dk, dlen, da)
# #         bids_for_intervals = build_bids(types, alpha_mat, dev=dev)
# #         alloc, payments, _ = interval_pay_as_bid(
# #             types=types,
# #             bids_for_intervals=bids_for_intervals,
# #             m_slots=m_slots,
# #             max_interval_len=L,
# #             cap_per_airline=cap_per_airline,
# #         )
# #         return float(airline_utilities(types, alloc, payments)[dev_i])

# #     for _ in range(n_passes):
# #         prev = alpha.copy()
# #         types_mc = [sample_airline_types(n_airlines, np.arange(m_slots), rng) for _t in range(n_mc)]

# #         for dk in range(K):
# #             for dlen in range(1, L + 1):
# #                 eus = []
# #                 for a_candidate in alpha_grid:
# #                     u_vals = []
# #                     for types in types_mc:
# #                         dev_candidates = [i for i, t in enumerate(types) if _KIND_TO_IDX.get(t.kind, 1) == dk]
# #                         if not dev_candidates:
# #                             continue
# #                         dev_i = dev_candidates[0]
# #                         u_vals.append(u_of_deviator(types, alpha, dev_i, dk=dk, dlen=dlen, da=a_candidate))
# #                     eus.append(float(np.mean(u_vals)) if len(u_vals) else -1e18)

# #                 a_br = float(alpha_grid[int(np.argmax(eus))])
# #                 alpha[dk, dlen - 1] = (1.0 - damping) * alpha[dk, dlen - 1] + damping * a_br

# #         if float(np.max(np.abs(alpha - prev))) < 1e-3:
# #             break

# #     # eq gap for deviator airline 0
# #     types_eval = [sample_airline_types(n_airlines, np.arange(m_slots), rng) for _t in range(n_mc_eval)]
# #     gaps = []
# #     for types in types_eval:
# #         dev_i = 0
# #         dk = _KIND_TO_IDX.get(types[dev_i].kind, 1)

# #         stay = u_of_deviator(types, alpha, dev_i)
# #         best = -1e18
# #         for dlen in range(1, L + 1):
# #             for a_candidate in alpha_grid:
# #                 best = max(best, u_of_deviator(types, alpha, dev_i, dk=dk, dlen=dlen, da=a_candidate))
# #         gaps.append(best - stay)

# #     eq_gap = float(np.mean(np.array(gaps, dtype=float)))
# #     return alpha, eq_gap


# # src/equilibrium.py
# import numpy as np
# from .metrics import airline_utilities, value_of_bundle
# from .mechanisms import sequential_first_price, interval_pay_as_bid
# from .models import sample_airline_types


# def solve_alpha_sequential_fp(
#     n_airlines: int,
#     m_slots: int,
#     rng: np.random.Generator,
#     cap_per_airline: int,
#     alpha_grid: np.ndarray = None,
#     n_mc: int = 30,
#     n_passes: int = 5,
#     damping: float = 0.6,
#     n_mc_eval: int = 80,
# ):
#     """
#     Find symmetric equilibrium shading parameter alpha for Sequential First-Price.

#     Strategy class:  b_i(s) = alpha * a_i(s)

#     Uses simulation-based best-response dynamics with damping.
#     Returns (alpha: float, eq_gap: float).
#     """
#     if alpha_grid is None:
#         alpha_grid = np.linspace(0.4, 1.0, 13)
#     alpha_grid = np.asarray(alpha_grid, dtype=float)

#     alpha = 0.8

#     for _ in range(n_passes):
#         alpha_prev = alpha
#         types_mc = [
#             sample_airline_types(n_airlines, np.arange(m_slots), rng)
#             for _ in range(n_mc)
#         ]

#         eus = []
#         for a_candidate in alpha_grid:
#             u_vals = []
#             for types in types_mc:
#                 bids = np.vstack([a_candidate * t.a for t in types])
#                 alloc, payments, _ = sequential_first_price(
#                     bids, cap_per_airline=cap_per_airline
#                 )
#                 u_vals.append(float(airline_utilities(types, alloc, payments)[0]))
#             eus.append(float(np.mean(u_vals)))

#         a_br = float(alpha_grid[int(np.argmax(eus))])
#         alpha = (1.0 - damping) * alpha + damping * a_br

#         if abs(alpha - alpha_prev) < 1e-3:
#             break

#     # Equilibrium gap: avg gain from unilateral deviation
#     types_eval = [
#         sample_airline_types(n_airlines, np.arange(m_slots), rng)
#         for _ in range(n_mc_eval)
#     ]

#     stay_u, best_u = [], []
#     for types in types_eval:
#         bids_stay = np.vstack([alpha * t.a for t in types])
#         alloc, payments, _ = sequential_first_price(
#             bids_stay, cap_per_airline=cap_per_airline
#         )
#         stay_u.append(float(airline_utilities(types, alloc, payments)[0]))

#         cand_us = []
#         for a_candidate in alpha_grid:
#             bids = np.vstack([alpha * t.a for t in types])
#             bids[0, :] = a_candidate * types[0].a
#             alloc2, pay2, _ = sequential_first_price(
#                 bids, cap_per_airline=cap_per_airline
#             )
#             cand_us.append(float(airline_utilities(types, alloc2, pay2)[0]))
#         best_u.append(float(np.max(cand_us)))

#     eq_gap = float(np.mean(np.array(best_u) - np.array(stay_u)))
#     return float(alpha), eq_gap


# def solve_alpha_interval(
#     n_airlines: int,
#     m_slots: int,
#     rng: np.random.Generator,
#     cap_per_airline: int,
#     max_interval_len: int = 3,
#     alpha_grid: np.ndarray = None,
#     n_mc: int = 30,
#     n_passes: int = 4,
#     damping: float = 0.6,
#     n_mc_eval: int = 80,
# ):
#     """
#     Find symmetric equilibrium shading parameter alpha for Interval PAB.

#     Strategy class:  b_i(B) = alpha * v_i(B)

#     Uses simulation-based best-response dynamics with damping.
#     Returns (alpha: float, eq_gap: float).
#     """
#     if alpha_grid is None:
#         alpha_grid = np.linspace(0.4, 1.0, 13)
#     alpha_grid = np.asarray(alpha_grid, dtype=float)

#     intervals = [
#         (l, r)
#         for l in range(m_slots)
#         for r in range(l, min(m_slots, l + max_interval_len))
#     ]

#     def build_bids(types, a):
#         bids_for_intervals = []
#         for t in types:
#             d = {}
#             for (l, r) in intervals:
#                 bundle = np.arange(l, r + 1, dtype=int)
#                 d[(l, r)] = float(a) * float(value_of_bundle(t, bundle))
#             bids_for_intervals.append(d)
#         return bids_for_intervals

#     alpha = 0.8

#     for _ in range(n_passes):
#         alpha_prev = alpha
#         types_mc = [
#             sample_airline_types(n_airlines, np.arange(m_slots), rng)
#             for _ in range(n_mc)
#         ]

#         eus = []
#         for a_candidate in alpha_grid:
#             u_vals = []
#             for types in types_mc:
#                 bids_for_intervals = build_bids(types, a_candidate)
#                 alloc, payments, _ = interval_pay_as_bid(
#                     types=types,
#                     bids_for_intervals=bids_for_intervals,
#                     m_slots=m_slots,
#                     max_interval_len=max_interval_len,
#                     cap_per_airline=cap_per_airline,
#                 )
#                 u_vals.append(float(airline_utilities(types, alloc, payments)[0]))
#             eus.append(float(np.mean(u_vals)))

#         a_br = float(alpha_grid[int(np.argmax(eus))])
#         alpha = (1.0 - damping) * alpha + damping * a_br

#         if abs(alpha - alpha_prev) < 1e-3:
#             break

#     # Equilibrium gap
#     types_eval = [
#         sample_airline_types(n_airlines, np.arange(m_slots), rng)
#         for _ in range(n_mc_eval)
#     ]

#     stay_u, best_u = [], []
#     for types in types_eval:
#         bids_stay = build_bids(types, alpha)
#         alloc, payments, _ = interval_pay_as_bid(
#             types=types,
#             bids_for_intervals=bids_stay,
#             m_slots=m_slots,
#             max_interval_len=max_interval_len,
#             cap_per_airline=cap_per_airline,
#         )
#         stay_u.append(float(airline_utilities(types, alloc, payments)[0]))

#         cand_us = []
#         for a_candidate in alpha_grid:
#             bids_dev = build_bids(types, alpha)
#             # deviator is airline 0
#             for (l, r) in intervals:
#                 bundle = np.arange(l, r + 1, dtype=int)
#                 bids_dev[0][(l, r)] = float(a_candidate) * float(
#                     value_of_bundle(types[0], bundle)
#                 )
#             alloc2, pay2, _ = interval_pay_as_bid(
#                 types=types,
#                 bids_for_intervals=bids_dev,
#                 m_slots=m_slots,
#                 max_interval_len=max_interval_len,
#                 cap_per_airline=cap_per_airline,
#             )
#             cand_us.append(float(airline_utilities(types, alloc2, pay2)[0]))
#         best_u.append(float(np.max(cand_us)))

#     eq_gap = float(np.mean(np.array(best_u) - np.array(stay_u)))
#     return float(alpha), eq_gap




# src/equilibrium.py
import numpy as np
from .metrics import airline_utilities, value_of_bundle
from .mechanisms import sequential_first_price, interval_pay_as_bid
from .models import sample_airline_types


def solve_alpha_sequential_fp(
    n_airlines: int,
    m_slots: int,
    rng: np.random.Generator,
    cap_per_airline: int,
    alpha_grid: np.ndarray = None,
    n_mc: int = 30,
    n_passes: int = 5,
    damping: float = 0.6,
    n_mc_eval: int = 80,
):
    """
    Find symmetric equilibrium shading parameter alpha for Sequential First-Price.

    Strategy class:  b_i(s) = alpha * a_i(s)

    Best-response dynamics: all others play current alpha, deviator (airline 0)
    tries each candidate alpha. Alpha updated toward best response with damping.

    Returns (alpha: float, eq_gap: float).
    """
    if alpha_grid is None:
        alpha_grid = np.linspace(0.4, 1.0, 13)
    alpha_grid = np.asarray(alpha_grid, dtype=float)

    alpha = 0.8

    for _ in range(n_passes):
        alpha_prev = alpha

        # Sample fresh type profiles for this pass (CRN)
        types_mc = [
            sample_airline_types(n_airlines, np.arange(m_slots), rng)
            for _ in range(n_mc)
        ]

        eus = []
        for a_candidate in alpha_grid:
            u_vals = []
            for types in types_mc:
                # Others (1..n-1) play current alpha, deviator (0) plays a_candidate
                bids = np.vstack([alpha * t.a for t in types])
                bids[0, :] = a_candidate * types[0].a
                alloc, payments, _ = sequential_first_price(
                    bids, cap_per_airline=cap_per_airline
                )
                u_vals.append(float(airline_utilities(types, alloc, payments)[0]))
            eus.append(float(np.mean(u_vals)))

        a_br = float(alpha_grid[int(np.argmax(eus))])
        alpha = (1.0 - damping) * alpha + damping * a_br

        if abs(alpha - alpha_prev) < 1e-3:
            break

    # Equilibrium gap: avg gain deviator (airline 0) can achieve vs staying at alpha
    types_eval = [
        sample_airline_types(n_airlines, np.arange(m_slots), rng)
        for _ in range(n_mc_eval)
    ]

    stay_u, best_u = [], []
    for types in types_eval:
        bids_stay = np.vstack([alpha * t.a for t in types])
        alloc, payments, _ = sequential_first_price(
            bids_stay, cap_per_airline=cap_per_airline
        )
        stay_u.append(float(airline_utilities(types, alloc, payments)[0]))

        cand_us = []
        for a_candidate in alpha_grid:
            bids = np.vstack([alpha * t.a for t in types])
            bids[0, :] = a_candidate * types[0].a
            alloc2, pay2, _ = sequential_first_price(
                bids, cap_per_airline=cap_per_airline
            )
            cand_us.append(float(airline_utilities(types, alloc2, pay2)[0]))
        best_u.append(float(np.max(cand_us)))

    eq_gap = float(np.mean(np.array(best_u) - np.array(stay_u)))
    return float(alpha), eq_gap


def solve_alpha_interval(
    n_airlines: int,
    m_slots: int,
    rng: np.random.Generator,
    cap_per_airline: int,
    max_interval_len: int = 3,
    alpha_grid: np.ndarray = None,
    n_mc: int = 30,
    n_passes: int = 4,
    damping: float = 0.6,
    n_mc_eval: int = 80,
):
    """
    Find symmetric equilibrium shading parameter alpha for Interval PAB.

    Strategy class:  b_i(B) = alpha * v_i(B)

    Best-response dynamics: all others play current alpha, deviator (airline 0)
    tries each candidate alpha. Alpha updated toward best response with damping.

    Returns (alpha: float, eq_gap: float).
    """
    if alpha_grid is None:
        alpha_grid = np.linspace(0.4, 1.0, 13)
    alpha_grid = np.asarray(alpha_grid, dtype=float)

    intervals = [
        (l, r)
        for l in range(m_slots)
        for r in range(l, min(m_slots, l + max_interval_len))
    ]

    def build_bids(types, alpha_all, alpha_dev=None):
        """
        Build interval bids. Others use alpha_all, airline 0 uses alpha_dev if given.
        """
        bids_for_intervals = []
        for i, t in enumerate(types):
            a = alpha_dev if (alpha_dev is not None and i == 0) else alpha_all
            d = {}
            for (l, r) in intervals:
                bundle = np.arange(l, r + 1, dtype=int)
                d[(l, r)] = float(a) * float(value_of_bundle(t, bundle))
            bids_for_intervals.append(d)
        return bids_for_intervals

    alpha = 0.8

    for _ in range(n_passes):
        alpha_prev = alpha

        types_mc = [
            sample_airline_types(n_airlines, np.arange(m_slots), rng)
            for _ in range(n_mc)
        ]

        eus = []
        for a_candidate in alpha_grid:
            u_vals = []
            for types in types_mc:
                bids_for_intervals = build_bids(types, alpha, alpha_dev=a_candidate)
                alloc, payments, _ = interval_pay_as_bid(
                    types=types,
                    bids_for_intervals=bids_for_intervals,
                    m_slots=m_slots,
                    max_interval_len=max_interval_len,
                    cap_per_airline=cap_per_airline,
                )
                u_vals.append(float(airline_utilities(types, alloc, payments)[0]))
            eus.append(float(np.mean(u_vals)))

        a_br = float(alpha_grid[int(np.argmax(eus))])
        alpha = (1.0 - damping) * alpha + damping * a_br

        if abs(alpha - alpha_prev) < 1e-3:
            break

    # Equilibrium gap
    types_eval = [
        sample_airline_types(n_airlines, np.arange(m_slots), rng)
        for _ in range(n_mc_eval)
    ]

    stay_u, best_u = [], []
    for types in types_eval:
        bids_stay = build_bids(types, alpha)
        alloc, payments, _ = interval_pay_as_bid(
            types=types,
            bids_for_intervals=bids_stay,
            m_slots=m_slots,
            max_interval_len=max_interval_len,
            cap_per_airline=cap_per_airline,
        )
        stay_u.append(float(airline_utilities(types, alloc, payments)[0]))

        cand_us = []
        for a_candidate in alpha_grid:
            bids_dev = build_bids(types, alpha, alpha_dev=a_candidate)
            alloc2, pay2, _ = interval_pay_as_bid(
                types=types,
                bids_for_intervals=bids_dev,
                m_slots=m_slots,
                max_interval_len=max_interval_len,
                cap_per_airline=cap_per_airline,
            )
            cand_us.append(float(airline_utilities(types, alloc2, pay2)[0]))
        best_u.append(float(np.max(cand_us)))

    eq_gap = float(np.mean(np.array(best_u) - np.array(stay_u)))
    return float(alpha), eq_gap
