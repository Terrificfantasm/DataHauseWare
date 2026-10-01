import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from audit_cdmx_coverage import eligibility


def test_exclusion_precedence_and_unknown_are_explicit():
    f = pd.DataFrame({"competencia": ["NA", "INCOMPETENCIA", "FUERO COMUN", "NA", "NEW"],
        "categoria_delito": ["X", "HECHO NO DELICTIVO", "X", "X", "X"],
        "delito": ["DENUNCIA DE HECHOS", "X", "SUSTRACCION DE MENORES", "X", "X"]})
    assert eligibility(f).tolist() == ["excluded_report_of_facts", "excluded_noncriminal",
        "candidate_common_jurisdiction", "candidate_unknown_competence", "review_other_competence"]
