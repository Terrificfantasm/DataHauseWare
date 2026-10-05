import numpy as np

from phase3_correlations import (
    DEFAULT_RELATIONSHIPS,
    choose_method,
    outlier_share,
)


def test_default_relationships_are_required():
    assert DEFAULT_RELATIONSHIPS == [
        ("population_density", "business_density"),
        ("population_density", "crime_records_per_1000"),
        ("business_density", "crime_records_per_1000"),
    ]


def test_choose_method_uses_pearson_when_no_trigger_is_present():
    x = np.arange(1, 11, dtype=float)
    y = np.arange(2, 22, 2, dtype=float)

    method, diagnostics = choose_method(x, y)

    assert method == "pearson"
    assert diagnostics["x_outlier_share"] <= 0.05
    assert diagnostics["y_outlier_share"] <= 0.05
    assert abs(diagnostics["x_skew"]) <= 1.0
    assert abs(diagnostics["y_skew"]) <= 1.0


def test_choose_method_uses_spearman_when_skew_exceeds_threshold():
    x = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 100], dtype=float)
    y = np.arange(1, 11, dtype=float)

    method, diagnostics = choose_method(x, y)

    assert method == "spearman"
    assert abs(diagnostics["x_skew"]) > 1.0


def test_choose_method_uses_spearman_when_outlier_share_exceeds_threshold():
    x = np.array(
        [10, 10, 10, 10, 10, 10, 10, 10, 10, 100],
        dtype=float,
    )
    y = np.arange(10, dtype=float)

    share = outlier_share(x)

    assert share > 0.05

    method, _ = choose_method(x, y)

    assert method == "spearman"
