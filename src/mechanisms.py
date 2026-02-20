import numpy as np

def _flatten_bids(bids: np.ndarray):
    # bids shape: (n_airlines, max_demand)
    n, k = bids.shape
    flat = []
    for i in range(n):
        for j in range(k):
            flat.append((bids[i, j], i, j))  # (bid, airline, unit-index)
    return flat

def allocate_top_m_units(bids: np.ndarray, m_slots: int):
    flat = _flatten_bids(bids)
    flat.sort(key=lambda x: x[0], reverse=True)
    winners = flat[:m_slots]
    alloc = np.zeros(bids.shape[0], dtype=int)
    for bid, i, j in winners:
        if bid > 0:
            alloc[i] += 1
    clearing = winners[-1][0] if len(winners) > 0 else 0.0
    return alloc, winners, clearing

def uniform_price_auction(bids: np.ndarray, m_slots: int):
    alloc, winners, clearing = allocate_top_m_units(bids, m_slots)
    price = clearing
    payments = alloc.astype(float) * price
    return alloc, payments, {"clearing_price": float(price)}

def discriminatory_price_auction(bids: np.ndarray, m_slots: int):
    alloc, winners, clearing = allocate_top_m_units(bids, m_slots)
    payments = np.zeros(bids.shape[0], dtype=float)
    for bid, i, j in winners:
        if bid > 0:
            payments[i] += bid
    return alloc, payments, {"clearing_price": float(clearing)}

def welfare_maximizing_allocation(values: np.ndarray, m_slots: int):
    # For additive marginal values, welfare max = allocate top m marginal values
    alloc, winners, _ = allocate_top_m_units(values, m_slots)
    return alloc, winners