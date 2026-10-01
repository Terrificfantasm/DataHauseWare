"""Profile required KPI inputs, preserving censored values; no final KPI computation."""
import argparse, hashlib, json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
from assess_geography import ROOT, read_csv_zip, select_scope

FIELDS = ['POBTOT','P_0A2','P_3A5','P_6A11','P_12A14','P_15A17','P_18A24',
          'P_18YMAS','P_60YMAS','P_12YMAS','PEA','PE_INAC','VIVTOT','TVIVHAB',
          'VIVPAR_HAB','VIVPARH_CV','VPH_INTER']

def profile(values):
    raw = values.str.strip()
    numeric = pd.to_numeric(raw, errors='coerce')
    return {'rows': len(raw), 'numeric': int(numeric.notna().sum()),
            'non_numeric_tokens': {str(k): int(v) for k,v in raw[numeric.isna()].value_counts(dropna=False).items()},
            'zero': int(numeric.eq(0).sum()), 'negative': int(numeric.lt(0).sum()),
            'non_integer': int((numeric.notna() & numeric.mod(1).ne(0)).sum())}

def run(path):
    cfg = json.loads(path.read_text(encoding='utf-8'))
    if not cfg.get('enabled'): raise ValueError('Disabled configuration')
    out = ROOT/'outputs'/cfg['id']/'phase1'
    baseline = json.loads((out/'quality_report.json').read_text(encoding='utf-8'))
    if baseline['territory'] != cfg: raise ValueError('Changed configuration')
    for k in ['census','boundaries','businesses']:
        if hashlib.sha256((ROOT/cfg['sources'][k]).read_bytes()).hexdigest() != baseline['sha256'][k]:
            raise ValueError('Changed source: '+k)
    census = read_csv_zip(ROOT/cfg['sources']['census'])
    scope = select_scope(census,cfg,'ENTIDAD','MUN','LOC')
    ageb = scope.loc[scope.MZA.eq('000') & scope.AGEB.ne('0000')].copy()
    ageb['CVEGEO'] = ageb.ENTIDAD+ageb.MUN+ageb.LOC+ageb.AGEB
    if ageb.CVEGEO.duplicated().any():raise ValueError('Duplicate geography')
    excluded = sorted(set(ageb.CVEGEO) - set(pd.read_csv(out/'area_diagnostics.csv', dtype={'CVEGEO':str}).CVEGEO))
    if excluded != sorted(cfg.get('acknowledged_census_without_polygon', [])):
        raise ValueError('Unexpected census coverage difference')
    ageb = ageb.loc[~ageb.CVEGEO.isin(excluded)].copy()
    profiles = {field: profile(ageb[field]) for field in FIELDS}
    n = ageb[FIELDS].apply(pd.to_numeric,errors='coerce')
    partial_age_columns=['P_0A2','P_3A5','P_6A11','P_12A14','P_15A17','P_18YMAS']
    age_sum=n[partial_age_columns].sum(axis=1,min_count=len(partial_age_columns))
    age_residual=n.POBTOT-age_sum
    active_residual=n.P_12YMAS-n[['PEA','PE_INAC']].sum(axis=1,min_count=2)
    derived_25_59=n.P_18YMAS-n.P_18A24-n.P_60YMAS
    checks = {
      'pea_greater_than_population_12plus':int(n.PEA.gt(n.P_12YMAS).sum()),
      'age_partition_not_evaluable':int(age_residual.isna().sum()),
      'age_partition_negative_residual':int(age_residual.lt(0).sum()),
      'age_partition_positive_residual':int(age_residual.gt(0).sum()),
      'age_partition_residual_total_known_rows':float(age_residual.sum()),
      'derived_25_59_missing':int(derived_25_59.isna().sum()),
      'derived_25_59_negative':int(derived_25_59.lt(0).sum()),
      'economic_condition_unknown_residual_rows':int(active_residual.gt(0).sum()),
      'economic_condition_negative_residual_rows':int(active_residual.lt(0).sum()),
      'economic_condition_residual_total_known_rows':float(active_residual.sum())}
    assignment=pd.read_csv(out/'business_assignment.csv',dtype=str,keep_default_na=False)
    selected=assignment.loc[assignment.assignment_status.eq('assigned'),['id','CVEGEO']]
    source=read_csv_zip(ROOT/cfg['sources']['businesses'],cfg.get('business_encoding'))
    businesses=selected.merge(source[['id','codigo_act','per_ocu']],on='id',validate='one_to_one')
    code=businesses.codigo_act.str.strip()
    sector=code.str[:2].replace({'31':'31-33','32':'31-33','33':'31-33','48':'48-49','49':'48-49'})
    counts=businesses.groupby('CVEGEO').size()
    areas=pd.read_csv(out/'area_diagnostics.csv',dtype={'CVEGEO':str}).set_index('CVEGEO')
    if set(areas.index)!=set(ageb.CVEGEO):raise ValueError('Area diagnostic key mismatch')
    businesses['sector']=sector
    sector_counts=businesses.groupby(['CVEGEO','sector']).size()
    maxima=sector_counts.groupby(level=0).transform('max')
    ties=sector_counts[sector_counts.eq(maxima)].groupby(level=0).size()
    result={'generated_utc':datetime.now(timezone.utc).isoformat(),'source_sha256':baseline['sha256'],
      'excluded_census_keys':excluded,'config':cfg,'census_fields':profiles,'consistency_checks':checks,
      'denominators':{'zero_population_ageb':int(n.POBTOT.eq(0).sum()),
                      'zero_population_12plus_ageb':int(n.P_12YMAS.eq(0).sum()),
                      'area_missing_or_nonpositive':int((areas.area_km2.isna()|areas.area_km2.le(0)).sum()),
                      'zero_assigned_business_ageb':int(ageb.CVEGEO.map(counts).fillna(0).eq(0).sum())},
      'business_inputs':{'rows':len(businesses),'invalid_six_digit_activity_code':int((~code.str.fullmatch(r'\d{6}')).sum()),
                         'sector_counts':{str(k):int(v) for k,v in sector.value_counts().sort_index().items()},
                         'size_categories':{str(k):int(v) for k,v in businesses.per_ocu.str.strip().value_counts().items()},
                         'ageb_with_dominant_sector_ties':int(ties.gt(1).sum())},
      'limitations':['Census symbols remain missing, never zero.','No final warehouse KPIs computed.',
                     'DENUE dictionary mentions SCIAN 2018; actual edition requires verification against release methodology.']}
    (out/'kpi_input_profile.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',type=Path,default=ROOT/'config/merida.json')
    run(parser.parse_args().config.resolve())
