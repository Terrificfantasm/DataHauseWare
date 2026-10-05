import geopandas as gpd
import numpy as np 
from shapely.geometry import box

from phase3_global_moran import analyze_variable, moran_i, permutation_test
from phase3_common import queen_weights


def grid_frame():
    return gpd.GeoDataFrame(
        {"geography_id": [1, 2, 3, 4], "metric": [1.0, 2.0, 4.0, 8.0]},
        geometry=[
            box(0, 0, 1, 1),
            box(1, 0, 2, 1),
            box(0, 1, 1, 2),
            box(1, 1, 2, 2),
        ],
        crs="EPSG:4326",
    )


def test_moran_is_finite_and_permutation_is_reproducible():
    frame = grid_frame()
    weights, _ = queen_weights(frame)
    values = frame["metric"].to_numpy(dtype=float)
    assert np.isfinite(moran_i(values, weights))
    first = permutation_test(values, weights, permutations=99, seed=42)
    second = permutation_test(values, weights, permutations=99, seed=42)
    assert first == second
    assert 0.0 < first["p_sim"] <= 1.0


def test_global_moran_writes_figure(tmp_path):
    result = analyze_variable(grid_frame(), "metric", 99, 42, tmp_path)
    assert result["variable"] == "metric"
    assert result["data_audit"]["included_rows"] == 4
    assert result["weights_audit"]["n"] == 4
    assert (tmp_path / "moran_scatter_metric.png").exists()
