"""Scope search-tool responses to the exact requested product URL, in a private cache.

Never use an unrelated search hit as the product's facts. Cached inputs contain
url, retrieved_at and result (the search tool's plain-text response).
"""
import argparse,hashlib,json,re
from pathlib import Path
from urllib.parse import urlparse,unquote
from product_facts_collect import clean_url

def same_product(a,b):
    a=urlparse(clean_url(a) or '');b=urlparse(clean_url(b) or '')
    if a.hostname!=b.hostname:return False
    if unquote(a.path).rstrip('/')==unquote(b.path).rstrip('/') and a.query==b.query:return True
    if a.hostname and a.hostname.endswith('walmart.com'):
        x=re.search(r'/ip/(?:[^/]+/)?(\d+)$',a.path);y=re.search(r'/ip/(?:[^/]+/)?(\d+)$',b.path)
        return bool(x and y and x[1]==y[1])
    if a.hostname and a.hostname.endswith('target.com'):
        x=re.search(r'/A-(\d+)$',a.path);y=re.search(r'/A-(\d+)$',b.path)
        return bool(x and y and x[1]==y[1])
    if a.hostname and a.hostname.endswith('alibaba.com'):
        x=re.search(r'(\d{10,})\.html$',a.path);y=re.search(r'(\d{10,})\.html$',b.path)
        return bool(x and y and x[1]==y[1])
    if a.hostname and a.hostname.endswith('ebay.com'):
        x=re.search(r'/itm/(?:[^/]+/)?(\d+)$',a.path);y=re.search(r'/itm/(?:[^/]+/)?(\d+)$',b.path)
        return bool(x and y and x[1]==y[1])
    if a.hostname and a.hostname.endswith('wayfair.com'):
        x=re.search(r'-([a-z]{4}\d+|w\d+)\.html?/?$',a.path);y=re.search(r'-([a-z]{4}\d+|w\d+)\.html?/?$',b.path)
        return bool(x and y and x[1]==y[1])
    if '/products/' in a.path and '/products/' in b.path and a.query==b.query:
        return a.path.split('/products/',1)[1].rstrip('/')==b.path.split('/products/',1)[1].rstrip('/')
    return False

def convert(cache):
    out=cache/'indexed-rendered';out.mkdir(exist_ok=True);count=0
    for p in list((cache/'indexed-pages').glob('*.json'))+list((cache/'indexed-title-retry').glob('*.json')):
        d=json.loads(p.read_text());blocks=re.split(r'\n-{10,}\n',d['result']);matched=[]
        for block in blocks:
            m=re.match(r'([^\n]+) \((https?://[^\s]+)\)',block)
            if m and same_product(d['url'],m[2]):matched.append((len(block),m,block))
        if not matched:continue
        _,m,block=max(matched,key=lambda x:x[0]);lines=block.splitlines()[2:]
        # Number the extracted document text, not surrounding search results.
        result=m[1]+' ('+m[2]+')\nTotal lines: '+str(len(lines))+'\n'+'\n'.join(f'L{i}: {line}' for i,line in enumerate(lines))
        v={'url':d['url'],'retrieved_at':d['retrieved_at'],'method':'web.search matched-URL product document','representation':'indexed_product_document_text','parent_response_sha256':hashlib.sha256(d['result'].encode()).hexdigest(),'result':result}
        existing=out/p.name
        if existing.exists() and len(json.loads(existing.read_text())['result'])>=len(result):continue
        existing.write_text(json.dumps(v,indent=2));count+=1
    print('Exact-URL indexed product documents:',count)
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cache-dir',type=Path,required=True);convert(ap.parse_args().cache_dir)
