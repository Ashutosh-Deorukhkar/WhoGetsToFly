import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm
import os
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
        ax.text(x, h + ypad, fmt.format(h), ha="center", va="bottom",
                fontsize=fontsize, rotation=rotate)


def main():
    # fixed airport day: 8am-6pm => 10 one-hour slots
    start_hour = 8
    end_hour = 18
    cap_per_airline = 3
    max_interval_len = 3

    seeds = list(range(10))
    n_list = [12]

    rows = []
    for n in n_list:
        for s in tqdm(seeds, desc=f"n={n}"):
            rows.append(run_one_scenario(
                n_airlines=n,
                start_hour=start_hour,
                end_hour=end_hour,
                cap_per_airline=cap_per_airline,
                seed=s,
                bidding_mode="truthful",
                max_interval_len=max_interval_len,
            ))
            rows.append(run_one_scenario(
                n_airlines=n,
                start_hour=start_hour,
                end_hour=end_hour,
                cap_per_airline=cap_per_airline,
                seed=s,
                bidding_mode="strategic",
                max_interval_len=max_interval_len,
            ))

    df = pd.DataFrame(rows)

    output_dir = r"C:\Users\toash\OneDrive\Desktop\E81 CSE 516P\Outputs"
    _ensure_dir(output_dir)
    plots_dir = _ensure_dir(os.path.join(output_dir, "plots_interval_vcg"))

    out_csv = os.path.join(output_dir, "results_interval_vcg.csv")
    df.to_csv(out_csv, index=False)
    print(f"\nSaved: {out_csv}")

    group_cols = ["bidding_mode", "n_airlines", "m_slots", "cap_per_airline"]
    mean_df = (
        df.groupby(group_cols)
          .mean(numeric_only=True)
          .reset_index()
          .sort_values(["n_airlines", "bidding_mode"])
    )

    mean_df["scenario"] = mean_df.apply(
        lambda r: f"n={int(r['n_airlines'])}, m={int(r['m_slots'])}, cap={int(r['cap_per_airline'])}",
        axis=1
    )

    truth = mean_df[mean_df["bidding_mode"] == "truthful"].copy()
    strat = mean_df[mean_df["bidding_mode"] == "strategic"].copy()

    scenarios = truth["scenario"].tolist()
    x = np.arange(len(scenarios))
    w = 0.18

    # Revenue
    plt.figure(figsize=(12, 5))
    plt.title("Revenue: Truthful vs Strategic")
    plt.xticks(x, scenarios, rotation=25, ha="right")

    b1 = plt.bar(x - 2*w, truth["seq_rev"].values, width=w, label="Seq FP (Truth)")
    b2 = plt.bar(x - 1*w, strat["seq_rev"].values, width=w, label="Seq FP (Strat)")
    b3 = plt.bar(x + 0*w, truth["int_rev"].values, width=w, label="Interval PAB (Truth)")
    b4 = plt.bar(x + 1*w, strat["int_rev"].values, width=w, label="Interval PAB (Strat)")
    b5 = plt.bar(x + 2*w, truth["vcg_rev"].values, width=w, label="VCG (Truth)")

    plt.ylabel("Average Revenue")
    plt.legend()
    _annotate_bars(b1, fmt="{:.0f}"); _annotate_bars(b2, fmt="{:.0f}")
    _annotate_bars(b3, fmt="{:.0f}"); _annotate_bars(b4, fmt="{:.0f}")
    _annotate_bars(b5, fmt="{:.0f}")
    _savefig(os.path.join(plots_dir, "01_revenue.png"))

    # Efficiency
    plt.figure(figsize=(12, 5))
    plt.title("Efficiency (Total Welfare): Truthful vs Strategic")
    plt.xticks(x, scenarios, rotation=25, ha="right")

    b1 = plt.bar(x - 2*w, truth["seq_eff"].values, width=w, label="Seq FP (Truth)")
    b2 = plt.bar(x - 1*w, strat["seq_eff"].values, width=w, label="Seq FP (Strat)")
    b3 = plt.bar(x + 0*w, truth["int_eff"].values, width=w, label="Interval PAB (Truth)")
    b4 = plt.bar(x + 1*w, strat["int_eff"].values, width=w, label="Interval PAB (Strat)")
    b5 = plt.bar(x + 2*w, truth["vcg_eff"].values, width=w, label="VCG (Truth)")

    plt.ylabel("Average Welfare")
    plt.legend()
    _annotate_bars(b1, fmt="{:.0f}"); _annotate_bars(b2, fmt="{:.0f}")
    _annotate_bars(b3, fmt="{:.0f}"); _annotate_bars(b4, fmt="{:.0f}")
    _annotate_bars(b5, fmt="{:.0f}")
    _savefig(os.path.join(plots_dir, "02_efficiency.png"))

    # Fairness
    plt.figure(figsize=(12, 5))
    plt.title("Fairness (1 - HHI): Truthful vs Strategic")
    plt.xticks(x, scenarios, rotation=25, ha="right")

    b1 = plt.bar(x - 2*w, truth["seq_fair"].values, width=w, label="Seq FP (Truth)")
    b2 = plt.bar(x - 1*w, strat["seq_fair"].values, width=w, label="Seq FP (Strat)")
    b3 = plt.bar(x + 0*w, truth["int_fair"].values, width=w, label="Interval PAB (Truth)")
    b4 = plt.bar(x + 1*w, strat["int_fair"].values, width=w, label="Interval PAB (Strat)")
    b5 = plt.bar(x + 2*w, truth["vcg_fair"].values, width=w, label="VCG (Truth)")

    plt.ylabel("Average Fairness (1 - HHI)")
    plt.legend()
    _annotate_bars(b1, fmt="{:.3f}"); _annotate_bars(b2, fmt="{:.3f}")
    _annotate_bars(b3, fmt="{:.3f}"); _annotate_bars(b4, fmt="{:.3f}")
    _annotate_bars(b5, fmt="{:.3f}")
    _savefig(os.path.join(plots_dir, "03_fairness.png"))

    # Eq gaps (strategic only)
    if "seq_eq_gap" in strat.columns or "int_eq_gap" in strat.columns:
        plt.figure(figsize=(12, 5))
        plt.title("Equilibrium Gap (smaller is better) — Strategic")
        plt.xticks(x, scenarios, rotation=25, ha="right")

        if "seq_eq_gap" in strat.columns:
            b1 = plt.bar(x - w/2, strat["seq_eq_gap"].values, width=w, label="Seq FP eq_gap")
            _annotate_bars(b1, fmt="{:.2f}")
        if "int_eq_gap" in strat.columns:
            b2 = plt.bar(x + w/2, strat["int_eq_gap"].values, width=w, label="Interval eq_gap")
            _annotate_bars(b2, fmt="{:.2f}")

        plt.ylabel("Average eq_gap")
        plt.legend()
        _savefig(os.path.join(plots_dir, "04_eq_gap.png"))

        # ==========================
    # Console diagnostics (ADD)
    # ==========================

    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 200)

    print("\n==============================")
    print("RAW RUNS (per seed, per mode)")
    print("==============================")

    # helpful ordering
    cols = [
        "seed", "bidding_mode",
        "seq_rev", "seq_eff", "seq_fair", "seq_eq_gap",
        "int_rev", "int_eff", "int_fair", "int_eq_gap",
        "vcg_rev", "vcg_eff", "vcg_fair",
    ]
    # if you didn't store seed in out, add it here from df index grouping
    if "seed" not in df.columns:
        # recover seed by merge logic: every seed has 2 rows in insertion order
        df = df.copy()
        df["seed"] = np.repeat(seeds, 2)

    print(df[cols].sort_values(["seed", "bidding_mode"]).to_string(index=False))

    print("\n============================================")
    print("MEANS BY MODE (what your bars are plotting)")
    print("============================================")

    summary_cols = [
        "seq_rev", "seq_eff", "seq_fair", "seq_eq_gap",
        "int_rev", "int_eff", "int_fair", "int_eq_gap",
        "vcg_rev", "vcg_eff", "vcg_fair",
    ]
    summary = (
        df.groupby(["bidding_mode"])
          [summary_cols]
          .mean(numeric_only=True)
          .round(4)
          .reset_index()
    )
    print(summary.to_string(index=False))

    print("\n============================================")
    print("CHECKS (should/shouldn't be true)")
    print("============================================")

    # VCG allocation same as interval allocation in YOUR code, so welfare/fairness should match exactly (up to fp noise)
    vcg_minus_int_eff = (df["vcg_eff"] - df["int_eff"]).abs().max()
    vcg_minus_int_fair = (df["vcg_fair"] - df["int_fair"]).abs().max()
    print(f"max |vcg_eff - int_eff|  = {vcg_minus_int_eff:.12f}")
    print(f"max |vcg_fair - int_fair|= {vcg_minus_int_fair:.12f}")

    # Revenue: VCG revenue can be lower than PAB/FP and can be lower than 0 in weird cases, so just print min/max
    print(f"vcg_rev min/max: {df['vcg_rev'].min():.4f} / {df['vcg_rev'].max():.4f}")
    print(f"int_rev min/max: {df['int_rev'].min():.4f} / {df['int_rev'].max():.4f}")
    print(f"seq_rev min/max: {df['seq_rev'].min():.4f} / {df['seq_rev'].max():.4f}")

    print(f"\nSaved plots to: {plots_dir}")


if __name__ == "__main__":
    main()