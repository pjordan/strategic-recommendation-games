"""Collect product-specific landing-page evidence into a local cache.
Requires beautifulsoup4. Raw cache files are private and not publication artifacts.
"""
import argparse,base64,hashlib,json,re,time,urllib.parse,urllib.request
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
from pathlib import Path
from bs4 import BeautifulSoup

REPO=Path(__file__).resolve().parents[1]

def now():return datetime.now(timezone.utc).isoformat()
def write(path,data):path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
def clean_url(url):
    url=urllib.parse.urljoin('https://www.bing.com',url)
    p=urllib.parse.urlparse(url);q=urllib.parse.parse_qs(p.query)
    if p.hostname and p.hostname.endswith('bing.com') and p.path.startswith('/alink') and q.get('url'):
        return clean_url(q['url'][0])
    if p.hostname and p.hostname.endswith('bing.com') and p.path.startswith('/ck/') and q.get('u'):
        raw=q['u'][0]
        if raw.startswith('a1'):
            try:return clean_url(base64.urlsafe_b64decode(raw[2:]+'='*((-len(raw[2:]))%4)).decode())
            except Exception:return None
    if p.scheme not in ('http','https') or not p.hostname:return None
    keep={'goid','id','pid','sku','variant','product_id','item','itemid','color','size','model'}
    query=urllib.parse.urlencode([(k,v) for k,vs in q.items() if k.lower() in keep for v in vs])
    return urllib.parse.urlunparse((p.scheme,p.netloc,p.path,'',query,''))

def get(url,cache):
    key=hashlib.sha256(url.encode()).hexdigest()
    meta_path=cache/(key+'.meta.json');html_path=cache/(key+'.html')
    if meta_path.exists():return json.loads(meta_path.read_text()),html_path.read_text(errors='replace') if html_path.exists() else ''
    meta={'url':url,'retrieved_at':now(),'method':'HTTP GET'};body=''
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req,timeout=18) as response:
            raw=response.read(8000000);body=raw.decode('utf-8',errors='replace')
            meta.update(status='retrieved',http_status=response.status,final_url=clean_url(response.url),content_sha256=hashlib.sha256(raw).hexdigest())
            html_path.write_bytes(raw)
    except Exception as e:meta.update(status='unavailable',error_type=type(e).__name__)
    write(meta_path,meta);return meta,body

def collect_bing(record,cache,out):
    target=out/(record['record_id']+'.json')
    if target.exists():return json.loads(target.read_text())
    meta,body=get(record['provider_product_url'],cache);s=BeautifulSoup(body,'html.parser')
    title=s.select_one('.product-bullseye__title')
    selected=s.select_one('a[aria-label="oboSnOptLink"]')
    facts=[]
    for i,li in enumerate(s.select('#gpdp-ps li')):
        k=li.select_one('.collapse-label');v=li.select_one('.collapse-item')
        if k and v:
            key=k.get_text(' ',strip=True);value=v.get_text(' ',strip=True)
            if key and value:facts.append({'name':key,'value':value,'locator':f'#gpdp-ps li:nth-of-type({i+1})'})
    links=[]
    if selected and selected.get('href'):
        u=clean_url(selected['href'])
        if u:links.append({'url':u,'merchant_label':selected.get('title'),'role':'selected_merchant'})
    for a in s.select('a[href]'):
        u=clean_url(a['href'])
        if u and urllib.parse.urlparse(u).hostname not in ['www.bing.com','bing.com','go.microsoft.com','support.microsoft.com','account.microsoft.com'] and a.get('title') and a.get('title') not in ['Visit site']:
            if not any(x['url']==u for x in links):links.append({'url':u,'merchant_label':a.get('title'),'role':'alternative_merchant_unmatched'})
    result={'record_id':record['record_id'],'frozen_title':record['title'],'source':meta,
            'page_product_title':title.get_text(' ',strip=True) if title else None,
            'page_specifications':facts,'merchant_candidates':links[:30]}
    write(target,result);return result

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cache-dir',required=True);ap.add_argument('--workers',type=int,default=4)
    ap.add_argument('--stage',choices=['bing','all'],default='all')
    args=ap.parse_args();cache=Path(args.cache_dir);cache.mkdir(parents=True,exist_ok=True);out=cache/'bing-resolved';out.mkdir(exist_ok=True)
    records=json.loads((REPO/'scenarios/scenario-1/versions/1.3.0/recommendations/bing.json').read_text())['records']
    done=0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        fs=[pool.submit(collect_bing,r,cache,out) for r in records]
        for f in as_completed(fs):
            result=f.result();done+=1
            if done%20==0 or done==len(records):print(f'Bing landing pages processed: {done}/{len(records)}',flush=True)
    results=[json.loads(p.read_text()) for p in out.glob('*.json')]
    if args.stage=='all':
        plan=json.loads((REPO/'scenarios/scenario-1/product-facts/versions/1.0.0/collection/resolution-plan.json').read_text())
        write(cache/'page-jobs.json',plan['page_jobs']);write(cache/'identity-decisions.json',plan['identity_decisions'])
        pages=cache/'merchant-pages';pages.mkdir(exist_ok=True)
        urls=sorted({j['url'] for j in plan['page_jobs']})
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            fs=[pool.submit(get,u,pages) for u in urls]
            for i,f in enumerate(as_completed(fs),1):
                f.result()
                if i%20==0 or i==len(urls):print(f'Merchant pages processed: {i}/{len(urls)}',flush=True)
    print(json.dumps({'records':len(results),'with_specs':sum(bool(r['page_specifications']) for r in results),'with_merchant_url':sum(bool(r['merchant_candidates']) for r in results)}),flush=True)

if __name__=='__main__':main()
