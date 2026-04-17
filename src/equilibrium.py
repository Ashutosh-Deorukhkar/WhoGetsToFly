# # src/equilibrium.py
# import numpy as np
# from .metrics import airline_utilities, value_of_bundle
# from .mechanisms import sequential_first_price, interval_pay_as_bid
# from .models import sample_airline_types



# # def solve_alpha_sequential_fp(
# #     n_airlines: int,
# #     m_slots: int,
# #     rng: np.random.Generator,
# #     cap_per_airline: int,
# #     alpha_grid=None,
# #     n_mc: int = 30,
# #     n_passes: int = 4,
# #     damping: float = 0.6,
# # ):
# #     """
# #     Symmetric per-slot shading parameter alpha:
# #       b_i(s) = alpha * a_i(s)

# #     Best response within alpha_grid, simulation-based CRN.
# #     Returns alpha, eq_gap.
# #     """
# #     if alpha_grid is None:
# #         alpha_grid = np.linspace(0.4, 1.0, 13)
# #     alpha_grid = np.asarray(alpha_grid, dtype=float)

# #     alpha = 0.8

# #     for _ in range(n_passes):
# #         alpha_prev = alpha

# #         # CRN profiles: sample types once per pass
# #         types_mc = []
# #         for _t in range(n_mc):
# #             slots = np.arange(m_slots)
# #             types = sample_airline_types(n_airlines, slots, rng)
# #             types_mc.append(types)

# #         eus = []
# #         for a_candidate in alpha_grid:
# #             u_vals = []
# #             for types in types_mc:
# #                 # bids = alpha * a_i(s)
# #                 bids = np.vstack([a_candidate * t.a for t in types])
# #                 alloc, payments, _ = sequential_first_price(bids, cap_per_airline=cap_per_airline)
# #                 u = airline_utilities(types, alloc, payments)[0]  # deviator airline 0
# #                 u_vals.append(float(u))
# #             eus.append(float(np.mean(u_vals)))

# #         a_br = float(alpha_grid[int(np.argmax(eus))])
# #         alpha = (1.0 - damping) * alpha + damping * a_br

# #         if abs(alpha - alpha_prev) < 1e-3:
# #             break

# #     # eq gap evaluation
# #     types_eval = []
# #     for _t in range(80):
# #         slots = np.arange(m_slots)
# #         types_eval.append(sample_airline_types(n_airlines, slots, rng))

# #     stay_u = []
# #     best_u = []
# #     for types in types_eval:
# #         bids_stay = np.vstack([alpha * t.a for t in types])
# #         alloc, payments, _ = sequential_first_price(bids_stay, cap_per_airline=cap_per_airline)
# #         stay_u.append(float(airline_utilities(types, alloc, payments)[0]))

# #         cand_us = []
# #         for a_candidate in alpha_grid:
# #             bids = np.vstack([alpha * t.a for t in types])
# #             bids[0, :] = a_candidate * types[0].a
# #             alloc2, pay2, _ = sequential_first_price(bids, cap_per_airline=cap_per_airline)
# #             cand_us.append(float(airline_utilities(types, alloc2, pay2)[0]))
# #         best_u.append(float(np.max(cand_us)))

# #     eq_gap = float(np.mean(np.array(best_u) - np.array(stay_u)))
# #     return float(alpha), eq_gap


# def solve_alpha_sequential_fp_groups(
#     n_airlines: int,
#     m_slots: int,
#     rng: np.random.Generator,
#     cap_per_airline: int,
#     alpha_grid=None,
#     n_mc: int = 30,
#     n_passes: int = 4,
#     damping: float = 0.6,
#     n_mc_eval: int = 80,
# ):
#     """
#     3-parameter symmetric strategy class (time groups):
#       b_i(s) = alpha_g(s) * a_i(s)

#     Groups (for m=10):
#       early: [0,1,2], mid: [3,4,5,6], late: [7,8,9]
#     Returns (alpha_vec[3], eq_gap).
#     """
#     if alpha_grid is None:
#         alpha_grid = np.linspace(0.4, 1.0, 13)
#     alpha_grid = np.asarray(alpha_grid, dtype=float)

#     # define groups
#     def group_of_slot(s: int) -> int:
#         if s <= 2:
#             return 0
#         elif s <= 6:
#             return 1
#         else:
#             return 2

#     G = 3
#     alpha = np.full(G, 0.8, dtype=float)

#     def bids_from_types(types, alpha_vec):
#         bids = np.zeros((n_airlines, m_slots), dtype=float)
#         for i, t in enumerate(types):
#             for s in range(m_slots):
#                 bids[i, s] = float(alpha_vec[group_of_slot(s)]) * float(t.a[s])
#         return bids

#     def eu_deviator(types, alpha_vec, g_dev=None, alpha_g_dev=None):
#         # symmetric others use alpha_vec; deviator can change one coordinate g_dev
#         a_use = alpha_vec.copy()
#         if g_dev is not None:
#             a_use[g_dev] = float(alpha_g_dev)
#         bids = bids_from_types(types, a_use)
#         alloc, payments, _ = sequential_first_price(bids, cap_per_airline=cap_per_airline)
#         return float(airline_utilities(types, alloc, payments)[0])

#     for _ in range(n_passes):
#         alpha_prev = alpha.copy()

#         # CRN profiles per pass
#         types_mc = [sample_airline_types(n_airlines, np.arange(m_slots), rng) for _t in range(n_mc)]

#         # coordinate best response
#         for g in range(G):
#             eus = []
#             for a_candidate in alpha_grid:
#                 u_vals = [eu_deviator(types, alpha, g_dev=g, alpha_g_dev=a_candidate) for types in types_mc]
#                 eus.append(float(np.mean(u_vals)))
#             a_br = float(alpha_grid[int(np.argmax(eus))])
#             alpha[g] = (1.0 - damping) * alpha[g] + damping * a_br

#         if float(np.max(np.abs(alpha - alpha_prev))) < 1e-3:
#             break

#     # eq gap evaluation: best unilateral coordinate deviation gain
#     types_eval = [sample_airline_types(n_airlines, np.arange(m_slots), rng) for _t in range(n_mc_eval)]
#     stay_u = np.array([eu_deviator(types, alpha) for types in types_eval], dtype=float)

#     best_u = []
#     for types in types_eval:
#         best = -1e18
#         for g in range(G):
#             for a_candidate in alpha_grid:
#                 best = max(best, eu_deviator(types, alpha, g_dev=g, alpha_g_dev=a_candidate))
#         best_u.append(best)

#     eq_gap = float(np.mean(np.array(best_u) - stay_u))
#     return alpha, eq_gap


# # def solve_alpha_interval(
# #     n_airlines: int,
# #     m_slots: int,
# #     rng: np.random.Generator,
# #     cap_per_airline: int,
# #     max_interval_len: int = 3,
# #     alpha_grid=None,
# #     n_mc: int = 30,
# #     n_passes: int = 3,
# #     damping: float = 0.6,
# #     n_mc_eval: int = 80,
# # ):
# #     """
# #     Symmetric bundle shading parameter alpha:
# #       b_i(B) = alpha * v_i(B) for allowed interval bundles B.

# #     Approx best-response over alpha_grid using simulation-based expected utility.
# #     Returns (alpha, eq_gap).
# #     """
# #     if alpha_grid is None:
# #         alpha_grid = np.linspace(0.4, 1.0, 13)
# #     alpha_grid = np.asarray(alpha_grid, dtype=float)

# #     alpha = 0.8
# #     intervals = [(l, r) for l in range(m_slots) for r in range(l, min(m_slots, l + max_interval_len))]

# #     def eu_given_alpha(types, alpha_candidate):
# #         bids_for_intervals = []
# #         for i in range(n_airlines):
# #             d = {}
# #             for (l, r) in intervals:
# #                 bundle = np.arange(l, r + 1, dtype=int)
# #                 d[(l, r)] = float(alpha_candidate) * float(value_of_bundle(types[i], bundle))
# #             bids_for_intervals.append(d)

# #         alloc, payments, _ = interval_pay_as_bid(
# #             types=types,
# #             bids_for_intervals=bids_for_intervals,
# #             m_slots=m_slots,
# #             max_interval_len=max_interval_len,
# #             cap_per_airline=cap_per_airline,
# #         )
# #         return float(airline_utilities(types, alloc, payments)[0])

# #     for _ in range(n_passes):
# #         alpha_prev = alpha

# #         # CRN: fix sampled types for this pass
# #         types_mc = [sample_airline_types(n_airlines, slots=np.arange(m_slots), rng=rng) for _ in range(n_mc)]

# #         eus = []
# #         for a_candidate in alpha_grid:
# #             u_vals = [eu_given_alpha(types, a_candidate) for types in types_mc]
# #             eus.append(float(np.mean(u_vals)))

# #         a_br = float(alpha_grid[int(np.argmax(eus))])
# #         alpha = (1.0 - damping) * alpha + damping * a_br

# #         if abs(alpha - alpha_prev) < 1e-3:
# #             break

# #     # eq gap: how much deviator could gain by switching alpha unilaterally
# #     types_eval = [sample_airline_types(n_airlines, slots=np.arange(m_slots), rng=rng) for _ in range(n_mc_eval)]

# #     stay_u = np.array([eu_given_alpha(types, alpha) for types in types_eval], dtype=float)

# #     best_u = []
# #     for types in types_eval:
# #         cand_us = [eu_given_alpha(types, a_candidate) for a_candidate in alpha_grid]
# #         best_u.append(float(np.max(cand_us)))
# #     best_u = np.array(best_u, dtype=float)

# #     eq_gap = float(np.mean(best_u - stay_u))
# #     return float(alpha), float(eq_gap)


# def solve_alpha_interval_by_length(
#     n_airlines: int,
#     m_slots: int,
#     rng: np.random.Generator,
#     cap_per_airline: int,
#     max_interval_len: int = 3,
#     alpha_grid=None,
#     n_mc: int = 30,
#     n_passes: int = 3,
#     damping: float = 0.6,
#     n_mc_eval: int = 80,
# ):
#     """
#     Symmetric per-length strategy class:
#       b_i(B) = alpha_{|B|} * v_i(B),  |B| in {1..max_interval_len}

#     Returns (alpha_len_vec[max_interval_len], eq_gap).
#     """
#     if alpha_grid is None:
#         alpha_grid = np.linspace(0.4, 1.0, 13)
#     alpha_grid = np.asarray(alpha_grid, dtype=float)

#     L = int(max_interval_len)
#     alpha_len = np.full(L, 0.8, dtype=float)

#     intervals = [(l, r) for l in range(m_slots) for r in range(l, min(m_slots, l + L))]

#     def build_bids(types, alpha_vec, dev_len=None, dev_alpha=None):
#         bids_for_intervals = []
#         for i in range(n_airlines):
#             d = {}
#             for (l, r) in intervals:
#                 bundle = np.arange(l, r + 1, dtype=int)
#                 length = (r - l + 1)
#                 a = alpha_vec[length - 1]
#                 if dev_len is not None and length == dev_len:
#                     a = float(dev_alpha)
#                 d[(l, r)] = float(a) * float(value_of_bundle(types[i], bundle))
#             bids_for_intervals.append(d)
#         return bids_for_intervals

#     def eu_deviator(types, alpha_vec, dev_len=None, dev_alpha=None):
#         bids_for_intervals = build_bids(types, alpha_vec, dev_len=dev_len, dev_alpha=dev_alpha)
#         alloc, payments, _ = interval_pay_as_bid(
#             types=types,
#             bids_for_intervals=bids_for_intervals,
#             m_slots=m_slots,
#             max_interval_len=L,
#             cap_per_airline=cap_per_airline,
#         )
#         return float(airline_utilities(types, alloc, payments)[0])

#     for _ in range(n_passes):
#         prev = alpha_len.copy()
#         types_mc = [sample_airline_types(n_airlines, np.arange(m_slots), rng) for _t in range(n_mc)]

#         for length in range(1, L + 1):
#             eus = []
#             for a_candidate in alpha_grid:
#                 u_vals = [eu_deviator(types, alpha_len, dev_len=length, dev_alpha=a_candidate) for types in types_mc]
#                 eus.append(float(np.mean(u_vals)))
#             a_br = float(alpha_grid[int(np.argmax(eus))])
#             idx = length - 1
#             alpha_len[idx] = (1.0 - damping) * alpha_len[idx] + damping * a_br

#         if float(np.max(np.abs(alpha_len - prev))) < 1e-3:
#             break

#     # eq gap
#     types_eval = [sample_airline_types(n_airlines, np.arange(m_slots), rng) for _t in range(n_mc_eval)]
#     stay_u = np.array([eu_deviator(types, alpha_len) for types in types_eval], dtype=float)

#     best_u = []
#     for types in types_eval:
#         best = -1e18
#         for length in range(1, L + 1):
#             for a_candidate in alpha_grid:
#                 best = max(best, eu_deviator(types, alpha_len, dev_len=length, dev_alpha=a_candidate))
#         best_u.append(best)

#     eq_gap = float(np.mean(np.array(best_u) - stay_u))
#     return alpha_len, eq_gap
























# # src/equilibrium.py
# import numpy as np
# from .metrics import airline_utilities, value_of_bundle
# from .mechanisms import sequential_first_price, interval_pay_as_bid
# from .models import sample_airline_types


# def solve_alpha_sequential_fp_groups(
#     n_airlines: int,
#     m_slots: int,
#     rng: np.random.Generator,
#     cap_per_airline: int,
#     alpha_grid=None,
#     n_mc: int = 30,
#     n_passes: int = 4,
#     damping: float = 0.6,
#     n_mc_eval: int = 80,
#     deviator: int = 0,
# ):
#     if alpha_grid is None:
#         alpha_grid = np.linspace(0.4, 1.0, 13)
#     alpha_grid = np.asarray(alpha_grid, dtype=float)

#     def group_of_slot(s: int) -> int:
#         if s <= 2:
#             return 0
#         elif s <= 6:
#             return 1
#         else:
#             return 2

#     G = 3
#     alpha = np.full(G, 0.8, dtype=float)

#     def bids_from_types(types, alpha_vec, g_dev=None, alpha_g_dev=None):
#         bids = np.zeros((n_airlines, m_slots), dtype=float)
#         for i, t in enumerate(types):
#             for s in range(m_slots):
#                 g = group_of_slot(s)
#                 a = float(alpha_vec[g])
#                 if (g_dev is not None) and (i == deviator) and (g == g_dev):
#                     a = float(alpha_g_dev)
#                 bids[i, s] = a * float(t.a[s])
#         return bids

#     def u_deviator(types, alpha_vec, g_dev=None, alpha_g_dev=None):
#         bids = bids_from_types(types, alpha_vec, g_dev=g_dev, alpha_g_dev=alpha_g_dev)
#         alloc, payments, _ = sequential_first_price(bids, cap_per_airline=cap_per_airline)
#         return float(airline_utilities(types, alloc, payments)[deviator])

#     for _ in range(n_passes):
#         prev = alpha.copy()
#         types_mc = [sample_airline_types(n_airlines, np.arange(m_slots), rng) for _t in range(n_mc)]

#         for g in range(G):
#             eus = []
#             for a_candidate in alpha_grid:
#                 u_vals = [u_deviator(types, alpha, g_dev=g, alpha_g_dev=a_candidate) for types in types_mc]
#                 eus.append(float(np.mean(u_vals)))
#             a_br = float(alpha_grid[int(np.argmax(eus))])
#             alpha[g] = (1.0 - damping) * alpha[g] + damping * a_br

#         if float(np.max(np.abs(alpha - prev))) < 1e-3:
#             break

#     types_eval = [sample_airline_types(n_airlines, np.arange(m_slots), rng) for _t in range(n_mc_eval)]
#     stay_u = np.array([u_deviator(types, alpha) for types in types_eval], dtype=float)

#     best_u = []
#     for types in types_eval:
#         best = -1e18
#         for g in range(G):
#             for a_candidate in alpha_grid:
#                 best = max(best, u_deviator(types, alpha, g_dev=g, alpha_g_dev=a_candidate))
#         best_u.append(best)

#     eq_gap = float(np.mean(np.array(best_u) - stay_u))
#     return alpha, eq_gap


# def solve_alpha_interval_by_length(
#     n_airlines: int,
#     m_slots: int,
#     rng: np.random.Generator,
#     cap_per_airline: int,
#     max_interval_len: int = 3,
#     alpha_grid=None,
#     n_mc: int = 30,
#     n_passes: int = 3,
#     damping: float = 0.6,
#     n_mc_eval: int = 80,
#     deviator: int = 0,
# ):
#     if alpha_grid is None:
#         alpha_grid = np.linspace(0.4, 1.0, 13)
#     alpha_grid = np.asarray(alpha_grid, dtype=float)

#     L = int(max_interval_len)
#     alpha_len = np.full(L, 0.8, dtype=float)

#     intervals = [(l, r) for l in range(m_slots) for r in range(l, min(m_slots, l + L))]

#     def build_bids(types, alpha_vec, dev_len=None, dev_alpha=None):
#         bids_for_intervals = []
#         for i in range(n_airlines):
#             d = {}
#             for (l, r) in intervals:
#                 bundle = np.arange(l, r + 1, dtype=int)
#                 length = (r - l + 1)
#                 a = float(alpha_vec[length - 1])

#                 # unilateral deviation ONLY for deviator airline
#                 if (dev_len is not None) and (i == deviator) and (length == dev_len):
#                     a = float(dev_alpha)

#                 d[(l, r)] = a * float(value_of_bundle(types[i], bundle))
#             bids_for_intervals.append(d)
#         return bids_for_intervals

#     def u_deviator(types, alpha_vec, dev_len=None, dev_alpha=None):
#         bids_for_intervals = build_bids(types, alpha_vec, dev_len=dev_len, dev_alpha=dev_alpha)
#         alloc, payments, _ = interval_pay_as_bid(
#             types=types,
#             bids_for_intervals=bids_for_intervals,
#             m_slots=m_slots,
#             max_interval_len=L,
#             cap_per_airline=cap_per_airline,
#         )
#         return float(airline_utilities(types, alloc, payments)[deviator])

#     for _ in range(n_passes):
#         prev = alpha_len.copy()
#         types_mc = [sample_airline_types(n_airlines, np.arange(m_slots), rng) for _t in range(n_mc)]

#         for length in range(1, L + 1):
#             eus = []
#             for a_candidate in alpha_grid:
#                 u_vals = [u_deviator(types, alpha_len, dev_len=length, dev_alpha=a_candidate) for types in types_mc]
#                 eus.append(float(np.mean(u_vals)))
#             a_br = float(alpha_grid[int(np.argmax(eus))])
#             idx = length - 1
#             alpha_len[idx] = (1.0 - damping) * alpha_len[idx] + damping * a_br

#         if float(np.max(np.abs(alpha_len - prev))) < 1e-3:
#             break

#     types_eval = [sample_airline_types(n_airlines, np.arange(m_slots), rng) for _t in range(n_mc_eval)]
#     stay_u = np.array([u_deviator(types, alpha_len) for types in types_eval], dtype=float)

#     best_u = []
#     for types in types_eval:
#         best = -1e18
#         for length in range(1, L + 1):
#             for a_candidate in alpha_grid:
#                 best = max(best, u_deviator(types, alpha_len, dev_len=length, dev_alpha=a_candidate))
#         best_u.append(best)

#     eq_gap = float(np.mean(np.array(best_u) - stay_u))
#     return alpha_len, eq_gap





# src/equilibrium.py
import numpy as np
from .metrics import airline_utilities, value_of_bundle
from .mechanisms import sequential_first_price, interval_pay_as_bid
from .models import sample_airline_types


_KIND_TO_IDX = {"hub": 0, "p2p": 1}


def solve_alpha_sequential_fp_by_kind_groups(
    n_airlines: int,
    m_slots: int,
    rng: np.random.Generator,
    cap_per_airline: int,
    alpha_grid=None,
    n_mc: int = 30,
    n_passes: int = 5,
    damping: float = 0.6,
    n_mc_eval: int = 80,
):
    """
    Two-population, 3-group strategy class:
      b_i(s) = alpha[kind(i), g(s)] * a_i(s)
    where kind in {hub, p2p} and g(s) in {early, mid, late}.

    Returns:
      alpha_seq: shape (2,3)
      eq_gap: avg unilateral gain of deviating ONE coordinate (kind,group) for a single deviator
    """

    if alpha_grid is None:
        alpha_grid = np.linspace(0.4, 1.0, 13)
    alpha_grid = np.asarray(alpha_grid, dtype=float)

    def group_of_slot(s: int) -> int:
        if s <= 2:
            return 0
        elif s <= 6:
            return 1
        else:
            return 2

    K, G = 2, 3
    alpha = np.full((K, G), 0.8, dtype=float)

    def bids_from_types(types, alpha_mat, dev=None):
        """
        dev can be (dev_i, dev_kind_idx, dev_group_idx, dev_alpha)
        """
        bids = np.zeros((n_airlines, m_slots), dtype=float)
        for i, t in enumerate(types):
            k = _KIND_TO_IDX.get(t.kind, 1)
            for s in range(m_slots):
                g = group_of_slot(s)
                a = float(alpha_mat[k, g])
                if dev is not None:
                    dev_i, dk, dg, da = dev
                    if i == dev_i and k == dk and g == dg:
                        a = float(da)
                bids[i, s] = a * float(t.a[s])
        return bids

    def u_of_deviator(types, alpha_mat, dev_i: int, dk=None, dg=None, da=None):
        dev = None
        if dk is not None:
            dev = (dev_i, dk, dg, da)
        bids = bids_from_types(types, alpha_mat, dev=dev)
        alloc, payments, _ = sequential_first_price(bids, cap_per_airline=cap_per_airline)
        return float(airline_utilities(types, alloc, payments)[dev_i])

    # --- solve by alternating best responses over (kind,group) ---
    for _ in range(n_passes):
        prev = alpha.copy()
        types_mc = [sample_airline_types(n_airlines, np.arange(m_slots), rng) for _t in range(n_mc)]

        for dk in range(K):
            for dg in range(G):
                eus = []
                for a_candidate in alpha_grid:
                    u_vals = []
                    for types in types_mc:
                        # choose a deviator of this kind if possible, else skip this sample
                        dev_candidates = [i for i, t in enumerate(types) if _KIND_TO_IDX.get(t.kind, 1) == dk]
                        if not dev_candidates:
                            continue
                        dev_i = dev_candidates[0]
                        u_vals.append(u_of_deviator(types, alpha, dev_i, dk=dk, dg=dg, da=a_candidate))
                    eus.append(float(np.mean(u_vals)) if len(u_vals) else -1e18)

                a_br = float(alpha_grid[int(np.argmax(eus))])
                alpha[dk, dg] = (1.0 - damping) * alpha[dk, dg] + damping * a_br

        if float(np.max(np.abs(alpha - prev))) < 1e-3:
            break

    # --- eq gap: unilateral deviation gain averaged over random deviators (by kind availability) ---
    types_eval = [sample_airline_types(n_airlines, np.arange(m_slots), rng) for _t in range(n_mc_eval)]

    gaps = []
    for types in types_eval:
        # pick deviator as airline 0 for consistency
        dev_i = 0
        dk = _KIND_TO_IDX.get(types[dev_i].kind, 1)

        stay = u_of_deviator(types, alpha, dev_i)

        best = -1e18
        for dg in range(G):
            for a_candidate in alpha_grid:
                best = max(best, u_of_deviator(types, alpha, dev_i, dk=dk, dg=dg, da=a_candidate))

        gaps.append(best - stay)

    eq_gap = float(np.mean(np.array(gaps, dtype=float)))
    return alpha, eq_gap


def solve_alpha_interval_by_kind_length(
    n_airlines: int,
    m_slots: int,
    rng: np.random.Generator,
    cap_per_airline: int,
    max_interval_len: int = 3,
    alpha_grid=None,
    n_mc: int = 30,
    n_passes: int = 4,
    damping: float = 0.6,
    n_mc_eval: int = 80,
):
    """
    Two-population, per-length strategy class:
      b_i(B) = alpha[kind(i), |B|] * v_i(B)

    Returns:
      alpha_int: shape (2, L)
      eq_gap: avg unilateral gain by deviating ONE length coordinate for deviator airline 0
    """

    if alpha_grid is None:
        alpha_grid = np.linspace(0.4, 1.0, 13)
    alpha_grid = np.asarray(alpha_grid, dtype=float)

    L = int(max_interval_len)
    K = 2
    alpha = np.full((K, L), 0.8, dtype=float)

    intervals = [(l, r) for l in range(m_slots) for r in range(l, min(m_slots, l + L))]

    def build_bids(types, alpha_mat, dev=None):
        """
        dev can be (dev_i, dev_kind_idx, dev_len, dev_alpha)
        """
        bids_for_intervals = []
        for i, t in enumerate(types):
            k = _KIND_TO_IDX.get(t.kind, 1)
            d = {}
            for (l, r) in intervals:
                bundle = np.arange(l, r + 1, dtype=int)
                length = int(r - l + 1)
                a = float(alpha_mat[k, length - 1])
                if dev is not None:
                    dev_i, dk, dlen, da = dev
                    if i == dev_i and k == dk and length == dlen:
                        a = float(da)
                d[(l, r)] = a * float(value_of_bundle(t, bundle))
            bids_for_intervals.append(d)
        return bids_for_intervals

    def u_of_deviator(types, alpha_mat, dev_i: int, dk=None, dlen=None, da=None):
        dev = None
        if dk is not None:
            dev = (dev_i, dk, dlen, da)
        bids_for_intervals = build_bids(types, alpha_mat, dev=dev)
        alloc, payments, _ = interval_pay_as_bid(
            types=types,
            bids_for_intervals=bids_for_intervals,
            m_slots=m_slots,
            max_interval_len=L,
            cap_per_airline=cap_per_airline,
        )
        return float(airline_utilities(types, alloc, payments)[dev_i])

    for _ in range(n_passes):
        prev = alpha.copy()
        types_mc = [sample_airline_types(n_airlines, np.arange(m_slots), rng) for _t in range(n_mc)]

        for dk in range(K):
            for dlen in range(1, L + 1):
                eus = []
                for a_candidate in alpha_grid:
                    u_vals = []
                    for types in types_mc:
                        dev_candidates = [i for i, t in enumerate(types) if _KIND_TO_IDX.get(t.kind, 1) == dk]
                        if not dev_candidates:
                            continue
                        dev_i = dev_candidates[0]
                        u_vals.append(u_of_deviator(types, alpha, dev_i, dk=dk, dlen=dlen, da=a_candidate))
                    eus.append(float(np.mean(u_vals)) if len(u_vals) else -1e18)

                a_br = float(alpha_grid[int(np.argmax(eus))])
                alpha[dk, dlen - 1] = (1.0 - damping) * alpha[dk, dlen - 1] + damping * a_br

        if float(np.max(np.abs(alpha - prev))) < 1e-3:
            break

    # eq gap for deviator airline 0
    types_eval = [sample_airline_types(n_airlines, np.arange(m_slots), rng) for _t in range(n_mc_eval)]
    gaps = []
    for types in types_eval:
        dev_i = 0
        dk = _KIND_TO_IDX.get(types[dev_i].kind, 1)

        stay = u_of_deviator(types, alpha, dev_i)
        best = -1e18
        for dlen in range(1, L + 1):
            for a_candidate in alpha_grid:
                best = max(best, u_of_deviator(types, alpha, dev_i, dk=dk, dlen=dlen, da=a_candidate))
        gaps.append(best - stay)

    eq_gap = float(np.mean(np.array(gaps, dtype=float)))
    return alpha, eq_gap