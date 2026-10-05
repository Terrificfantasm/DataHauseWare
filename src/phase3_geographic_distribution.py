"""Descriptive geographic distribution maps for Phase 3 KPIs.

Consumes the KPI/geometry export produced from PostgreSQL/PostGIS. The maps are
exploratory/descriptive and are not treated as evidence of spatial association.
"""
from __future__ import annotations

import argparse
import json

import matplotlib.pyplot as plt

from phase3_common import load_ageb_kpis, numeric_subset, output_dir, write_json

DEFAULT_VARIABLES = [
    "population_density",
    "business_density",
    "crime_records_per_1000",
]


def analyze_variable(frame, variable: str, destination) -> dict:
    subset, data_audit = numeric_subset(frame, [variable])
    values = subset[variable]

    figure_path = destination / f"map_{variable}.png"
    fig, ax = plt.subplots(figsize=(8, 8))
    subset.plot(column=variable, legend=True, ax=ax)
    ax.set_title(f"CDMX AGEB — {variable}")
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(figure_path, dpi=180, bbox_inches="tight")
    plt.close(fig)

    return {
        "variable": variable,
        "minimum": float(values.min()),
        "q1": float(values.quantile(0.25)),
        "median": float(values.median()),
        "q3": float(values.quantile(0.75)),
        "maximum": float(values.max()),
        "data_audit": data_audit,
        "figure": str(figure_path),
    }


def run(dataset_id: int, variables: list[str]) -> dict:
    frame = load_ageb_kpis(dataset_id)
    destination = output_dir(dataset_id) / "geographic_distribution"
    destination.mkdir(parents=True, exist_ok=True)

    results = [analyze_variable(frame, variable, destination) for variable in variables]
    payload = {
        "dataset_id": dataset_id,
        "unit": "AGEB urbana, CDMX",
        "variables": results,
        "caution": (
            "These maps are descriptive. Visible geographic patterns do not by "
            "themselves establish spatial autocorrelation or causation."
        ),
    }
    write_json(destination / "geographic_distribution_summary.json", payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-id", required=True, type=int)
    parser.add_argument("--variables", nargs="+", default=DEFAULT_VARIABLES)
    args = parser.parse_args()
    run(args.dataset_id, args.variables)
