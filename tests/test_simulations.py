import sys
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import box
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from simulate_spatial_cdmx import offsets,locate,counts

def test_disk_is_bounded_reproducible_and_zero_is_identity():
    x,y=offsets(1000,25,1); a,b=offsets(1000,25,1)
    assert np.array_equal(x,a) and np.array_equal(y,b)
    assert np.all(np.hypot(x,y)<=25)
    z,w=offsets(10,0,1);assert np.all(z==0) and np.all(w==0)

def test_unique_outside_and_shared_border_preserve_counts():
    tree=shapely.STRtree([box(0,0,1,1),box(1,0,2,1)])
    result=locate(tree,np.array([.5,1,3,1.5]),np.array([.5,.5,.5,.5]))
    assert result.tolist()==[0,-2,-1,1]
    assert counts(result,2).tolist()==[1,1]
