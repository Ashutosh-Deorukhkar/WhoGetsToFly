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
