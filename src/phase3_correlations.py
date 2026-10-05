"""Three required Phase 3 correlations with reproducible method selection."""
from __future__ import annotations

import argparse
import json

import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

from phase3_common import load_ageb_kpis, numeric_subset, output_dir, write_json

DEFAULT_RELATIONSHIPS = [
    ("population_density", "business_density"),
    ("population_density", "crime_records_per_1000"),
    ("business_density", "crime_records_per_1000"),
]


def outlier_share(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    q1, q3 = np.quantile(values, [0.25, 0.75])
    iqr = q3 - q1
    if iqr == 0:
        return 0.0
    low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return float(np.mean((values < low) | (values > high)))


def choose_method(x: np.ndarray, y: np.ndarray) -> tuple[str, dict]:
    diagnostics = {
        "x_skew": float(stats.skew(x, bias=False)),
        "y_skew": float(stats.skew(y, bias=False)),
        "x_outlier_share": outlier_share(x),
        "y_outlier_share": outlier_share(y),
        "selection_rule": "Spearman if |skew| > 1 or IQR-outlier share > 5% in either variable; otherwise Pearson.",
    }
    spearman = (
        abs(diagnostics["x_skew"]) > 1.0
        or abs(diagnostics["y_skew"]) > 1.0
        or diagnostics["x_outlier_share"] > 0.05
        or diagnostics["y_outlier_share"] > 0.05
    )
    return ("spearman" if spearman else "pearson"), diagnostics


def analyze_pair(frame, x_name: str, y_name: str, destination) -> dict:
    subset, audit = numeric_subset(frame, [x_name, y_name])
    x = subset[x_name].to_numpy(dtype=float)
    y = subset[y_name].to_numpy(dtype=float)

    if np.unique(x).size < 2 or np.unique(y).size < 2:
        raise ValueError(f"Correlation undefined for constant pair: {x_name}, {y_name}")

    method, diagnostics = choose_method(x, y)
    result = stats.spearmanr(x, y) if method == "spearman" else stats.pearsonr(x, y)
    coefficient = float(result.statistic)
    p_value = float(result.pvalue)

    figure_path = destination / f"correlation_{x_name}__{y_name}.png"
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.scatter(x, y, alpha=0.45)
    ax.set_xlabel(x_name)
    ax.set_ylabel(y_name)
    ax.set_title(f"{method.title()} correlation\nr={coefficient:.3f}, p={p_value:.4g}, n={len(subset)}")
    fig.tight_layout()
    fig.savefig(figure_path, dpi=180)
    plt.close(fig)

    return {
        "x": x_name,
        "y": y_name,
        "method": method,
        "coefficient": coefficient,
        "p_value": p_value,
        "significant_at_0_05": bool(p_value < 0.05),
        "n": int(len(subset)),
        "diagnostics": diagnostics,
        "data_audit": audit,
        "figure": str(figure_path),
        "caution": "Correlation does not imply causation.",
    }


def run(dataset_id: int, relationships: list[tuple[str, str]]) -> dict:
    if len(relationships) < 3:
        raise ValueError("At least three relationships are required")
    frame = load_ageb_kpis(dataset_id)
    destination = output_dir(dataset_id) / "correlations"
    destination.mkdir(parents=True, exist_ok=True)

    results = [analyze_pair(frame, x, y, destination) for x, y in relationships]
    payload = {"dataset_id": dataset_id, "unit": "AGEB urbana, CDMX", "relationships": results}
    write_json(destination / "correlations_summary.json", payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-id", required=True, type=int)
    args = parser.parse_args()
    run(args.dataset_id, DEFAULT_RELATIONSHIPS)
