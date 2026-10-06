# Phase 3 — Spatial Analysis Results

Real execution for **dataset 2: CDMX urbano 2020**, using the analytical export generated from the PostgreSQL/PostGIS Data Warehouse.

## Reproducibility

- Geographic unit: urban AGEB, Ciudad de México.
- Spatial neighborhood: Queen contiguity (shared edge or vertex).
- Permutations: 999.
- Random seed: 42.
- Missing/undefined analytical values were excluded, never imputed as zero.
- Source provenance is recorded in `input_manifest.json`.

## Main results

### Correlations

| Relationship | Method | Coefficient | p-value | n |
|---|---|---:|---:|---:|
| Population density vs. business density | Spearman | 0.4012 | 1.139e-94 | 2431 |
| Population density vs. crime records per 1,000 | Spearman | -0.3663 | 1.572e-77 | 2414 |
| Business density vs. crime records per 1,000 | Spearman | 0.3007 | 1.245e-51 | 2414 |

Interpretation: denser population areas tend to have greater business density. Population density has a moderate negative monotonic association with the crime rate used here, while business density has a positive but weaker association with that rate. These are associations, not causal effects.

### Global Moran's I

| Indicator | Moran's I | permutation p-value | n |
|---|---:|---:|---:|
| Crime records per 1,000 | 0.0250 | 0.0220 | 2414 |
| Business density | 0.4398 | 0.0010 | 2431 |

Interpretation: business density shows clear positive spatial clustering. Crime records per 1,000 show a much smaller positive spatial autocorrelation, although it is statistically significant under the permutation test.

### Local Moran / LISA

- Crime records per 1,000: **141** significant AGEB at alpha = 0.05.
- Business density: **170** significant AGEB at alpha = 0.05.
- One geographic island (`geography_id = 4081`) is reported rather than artificially connected.

The detailed AGEB-level classifications are in `tables/`.

### Bivariate Moran's I

Local business density versus the spatial lag of crime records per 1,000:

- Bivariate Moran's I = **0.0261**
- permutation p-value = **0.0470**
- n = **2414**

This is a small positive cross-variable spatial association and should not be interpreted as causal.

## Folder contents

- `figures/`: descriptive maps, correlation plots, Moran scatterplots, and LISA maps.
- `tables/`: AGEB-level LISA outputs.
- `summaries/`: complete JSON results for every Phase 3 module and the integrated summary.
- `input_manifest.json`: provenance and hashes of the Data Warehouse export.

## Caution

Spatial association and conventional correlation do not establish causation. Results depend on the selected geographic grain, Queen neighborhood definition, indicator definitions, and handling of undefined denominators.
