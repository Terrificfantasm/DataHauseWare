import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import geopandas as gpd
import numpy as np
from shapely.geometry import box

from phase3_bivariate_moran import bivariate_moran_i, permutation_test
from phase3_common import queen_weights


def grid_frame():
    return gpd.GeoDataFrame(
        {
            "geography_id": [1, 2, 3, 4],
            "x": [1.0, 2.0, 4.0, 8.0],
            "y": [8.0, 4.0, 2.0, 1.0],
        },
        geometry=[
            box(0, 0, 1, 1), box(1, 0, 2, 1),
            box(0, 1, 1, 2), box(1, 1, 2, 2),
        ],
        crs="EPSG:4326",
    )


def test_bivariate_moran_is_finite_and_reproducible():
    frame = grid_frame()
    weights, _ = queen_weights(frame)
    x = frame["x"].to_numpy()
    y = frame["y"].to_numpy()
    assert np.isfinite(bivariate_moran_i(x, y, weights))
    first = permutation_test(x, y, weights, permutations=99, seed=42)
    second = permutation_test(x, y, weights, permutations=99, seed=42)
    assert first == second
    assert 0 < first["p_sim"] <= 1
