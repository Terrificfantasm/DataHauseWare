import geopandas as gpd
import numpy as np
from shapely.geometry import box

from phase3_common import queen_weights
from phase3_bivariate_moran import bivariate_moran_i, permutation_test


def grid():
    return gpd.GeoDataFrame(
        {"geography_id":[1,2,3,4],"x":[1.,2.,4.,8.],"y":[8.,4.,2.,1.]},
        geometry=[box(0,0,1,1),box(1,0,2,1),box(0,1,1,2),box(1,1,2,2)],
        crs="EPSG:4326",
    )


def test_bivariate_is_finite_and_reproducible():
    frame=grid()
    w,_=queen_weights(frame)
    x=frame["x"].to_numpy(float)
    y=frame["y"].to_numpy(float)
    assert np.isfinite(bivariate_moran_i(x,y,w))
    r1=permutation_test(x,y,w,99,42)
    r2=permutation_test(x,y,w,99,42)
    assert r1==r2
    assert 0 < r1["p_sim"] <= 1
