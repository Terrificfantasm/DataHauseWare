import geopandas as gpd 
import numpy as np
from shapely.geometry import box

from phase3_common import numeric_subset, queen_weights


def sample_frame():
    return gpd.GeoDataFrame(
        {"geography_id": [1, 2, 3], "metric": [1.0, np.nan, 3.0]},
        geometry=[box(0, 0, 1, 1), box(1, 0, 2, 1), box(2, 0, 3, 1)],
        crs="EPSG:4326",
    )


def test_numeric_subset_excludes_null_without_imputation():
    subset, audit = numeric_subset(sample_frame(), ["metric"])
    assert subset["geography_id"].tolist() == [1, 3]
    assert audit["input_rows"] == 3
    assert audit["included_rows"] == 2
    assert audit["excluded_rows"] == 1


def test_queen_weights_reports_topology():
    weights, audit = queen_weights(sample_frame())
    assert weights.n == 3
    assert audit["rule"].startswith("Queen")
    assert audit["island_count"] == 0
    assert audit["components"] == 1
    assert audit["min_neighbors"] >= 1
