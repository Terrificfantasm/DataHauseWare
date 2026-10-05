import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import geopandas as gpd
from shapely.geometry import box

from phase3_geographic_distribution import analyze_variable


def sample_frame():
    return gpd.GeoDataFrame(
        {"geography_id": [1, 2, 3], "metric": [1.0, 2.0, 3.0]},
        geometry=[box(0, 0, 1, 1), box(1, 0, 2, 1), box(2, 0, 3, 1)],
        crs="EPSG:4326",
    )


def test_map_summary_and_figure(tmp_path):
    result = analyze_variable(sample_frame(), "metric", tmp_path)
    assert result["minimum"] == 1.0
    assert result["median"] == 2.0
    assert result["maximum"] == 3.0
    assert (tmp_path / "map_metric.png").exists()
