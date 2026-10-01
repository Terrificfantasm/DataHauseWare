import sys
from pathlib import Path
import zipfile
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from assess_geography import locality_totals, read_csv_zip


def test_all_localities_do_not_double_count_administrative_totals():
    frame = pd.DataFrame({"MUN": ["000", "002", "002", "002"],
        "LOC": ["0000", "0000", "0001", "0001"],
        "AGEB": ["0000", "0000", "0000", "0010"],
        "MZA": ["000"] * 4, "POBTOT": ["100", "100", "100", "100"]})
    assert locality_totals(frame).tolist() == ["100"]


def test_explicit_encoding_preserves_undefined_cp1252_byte(tmp_path):
    path = tmp_path / "data.zip"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("conjunto_de_datos/data.csv", b"id,name\n1,a\x90b\n")
    result = read_csv_zip(path, "latin1")
    assert result.loc[0, "name"] == "a\x90b"


def test_denue_numeric_codes_restore_leading_zeroes():
    from assess_geography import normalize_business_keys
    f = pd.DataFrame({"cve_ent": ["9"], "cve_mun": ["2"], "cve_loc": ["1"]})
    r = normalize_business_keys(f)
    assert r.iloc[0].tolist() == ["09", "002", "0001"]
    assert f.iloc[0].tolist() == ["9", "2", "1"]
