"""Read official XLSX catalog and compare DENUE vintages without changing active inputs."""
import csv,io,json,hashlib,re,zipfile,posixpath,unicodedata
from datetime import datetime,timezone
from pathlib import Path
from xml.etree import ElementTree as ET
import geopandas as gpd
import pandas as pd
from assess_geography import ROOT,select_scope
from spatial import assign_points

NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

def catalog(path):
    with zipfile.ZipFile(path) as z:
        strings=[''.join(e.itertext()) for e in []]
        shared=ET.fromstring(z.read('xl/sharedStrings.xml'))
        strings=[''.join(t.text or '' for t in e.findall('.//s:t',NS)) for e in shared]
        wb=ET.fromstring(z.read('xl/workbook.xml'))
        sheet=next(s for s in wb.findall('s:sheets/s:sheet',NS) if s.attrib['name']=='CLASE')
        rid=sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']
        rel=next(e for e in ET.fromstring(z.read('xl/_rels/workbook.xml.rels')) if e.attrib['Id']==rid)
        target=rel.attrib['Target']
        member=target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/'+target)
        data=ET.fromstring(z.read(member))
        result={}
        for row in data.findall('s:sheetData/s:row',NS):
            values={}
            for cell in row.findall('s:c',NS):
                col=re.sub(r'\d','',cell.attrib['r'])
                if col not in ('A','B'):continue
                value=cell.find('s:v',NS)
                text=value.text if value is not None else ''
                if cell.attrib.get('t')=='s':text=strings[int(text)]
                elif cell.attrib.get('t')=='inlineStr':text=''.join(t.text or '' for t in cell.findall('.//s:t',NS))
                values[col]=text
            code=values.get('A','')
            if re.fullmatch(r'\d{6}',code):
                name=values.get('B','').strip()
                if code in result and result[code]!=name:raise ValueError('Conflicting catalog duplicate')
                result[code]=name
        if len(result)<1000:raise ValueError('Catalog unexpectedly small')
        return result

def read_source(path):
    with zipfile.ZipFile(path) as z:
        member=next(m for m in z.namelist() if 'conjunto_de_datos/' in m and m.endswith('.csv'))
        blob=z.read(member)
        for enc in ('utf-8-sig','cp1252','latin1'):
            try:text=blob.decode(enc);break
            except UnicodeDecodeError:pass
        # Latin-1 preserves every byte, including C1 controls. Report them, never replace silently.
        controls=sum(0x80<=ord(c)<=0x9f for c in text)
        df=pd.read_csv(io.StringIO(text),dtype=str,keep_default_na=False)
        return df,{'encoding':enc,'c1_control_characters':controls,'member':member}

def normalize(text):
    return ' '.join(unicodedata.normalize('NFC',text).casefold().split())

def main():
    cfg=json.loads((ROOT/'config/merida.json').read_text(encoding='utf-8'))
    catpath=ROOT/'data/raw/inegi_scian2023/scian_2023_categorias_y_productos.xlsx'
    cat=catalog(catpath)
    specs=[('2026-05','inegi_denue/denue_31_csv.zip'),
           ('2020-04_URL_EDITION_UNRESOLVED','inegi_denue_202004/denue_31_0420_csv.zip'),
           ('2020-11','inegi_denue_202011/denue_31_1120_csv.zip')]
    output=ROOT/'outputs/merida/source_comparison';output.mkdir(parents=True,exist_ok=True)
    areas=gpd.read_file('/vsizip/'+(ROOT/cfg['sources']['boundaries']).as_posix()+'/'+cfg['sources']['boundary_member'])
    areas=select_scope(areas,cfg,'CVE_ENT','CVE_MUN','CVE_LOC')
    result={'generated_utc':datetime.now(timezone.utc).isoformat(),'catalog_classes':len(cat),
            'catalog_sha256':hashlib.sha256(catpath.read_bytes()).hexdigest(),
            'geography_sha256':hashlib.sha256((ROOT/cfg['sources']['boundaries']).read_bytes()).hexdigest(),
            'vintages':[]}
    for label,rel in specs:
        path=ROOT/'data/raw'/rel;df,meta=read_source(path)
        state=df.loc[df.cve_ent.eq(cfg['state'])].copy()
        if state.id.duplicated().any():raise ValueError('Duplicate ID in '+label)
        if label=='2026-05':
            pairs=state.groupby(['codigo_act','nombre_act']).size().reset_index(name='records')
            pairs['catalog_title']=pairs.codigo_act.map(cat).fillna('')
            pairs['valid_code']=pairs.codigo_act.isin(cat)
            pairs['title_equal_normalized']=[normalize(a)==normalize(b) for a,b in zip(pairs.nombre_act,pairs.catalog_title)]
            pairs.to_csv(output/'scian_2023_class_check.csv',index=False)
            result['scian_validation']={'distinct_codes':int(state.codigo_act.nunique()),
              'unknown_codes':sorted(set(state.codigo_act)-set(cat)),
              'unknown_code_records':int((~state.codigo_act.isin(cat)).sum()),
              'title_mismatch_pairs':int((~pairs.title_equal_normalized).sum()),
              'title_mismatch_records':int(pairs.loc[~pairs.title_equal_normalized,'records'].sum())}
            print('SCIAN',result['scian_validation'],flush=True)
        assigned=assign_points(state,areas,'longitud','latitud')
        declared=assigned.index.isin(select_scope(assigned,cfg,'cve_ent','cve_mun','cve_loc').index)
        inside=assigned.assignment_status.eq('assigned')
        counts=assigned.loc[inside].groupby('CVEGEO').size()
        report={'edition':label,'file':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                'rows':len(df),'state_rows':len(state),'municipality_rows':int(state.cve_mun.isin(cfg['municipalities']).sum()),
                'declared_locality_rows':int(declared.sum()),'assigned':int(inside.sum()),
                'declared_locality_not_assigned':int((declared & ~inside).sum()),
                'assigned_other_codes':int((~declared & inside).sum()),
                'zero_business_ageb':int(areas.CVEGEO.map(counts).fillna(0).eq(0).sum()),
                'assignment_counts':{str(k):int(v) for k,v in assigned.assignment_status.value_counts().items()},
                'latest_alta_labels':sorted(df.fecha_alta.unique())[-5:],**meta}
        assert sum(report['assignment_counts'].values())==len(state)
        result['vintages'].append(report)
        print(label,json.dumps(report,ensure_ascii=False),flush=True)
    (output/'comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':main()
