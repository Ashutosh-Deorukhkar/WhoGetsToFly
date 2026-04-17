# # src/mechanisms.py
# import numpy as np
# from .models import AirlineType

# def sequential_first_price(bids_per_slot: np.ndarray, cap_per_airline: int | None = None):
#     n, m = bids_per_slot.shape
#     alloc = [[] for _ in range(n)]
#     payments = np.zeros(n, dtype=float)

#     for s in range(m):
#         eligible = np.ones(n, dtype=bool)
#         if cap_per_airline is not None:
#             for i in range(n):
#                 if len(alloc[i]) >= cap_per_airline:
#                     eligible[i] = False
#         if not np.any(eligible):
#             continue

#         b = bids_per_slot[:, s].copy()
#         b[~eligible] = -1.0
#         winner = int(np.argmax(b))
#         if b[winner] <= 0:
#             continue

#         alloc[winner].append(s)
#         payments[winner] += float(bids_per_slot[winner, s])

#     alloc_sets = [np.array(a, dtype=int) for a in alloc]
#     return alloc_sets, payments, {"method": "sequential_fp"}


# def _build_intervals_from_bids(bids_for_intervals, max_interval_len, m_slots):
#     """
#     Returns flat interval list:
#       intervals[j] = (l, r, i, bid, length)
#     Only includes positive bids.
#     """
#     intervals = []
#     n = len(bids_for_intervals)
#     for i in range(n):
#         for (l, r), b in bids_for_intervals[i].items():
#             if b <= 0:
#                 continue
#             if r < l:
#                 continue
#             if (r - l + 1) > max_interval_len:
#                 continue
#             if l < 0 or r >= m_slots:
#                 continue
#             intervals.append((l, r, i, float(b), int(r - l + 1)))
#     # sort by end time for WIS DP
#     intervals.sort(key=lambda x: (x[1], x[0]))
#     return intervals


# def _compute_p(intervals):
#     """p[j] = largest index < j that doesn't overlap j (by end-time sorted intervals)."""
#     ends = [it[1] for it in intervals]  # r
#     p = [-1] * len(intervals)
#     for j, (l_j, r_j, *_rest) in enumerate(intervals):
#         # binary search for rightmost interval with end < l_j
#         lo, hi = 0, j - 1
#         ans = -1
#         while lo <= hi:
#             mid = (lo + hi) // 2
#             if ends[mid] < l_j:
#                 ans = mid
#                 lo = mid + 1
#             else:
#                 hi = mid - 1
#         p[j] = ans
#     return p


# def _wis_dp_with_cap(intervals, cap_total_len):
#     """
#     Weighted interval scheduling with 'total length' cap.
#     Returns chosen interval indices (in 'intervals' list).
#     """
#     J = len(intervals)
#     if J == 0 or cap_total_len <= 0:
#         return []

#     p = _compute_p(intervals)

#     # dp[j][c] for j in [0..J], c in [0..cap]
#     dp = np.zeros((J + 1, cap_total_len + 1), dtype=float)
#     take = np.zeros((J + 1, cap_total_len + 1), dtype=bool)

#     for j in range(1, J + 1):
#         l, r, i, w, length = intervals[j - 1]
#         pj = p[j - 1] + 1  # shift because dp is 1-indexed in j

#         for c in range(cap_total_len + 1):
#             best_skip = dp[j - 1, c]
#             best_take = -1.0
#             if length <= c:
#                 best_take = w + dp[pj, c - length]
#             if best_take > best_skip:
#                 dp[j, c] = best_take
#                 take[j, c] = True
#             else:
#                 dp[j, c] = best_skip

#     # backtrack
#     chosen = []
#     j = J
#     c = cap_total_len
#     while j > 0 and c >= 0:
#         if take[j, c]:
#             chosen.append(j - 1)
#             length = intervals[j - 1][4]
#             pj = p[j - 1] + 1
#             c -= length
#             j = pj
#         else:
#             j -= 1

#     chosen.reverse()
#     return chosen


# def interval_pay_as_bid(
#     types: list[AirlineType],
#     bids_for_intervals: list[dict[tuple[int, int], float]],
#     m_slots: int,
#     max_interval_len: int = 3,
#     cap_per_airline: int | None = None,
# ):
#     """
#     Restricted interval mechanism (pay-as-bid), solved optimally by DP:

#       WDP: choose non-overlapping interval bids maximizing total bid
#            with a total-slot cap_per_airline per airline.

#     Implementation trick:
#       - enforce per-airline cap by filtering bids that exceed cap length, and
#       - enforce cap during reconstruction by not allowing an airline to exceed cap.
#     For strict correctness with cap, we solve with a global cap on total length per airline
#     by splitting into per-airline capacity in the state would be huge.
#     So we keep cap small (e.g., 3) and enforce it in bid generation:
#       only generate intervals of length <= cap, and at most one winning interval per airline
#       if cap is very small.
#     """
#     n = len(types)
#     if cap_per_airline is None:
#         cap_per_airline = m_slots

#     intervals = _build_intervals_from_bids(bids_for_intervals, max_interval_len, m_slots)

#     # IMPORTANT: to keep DP exact with cap, we enforce: at most ONE interval can win per airline.
#     # This matches "airline submits at most one interval bid that can be accepted" (XOR-like).
#     # If you want multiple intervals per airline, we’d switch to OR-Tools or a bigger DP state.
#     # For now: keep this restriction for clarity/tractability.
#     best_per_airline = {}
#     for idx, (l, r, i, w, length) in enumerate(intervals):
#         if length > cap_per_airline:
#             continue
#         key = i
#         if key not in best_per_airline or w > best_per_airline[key][0]:
#             best_per_airline[key] = (w, idx)

#     filtered = [intervals[idx] for (_w, idx) in best_per_airline.values()]
#     filtered.sort(key=lambda x: (x[1], x[0]))

#     chosen_idx = _wis_dp_with_cap(filtered, cap_total_len=m_slots)  # global cap irrelevant now
#     chosen = [filtered[k] for k in chosen_idx]

#     taken = np.zeros(m_slots, dtype=bool)
#     alloc = [[] for _ in range(n)]
#     payments = np.zeros(n, dtype=float)

#     for (l, r, i, w, length) in chosen:
#         if np.any(taken[l:r + 1]):
#             continue
#         if (len(alloc[i]) + length) > cap_per_airline:
#             continue
#         taken[l:r + 1] = True
#         alloc[i].extend(range(l, r + 1))
#         payments[i] += w

#     alloc_sets = [np.array(sorted(set(a)), dtype=int) for a in alloc]
#     return alloc_sets, payments, {"method": "dp_pay_as_bid", "chosen": len(chosen)}


# def vcg_interval(
#     types: list[AirlineType],
#     bids_for_intervals: list[dict[tuple[int, int], float]],
#     m_slots: int,
#     max_interval_len: int = 3,
#     cap_per_airline: int | None = None,
# ):
#     """
#     Restricted-interval VCG benchmark:
#       - same bidding language as interval mechanism (contiguous intervals)
#       - allocation = maximize total reported bid (DP)
#       - payment p_i = W_{-i}^* - W_{-i}(S^*)
#     """
#     n = len(types)
#     if cap_per_airline is None:
#         cap_per_airline = m_slots

#     alloc_all, pay_dummy, info = interval_pay_as_bid(
#         types=types,
#         bids_for_intervals=bids_for_intervals,
#         m_slots=m_slots,
#         max_interval_len=max_interval_len,
#         cap_per_airline=cap_per_airline,
#     )

#     # total reported welfare under chosen allocation
#     def reported_welfare(bids_for_intervals, alloc_sets):
#         total = 0.0
#         for i in range(n):
#             # find which interval was effectively chosen: since we restricted to <=1 interval per airline,
#             # recover the interval whose slots match alloc_sets[i]
#             s = alloc_sets[i]
#             if s.size == 0:
#                 continue
#             l, r = int(s.min()), int(s.max())
#             total += float(bids_for_intervals[i].get((l, r), 0.0))
#         return float(total)

#     W_star = reported_welfare(bids_for_intervals, alloc_all)

#     payments = np.zeros(n, dtype=float)
#     for i in range(n):
#         # solve without bidder i
#         bids_minus = [bids_for_intervals[j] if j != i else {} for j in range(n)]
#         alloc_minus, _pay_minus, _ = interval_pay_as_bid(
#             types=types,
#             bids_for_intervals=bids_minus,
#             m_slots=m_slots,
#             max_interval_len=max_interval_len,
#             cap_per_airline=cap_per_airline,
#         )
#         W_minus_star = reported_welfare(bids_minus, alloc_minus)

#         # others' welfare in the original allocation
#         W_minus_in_star = W_star
#         # subtract i's own reported value in the chosen alloc
#         s_i = alloc_all[i]
#         if s_i.size > 0:
#             l, r = int(s_i.min()), int(s_i.max())
#             W_minus_in_star -= float(bids_for_intervals[i].get((l, r), 0.0))

#         payments[i] = float(W_minus_star - W_minus_in_star)

#     return alloc_all, payments, {"method": "dp_vcg_interval"}

# src/mechanisms.py
import numpy as np


def sequential_first_price(bids_per_slot: np.ndarray, cap_per_airline=None):
    n, m = bids_per_slot.shape
    alloc = [[] for _ in range(n)]
    payments = np.zeros(n, dtype=float)

    for s in range(m):
        eligible = np.ones(n, dtype=bool)
        if cap_per_airline is not None:
            for i in range(n):
                if len(alloc[i]) >= cap_per_airline:
                    eligible[i] = False
        if not np.any(eligible):
            continue

        b = bids_per_slot[:, s].copy()
        b[~eligible] = -1.0
        winner = int(np.argmax(b))
        if b[winner] <= 0:
            continue

        alloc[winner].append(s)
        payments[winner] += float(bids_per_slot[winner, s])

    alloc_sets = [np.array(a, dtype=int) for a in alloc]
    return alloc_sets, payments, {"method": "sequential_fp"}


def _build_intervals_from_bids(bids_for_intervals, max_interval_len, m_slots):
    """
    Returns flat interval list:
      intervals[j] = (l, r, i, bid, length)
    Only includes positive bids.
    """
    intervals = []
    n = len(bids_for_intervals)
    for i in range(n):
        for (l, r), b in bids_for_intervals[i].items():
            if b <= 0:
                continue
            if r < l:
                continue
            if (r - l + 1) > max_interval_len:
                continue
            if l < 0 or r >= m_slots:
                continue
            intervals.append((l, r, i, float(b), int(r - l + 1)))
    # sort by end time for WIS DP (fast solver)
    intervals.sort(key=lambda x: (x[1], x[0]))
    return intervals


def _compute_p(intervals):
    """p[j] = largest index < j that doesn't overlap j (by end-time sorted intervals)."""
    ends = [it[1] for it in intervals]  # r
    p = [-1] * len(intervals)
    for j, (l_j, r_j, *_rest) in enumerate(intervals):
        lo, hi = 0, j - 1
        ans = -1
        while lo <= hi:
            mid = (lo + hi) // 2
            if ends[mid] < l_j:
                ans = mid
                lo = mid + 1
            else:
                hi = mid - 1
        p[j] = ans
    return p


def _wis_dp(intervals):
    """
    Weighted interval scheduling (no per-airline cap, no XOR).
    Maximizes sum of bids subject to non-overlap only.
    Returns indices of chosen intervals in 'intervals'.
    """
    J = len(intervals)
    if J == 0:
        return []

    p = _compute_p(intervals)

    dp = np.zeros(J + 1, dtype=float)
    take = np.zeros(J + 1, dtype=bool)

    for j in range(1, J + 1):
        l, r, i, w, length = intervals[j - 1]
        skip = dp[j - 1]
        use = float(w) + dp[p[j - 1] + 1]
        if use > skip:
            dp[j] = use
            take[j] = True
        else:
            dp[j] = skip

    chosen = []
    j = J
    while j > 0:
        if take[j]:
            chosen.append(j - 1)
            j = p[j - 1] + 1
        else:
            j -= 1
    chosen.reverse()
    return chosen


def _wdp_exact_small(intervals, n_airlines, m_slots, cap_per_airline, max_nodes=200000):
    """
    Exact WDP with:
      - non-overlap across slots
      - per-airline cap on total slots
    Uses branch-and-bound. This is ONLY intended for small cases (m_slots=10, cap<=3).
    max_nodes prevents blow-ups.
    Returns list of chosen interval tuples.
    """
    if not intervals:
        return []

    # sort by bid descending for bounding
    intervals = sorted(intervals, key=lambda x: x[3], reverse=True)
    J = len(intervals)

    masks = []
    for (l, r, _i, _w, _length) in intervals:
        mask = 0
        for s in range(l, r + 1):
            mask |= (1 << s)
        masks.append(mask)

    suffix_sum = np.zeros(J + 1, dtype=float)
    for j in range(J - 1, -1, -1):
        suffix_sum[j] = suffix_sum[j + 1] + float(intervals[j][3])

    best_val = -1e18
    best_choice = []

    counts = np.zeros(n_airlines, dtype=int)
    choice = []
    nodes = 0

    def dfs(j, taken_mask, cur_val):
        nonlocal best_val, best_choice, nodes
        nodes += 1
        if nodes > max_nodes:
            return

        if cur_val + suffix_sum[j] <= best_val:
            return

        if j == J:
            if cur_val > best_val:
                best_val = cur_val
                best_choice = choice.copy()
            return

        l, r, i, w, length = intervals[j]
        mask = masks[j]

        # skip
        dfs(j + 1, taken_mask, cur_val)

        # take
        if (taken_mask & mask) == 0 and (counts[i] + length) <= cap_per_airline:
            counts[i] += length
            choice.append(j)
            dfs(j + 1, taken_mask | mask, cur_val + float(w))
            choice.pop()
            counts[i] -= length

    dfs(0, 0, 0.0)
    return [intervals[idx] for idx in best_choice], nodes


def interval_pay_as_bid(
    types,
    bids_for_intervals,
    m_slots,
    max_interval_len=3,
    cap_per_airline=None,
    solve_mode="fast",      # "fast" or "exact"
    exact_max_nodes=200000  # safety cap for exact mode
):
    """
    Restricted interval mechanism (pay-as-bid).

    solve_mode="fast":
      - maximizes total bid subject to non-overlap ONLY (WIS DP)
      - then enforces per-airline cap greedily during reconstruction
      - this is what keeps equilibrium runs fast

    solve_mode="exact":
      - exact WDP with per-airline cap (branch-and-bound) for small m_slots
      - use for your plotting/benchmark runs, NOT inside equilibrium loops
    """
    n = len(types)
    if cap_per_airline is None:
        cap_per_airline = m_slots

    intervals = _build_intervals_from_bids(bids_for_intervals, max_interval_len, m_slots)

    if solve_mode == "exact":
        chosen, nodes = _wdp_exact_small(
            intervals=intervals,
            n_airlines=n,
            m_slots=m_slots,
            cap_per_airline=cap_per_airline,
            max_nodes=exact_max_nodes,
        )
        info = {"method": "interval_pab_exact", "chosen": len(chosen), "nodes": int(nodes), "chosen_intervals": chosen}
    else:
        chosen_idx = _wis_dp(intervals)
        chosen = [intervals[k] for k in chosen_idx]
        info = {"method": "interval_pab_fast_wis", "chosen": len(chosen), "chosen_intervals": chosen}

    taken = np.zeros(m_slots, dtype=bool)
    alloc = [[] for _ in range(n)]
    payments = np.zeros(n, dtype=float)

    for (l, r, i, w, length) in chosen:
        if np.any(taken[l:r + 1]):
            continue
        if (len(alloc[i]) + length) > cap_per_airline:
            continue
        taken[l:r + 1] = True
        alloc[i].extend(range(l, r + 1))
        payments[i] += float(w)

    alloc_sets = [np.array(sorted(set(a)), dtype=int) for a in alloc]
    return alloc_sets, payments, info


def vcg_interval(
    types,
    bids_for_intervals,
    m_slots,
    max_interval_len=3,
    cap_per_airline=None,
    solve_mode="fast",
    exact_max_nodes=200000
):
    """
    VCG payments on top of the allocation rule defined by interval_pay_as_bid(..., solve_mode=...).
    This makes VCG a consistent benchmark WITH RESPECT TO that allocation rule.

    If you want "truthful welfare benchmark" behavior in plots, run with solve_mode="exact".
    """
    n = len(types)
    if cap_per_airline is None:
        cap_per_airline = m_slots

    alloc_all, _pay_dummy, info_all = interval_pay_as_bid(
        types=types,
        bids_for_intervals=bids_for_intervals,
        m_slots=m_slots,
        max_interval_len=max_interval_len,
        cap_per_airline=cap_per_airline,
        solve_mode=solve_mode,
        exact_max_nodes=exact_max_nodes,
    )
    chosen_all = info_all.get("chosen_intervals", [])
    W_star = float(sum(w for (_l, _r, _i, w, _len) in chosen_all))

    payments = np.zeros(n, dtype=float)
    for i in range(n):
        bids_minus = [bids_for_intervals[j] if j != i else {} for j in range(n)]
        _alloc_minus, _pay_minus, info_minus = interval_pay_as_bid(
            types=types,
            bids_for_intervals=bids_minus,
            m_slots=m_slots,
            max_interval_len=max_interval_len,
            cap_per_airline=cap_per_airline,
            solve_mode=solve_mode,
            exact_max_nodes=exact_max_nodes,
        )
        chosen_minus = info_minus.get("chosen_intervals", [])
        W_minus_star = float(sum(w for (_l, _r, _j, w, _len) in chosen_minus))

        W_minus_in_star = float(sum(w for (_l, _r, j, w, _len) in chosen_all if j != i))
        payments[i] = float(W_minus_star - W_minus_in_star)

    return alloc_all, payments, {"method": f"vcg_interval_{solve_mode}", "W_star": W_star}