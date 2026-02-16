import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import pandas as pd
from tqdm import tqdm
from src.simulator import run_one_scenario

def main():
    seeds = list(range(10))
    grid = [
        (10, 20),
        (20, 30),
        (30, 40),
        (40, 50),
    ]  # (n_airlines, m_slots)
    max_demand = 5

    rows = []
    for n, m in grid:
        for s in tqdm(seeds, desc=f"n={n}, m={m}"):
            rows.append(run_one_scenario(n, m, max_demand, seed=s))

    df = pd.DataFrame(rows)
    print(df.groupby(["n_airlines", "m_slots"])[
        ["uniform_eff", "uniform_rev", "disc_eff", "disc_rev", "welfare_eff"]
    ].mean().round(2))

    df.to_csv("initial_results.csv", index=False)
    print("\nSaved: initial_results.csv")

if __name__ == "__main__":
    main()