"""Local Moran / LISA analysis using Queen contiguity and conditional permutations."""
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


def local_moran(z: np.ndarray, weights) -> tuple[np.ndarray, np.ndarray]:
    z = np.asarray(z, dtype=float)
    lag_z = weights.lag(z)
    return z * lag_z, lag_z


def local_permutation_pvalues(
    z: np.ndarray,
    weights,
    permutations: int = 999,
    seed: int = 42,
) -> np.ndarray:
    if permutations < 1:
        raise ValueError("permutations must be at least 1")

    z = np.asarray(z, dtype=float)
    observed, _ = local_moran(z, weights)
    rng = np.random.default_rng(seed)
    ids = weights.ids
    index = {key: pos for pos, key in enumerate(ids)}
    p_values = np.ones(len(z), dtype=float)

    for pos, key in enumerate(ids):
        neighbors = weights.neighbors[key]
        degree = len(neighbors)
        if degree == 0:
            p_values[pos] = 1.0
            continue

        pool = np.delete(z, pos)
        simulated = np.empty(permutations, dtype=float)
        for k in range(permutations):
            sampled = rng.choice(pool, size=degree, replace=False)
            simulated[k] = z[pos] * float(np.mean(sampled))

        extreme = np.sum(np.abs(simulated) >= abs(observed[pos]))
        p_values[pos] = float((extreme + 1) / (permutations + 1))

    return p_values


def cluster_label(z_value: float, lag_value: float, p_value: float, island: bool, alpha: float) -> str:
    if island:
        return "Island"
    if p_value >= alpha:
        return "Not significant"
    if z_value >= 0 and lag_value >= 0:
        return "High-High"
    if z_value < 0 and lag_value < 0:
        return "Low-Low"
    if z_value >= 0 and lag_value < 0:
        return "High-Low"
    return "Low-High"


def analyze_variable(frame, variable: str, permutations: int, seed: int, alpha: float, destination) -> dict:
    subset, data_audit = numeric_subset(frame, [variable])
    weights, weights_audit = queen_weights(subset)
    values = subset[variable].to_numpy(dtype=float)
    z = standardize(values)
    local_i, lag_z = local_moran(z, weights)
    p_values = local_permutation_pvalues(z, weights, permutations, seed)

    island_ids = set(weights.islands)
    ids = subset["geography_id"].astype(str).tolist()
    labels = [
        cluster_label(z[i], lag_z[i], p_values[i], ids[i] in island_ids, alpha)
        for i in range(len(subset))
    ]

    result_table = subset[["dataset_id", "geography_id", "cvegeo", variable]].copy() if "dataset_id" in subset.columns and "cvegeo" in subset.columns else subset[["geography_id", variable]].copy()
    result_table["z"] = z
    result_table["spatial_lag_z"] = lag_z
    result_table["local_moran_i"] = local_i
    result_table["p_perm"] = p_values
    result_table["lisa_cluster"] = labels

    csv_path = destination / f"lisa_clusters_{variable}.csv"
    result_table.to_csv(csv_path, index=False)

    map_frame = subset.copy()
    map_frame["lisa_cluster"] = labels
    figure_path = destination / f"lisa_map_{variable}.png"
    fig, ax = plt.subplots(figsize=(8, 8))
    map_frame.plot(column="lisa_cluster", categorical=True, legend=True, ax=ax)
    ax.set_title(f"LISA clusters — {variable} (alpha={alpha})")
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(figure_path, dpi=180, bbox_inches="tight")
    plt.close(fig)

    counts = {}
    for label in labels:
        counts[label] = counts.get(label, 0) + 1

    return {
        "variable": variable,
        "alpha": float(alpha),
        "permutations": int(permutations),
        "seed": int(seed),
        "cluster_counts": counts,
        "significant_count": int(np.sum(p_values < alpha)),
        "data_audit": data_audit,
        "weights_audit": weights_audit,
        "table": str(csv_path),
        "figure": str(figure_path),
        "caution": "LISA identifies local spatial association/outliers; it does not establish causation.",
    }


def run(dataset_id: int, variables: list[str], permutations: int = 999, seed: int = 42, alpha: float = 0.05) -> dict:
    frame = load_ageb_kpis(dataset_id)
    destination = output_dir(dataset_id) / "lisa"
    destination.mkdir(parents=True, exist_ok=True)

    results = [analyze_variable(frame, v, permutations, seed, alpha, destination) for v in variables]
    payload = {
        "dataset_id": dataset_id,
        "unit": "AGEB urbana, CDMX",
        "neighborhood_rule": "Queen contiguity",
        "variables": results,
    }
    write_json(destination / "lisa_summary.json", payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-id", required=True, type=int)
    parser.add_argument("--variables", nargs="+", default=DEFAULT_VARIABLES)
    parser.add_argument("--permutations", type=int, default=999)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--alpha", type=float, default=0.05)
    args = parser.parse_args()
    run(args.dataset_id, args.variables, args.permutations, args.seed, args.alpha)
