import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm
from src.simulator import run_one_scenario

def scalar_from_group(row_df: pd.DataFrame, col: str) -> float:
    """Safely extract a scalar from a 0-or-1 row DataFrame produced by filtering."""
    if row_df.empty:
        return 0.0
    return float(row_df[col].iloc[0])

def case_label(n, m, k):
    return f"n={n}, m={m}, k={k}"

def main():
    seeds = [0, 1, 2]

    cases = [
        (5, 4, 3),
        (6, 4, 3),
        (8, 5, 4),
    ]

    rows = []
    for n, m, k in cases:
        for s in tqdm(seeds, desc=f"n={n}, m={m}, k={k}"):
            rows.append(run_one_scenario(n, m, k, seed=s, bidding_mode="truthful"))
            rows.append(run_one_scenario(n, m, k, seed=s, bidding_mode="strategic"))

    df = pd.DataFrame(rows)

    # Print summary
    cols = [
        "uniform_eff","uniform_rev","uniform_fair",
        "disc_eff","disc_rev","disc_fair",
        "uniform_alpha","uniform_eq_gap","disc_alpha","disc_eq_gap",
    ]
    # include per-unit alphas if present
    per_unit_cols = [c for c in df.columns if c.startswith("uniform_alpha") and c != "uniform_alpha"]
    per_unit_cols += [c for c in df.columns if c.startswith("disc_alpha") and c != "disc_alpha"]
    # Keep only columns that exist (in case k differs)
    cols = [c for c in cols if c in df.columns]
    per_unit_cols = sorted([c for c in per_unit_cols if c in df.columns])

    print(
        df.groupby(["bidding_mode","n_airlines","m_slots","max_demand"])[cols]
          .mean()
          .round(3)
    )

    output_dir = r"C:\Users\toash\OneDrive\Desktop\E81 CSE 516P\Outputs"
    os.makedirs(output_dir, exist_ok=True)

    csv_path = os.path.join(output_dir, "small_results.csv")
    df.to_csv(csv_path, index=False)
    print(f"\nSaved: {csv_path}")

    g = (
        df.groupby(["bidding_mode","n_airlines","m_slots","max_demand"])
          .mean(numeric_only=True)
          .reset_index()
    )
    g["case"] = g.apply(lambda r: case_label(int(r["n_airlines"]), int(r["m_slots"]), int(r["max_demand"])), axis=1)

    # Plot 1: Per-unit alpha profile (strategic only)
    strategic = df[df["bidding_mode"] == "strategic"].copy()
    strategic["case"] = strategic.apply(lambda r: case_label(int(r["n_airlines"]), int(r["m_slots"]), int(r["max_demand"])), axis=1)

    max_k = int(strategic["max_demand"].max())

    for (n, m, k) in cases:
        label = case_label(n, m, k)
        sub = strategic[(strategic["n_airlines"] == n) & (strategic["m_slots"] == m) & (strategic["max_demand"] == k)]
        if sub.empty:
            continue

        js = list(range(k))
        u = [sub[f"uniform_alpha{j}"].mean() for j in js]
        d = [sub[f"disc_alpha{j}"].mean() for j in js]

        plt.figure()
        plt.plot(js, u, marker="o", label="Uniform (strategic)")
        plt.plot(js, d, marker="o", label="Discriminatory (strategic)")
        plt.xlabel("Unit index j (0 = 1st slot, higher = later slot)")
        plt.ylabel("Mean shading alpha_j")
        plt.title(f"Per-unit shading profile: {label}")
        plt.xticks(js)
        plt.legend()
        plt.tight_layout()

        out_path = os.path.join(output_dir, f"alpha_profile_{n}_{m}_{k}.png")
        plt.savefig(out_path, dpi=200)
        plt.close()

    # Plot 2: Revenue comparison (truthful vs strategic)
    for mech in ["uniform", "disc"]:
        plt.figure()
        x_labels = [case_label(n, m, k) for (n, m, k) in cases]
        x = list(range(len(x_labels)))

        vals_truth = []
        vals_strat = []
        for (n, m, k) in cases:
            row_t = g[(g["bidding_mode"] == "truthful") & (g["n_airlines"] == n) & (g["m_slots"] == m) & (g["max_demand"] == k)]
            row_s = g[(g["bidding_mode"] == "strategic") & (g["n_airlines"] == n) & (g["m_slots"] == m) & (g["max_demand"] == k)]
            vals_truth.append(scalar_from_group(row_t, f"{mech}_rev"))
            vals_strat.append(scalar_from_group(row_s, f"{mech}_rev"))

        width = 0.35
        plt.bar([i - width/2 for i in x], vals_truth, width=width, label="Truthful")
        plt.bar([i + width/2 for i in x], vals_strat, width=width, label="Strategic")
        plt.xticks(x, x_labels, rotation=20, ha="right")
        plt.ylabel("Mean revenue")
        plt.title(f"{mech.capitalize()} revenue: Truthful vs Strategic")
        plt.legend()
        plt.tight_layout()

        out_path = os.path.join(output_dir, f"{mech}_revenue_truthful_vs_strategic.png")
        plt.savefig(out_path, dpi=200)
        plt.close()

    # Plot 3: Efficiency + Fairness 
    for metric in ["eff", "fair"]:
        for mech in ["uniform", "disc"]:
            plt.figure()
            x_labels = [case_label(n, m, k) for (n, m, k) in cases]
            x = list(range(len(x_labels)))

            vals_truth = []
            vals_strat = []
            for (n, m, k) in cases:
                row_t = g[(g["bidding_mode"] == "truthful") & (g["n_airlines"] == n) & (g["m_slots"] == m) & (g["max_demand"] == k)]
                row_s = g[(g["bidding_mode"] == "strategic") & (g["n_airlines"] == n) & (g["m_slots"] == m) & (g["max_demand"] == k)]
                vals_truth.append(scalar_from_group(row_t, f"{mech}_{metric}"))
                vals_strat.append(scalar_from_group(row_s, f"{mech}_{metric}"))

            width = 0.35
            plt.bar([i - width/2 for i in x], vals_truth, width=width, label="Truthful")
            plt.bar([i + width/2 for i in x], vals_strat, width=width, label="Strategic")
            plt.xticks(x, x_labels, rotation=20, ha="right")
            plt.ylabel(f"Mean {metric}")
            plt.title(f"{mech.capitalize()} {metric}: Truthful vs Strategic")
            plt.legend()
            plt.tight_layout()

            out_path = os.path.join(output_dir, f"{mech}_{metric}_truthful_vs_strategic.png")
            plt.savefig(out_path, dpi=200)
            plt.close()

    print(f"\nSaved plots to: {output_dir}")

if __name__ == "__main__":
    main()
