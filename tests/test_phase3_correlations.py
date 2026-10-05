import geopandas as gpd
import numpy as np
from shapely.geometry import box

from phase3_correlations import choose_method, analyze_pair


def frame():
    x=np.arange(1.0, 101.0)
    return gpd.GeoDataFrame(
        {"geography_id": np.arange(100), "x": x, "y": 2*x+5},
        geometry=[box(i,0,i+1,1) for i in range(100)],
        crs="EPSG:4326",
    )


def test_method_pearson_for_linear_clean_data():
    x=np.arange(1.0,101.0)
    y=2*x+5
    method,_=choose_method(x,y)
    assert method=="pearson"


def test_pair_writes_figure(tmp_path):
    result=analyze_pair(frame(),"x","y",tmp_path)
    assert result["method"]=="pearson"
    assert result["coefficient"] > 0.99
    assert (tmp_path/"correlation_x__y.png").exists()
