import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from profile_kpi_inputs import profile
from profile_spatial_sensitivity import summarize

def test_reserved_census_values_are_not_zero():
    r=profile(pd.Series(['*','0','2','']))
    assert r['numeric']==2 and r['zero']==1
    assert r['non_numeric_tokens']=={'*':1,'':1}

def test_distance_thresholds_include_boundary_and_are_cumulative():
    r=summarize(np.array([0.,10.,25.,50.,100.,101.]))
    assert [r[str(x)]['rows'] for x in (10,25,50,100)]==[2,3,4,5]
