"""Download source-register URLs to data/raw; preserves original bytes and a manifest."""
from pathlib import Path
import hashlib, time
import pandas as pd
import requests
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data'/'raw'
HEADERS={'User-Agent':'MA-Synergy-Analyzer academic research contact@example.com'}
def main():
    df=pd.read_csv(ROOT/'data'/'source_register.csv')
    rows=[]
    for row in df.itertuples(index=False):
        folder=RAW/row.deal_id.lower(); folder.mkdir(parents=True,exist_ok=True)
        safe=''.join(ch if ch.isalnum() or ch in '-_' else '_' for ch in row.source_id)
        path=folder/(safe+'.source')
        try:
            r=requests.get(row.url,headers=HEADERS,timeout=45); r.raise_for_status()
            path.write_bytes(r.content)
            rows.append({'source_id':row.source_id,'url':row.url,'status':'downloaded','http_status':r.status_code,'sha256':hashlib.sha256(r.content).hexdigest(),'bytes':len(r.content)})
        except Exception as e:
            rows.append({'source_id':row.source_id,'url':row.url,'status':'failed','error':str(e)})
        time.sleep(0.25)
    pd.DataFrame(rows).to_csv(ROOT/'data'/'processed'/'download_manifest.csv',index=False)
    print('Wrote download manifest; review failed URLs and respect source terms/rate limits.')
if __name__=='__main__': main()
