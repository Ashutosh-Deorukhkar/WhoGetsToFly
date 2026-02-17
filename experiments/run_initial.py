import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
from tqdm import tqdm
from src.simulator import run_one_scenario

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
        # Optional: keep slots below number of airlines to force competition across airlines
        # m = min(m, n - 1)
        grid.append((n, m))
    # grid is list of (n_airlines, m_slots)

    rows = []
    for n, m in grid:
        for s in tqdm(seeds, desc=f"n={n}, m={m}"):
            rows.append(run_one_scenario(n, m, max_demand, seed=s))

    df = pd.DataFrame(rows)

    print(
        df.groupby(["n_airlines", "m_slots"])[
            [
                "uniform_eff", "uniform_rev", "uniform_fair",
                "disc_eff", "disc_rev", "disc_fair",
                "welfare_eff", "welfare_fair",
            ]
        ].mean().round(3)
    )

    output_dir = r"C:\Users\toash\OneDrive\Desktop\E81 CSE 516P\Outputs"
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "initial_results.csv")
    df.to_csv(output_path, index=False)
    print(f"\nSaved: {output_path}")

if __name__ == "__main__":
    main()