# src/mechanisms.py
import numpy as np
from ortools.sat.python import cp_model


# ─────────────────────────────────────────────
# Sequential First-Price
# ─────────────────────────────────────────────

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


# ─────────────────────────────────────────────
# Interval Pay-As-Bid helpers
# ─────────────────────────────────────────────

def _build_intervals_from_bids(bids_for_intervals, max_interval_len, m_slots):
    intervals = []
    for i in range(len(bids_for_intervals)):
        for (l, r), b in bids_for_intervals[i].items():
            if b <= 0:
                continue
            if r < l or (r - l + 1) > max_interval_len:
                continue
            if l < 0 or r >= m_slots:
                continue
            intervals.append((l, r, i, float(b), int(r - l + 1)))
    intervals.sort(key=lambda x: (x[1], x[0]))
    return intervals


def _compute_p(intervals):
    ends = [it[1] for it in intervals]
    p = [-1] * len(intervals)
    for j, (l_j, r_j, *_rest) in enumerate(intervals):
        lo, hi, ans = 0, j - 1, -1
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
    if not intervals:
        return [], 0
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
        dfs(j + 1, taken_mask, cur_val)
        if (taken_mask & mask) == 0 and (counts[i] + length) <= cap_per_airline:
            counts[i] += length
            choice.append(j)
            dfs(j + 1, taken_mask | mask, cur_val + float(w))
            choice.pop()
            counts[i] -= length

    dfs(0, 0, 0.0)
    return [intervals[idx] for idx in best_choice], nodes


# ─────────────────────────────────────────────
# Interval Pay-As-Bid
# ─────────────────────────────────────────────

def interval_pay_as_bid(
    types,
    bids_for_intervals,
    m_slots,
    max_interval_len=3,
    cap_per_airline=None,
    solve_mode="fast",
    exact_max_nodes=200000,
):
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
        info = {"method": "interval_pab_exact", "chosen": len(chosen),
                "nodes": int(nodes), "chosen_intervals": chosen}
    else:
        chosen_idx = _wis_dp(intervals)
        chosen = [intervals[k] for k in chosen_idx]
        info = {"method": "interval_pab_fast_wis", "chosen": len(chosen),
                "chosen_intervals": chosen}

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


# ─────────────────────────────────────────────
# Interval VCG (restricted — kept as baseline)
# ─────────────────────────────────────────────

def vcg_interval(
    types,
    bids_for_intervals,
    m_slots,
    max_interval_len=3,
    cap_per_airline=None,
    solve_mode="fast",
    exact_max_nodes=200000,
):
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


# ─────────────────────────────────────────────
# Full Combinatorial WDP via CP-SAT
# ─────────────────────────────────────────────

def _solve_wdp_cpsat(bundle_values, n_airlines, m_slots, cap_per_airline):
    """
    Solve the Winner Determination Problem using CP-SAT.

    bundle_values: list of (airline_idx, frozenset_of_slots, value)
    Returns: list of (airline_idx, frozenset_of_slots, value) for winning bundles.

    Constraints:
      - Each slot allocated to at most one airline
      - Each airline wins at most cap_per_airline slots total
      - Maximize total reported value
    """
    model = cp_model.CpModel()

    # Scale values to integers (CP-SAT requires integer objective)
    scale = 1000
    scaled_values = [int(round(v * scale)) for (_, _, v) in bundle_values]

    # Binary variable x[j] = 1 if bundle j is allocated
    x = [model.new_bool_var(f"x_{j}") for j in range(len(bundle_values))]

    # Constraint 1: each slot allocated at most once
    for s in range(m_slots):
        model.add(
            sum(x[j] for j, (i, slots, v) in enumerate(bundle_values) if s in slots) <= 1
        )

    # Constraint 2: each airline wins at most cap_per_airline slots
    for i in range(n_airlines):
        model.add(
            sum(x[j] * len(slots)
                for j, (ai, slots, v) in enumerate(bundle_values) if ai == i) <= cap_per_airline
        )

    # Objective: maximize total reported value
    model.maximize(sum(x[j] * scaled_values[j] for j in range(len(bundle_values))))

    solver = cp_model.CpSolver()
    solver.parameters.log_search_progress = False
    solver.parameters.max_time_in_seconds = 10.0
    status = solver.solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return []

    return [
        bundle_values[j]
        for j in range(len(bundle_values))
        if solver.value(x[j]) == 1
    ]


def _build_all_bundles(types, m_slots, cap_per_airline):
    """
    Build all non-empty subsets of slots up to cap_per_airline size
    with their TRUE valuations for each airline.

    Returns list of (airline_idx, frozenset_of_slots, true_value).
    Only includes bundles with positive value.
    """
    from itertools import combinations

    bundles = []
    for i, t in enumerate(types):
        for size in range(1, cap_per_airline + 1):
            for slot_combo in combinations(range(m_slots), size):
                slot_array = np.array(slot_combo, dtype=int)
                val = float(_value_of_bundle_local(t, slot_array))
                if val > 0:
                    bundles.append((i, frozenset(slot_combo), val))
    return bundles


def _value_of_bundle_local(t, slot_indices):
    """Local copy of value_of_bundle to avoid circular imports."""
    if slot_indices.size == 0:
        return 0.0
    s = np.sort(slot_indices)
    base = float(np.sum(t.a[s]))
    adj = int(np.sum(s[1:] == s[:-1] + 1)) if s.size > 1 else 0
    bonus = float(t.beta * adj)
    excess = max(0, int(s.size) - int(t.k))
    penalty = float(t.lam * (excess ** 2))
    return base + bonus - penalty


# ─────────────────────────────────────────────
# Full Combinatorial VCG
# ─────────────────────────────────────────────

def vcg_combinatorial(types, m_slots, cap_per_airline):
    """
    Full Combinatorial VCG:
      - Bidding language: all subsets of slots up to cap_per_airline size
      - Airlines bid truthfully (VCG is incentive compatible)
      - Allocation: welfare-maximizing WDP solved by CP-SAT
      - Payments: VCG externality rule

    Returns (alloc_sets, payments, info).
    """
    n = len(types)

    # Build all bundles with true valuations (truthful bidding)
    all_bundles = _build_all_bundles(types, m_slots, cap_per_airline)

    # Solve WDP for all airlines
    winning = _solve_wdp_cpsat(all_bundles, n, m_slots, cap_per_airline)
    W_star = float(sum(v for (_, _, v) in winning))

    # Recover allocation
    alloc = [[] for _ in range(n)]
    for (i, slots, v) in winning:
        alloc[i].extend(list(slots))
    alloc_sets = [np.array(sorted(a), dtype=int) for a in alloc]

    # VCG payments: p_i = W*_{-i} - sum_{j != i} v_j(S*_j)
    payments = np.zeros(n, dtype=float)
    for i in range(n):
        # Others' value in the grand allocation
        W_others_in_star = float(sum(v for (ai, _, v) in winning if ai != i))

        # Solve WDP without airline i
        bundles_minus_i = [(ai, slots, v) for (ai, slots, v) in all_bundles if ai != i]
        winning_minus_i = _solve_wdp_cpsat(bundles_minus_i, n, m_slots, cap_per_airline)
        W_minus_i_star = float(sum(v for (_, _, v) in winning_minus_i))

        payments[i] = max(0.0, W_minus_i_star - W_others_in_star)

    total_welfare = float(sum(v for (_, _, v) in winning))

    return alloc_sets, payments, {
        "method": "vcg_combinatorial_cpsat",
        "W_star": total_welfare,
        "n_bundles": len(all_bundles),
    }
