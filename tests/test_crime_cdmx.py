import sys
from pathlib import Path
import pandas as pd
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from assess_crime_cdmx import prepare


def sample():
    return pd.DataFrame({"_id": ["1", "2"], "fecha_inicio": ["2020-01-02"]*2,
        "fecha_hecho": ["2019-12-31"]*2, "latitud": ["NA"]*2, "longitud": ["NA"]*2,
        "delito": ["X"]*2, "categoria_delito": ["HECHO NO DELICTIVO"]*2, "competencia": ["NA"]*2})


def test_repeated_attributes_preserved_and_years_not_conflated():
    r = prepare(sample(), "hash")
    assert len(r) == 2 and r.source_record_id.is_unique
    assert r.duplicate_public_attributes.all()
    assert not r.event_in_2020.any()
    assert r.flag_noncriminal.all()


def test_rejects_wrong_cohort():
    f = sample(); f.loc[0, "fecha_inicio"] = "2021-01-01"
    with pytest.raises(ValueError, match="cohort"):
        prepare(f, "hash")


def test_duplicate_source_id_fails():
    f = sample(); f.loc[1, "_id"] = "1"
    with pytest.raises(ValueError, match="identifiers"):
        prepare(f, "hash")
