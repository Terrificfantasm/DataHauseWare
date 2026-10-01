import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box
from spatial import assign_points


def test_assignment_preserves_rows_and_quarantines_shared_border():
    areas = gpd.GeoDataFrame({"CVEGEO": ["A", "B"]},
        geometry=[box(10, 10, 11, 11), box(11, 10, 12, 11)], crs=4326)
    points = pd.DataFrame({"longitude": [10.5, 11, 15, None, 0, 10],
                           "latitude": [10.5, 10.5, 15, 10, 0, 10.5]})
    result = assign_points(points, areas)
    assert result.assignment_status.tolist() == ["assigned", "ambiguous", "outside_selected_areas",
                                                "invalid_coordinates", "invalid_coordinates", "assigned"]
    assert result.match_count.tolist() == [1, 2, 0, 0, 0, 1]
    assert pd.isna(result.loc[1, "CVEGEO"])
    assert result.loc[5, "CVEGEO"] == "A"


def test_assignment_reprojects_points():
    areas = gpd.GeoDataFrame({"CVEGEO": ["A"]}, geometry=[box(10, 10, 11, 11)], crs=4326).to_crs(3857)
    result = assign_points(pd.DataFrame({"longitude": [10.5], "latitude": [10.5]}), areas)
    assert result.loc[0, "CVEGEO"] == "A"


def test_duplicate_polygon_keys_rejected():
    areas = gpd.GeoDataFrame({"CVEGEO": ["A", "A"]}, geometry=[box(10, 10, 11, 11), box(11, 10, 12, 11)], crs=4326)
    with pytest.raises(ValueError):
        assign_points(pd.DataFrame({"longitude": [10.5], "latitude": [10.5]}), areas)
