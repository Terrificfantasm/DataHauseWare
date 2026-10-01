"""Restore exact documented sources; fail on upstream changes, never overwrite originals."""
import hashlib,json,urllib.request,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    manifest=json.loads((ROOT/'docs/cdmx_acquisition.json').read_text(encoding='utf-8'))
    manifest.append(json.loads((ROOT/'docs/cdmx_scian2018_acquisition.json').read_text(encoding='utf-8')))
    for entry in manifest:
        path=(ROOT/entry['path'].replace('\\','/')).resolve()
        if not path.is_relative_to(ROOT/'data/raw/cdmx'):raise ValueError('Unexpected source path')
        path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists():
            if digest(path)!=entry['sha256']:raise ValueError('Existing file hash mismatch: '+path.name)
            print('Verified',path.name);continue
        partial=path.with_suffix(path.suffix+'.part')
        with urllib.request.urlopen(entry['url'],timeout=120) as response,partial.open('wb') as output:
            while chunk:=response.read(1024*1024):output.write(chunk)
        if digest(partial)!=entry['sha256']:raise ValueError('Upstream changed; retained .part for review: '+path.name)
        if path.suffix=='.zip':
            with zipfile.ZipFile(partial) as archive:
                if archive.testzip() is not None:raise ValueError('ZIP corruption')
        partial.rename(path);print('Restored',path.name)
    for name in ['fgj_count_metadata.json','fgj_resource_metadata.json']:
        source=ROOT/'docs'/('cdmx_'+name);target=ROOT/'data/raw/cdmx'/name
        if target.exists() and target.read_bytes()!=source.read_bytes():raise ValueError('Metadata differs: '+name)
        if not target.exists():target.write_bytes(source.read_bytes())
if __name__=='__main__':main()
