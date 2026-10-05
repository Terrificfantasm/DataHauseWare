"""Run the complete Phase 3 analytical workflow."""
from __future__ import annotations

import argparse
import json

from phase3_geographic_distribution import DEFAULT_VARIABLES as MAP_VARIABLES, run as run_maps
from phase3_correlations import DEFAULT_RELATIONSHIPS, run as run_correlations
from phase3_global_moran import DEFAULT_VARIABLES as MORAN_VARIABLES, run as run_global
from phase3_lisa import DEFAULT_VARIABLES as LISA_VARIABLES, run as run_lisa
from phase3_bivariate_moran import run as run_bivariate
from phase3_common import output_dir, write_json


def run(dataset_id: int, permutations: int = 999, seed: int = 42) -> dict:
    payload = {
        "dataset_id": dataset_id,
        "geographic_distribution": run_maps(dataset_id, MAP_VARIABLES),
        "correlations": run_correlations(dataset_id, DEFAULT_RELATIONSHIPS),
        "global_moran": run_global(dataset_id, MORAN_VARIABLES, permutations, seed),
        "lisa": run_lisa(dataset_id, LISA_VARIABLES, permutations, seed, 0.05),
        "bivariate_moran": run_bivariate(
            dataset_id,
            "business_density",
            "crime_records_per_1000",
            permutations,
            seed,
        ),
    }
    path = output_dir(dataset_id) / "phase3_summary.json"
    write_json(path, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-id", required=True, type=int)
    parser.add_argument("--permutations", type=int, default=999)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    run(args.dataset_id, args.permutations, args.seed)
