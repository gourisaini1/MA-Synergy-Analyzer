"""Check source register and mark retrieval metadata without fabricating it."""
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=ROOT/'data'/'source_register.csv'; df=pd.read_csv(p)
    required={'deal_id','document','publisher','url','source_type'}
    if required-set(df.columns): raise ValueError(f'Missing: {required-set(df.columns)}')
    if df.url.isna().any() or not df.url.astype(str).str.startswith('https://').all(): raise ValueError('Every source must have HTTPS URL')
    if df.source_id.duplicated().any(): raise ValueError('source_id must be unique')
    df['retrieval_status']='not_downloaded'; df['retrieved_at']=''
    out=ROOT/'data'/'processed'/'source_register_status.csv'; out.parent.mkdir(exist_ok=True)
    df.to_csv(out,index=False); print(f'Validated {len(df)} sources')
if __name__=='__main__': main()
