"""Global Moran's I for selected AGEB KPIs.

The implementation uses row-standardized Queen contiguity and a reproducible
permutation test, avoiding hidden changes to missing data or spatial topology.
"""
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

DEFAULT_VARIABLES = ["crime_records_per_1000", "business_density"]


def moran_i(values: np.ndarray, weights) -> float:
    """Compute Global Moran's I with row-standardized spatial weights."""
    values = np.asarray(values, dtype=float)
    centered = values - values.mean()
    denominator = float(np.dot(centered, centered))
    if denominator == 0:
        raise ValueError("Moran's I is undefined for a constant variable")
    if weights.s0 == 0:
        raise ValueError("Moran's I is undefined when every observation is an island")
    spatial_lag = weights.lag(centered)
    numerator = float(np.dot(centered, spatial_lag))
    return float((len(values) / weights.s0) * (numerator / denominator))


def permutation_test(
    values: np.ndarray,
    weights,
    permutations: int,
    seed: int,
) -> dict:
    if permutations < 1:
        raise ValueError("permutations must be at least 1")
    observed = moran_i(values, weights)
    expected = -1.0 / (len(values) - 1) if len(values) > 1 else np.nan
    rng = np.random.default_rng(seed)
    simulated = np.empty(permutations, dtype=float)
    for index in range(permutations):
        simulated[index] = moran_i(rng.permutation(values), weights)

    distance = abs(observed - expected)
    extreme = np.sum(np.abs(simulated - expected) >= distance)
    p_sim = float((extreme + 1) / (permutations + 1))
    sim_std = float(simulated.std(ddof=1)) if permutations > 1 else 0.0
    z_sim = float((observed - simulated.mean()) / sim_std) if sim_std > 0 else 0.0
    return {
        "moran_i": observed,
        "expected_i": float(expected),
        "p_sim": p_sim,
        "z_sim": z_sim,
        "sim_mean": float(simulated.mean()),
        "sim_std": sim_std,
    }


def analyze_variable(frame, variable: str, permutations: int, seed: int, destination) -> dict:
    subset, data_audit = numeric_subset(frame, [variable])
    weights, weights_audit = queen_weights(subset)
    values = subset[variable].to_numpy(dtype=float)
    test = permutation_test(values, weights, permutations, seed)

    z = standardize(values)
    lag_z = weights.lag(z)

    figure_path = destination / f"moran_scatter_{variable}.png"
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.scatter(z, lag_z, alpha=0.55)
    xlim = max(abs(z.min()), abs(z.max()))
    xx = np.linspace(-xlim, xlim, 100)
    ax.plot(xx, test["moran_i"] * xx)
    ax.axhline(0, linewidth=0.8)
    ax.axvline(0, linewidth=0.8)
    ax.set_xlabel(f"Standardized {variable}")
    ax.set_ylabel("Row-standardized spatial lag")
    ax.set_title(
        f"Global Moran's I — {variable}\n"
        f"I={test['moran_i']:.4f}, p(perm)={test['p_sim']:.4f}"
    )
    fig.tight_layout()
    fig.savefig(figure_path, dpi=180)
    plt.close(fig)

    return {
        "variable": variable,
        **test,
        "permutations": int(permutations),
        "seed": int(seed),
        "significant_at_0_05": bool(test["p_sim"] < 0.05),
        "data_audit": data_audit,
        "weights_audit": weights_audit,
        "figure": str(figure_path),
        "caution": (
            "Spatial association does not imply causation. Results depend on "
            "the Queen-neighborhood rule, missing-value exclusions, and the "
            "operational definition of the underlying indicators."
        ),
    }


def run(dataset_id: int, variables: list[str], permutations: int = 999, seed: int = 42) -> dict:
    if len(variables) < 2:
        raise ValueError("Provide at least two indicators for Global Moran's I")
    frame = load_ageb_kpis(dataset_id)
    destination = output_dir(dataset_id) / "global_moran"
    destination.mkdir(parents=True, exist_ok=True)
    results = [
        analyze_variable(frame, variable, permutations, seed, destination)
        for variable in variables
    ]
    payload = {
        "dataset_id": dataset_id,
        "unit": "AGEB urbana, CDMX",
        "neighborhood_rule": "Queen contiguity",
        "variables": results,
    }
    write_json(destination / "global_moran_summary.json", payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-id", required=True, type=int)
    parser.add_argument("--variables", nargs="+", default=DEFAULT_VARIABLES)
    parser.add_argument("--permutations", type=int, default=999)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    run(args.dataset_id, args.variables, args.permutations, args.seed)
