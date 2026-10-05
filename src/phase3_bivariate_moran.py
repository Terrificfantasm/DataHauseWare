"""Bivariate Moran's I for a cross-variable spatial relationship."""
from __future__ import annotations

import argparse
import json

import matplotlib.pyplot as plt
import numpy as np

from phase3_common import (
    load_ageb_kpis,
    numeric_subset,
    output_dir,
    queen_weights,
    standardize,
    write_json,
)

DEFAULT_X = "business_density"
DEFAULT_Y = "crime_records_per_1000"


def bivariate_moran_i(x: np.ndarray, y: np.ndarray, weights) -> float:
    zx = standardize(np.asarray(x, dtype=float))
    zy = standardize(np.asarray(y, dtype=float))
    if weights.s0 == 0:
        raise ValueError("Bivariate Moran's I is undefined when every observation is an island")
    lag_y = weights.lag(zy)
    return float(np.dot(zx, lag_y) / weights.s0)


def permutation_test(x: np.ndarray, y: np.ndarray, weights, permutations: int, seed: int) -> dict:
    if permutations < 1:
        raise ValueError("permutations must be at least 1")
    observed = bivariate_moran_i(x, y, weights)
    rng = np.random.default_rng(seed)
    simulated = np.empty(permutations, dtype=float)
    for k in range(permutations):
        simulated[k] = bivariate_moran_i(x, rng.permutation(y), weights)

    sim_mean = float(simulated.mean())
    distance = abs(observed - sim_mean)
    extreme = np.sum(np.abs(simulated - sim_mean) >= distance)
    p_sim = float((extreme + 1) / (permutations + 1))
    sim_std = float(simulated.std(ddof=1)) if permutations > 1 else 0.0
    z_sim = float((observed - sim_mean) / sim_std) if sim_std > 0 else 0.0
    return {
        "moran_bv_i": observed,
        "p_sim": p_sim,
        "z_sim": z_sim,
        "sim_mean": sim_mean,
        "sim_std": sim_std,
    }


def run(dataset_id: int, x_name: str = DEFAULT_X, y_name: str = DEFAULT_Y, permutations: int = 999, seed: int = 42) -> dict:
    frame = load_ageb_kpis(dataset_id)
    subset, data_audit = numeric_subset(frame, [x_name, y_name])
    weights, weights_audit = queen_weights(subset)

    x = subset[x_name].to_numpy(dtype=float)
    y = subset[y_name].to_numpy(dtype=float)
    test = permutation_test(x, y, weights, permutations, seed)

    zx = standardize(x)
    zy = standardize(y)
    lag_y = weights.lag(zy)

    destination = output_dir(dataset_id) / "bivariate_moran"
    destination.mkdir(parents=True, exist_ok=True)

    figure_path = destination / f"bivariate_moran_{x_name}__{y_name}.png"
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.scatter(zx, lag_y, alpha=0.55)
    xlim = max(abs(zx.min()), abs(zx.max()))
    xx = np.linspace(-xlim, xlim, 100)
    ax.plot(xx, test["moran_bv_i"] * xx)
    ax.axhline(0, linewidth=0.8)
    ax.axvline(0, linewidth=0.8)
    ax.set_xlabel(f"Standardized local {x_name}")
    ax.set_ylabel(f"Spatial lag of standardized {y_name}")
    ax.set_title(
        f"Bivariate Moran's I\n{x_name} -> spatial lag({y_name})\n"
        f"I={test['moran_bv_i']:.4f}, p(perm)={test['p_sim']:.4f}"
    )
    fig.tight_layout()
    fig.savefig(figure_path, dpi=180)
    plt.close(fig)

    payload = {
        "dataset_id": dataset_id,
        "unit": "AGEB urbana, CDMX",
        "x_local": x_name,
        "y_spatial_lag": y_name,
        **test,
        "significant_at_0_05": bool(test["p_sim"] < 0.05),
        "permutations": int(permutations),
        "seed": int(seed),
        "data_audit": data_audit,
        "weights_audit": weights_audit,
        "figure": str(figure_path),
        "caution": "This is spatial association between different variables and does not establish causation.",
    }
    write_json(destination / "bivariate_moran_summary.json", payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-id", required=True, type=int)
    parser.add_argument("--x", default=DEFAULT_X)
    parser.add_argument("--y", default=DEFAULT_Y)
    parser.add_argument("--permutations", type=int, default=999)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    run(args.dataset_id, args.x, args.y, args.permutations, args.seed)
