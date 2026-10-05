import geopandas as gpd
import numpy as np
from shapely.geometry import box

from phase3_common import queen_weights, standardize
from phase3_lisa import local_moran, local_permutation_pvalues, cluster_label


def grid():
    return gpd.GeoDataFrame(
        {"geography_id":[1,2,3,4],"metric":[1.0,2.0,4.0,8.0]},
        geometry=[box(0,0,1,1),box(1,0,2,1),box(0,1,1,2),box(1,1,2,2)],
        crs="EPSG:4326",
    )


def test_local_permutation_is_reproducible():
    frame=grid()
    w,_=queen_weights(frame)
    z=standardize(frame["metric"].to_numpy(float))
    p1=local_permutation_pvalues(z,w,99,42)
    p2=local_permutation_pvalues(z,w,99,42)
    assert np.allclose(p1,p2)
    assert np.all((p1>0)&(p1<=1))


def test_cluster_labels():
    assert cluster_label(1,1,0.01,False,0.05)=="High-High"
    assert cluster_label(-1,-1,0.01,False,0.05)=="Low-Low"
    assert cluster_label(1,-1,0.01,False,0.05)=="High-Low"
    assert cluster_label(-1,1,0.01,False,0.05)=="Low-High"
    assert cluster_label(1,1,0.50,False,0.05)=="Not significant"
    assert cluster_label(1,1,0.01,True,0.05)=="Island"
