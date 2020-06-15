from io import BytesIO
import logging
import requests
from tqdm.auto import tqdm
from zipfile import ZipFile
import pandas as pd
from pathlib import Path
import gzip
import numpy as np
from rebar import parallel
import ast

log = logging.getLogger(__name__)

def download(url):
    bs = BytesIO()
    log.info(f'Downloading {url}')
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        total = int(r.headers['Content-Length']) if 'Content-Length' in r.headers else None
        with tqdm(total=total, unit_scale=True, unit_divisor=1024, unit='B') as pbar:
            for chunk in r.iter_content(chunk_size=2**20): 
                pbar.update(len(chunk))
                bs.write(chunk)
    return bs.getvalue()

def cubicasa5k():
    p = Path('.cache/cubicasa.zip')
    if not p.exists():
        url = 'https://zenodo.org/record/2613548/files/cubicasa5k.zip?download=1'
        p.parent.mkdir(exist_ok=True, parents=True)
        p.write_bytes(download(url))
    return str(p)

def svgdata(regenerate=False):
    p = Path('.cache/cubicasa-svgs.json.gz')
    if not p.exists() or regenerate:
        p.parent.mkdir(exist_ok=True, parents=True)
        if regenerate:
            log.info('Regenerating SVG cache from cubicasa dataset. This will require a 5G download.')
            with ZipFile(cubicasa5k()) as zf:
                pattern = r'cubicasa5k/(?P<category>[^/]*)/(?P<id>\d+)/(?P<filename>[^.]*)\.svg'
                svgs = (pd.Series(zf.namelist(), name='path')
                            .to_frame()
                            .loc[lambda df: df.path.str.match(pattern)]
                            .reset_index(drop=True))
                svgs = pd.concat([svgs, svgs.path.str.extract(pattern)], axis=1)
                svgs['svg'] = svgs.path.apply(lambda p: zf.read(p).decode())
                compressed = gzip.compress(svgs.to_json().encode())
                p.write_bytes(compressed)
        else:
            #TODO: Shift this to Github 
            url = 'https://www.dropbox.com/s/iblduqobhqomz4g/cubicasa-svgs.json.gzip?raw=1'
            p.write_bytes(download(url))
    return pd.read_json(gzip.decompress(p.read_bytes()))

def flatten(tree):
    flat = {}
    for k, v in tree.items():
        if isinstance(v, dict):
            for kk, vv in flatten(v).items():
                flat[f'{k}/{kk}'] = vv
        else:
            flat[k] = v
    return flat

def unflatten(d):
    tree = {}
    for k, v in d.items():
        parts = k.split('/')
        node = tree
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        node[parts[-1]] = v
    return tree
        
def safe_geometry(id, svg):
    try: 
        # Hide the import since it uses a fair number of libraries not used elsewhere.
        from . import geometry
        return geometry.geometry(svg)
    except:
        # We'll lose ~8 SVGs to them not having any spaces
        log.info(f'Geometry generation failed on on #{id}')

def fastload(raw):
    """Most of the time when loading a numpy array is spent parsing the header, since
    it could have a giant mess of record types in it. But we know here that it doesn't!"""
    headerlen = np.frombuffer(raw[8:9], dtype=np.uint8)[0]
    header = ast.literal_eval(raw[10:10+headerlen].decode())
    return np.frombuffer(raw[10+headerlen:], dtype=header['descr']).reshape(header['shape'])

def geometrydata(regenerate=False):
    # Why .npz.gz? Because applying gzip manually manages x10 better compression than
    # np.savez_compressed. They use the same compression alg, so I assume the difference
    # is in the default compression setting.
    p = Path('.cache/cubicasa-geometry.npz.gz')
    if not p.exists() or regenerate:
        p.parent.mkdir(exist_ok=True, parents=True)
        if regenerate:
            log.info('Regenerating geometry cache from SVG cache.')
            with parallel.parallel(safe_geometry) as pool:
                gs = pool.wait({str(row.id): pool(row.id, row.svg) for _, row in svgdata().iterrows()})
            gs = flatten({k: v for k, v in gs.items() if v is not None})

            bs = BytesIO()
            np.savez(bs, **gs)
            p.write_bytes(gzip.compress(bs.getvalue()))
        else:
            #TODO: Shift this to Github 
            url = ''
            p.write_bytes(download(url))
    d = np.load(BytesIO(gzip.decompress(p.read_bytes())))
    flat = {n[:-4]: fastload(d.zip.read(n)) for n in d.zip.namelist()}
    return unflatten(flat)
