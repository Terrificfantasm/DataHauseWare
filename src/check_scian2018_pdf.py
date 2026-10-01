"""Run with a Python environment containing pypdf (bundled runtime)."""
import re, json, hashlib, csv, io, zipfile
from pathlib import Path
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'data/raw/cdmx/scian2018_estructura.pdf'
codes=set()
for page in PdfReader(p).pages:
    codes.update(re.findall(r"(?m)^\s*(\d{6})\s+",page.extract_text()))
if len(codes)<1000: raise ValueError('Unexpectedly small extracted catalog')
with zipfile.ZipFile(ROOT/'data/raw/cdmx/denue_09_1120_csv.zip') as z:
    member=next(n for n in z.namelist() if 'conjunto_de_datos/' in n and n.endswith('.csv'))
    rows=list(csv.DictReader(io.StringIO(z.read(member).decode('latin1'))))
unknown=sorted({r['codigo_act'] for r in rows}-codes)
report={'catalog_sha256':hashlib.sha256(p.read_bytes()).hexdigest(), 'catalog_extracted_classes':len(codes),
        'observed_distinct_classes':len({r['codigo_act'] for r in rows}), 'unknown_classes':unknown,
        'unknown_records':sum(r['codigo_act'] in unknown for r in rows),
        'scope':'Entire CDMX DENUE source', 'method':'Six digit codes at beginning of extracted lines; membership only, descriptions not compared'}
(ROOT/'outputs/cdmx/phase1/scian2018_check.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
