"""Download ACRA's register of companies from data.gov.sg and keep only moving companies.

    .venv\\Scripts\\python tools\\fetch_acra_movers.py        (Windows)
    .venv/bin/python tools/fetch_acra_movers.py              (macOS / Linux)

ACRA "Information on Corporate Entities" (data.gov.sg collection 2) is split into many CSV files.
This script downloads each one in turn, keeps the rows whose primary or secondary SSIC code is
49232 "Moving services" (house and office removals), and writes them to
data/processed/acra_movers.csv (small, a few thousand rows). The full files are not kept.
Takes a few minutes; data.gov.sg limits how fast files can be requested, so it waits between them.
"""
import io, sys, time
from pathlib import Path
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'data' / 'processed' / 'acra_movers.csv'
SSIC = '49232'
META = 'https://api-production.data.gov.sg/v2/public/api/collections/{}/metadata'
DMETA = 'https://api-production.data.gov.sg/v2/public/api/datasets/{}/metadata'
INIT = 'https://api-open.data.gov.sg/v1/public/api/datasets/{}/initiate-download'
POLL = 'https://api-open.data.gov.sg/v1/public/api/datasets/{}/poll-download'
S = requests.Session(); S.headers['User-Agent'] = 'MoveWell-SCA-coursework'


def get(url, tries=8):
    """GET with patience for data.gov.sg's rate limit (HTTP 429)."""
    for k in range(tries):
        r = S.get(url, timeout=120)
        if r.status_code == 429:
            time.sleep(5 * (k + 1)); continue
        r.raise_for_status(); return r
    raise RuntimeError(f'gave up after {tries} tries: {url}')


def csv_url(did):
    get(INIT.format(did))
    for _ in range(60):
        d = get(POLL.format(did)).json().get('data', {})
        if d.get('url'): return d['url']
        time.sleep(3)
    raise RuntimeError(f'no download link for {did}')


def main():
    meta = get(META.format(2)).json()['data']['collectionMetadata']
    kids = meta['childDatasets']
    print(f"{meta.get('name', 'ACRA')}: {len(kids)} files")
    keep = []
    for i, did in enumerate(kids, 1):
        name = get(DMETA.format(did)).json().get('data', {}).get('name', did)
        raw = get(csv_url(did)).content
        df = pd.read_csv(io.BytesIO(raw), dtype=str, low_memory=False)
        cols = [c for c in df.columns if 'ssic_code' in c.lower()]
        hit = df[df[cols].apply(lambda s: s.str.strip().eq(SSIC)).any(axis=1)] if cols else df.iloc[0:0]
        keep.append(hit)
        print(f'  {i:>2}/{len(kids)} {name}: {len(df):,} entities, {len(hit):,} movers')
        time.sleep(2)
    out = pd.concat(keep, ignore_index=True).drop_duplicates()
    OUT.parent.mkdir(parents=True, exist_ok=True); out.to_csv(OUT, index=False)
    print(f'\nwrote {OUT.relative_to(ROOT)}: {len(out):,} moving companies (SSIC {SSIC}, primary or secondary)')


if __name__ == '__main__':
    try: main()
    except requests.RequestException as e:
        print('download failed:', e); sys.exit(1)
