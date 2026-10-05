"""Shared utilities for Phase 3 spatial analytics.

All final Phase 3 analyses consume exports generated from PostgreSQL/PostGIS.
Raw source files are not read here. Missing values are never imputed as zero.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import geopandas as gpd
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class QueenWeights:
    """Minimal row-standardized Queen contiguity representation."""

    ids: list[str]
    neighbors: dict[str, list[str]]

    @property
    def n(self) -> int:
        return len(self.ids)

    @property
    def islands(self) -> list[str]:
        return [key for key, values in self.neighbors.items() if not values]

    def lag(self, values: np.ndarray) -> np.ndarray:
        values = np.asarray(values, dtype=float)
        index = {key: pos for pos, key in enumerate(self.ids)}
        result = np.zeros(self.n, dtype=float)
        for pos, key in enumerate(self.ids):
            neigh = self.neighbors[key]
            if not neigh:
                result[pos] = 0.0
            else:
                result[pos] = float(np.mean([values[index[n]] for n in neigh]))
        return result

    @property
    def s0(self) -> float:
        # Row-standardized weights: every non-island row sums to 1.
        return float(sum(1.0 for key in self.ids if self.neighbors[key]))


def input_dir(dataset_id: int) -> Path:
    return ROOT / "outputs" / "cdmx" / "phase3_inputs" / str(dataset_id)


def output_dir(dataset_id: int) -> Path:
    path = ROOT / "outputs" / "cdmx" / "phase3" / str(dataset_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_ageb_kpis(dataset_id: int) -> gpd.GeoDataFrame:
    """Load KPI attributes and AGEB geometry exported from the DW."""
    source = input_dir(dataset_id)
    kpi_path = source / "kpi_ageb.csv"
    geo_path = source / "areas.geojson"

    if not kpi_path.exists() or not geo_path.exists():
        raise FileNotFoundError(
            "Phase 3 inputs are missing. Run "
            f"'python src/export_analysis.py --dataset-id {dataset_id}' first."
        )

    kpis = pd.read_csv(kpi_path, dtype={"cvegeo": "string"})
    areas = gpd.read_file(geo_path)

    if "CVEGEO" in areas.columns and "cvegeo" not in areas.columns:
        areas = areas.rename(columns={"CVEGEO": "cvegeo"})
    areas["cvegeo"] = areas["cvegeo"].astype("string")

    required = {"dataset_id", "geography_id", "cvegeo"}
    missing_kpi = required.difference(kpis.columns)
    missing_geo = required.difference(areas.columns)
    if missing_kpi or missing_geo:
        raise ValueError(
            f"Missing join columns; KPI={sorted(missing_kpi)}, "
            f"geometry={sorted(missing_geo)}"
        )

    if kpis.duplicated(["dataset_id", "geography_id"]).any():
        raise ValueError("kpi_ageb must contain one row per dataset/geography")
    if areas.duplicated(["dataset_id", "geography_id"]).any():
        raise ValueError("areas.geojson must contain one geometry per dataset/geography")

    merged = areas.merge(
        kpis,
        on=["dataset_id", "geography_id", "cvegeo"],
        how="inner",
        validate="one_to_one",
    )

    if len(merged) != len(kpis):
        raise ValueError(
            f"Geometry/KPI mismatch: {len(kpis)} KPI rows, {len(merged)} matched rows"
        )
    if merged.crs is None:
        raise ValueError("AGEB geometry has no CRS")
    if merged.geometry.isna().any() or merged.geometry.is_empty.any():
        raise ValueError("AGEB geometry contains null or empty geometries")
    if not merged.is_valid.all():
        raise ValueError("AGEB geometry contains invalid geometries")

    return merged


def numeric_subset(
    frame: gpd.GeoDataFrame,
    columns: Iterable[str],
) -> tuple[gpd.GeoDataFrame, dict]:
    """Return rows with finite values for all requested variables."""
    columns = list(columns)
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise KeyError(f"Missing analytical columns: {missing}")

    converted = frame.copy()
    for column in columns:
        converted[column] = pd.to_numeric(converted[column], errors="coerce")

    finite = np.ones(len(converted), dtype=bool)
    for column in columns:
        values = converted[column].to_numpy(dtype=float, na_value=np.nan)
        finite &= np.isfinite(values)

    subset = converted.loc[finite].copy()
    audit = {
        "requested_columns": columns,
        "input_rows": int(len(frame)),
        "included_rows": int(len(subset)),
        "excluded_rows": int(len(frame) - len(subset)),
    }
    if subset.empty:
        raise ValueError(f"No complete finite observations for {columns}")
    return subset, audit


def _component_count(neighbors: dict[str, list[str]]) -> int:
    remaining = set(neighbors)
    components = 0
    while remaining:
        components += 1
        stack = [remaining.pop()]
        while stack:
            current = stack.pop()
            for neighbor in neighbors[current]:
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
    return components


def queen_weights(frame: gpd.GeoDataFrame) -> tuple[QueenWeights, dict]:
    """Build Queen contiguity weights using the GeoPandas spatial index.

    Two AGEB are neighbors when their polygon boundaries or interiors intersect.
    Because the analytical polygons are expected not to overlap, this corresponds
    to sharing an edge or vertex. Islands are reported and are not artificially
    connected with nearest-neighbor rules.
    """
    if frame.empty:
        raise ValueError("Cannot build spatial weights for an empty frame")
    if frame.crs is None:
        raise ValueError("A CRS is required before building spatial weights")

    ids = frame["geography_id"].astype(str).tolist()
    if len(ids) != len(set(ids)):
        raise ValueError("geography_id must be unique before building weights")

    neighbors = {key: set() for key in ids}
    left_idx, right_idx = frame.sindex.query(frame.geometry, predicate="intersects")
    for left, right in zip(left_idx, right_idx):
        if int(left) == int(right):
            continue
        left_id = ids[int(left)]
        right_id = ids[int(right)]
        neighbors[left_id].add(right_id)
        neighbors[right_id].add(left_id)

    neighbor_lists = {key: sorted(values) for key, values in neighbors.items()}
    weights = QueenWeights(ids=ids, neighbors=neighbor_lists)
    counts = [len(values) for values in neighbor_lists.values()]
    audit = {
        "rule": "Queen contiguity (shared edge or vertex)",
        "implementation": "GeoPandas spatial index with polygon intersects predicate",
        "n": weights.n,
        "islands": weights.islands,
        "island_count": len(weights.islands),
        "components": _component_count(neighbor_lists),
        "min_neighbors": int(min(counts)),
        "max_neighbors": int(max(counts)),
        "mean_neighbors": float(np.mean(counts)),
    }
    return weights, audit


def standardize(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    std = values.std(ddof=0)
    if std == 0:
        raise ValueError("Standardization is undefined for a constant variable")
    return (values - values.mean()) / std


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
