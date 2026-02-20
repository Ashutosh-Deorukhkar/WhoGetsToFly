# Airport Slot Allocation Simulator (Multi-Unit Auctions)

This repository contains a simulation framework for studying **airport slot allocation** as a **multi-unit auction** with **strategic airlines**. It compares auction mechanisms under **truthful bidding** vs **strategic bid shading**, and evaluate outcomes using **efficiency**, **revenue**, **fairness**, and **equilibrium gap** diagnostics.

---
## Repository Structure

### `experiments/`
Experiment runners (entry points). These scripts call the simulator, aggregate results across seeds and scenarios, and optionally generate plots.

- **`run_small.py`**
  - Purpose: fast sanity checks on small scenarios (few airlines/slots).
  - Runs both **truthful** and **strategic** modes on a small set of cases.
  - Outputs:
    - `Outputs/small_results.csv`
    - alpha-profile plots per case
    - revenue/efficiency/fairness bar charts (truthful vs strategic)

- **`run_initial.py`**
  - Purpose: “big run” / main experiment sweep used for progress reporting.
  - Builds a grid of scenarios using a **scarcity rule**:
    - `m_slots = scarcity_frac * n_airlines * max_demand`
  - Runs multiple random seeds for each scenario under:
    - **truthful bidding**
    - **strategic bidding** (approx equilibrium in a restricted strategy class)
  - Outputs:
    - `Outputs/big_results.csv`
    - `Outputs/plots_big/` with 4 summary bar plots:
      - revenue
      - efficiency
      - fairness
      - equilibrium gap



---

## Core Library Code (`src/`)

### `src/models.py`
Defines how airline **private values** are generated.

- `sample_marginal_values(n_airlines, max_demand, rng, base_scale=100, diminishing=0.85)`
  - Produces a matrix `values[i, j]` = airline *i*’s marginal value for its *(j+1)th* slot.
  - Uses:
    - lognormal base valuation per airline
    - geometric decay across units to model **diminishing returns**
    - small noise, clipped at 0
- `truthful_bids_from_values(values)`
  - Returns `values.copy()` (truthful marginal bids).

---

### `src/mechanisms.py`
Implements multi-unit allocation rules and payments.

- `_flatten_bids(bids)`
  - Converts bids `(n_airlines, max_demand)` into a sortable list of `(bid, airline_id, unit_index)`.

- `allocate_top_m_units(bids, m_slots)`
  - Sorts all marginal unit bids and selects the top `m_slots`.
  - Returns:
    - `alloc[i]` = number of slots assigned to airline i
    - `winners` list (winning marginal units)
    - `clearing` = the last winning bid (m-th highest)

- `uniform_price_auction(bids, m_slots)`
  - Allocates top `m_slots` units.
  - Everyone pays `clearing_price` per unit won:
    - `payment_i = alloc[i] * clearing_price`

- `discriminatory_price_auction(bids, m_slots)`
  - Allocates top `m_slots` units.
  - Winners pay their own winning bids (pay-as-bid).

- `welfare_maximizing_allocation(values, m_slots)`
  - Benchmark allocation for **additive marginal values**:
    - allocate the top `m_slots` marginal **values** (not bids)

---

### `src/metrics.py`
Computes evaluation metrics.

- `total_value(values, alloc)`
  - Efficiency = sum of true marginal values for allocated slots.
  - For airline i with `a` slots:
    - adds `values[i, :a].sum()`

- `airline_utilities(values, alloc, payments)`
  - Utility per airline:
    - `u_i = value_i(alloc) - payment_i`

- `alloc_hhi(alloc)`
  - HHI concentration of allocation shares:
    - `HHI = sum(share_i^2)`

- `fairness_1_minus_hhi(alloc)`
  - Fairness score:
    - `1 - HHI`
  - Higher means more equal allocation across airlines.

---

### `src/equilibrium.py`
Approximates strategic bidding behavior in a **restricted parametric strategy class**:

> Strategy class (symmetric, per-unit shading):  
> **`b_{i,j} = alpha_j * v_{i,j}`**

Key ideas:
- Solve for an approximate equilibrium `alpha = (alpha_0, ..., alpha_{K-1})`
- Uses **damped coordinate best response** with **common random numbers (CRN)**
  to reduce Monte Carlo noise.

Functions:

- `_sample_profiles(n_airlines, max_demand, rng, n_mc)`
  - Pre-samples `n_mc` value profiles once, reused for all candidate `alpha_j` at a step.

- `_eu_deviator_per_unit_on_profiles(mechanism_fn, profiles, m_slots, alpha_other, j, alpha_j_i)`
  - Computes deviator (airline 0) expected utility when deviating only at coordinate `j`
    while others play `alpha_other`.

- `solve_symmetric_alpha_per_unit(...)`
  - Iterates over units `j = 0..K-1` and finds best-response alpha on a grid.
  - Applies damping for stability:
    - `alpha[j] <- (1-damping)*alpha[j] + damping*alpha_br`
  - Computes `eq_gap` as:
    - maximum profitable single-coordinate deviation gain at the final alpha vector.
  - Returns:
    - `alpha_vec`
    - `eq_gap` (smaller is “more equilibrium-like”)

---

### `src/simulator.py`
Runs one scenario end-to-end.

- `run_one_scenario(n_airlines, m_slots, max_demand, seed, bidding_mode, n_mc, n_passes)`
  1. Sample values `values[i, j]`.
  2. Choose bids:
     - **truthful**: bids = values
     - **strategic**:
       - solve `alpha_vec` for uniform auction
       - solve `alpha_vec` for discriminatory auction
       - apply shading: `bids = alpha_vec * values`
  3. Run mechanisms:
     - uniform-price
     - discriminatory
     - welfare-max benchmark allocation
  4. Compute metrics:
     - efficiency, revenue, fairness for each mechanism
     - welfare benchmarks
     - alpha summaries + per-unit alpha values
     - equilibrium gaps
  5. Return a dictionary row (for DataFrame assembly).

---

## Outputs

Typical generated artifacts:

### CSV results
- `Outputs/small_results.csv`
- `Outputs/big_results.csv`

Each row corresponds to a `(scenario, seed, bidding_mode)` run and includes:
- `uniform_eff`, `uniform_rev`, `uniform_fair`, ...
- `disc_eff`, `disc_rev`, `disc_fair`, ...
- `welfare_eff`, `welfare_fair`
- `uniform_alpha`, `disc_alpha`
- `uniform_eq_gap`, `disc_eq_gap`
- per-unit `uniform_alpha0..` and `disc_alpha0..`

### Plots
- Small run:
  - alpha profile per case
  - bar charts comparing truthful vs strategic
- Big run:
  - `01_revenue_truth_vs_strat.png`
  - `02_efficiency_strategic.png`
  - `03_fairness_strategic.png`
  - `04_eq_gap.png`


