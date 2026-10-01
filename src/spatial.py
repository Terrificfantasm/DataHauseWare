"""Point assignment: never duplicate or arbitrarily snap observations."""
import geopandas as gpd
import pandas as pd


def assign_points(frame, areas, longitude="longitude", latitude="latitude"):
    """Return exactly one row per input, including invalid/outside/ambiguous rows.

    Coordinates must be WGS84. Areas must have a CRS and unique CVEGEO keys.
    Intersects includes borders; multiple matches remain unassigned.
    """
    if areas.crs is None or areas.CVEGEO.duplicated().any():
        raise ValueError("Areas require a CRS and unique CVEGEO")
    if areas.geometry.isna().any() or areas.geometry.is_empty.any() or not areas.is_valid.all():
        raise ValueError("Invalid or empty area geometry")
    result = frame.reset_index(drop=True).copy()
    x = pd.to_numeric(result[longitude], errors="coerce")
    y = pd.to_numeric(result[latitude], errors="coerce")
    valid = x.between(-180, 180) & y.between(-90, 90) & ~((x == 0) & (y == 0))
    result["assignment_status"] = "invalid_coordinates"
    result["CVEGEO"] = pd.Series(pd.NA, index=result.index, dtype="string")
    result["match_count"] = 0
    if valid.any():
        points = gpd.GeoDataFrame(index=result.index[valid],
            geometry=gpd.points_from_xy(x[valid], y[valid]), crs="EPSG:4326")
        matches = gpd.sjoin(points.to_crs(areas.crs), areas[["CVEGEO", "geometry"]],
                            how="left", predicate="intersects")
        counts = matches.groupby(level=0)["CVEGEO"].count()
        result.loc[valid, "assignment_status"] = "outside_selected_areas"
        result.loc[counts.index, "match_count"] = counts
        single = counts[counts == 1].index
        unique = matches.loc[single, "CVEGEO"]
        result.loc[single, "CVEGEO"] = unique
        result.loc[single, "assignment_status"] = "assigned"
        result.loc[counts[counts > 1].index, "assignment_status"] = "ambiguous"
    assert len(result) == len(frame)
    return result
