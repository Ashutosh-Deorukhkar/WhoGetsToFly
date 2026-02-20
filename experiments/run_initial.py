# import sys
# import os
# sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# import pandas as pd
# from tqdm import tqdm
# from src.simulator import run_one_scenario

# def main():
#     seeds = list(range(10))

#     # --- Scarcity settings ---
#     max_demand = 5
#     scarcity_frac = 0.25  # fraction of total possible demand (n_airlines * max_demand)

#     # Choose airline counts; compute m_slots from scarcity
#     n_list = [20, 30, 40, 50]
#     grid = []
#     for n in n_list:
#         m = max(1, int(round(scarcity_frac * n * max_demand)))
#         # Optional: keep slots below number of airlines to force competition across airlines
#         # m = min(m, n - 1)
#         grid.append((n, m))
#     # grid is list of (n_airlines, m_slots)

#     rows = []
#     for n, m in grid:
#         for s in tqdm(seeds, desc=f"n={n}, m={m}"):
#             rows.append(run_one_scenario(n, m, max_demand, seed=s, bidding_mode="truthful"))
#             rows.append(run_one_scenario(n, m, max_demand, seed=s, bidding_mode="strategic"))

#     df = pd.DataFrame(rows)

#     # Base metrics
#     cols = [
#         "uniform_eff","uniform_rev","uniform_fair",
#         "disc_eff","disc_rev","disc_fair",
#     ]

#     # Add strategic diagnostics if present
#     extra = ["uniform_alpha","uniform_eq_gap","disc_alpha","disc_eq_gap"]
#     for c in extra:
#         if c in df.columns:
#             cols.append(c)

#     print(
#         df.groupby(["bidding_mode", "n_airlines", "m_slots"])[cols]
#           .mean()
#           .round(3)
#     )

#     output_dir = r"C:\Users\toash\OneDrive\Desktop\E81 CSE 516P\Outputs"
#     os.makedirs(output_dir, exist_ok=True)

#     output_path = os.path.join(output_dir, "initial_results.csv")
#     df.to_csv(output_path, index=False)
#     print(f"\nSaved: {output_path}")

# if __name__ == "__main__":
#     main()




# import sys
# import os
# sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# import pandas as pd
# from tqdm import tqdm
# from src.simulator import run_one_scenario


# def main():
#     seeds = list(range(10))

#     # --- Scarcity settings ---
#     max_demand = 5
#     scarcity_frac = 0.25  # fraction of total possible demand (n_airlines * max_demand)

#     # Choose airline counts; compute m_slots from scarcity
#     n_list = [20, 30, 40, 50]
#     grid = []
#     for n in n_list:
#         m = max(1, int(round(scarcity_frac * n * max_demand)))
#         grid.append((n, m))

#     # --- Strategic solver settings for BIG run (controls runtime) ---
#     # (truthful ignores these)
#     strategic_kwargs = dict(
#         n_mc=20,       # MC samples per utility estimate
#         n_passes=4,    # coordinate-descent passes over units
#     )

#     rows = []
#     for n, m in grid:
#         for s in tqdm(seeds, desc=f"n={n}, m={m}"):
#             rows.append(run_one_scenario(n, m, max_demand, seed=s, bidding_mode="truthful"))
#             rows.append(run_one_scenario(n, m, max_demand, seed=s, bidding_mode="strategic", **strategic_kwargs))

#     df = pd.DataFrame(rows)

#     # Base metrics
#     cols = [
#         "uniform_eff","uniform_rev","uniform_fair",
#         "disc_eff","disc_rev","disc_fair",
#         "welfare_eff","welfare_fair",
#         "uniform_alpha","uniform_eq_gap","disc_alpha","disc_eq_gap",
#     ]
#     cols = [c for c in cols if c in df.columns]

#     print(
#         df.groupby(["bidding_mode", "n_airlines", "m_slots"])[cols]
#           .mean()
#           .round(3)
#     )

#     output_dir = r"C:\Users\toash\OneDrive\Desktop\E81 CSE 516P\Outputs"
#     os.makedirs(output_dir, exist_ok=True)

#     # Don’t overwrite previous results
#     output_path = os.path.join(output_dir, "big_results.csv")
#     df.to_csv(output_path, index=False)
#     print(f"\nSaved: {output_path}")


# if __name__ == "__main__":
#     main()

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm
from src.simulator import run_one_scenario


def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)
    return path


def _savefig(path: str):
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close()


def _annotate_bars(bar_container, fmt="{:.1f}", ypad_frac=0.01, fontsize=8, rotate=0):
    ax = plt.gca()
    ymin, ymax = ax.get_ylim()
    ypad = (ymax - ymin) * ypad_frac

    for bar in bar_container:
        h = bar.get_height()
        if np.isnan(h):
            continue
        x = bar.get_x() + bar.get_width() / 2.0
        ax.text(
            x, h + ypad, fmt.format(h),
            ha="center", va="bottom",
            fontsize=fontsize, rotation=rotate
        )


def main():
    seeds = list(range(10))

    # --- Scarcity settings ---
    max_demand = 5
    scarcity_frac = 0.25  # fraction of total possible demand (n_airlines * max_demand)

    # Choose airline counts; compute m_slots from scarcity
    n_list = [20, 30, 40, 50]
    grid = []
    for n in n_list:
        m = max(1, int(round(scarcity_frac * n * max_demand)))
        grid.append((n, m))

    # --- Strategic solver settings ---
    strategic_kwargs = dict(
        n_mc=20,
        n_passes=4,
    )

    rows = []
    for n, m in grid:
        for s in tqdm(seeds, desc=f"n={n}, m={m}"):
            rows.append(run_one_scenario(n, m, max_demand, seed=s, bidding_mode="truthful"))
            rows.append(run_one_scenario(n, m, max_demand, seed=s, bidding_mode="strategic", **strategic_kwargs))

    df = pd.DataFrame(rows)

    output_dir = r"C:\Users\toash\OneDrive\Desktop\E81 CSE 516P\Outputs"
    _ensure_dir(output_dir)
    plots_dir = _ensure_dir(os.path.join(output_dir, "plots_big"))

    # Save full results
    out_csv = os.path.join(output_dir, "big_results.csv")
    df.to_csv(out_csv, index=False)
    print(f"\nSaved: {out_csv}")

    # --- Aggregate means for plotting ---
    group_cols = ["bidding_mode", "n_airlines", "m_slots", "max_demand"]
    mean_df = (
        df.groupby(group_cols)
          .mean(numeric_only=True)
          .reset_index()
          .sort_values(["n_airlines", "bidding_mode"])
    )

    mean_df["scenario"] = mean_df.apply(
        lambda r: f"n={int(r['n_airlines'])}, m={int(r['m_slots'])}, k={int(r['max_demand'])}",
        axis=1
    )

    truth = mean_df[mean_df["bidding_mode"] == "truthful"].copy()
    strat = mean_df[mean_df["bidding_mode"] == "strategic"].copy()

    scenarios = truth["scenario"].tolist()
    x = np.arange(len(scenarios))
    w = 0.2

    # ---------------------------
    # Plot 1: Revenue
    # ---------------------------
    plt.figure(figsize=(12, 5))
    plt.title("Revenue: Truthful vs Strategic")
    plt.xticks(x, scenarios, rotation=25, ha="right")

    b1 = plt.bar(x - 1.5*w, truth["uniform_rev"].values, width=w, label="Uniform (Truth)")
    b2 = plt.bar(x - 0.5*w, strat["uniform_rev"].values, width=w, label="Uniform (Strat)")
    b3 = plt.bar(x + 0.5*w, truth["disc_rev"].values, width=w, label="Disc (Truth)")
    b4 = plt.bar(x + 1.5*w, strat["disc_rev"].values, width=w, label="Disc (Strat)")

    plt.ylabel("Average Revenue")
    plt.legend()

    _annotate_bars(b1, fmt="{:.0f}")
    _annotate_bars(b2, fmt="{:.0f}")
    _annotate_bars(b3, fmt="{:.0f}")
    _annotate_bars(b4, fmt="{:.0f}")

    _savefig(os.path.join(plots_dir, "01_revenue_truth_vs_strat.png"))

    # ---------------------------
    # Plot 2: Efficiency
    # ---------------------------
    plt.figure(figsize=(12, 5))
    plt.title("Efficiency (Total Value): Strategic")
    plt.xticks(x, scenarios, rotation=25, ha="right")

    b1 = plt.bar(x - w, strat["uniform_eff"].values, width=w, label="Uniform (Strat)")
    b2 = plt.bar(x,      strat["disc_eff"].values,   width=w, label="Disc (Strat)")

    if "welfare_eff" in strat.columns:
        b3 = plt.bar(x + w, strat["welfare_eff"].values, width=w, label="Welfare-max")
        _annotate_bars(b3, fmt="{:.0f}")

    plt.ylabel("Average Efficiency")
    plt.legend()

    _annotate_bars(b1, fmt="{:.0f}")
    _annotate_bars(b2, fmt="{:.0f}")

    _savefig(os.path.join(plots_dir, "02_efficiency_strategic.png"))

    # ---------------------------
    # Plot 3: Fairness
    # ---------------------------
    plt.figure(figsize=(12, 5))
    plt.title("Fairness (1 - HHI): Strategic")
    plt.xticks(x, scenarios, rotation=25, ha="right")

    b1 = plt.bar(x - w, strat["uniform_fair"].values, width=w, label="Uniform (Strat)")
    b2 = plt.bar(x,      strat["disc_fair"].values,   width=w, label="Disc (Strat)")

    if "welfare_fair" in strat.columns:
        b3 = plt.bar(x + w, strat["welfare_fair"].values, width=w, label="Welfare-max")
        _annotate_bars(b3, fmt="{:.3f}")

    plt.ylabel("Average Fairness (1 - HHI)")
    plt.legend()

    _annotate_bars(b1, fmt="{:.3f}")
    _annotate_bars(b2, fmt="{:.3f}")

    _savefig(os.path.join(plots_dir, "03_fairness_strategic.png"))

    # ---------------------------
    # Plot 4: Eq gap
    # ---------------------------
    if "uniform_eq_gap" in strat.columns and "disc_eq_gap" in strat.columns:
        plt.figure(figsize=(12, 5))
        plt.title("Equilibrium Gap (smaller is better)")
        plt.xticks(x, scenarios, rotation=25, ha="right")

        b1 = plt.bar(x - w/2, strat["uniform_eq_gap"].values, width=w, label="Uniform eq_gap")
        b2 = plt.bar(x + w/2, strat["disc_eq_gap"].values,   width=w, label="Disc eq_gap")

        plt.ylabel("Average eq_gap")
        plt.legend()

        _annotate_bars(b1, fmt="{:.2f}")
        _annotate_bars(b2, fmt="{:.2f}")

        _savefig(os.path.join(plots_dir, "04_eq_gap.png"))

    # Console summary
    cols_to_print = [
        "uniform_eff","uniform_rev","uniform_fair",
        "disc_eff","disc_rev","disc_fair",
        "welfare_eff","welfare_fair",
        "uniform_alpha","uniform_eq_gap","disc_alpha","disc_eq_gap",
    ]
    cols_to_print = [c for c in cols_to_print if c in df.columns]

    print(
        df.groupby(["bidding_mode", "n_airlines", "m_slots"])[cols_to_print]
          .mean()
          .round(3)
    )

    print(f"\nSaved plots to: {plots_dir}")

if __name__ == "__main__":
    main()