"""Download public INEGI sources, preserving existing originals. Python standard library only."""
from pathlib import Path
import urllib.request,hashlib,json,datetime,zipfile,io,csv
ROOT=Path(__file__).resolve().parents[1]
SOURCES=[('inegi_denue','denue_31_csv.zip','https://www.inegi.org.mx/contenidos/masiva/denue/denue_31_csv.zip'),('inegi_marco2020','31_yucatan.zip','https://www.inegi.org.mx/contenidos/productos/prod_serv/contenidos/espanol/bvinegi/productos/geografia/marcogeo/889463807469/31_yucatan.zip')]
def main():
 records=[]
 for folder,name,url in SOURCES:
  p=ROOT/'data'/'raw'/folder/name
  p.parent.mkdir(parents=True,exist_ok=True)
  cached=p.exists()
  if cached:data=p.read_bytes()
  else:
   with urllib.request.urlopen(url,timeout=90) as response:data=response.read()
  if not zipfile.is_zipfile(io.BytesIO(data)):raise ValueError('Response is not a ZIP: '+url)
  with zipfile.ZipFile(io.BytesIO(data)) as z:
   bad=z.testzip()
   if bad:raise ValueError('Corrupt ZIP member: '+bad)
   names=z.namelist()
   record={'file':p.relative_to(ROOT).as_posix(),'url':url,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reused_local':cached,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'members':names}
   if folder=='inegi_denue':
    for member in names:
     if member.lower().endswith('.csv') and 'conjunto_de_datos' in member.lower():
      blob=z.read(member)
      try:text=blob.decode('utf-8-sig');encoding='utf-8-sig'
      except UnicodeDecodeError:text=blob.decode('cp1252');encoding='cp1252'
      reader=csv.DictReader(io.StringIO(text)); rows=list(reader)
      municipality=[r for r in rows if r.get('cve_mun','').zfill(3)=='050']
      record['profile']={'encoding':encoding,'rows':len(rows),'columns':reader.fieldnames,'merida_municipality_rows':len(municipality),'date_field_values':sorted({r.get('fecha_alta','') for r in rows})[:30]}
   if not cached:p.write_bytes(data)
   print(name,len(data),'bytes',len(names),'ZIP entries',record.get('profile',{}),flush=True)
   records.append(record)
 out=ROOT/'docs'/'inegi_additional_acquisition.json'
 if not out.exists():out.write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
 else:print('Existing acquisition manifest preserved.')
if __name__=='__main__':main()
