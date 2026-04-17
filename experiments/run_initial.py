import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm
from src.simulator import run_one_scenario


def _ensure_dir(path):
    os.makedirs(path, exist_ok=True)
    return path


def _savefig(path):
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close()


def _annotate_bars(bar_container, fmt="{:.0f}", fontsize=8):
    ax = plt.gca()
    ymin, ymax = ax.get_ylim()
    ypad = (ymax - ymin) * 0.01
    for bar in bar_container:
        h = bar.get_height()
        if np.isnan(h):
            continue
        x = bar.get_x() + bar.get_width() / 2.0
        ax.text(x, h + ypad, fmt.format(h), ha="center", va="bottom", fontsize=fontsize)


def main():
    start_hour     = 8
    end_hour       = 18
    cap_per_airline = 3
    max_interval_len = 3
    seeds  = list(range(10))
    n_list = [12]

    rows = []
    for n in n_list:
        for s in tqdm(seeds, desc=f"n={n}"):
            rows.append(run_one_scenario(
                n_airlines=n, start_hour=start_hour, end_hour=end_hour,
                cap_per_airline=cap_per_airline, seed=s,
                bidding_mode="truthful", max_interval_len=max_interval_len,
            ))
            rows.append(run_one_scenario(
                n_airlines=n, start_hour=start_hour, end_hour=end_hour,
                cap_per_airline=cap_per_airline, seed=s,
                bidding_mode="strategic", max_interval_len=max_interval_len,
            ))

    df = pd.DataFrame(rows)

    output_dir = r"C:\Users\toash\OneDrive\Desktop\E81 CSE 516P\Outputs"
    plots_dir  = _ensure_dir(os.path.join(output_dir, "plots_interval_vcg"))
    df.to_csv(os.path.join(output_dir, "results_interval_vcg.csv"), index=False)
    print(f"\nSaved CSV to: {output_dir}")

    # ── aggregate ──
    group_cols = ["bidding_mode", "n_airlines", "m_slots", "cap_per_airline"]
    mean_df = (
        df.groupby(group_cols).mean(numeric_only=True).reset_index()
          .sort_values(["n_airlines", "bidding_mode"])
    )
    mean_df["scenario"] = mean_df.apply(
        lambda r: f"n={int(r['n_airlines'])}, m={int(r['m_slots'])}, cap={int(r['cap_per_airline'])}",
        axis=1,
    )

    truth = mean_df[mean_df["bidding_mode"] == "truthful"].copy()
    strat = mean_df[mean_df["bidding_mode"] == "strategic"].copy()
    scenarios = truth["scenario"].tolist()
    x = np.arange(len(scenarios))
    w = 0.15

    # ── Revenue ──
    plt.figure(figsize=(14, 5))
    plt.title("Revenue: Truthful vs Strategic")
    plt.xticks(x, scenarios, rotation=25, ha="right")
    b1 = plt.bar(x - 2.5*w, truth["seq_rev"].values,  width=w, label="Seq FP (Truth)")
    b2 = plt.bar(x - 1.5*w, strat["seq_rev"].values,  width=w, label="Seq FP (Strat)")
    b3 = plt.bar(x - 0.5*w, truth["int_rev"].values,  width=w, label="Interval PAB (Truth)")
    b4 = plt.bar(x + 0.5*w, strat["int_rev"].values,  width=w, label="Interval PAB (Strat)")
    b5 = plt.bar(x + 1.5*w, truth["ivcg_rev"].values, width=w, label="Interval VCG (Truth)")
    b6 = plt.bar(x + 2.5*w, truth["cvcg_rev"].values, width=w, label="Full Comb. VCG (Truth)")
    for b in [b1, b2, b3, b4, b5, b6]:
        _annotate_bars(b)
    plt.ylabel("Average Revenue")
    plt.legend(fontsize=8)
    _savefig(os.path.join(plots_dir, "01_revenue.png"))

    # ── Efficiency ──
    plt.figure(figsize=(14, 5))
    plt.title("Efficiency (Total Welfare): Truthful vs Strategic")
    plt.xticks(x, scenarios, rotation=25, ha="right")
    b1 = plt.bar(x - 2.5*w, truth["seq_eff"].values,  width=w, label="Seq FP (Truth)")
    b2 = plt.bar(x - 1.5*w, strat["seq_eff"].values,  width=w, label="Seq FP (Strat)")
    b3 = plt.bar(x - 0.5*w, truth["int_eff"].values,  width=w, label="Interval PAB (Truth)")
    b4 = plt.bar(x + 0.5*w, strat["int_eff"].values,  width=w, label="Interval PAB (Strat)")
    b5 = plt.bar(x + 1.5*w, truth["ivcg_eff"].values, width=w, label="Interval VCG (Truth)")
    b6 = plt.bar(x + 2.5*w, truth["cvcg_eff"].values, width=w, label="Full Comb. VCG (Truth)")
    for b in [b1, b2, b3, b4, b5, b6]:
        _annotate_bars(b)
    plt.ylabel("Average Welfare")
    plt.legend(fontsize=8)
    _savefig(os.path.join(plots_dir, "02_efficiency.png"))

    # ── Fairness ──
    plt.figure(figsize=(14, 5))
    plt.title("Fairness (1 - HHI): Truthful vs Strategic")
    plt.xticks(x, scenarios, rotation=25, ha="right")
    b1 = plt.bar(x - 2.5*w, truth["seq_fair"].values,  width=w, label="Seq FP (Truth)")
    b2 = plt.bar(x - 1.5*w, strat["seq_fair"].values,  width=w, label="Seq FP (Strat)")
    b3 = plt.bar(x - 0.5*w, truth["int_fair"].values,  width=w, label="Interval PAB (Truth)")
    b4 = plt.bar(x + 0.5*w, strat["int_fair"].values,  width=w, label="Interval PAB (Strat)")
    b5 = plt.bar(x + 1.5*w, truth["ivcg_fair"].values, width=w, label="Interval VCG (Truth)")
    b6 = plt.bar(x + 2.5*w, truth["cvcg_fair"].values, width=w, label="Full Comb. VCG (Truth)")
    for b in [b1, b2, b3, b4, b5, b6]:
        _annotate_bars(b, fmt="{:.3f}")
    plt.ylabel("Average Fairness (1 - HHI)")
    plt.legend(fontsize=8)
    _savefig(os.path.join(plots_dir, "03_fairness.png"))

    # ── Equilibrium Gap ──
    plt.figure(figsize=(14, 5))
    plt.title("Equilibrium Gap (smaller = closer to equilibrium) — Strategic only")
    plt.xticks(x, scenarios, rotation=25, ha="right")
    b1 = plt.bar(x - w/2, strat["seq_eq_gap"].values, width=w, label="Seq FP eq_gap")
    b2 = plt.bar(x + w/2, strat["int_eq_gap"].values, width=w, label="Interval PAB eq_gap")
    _annotate_bars(b1, fmt="{:.1f}")
    _annotate_bars(b2, fmt="{:.1f}")
    plt.ylabel("Average eq_gap")
    plt.legend(fontsize=8)
    _savefig(os.path.join(plots_dir, "04_eq_gap.png"))

    # ── Console summary ──
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 30)

    print("\n==============================")
    print("RAW RUNS (per seed, per mode)")
    print("==============================")
    if "seed" not in df.columns:
        df = df.copy()
        df["seed"] = np.repeat(list(range(len(seeds))), 2)

    cols = [
        "seed", "bidding_mode",
        "seq_rev", "seq_eff", "seq_fair", "seq_eq_gap",
        "int_rev", "int_eff", "int_fair", "int_eq_gap",
        "ivcg_rev", "ivcg_eff", "ivcg_fair",
        "cvcg_rev", "cvcg_eff", "cvcg_fair",
    ]
    print(df[cols].sort_values(["seed", "bidding_mode"]).to_string(index=False))

    print("\n============================================")
    print("MEANS BY MODE")
    print("============================================")
    summary_cols = [c for c in cols if c not in ["seed", "bidding_mode"]]
    summary = (
        df.groupby("bidding_mode")[summary_cols]
          .mean(numeric_only=True).round(4).reset_index()
    )
    print(summary.to_string(index=False))

    print("\n============================================")
    print("CHECKS")
    print("============================================")
    print(f"max |ivcg_eff - int_eff|  = {(df['ivcg_eff'] - df['int_eff']).abs().max():.12f}")
    print(f"cvcg_eff >= ivcg_eff always? {(df['cvcg_eff'] >= df['ivcg_eff'] - 1e-6).all()}")
    print(f"cvcg_rev min/max : {df['cvcg_rev'].min():.2f} / {df['cvcg_rev'].max():.2f}")
    print(f"ivcg_rev min/max : {df['ivcg_rev'].min():.2f} / {df['ivcg_rev'].max():.2f}")
    print(f"int_rev  min/max : {df['int_rev'].min():.2f} / {df['int_rev'].max():.2f}")
    print(f"seq_rev  min/max : {df['seq_rev'].min():.2f} / {df['seq_rev'].max():.2f}")
    print(f"\nSaved plots to: {plots_dir}")


if __name__ == "__main__":
    main()
