"""Build a frozen product-fact release from private HTTP/web caches.

Raw pages never enter the release. Only scoped, typed claims and provenance do.
Requires beautifulsoup4; review identity decisions before freezing a new release.
"""
import argparse, hashlib, json, re, unicodedata
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from product_facts_collect import clean_url

ROOT = Path(__file__).resolve().parents[1]

def read(p): return json.loads(p.read_text())
def write(p, v):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(v, indent=2, ensure_ascii=False) + '\n')
def sha(b): return hashlib.sha256(b).hexdigest()
def norm(s): return unicodedata.normalize('NFKC', str(s)).replace('\u2011','-').replace('\u2013','-').replace('\u2014','-')
def plain(s): return norm(BeautifulSoup(str(s),'html.parser').get_text(' ',strip=True))
def types(d):
    t=d.get('@type',[])
    return t if isinstance(t,list) else [t]
def primary_products(d, loc='$'):
    # Traverse only top-level JSON-LD graphs, never related products/reviews.
    if isinstance(d,list):
        for i,x in enumerate(d): yield from primary_products(x, f'{loc}[{i}]')
    elif isinstance(d,dict):
        if 'Product' in types(d): yield loc,d
        elif '@graph' in d: yield from primary_products(d['@graph'],loc+'.@graph')

STOP=set('espresso expresso machine machines coffee maker makers with and the of for in a an to automatic semi semiautomatic milk frother steam wand grinder builtin built integrated stainless steel bar home professional oz cup cups water tank removable color size at latte cappuccino cappuccinos lattes touch screen control i set piece inch inone allinone all series preset presets builtin froth frothing auto large baristas professionalgrade cold brew pressure bars fully one multi grade classic style drinks drink presets black white silver gray grey bluetooth fast use shot volume high power brewing professionalgrade builtin stainlesssteel adjustable double single bean beans cappuccino milkfrother espressoandcoffee machinewithgrinder steamwand conical burr system feature features'.split())
def tokens(s): return {t for t in re.findall(r'[a-z0-9]+',''.join(c for c in unicodedata.normalize('NFKD',norm(str(s).replace('™','').replace('®',''))) if not unicodedata.combining(c)).lower().replace("de'longhi",'delonghi').replace('de’longhi','delonghi')) if not t.isdigit() and not re.fullmatch(r'\d+bar',t)}-STOP
def identity(record, title, method):
    a=tokens(record['title']);b=tokens(title)
    score=len(a&b)/max(1,len(a))
    if not a:
        full_a=set(re.findall(r'[a-z0-9]+',norm(record['title']).lower()));full_b=set(re.findall(r'[a-z0-9]+',norm(title).lower()))
        score=len(full_a&full_b)/max(1,len(full_a))
    variants={'impress','plus','mini','maestro','opera','deluxe','supreme','next','evo','start','bambino','baristina','premier','pro','touch'}
    named={'breville','philips','ninja','delonghi','cowsar','gaomon','garvee','simzlife','loheer','casabrews','kismile','airmsen','chefman','gevi','vevor','bluebow','zulay','kenmore','hibrew','gemilai','amumu','hausmojo','euhomy','zafro','memoryfield','chaolink','kicctian','lifeimpree','boupower','towallmark','idealhouse','antarctic','havato','cusimax','justsmart','encalife','mooye','free'}
    mismatch=(a&variants)-(b&variants)
    extra=(b&variants)-(a&variants)
    brand_missing=(a&named)-(b&named)
    colors={'black','white','silver','gray','grey','blue','cream'}
    ca=a&colors;cb=b&colors
    reasons=[]
    if mismatch or (extra and (a&variants or 'breville' in a or 'ninja' in a)):reasons.append('Model or subtype differs from frozen title.')
    if brand_missing:reasons.append('Frozen brand not established by landing-page title.')
    if ca and cb and not ca&cb and not (ca|cb <= {'gray','grey','silver'}):reasons.append('Color differs from frozen title.')
    if ('refurbished' in a or 'restored' in a) != ('refurbished' in b or 'restored' in b):reasons.append('Condition differs or is unspecified between frozen listing and page.')
    if 'open' in b and 'box' in b and not ('open' in a and 'box' in a):reasons.append('Page is open-box; frozen condition does not establish that offer.')
    # Retained provider IDs establish URL lineage, not immunity to changed product identity.
    threshold=.52 if method.startswith('retained_bing') else .75
    if score<threshold:reasons.append('Insufficient title agreement for an exact listing match.')
    if not title or not re.search('espresso|coffee|barista|bambino|magnifica|baristina|oracle',title,re.I):reasons.append('No product-specific espresso-equipment identity established.')
    return {'status':'matched_listing' if not reasons else 'ambiguous','token_overlap':round(score,3),'reasons':reasons,'method':method,'page_title':title}

RULES=[
 ('grinding','integrated_grinder',True,r'\b(?:built[ -]?in|integrated|inbuilt) (?:coffee |conical |burr |ceramic |steel |adjustable )*grinder\b|\bwith (?:a |an )?(?:conical burr |burr |coffee )?grinder\b'),
 ('grinding','burr_type','conical',r'\bconical burr\b'),
 ('grinding','burr_material','ceramic',r'\bceramic (?:burr|grinder)\b'),
 ('milk','steam_wand_present',True,r'\bsteam(?:ing|er)? wand\b'),
 ('milk','manual_frothing_explicit',True,r'\bmanual (?:milk )?(?:froth\w*|steam\w*)|\bmanual (?:microfoam )?milk textur'),
 ('milk','automatic_frothing_explicit',True,r'\b(?:automatic|auto|hands[ -]free) (?:microfoam |milk |steam |froth\w* )*(?:froth\w*|textur\w*)|\bautofroth\b|\blattecrema\b|\blattego\b'),
 ('brewing','pid_temperature_control',True,r'\bPID\b'),
 ('brewing','cold_brew_mode',True,r'\bcold brew\b'),
 ('brewing','drip_coffee_mode',True,r'\bdrip coffee\b'),
 ('brewing','integrated_scale',True,r'\b(?:built[ -]in |integrated |precision )scale\b|\bweight[ -]based dosing\b'),
 ('brewing','dual_boiler_claim',True,r'\b(?:dual|double)[ -]boiler\b'),
 ('maintenance','self_cleaning_claim',True,r'\bself[ -]clean\w*|\bauto(?:matic)?[ -]clean\w*'),
 ('maintenance','removable_brew_unit',True,r'\b(?:removable|detachable) (?:brew(?:ing)? (?:unit|group)|brewer)\b'),
 ('maintenance','descaling_alert',True,r'\bdescal\w* (?:alert|reminder|indicator)\b'),
 ('physical','removable_water_tank',True,r'\bremovable (?:water )?(?:tank|reservoir)\b'),
]
NUMRULES=[
 ('grinding','grind_settings',r'\b(\d{1,3})[ -](?:step|setting|level|adjustable)(?:s| (?:burr |conical )?grinder)?\b|\b(\d{1,3}) (?:grind(?:ing)? (?:settings|levels)|adjustable (?:grind )?settings)\b',None),
 ('brewing','advertised_pressure_bar',r'\b(\d{1,2}(?:\.\d+)?)[ -]?bar\b','bar'),
 ('electrical','voltage',r'\b(1[012][05](?:[ -]+120)?|220[ -]+240|220|230|240)[ -]?(?:V\b|volts?\b)','V'),
 ('electrical','power',r'\b(\d{3,4})[ -]?(?:W\b|watts?\b)','W'),
 ('physical','water_tank_capacity',r'\b(\d(?:\.\d+)?)[ -]?(?:L\b|liters?\b|litres?\b)(?=.{0,30}(?:tank|reservoir))','L'),
 ('physical','water_tank_capacity',r'\b(\d{2,3}(?:\.\d+)?)[ -]?(?:fl\.? ?)?(?:oz|ounces?)\b(?=.{0,30}(?:tank|reservoir))','fl oz'),
 ('brewing','portafilter_diameter',r'\b(\d{2})[ -]?mm\s+(?:\w+\s+){0,3}(?:portafilter|filter basket)','mm'),
 ('brewing','heat_up_time',r'\b(\d{1,3})[ -]second(?:s)?\b(?=.{0,35}(?:heat|start|ready))','s'),
]

def extract_claims(segments, source_id):
    facts=[];seen=set()
    def add(group,name,value,loc,unit=None):
        key=(group,name,str(value),unit)
        if key in seen:return
        seen.add(key);v={'category':group,'name':name,'value':value,'evidence':[{'source_id':source_id,'locator':loc}]}
        if unit:v['unit']=unit
        facts.append(v)
    for text,loc in segments:
        text=norm(text)
        if text.startswith('SCALAR:'):
            data=json.loads(text[7:]);add(data['category'],data['name'],data['value'],loc,data.get('unit'));continue
        if text.lstrip().startswith('#'):continue
        if re.fullmatch(r'(?:Integrated (?:Coffee )?Grinder|Built.In Grinder|Automatic Milk Frother|Manual Milk Frother|Removable Water Tank)',text.strip(),re.I):continue
        if text.startswith('Integrated grinder explicit value:'):
            add('grinding','integrated_grinder',text.lower().endswith('yes'),loc);continue
        for cat,name,val,pat in RULES:
            if re.search(pat,text,re.I) and not (name=='integrated_grinder' and re.fullmatch(r'Integrated (?:Coffee )?Grinder',text.strip(),re.I)):add(cat,name,val,loc)
        for cat,name,pat,unit in NUMRULES:
            for m in re.finditer(pat,text,re.I):
                value=next(x for x in m.groups() if x is not None)
                if name=='grind_settings' and (int(value)<2 or not re.search(r'grind',text[max(0,m.start()-45):m.end()+45],re.I)):continue
                claim_name=name
                if name=='advertised_pressure_bar':
                    following=text[m.end():m.end()+35].lower()
                    if re.match(r'\s*(?:italian )?pump',following):claim_name='pump_pressure_bar'
                    elif re.match(r'\s*(?:espresso|extraction)',following):claim_name='extraction_pressure_bar'
                    elif re.match(r'\s*system',following):claim_name='system_pressure_bar'
                add(cat,claim_name,value,loc,unit)
        # Extract short, labeled dimensions and model IDs; never free-form marketing paragraphs.
        for name,pat in [('dimensions',r'(?:product dimensions|dimensions\s*\(.*?\))\s*[:：]?\s*([^\n]{5,95})'),('model',r'\bmodel(?: name| number| #)?\s*[:：#]\s*([a-z0-9][a-z0-9_-]{3,35})')]:
            m=re.search(pat,text,re.I)
            if m:
                value=m.group(1).strip()
                if name!='dimensions' or re.search(r'\d.*[x×].*\d',value):add('identity' if name=='model' else 'physical',name,value,loc)
        for m in re.finditer(r'(?:purchase includes|included components|included accessories|what.s (?:in the box|included)|accessories included)\s*[:：]?\s*([^\n]{3,400}(?:\n[^\n]{1,80}){0,10})',text,re.I):
            block=m.group(1)
            for label,pat in [('tamper','tamper'),('milk_pitcher','milk (?:jug|pitcher)|frothing pitcher'),('cleaning_brush','cleaning brush'),('single_shot_basket','single[ -](?:cup|shot).*?(?:basket|filter)'),('double_shot_basket','double[ -](?:cup|shot).*?(?:basket|filter)'),('portafilter','portafilter'),('dosing_funnel','dosing funnel|dosing ring')]:
                if re.search(pat,block,re.I):add('included_items',label,True,loc)
    return facts

def load_page(url,cache):
    key=sha(url.encode());sources=[]
    hp=cache/'merchant-pages'/f'{key}.html';mp=cache/'merchant-pages'/f'{key}.meta.json'
    if hp.exists():
        meta=read(mp);s=BeautifulSoup(hp.read_text(errors='replace'),'html.parser');products=[]
        for i,tag in enumerate(s.find_all('script',type='application/ld+json')):
            try:
                for loc,obj in primary_products(json.loads(tag.string or tag.get_text())):products.append((f'script[type="application/ld+json"] index {i}; {loc}',obj))
            except (ValueError,TypeError):pass
        # A single top-level Product is safe to scope. Multiple Product entries need identity matching later.
        if products:
            for loc,obj in products:
                title=plain(obj.get('name',''));segs=[(title,loc+'.name')]
                if obj.get('description'):segs.append((BeautifulSoup(str(obj['description']),'html.parser').get_text('\n',strip=True),loc+'.description'))
                # Shopify full product description is scoped to the primary product, excluding recommendations.
                if len(products)==1:
                    for sel in ['.product__description','.product-description.rte','[itemprop="description"]']:
                        e=s.select_one(sel)
                        if e:segs.append((e.get_text('\n',strip=True),sel));break
                sources.append({'title':title,'segments':segs,'object':obj,'object_locator':loc,'meta':meta,'representation':'raw_http_html'})
    for wp in [cache/'web-pages'/f'{key}.json',cache/'indexed-rendered'/f'{key}.json']:
        if not wp.exists():continue
        d=read(wp);raw=d['result'];lines=re.findall(r'L(\d+):\s*(.*?)(?=\s*L\d+:|\Z)',raw,re.S)
        lines=[(int(n),re.sub(r'cite.*?','',s).strip()) for n,s in lines]
        lines=sorted(dict(lines).items())
        title=raw.split('\n')[0].rsplit(' (http',1)[0]
        headings=[(n,s[2:]) for n,s in lines if s.startswith('# ')]
        if headings:title=headings[0][1]
        segments=[];host=urlparse(url).hostname or ''
        # Only dedicated product-detail sections. Review, comparison and recommendation sections end scope.
        starts={'bestbuy.com':r'^(?:#+ )?(?:Features|Specifications|Description|What.s Included|About this product)$',
                'walmart.com':r'^#+ (?:About this item|Product details|Specifications|Specs|Key item features)',
                'lowes.com':r'^## (?:Overview|Product Features|Specifications)',
                'target.com':r'^#+ (?:About this item|Highlights|Description|Specifications)',
                'homedepot.com':r'^#+ (?:About This Product|Product Information|Specifications|Product Details)',
                'wayfair.com':r'^#+ (?:About This Product|Description|Features|Specifications|Product Overview)'}
        start=next((v for k,v in starts.items() if host.endswith(k)),None)
        active=False;ended=False
        for n,line in lines:
            if re.search(r'^## (?:Compare|Related|You may|Similar)',line,re.I):ended=True
            if ended:continue
            if start and re.search(start,line,re.I):active=True
            if active and re.search(r'^(?:#+ )?(?:Sponsored|Add to cart|Customer |Ratings|Reviews|Questions|Community|COMPARE|Compare|Similar|Related|You may|Customers also|More to consider|Frequently bought|Recommended)',line,re.I):active=False
            if active and line and not line.startswith(('Image:','[Button','[Input','[Select')):segments.append((line,f'web text line {n}'))
        # Generic merchant product pages: primary heading -> first unrelated block. No header/footer material.
        if not start and headings:
            active=False
            for n,line in lines:
                if n==headings[0][0]:active=True
                elif active and re.search(r'^[* ]*(?:#+ )?(?:Shipping|Ratings|Related|You may|Customers also|Recently viewed|Customer reviews|Reviews|Recommendations|Join |Subscribe|Footer|Recommended|Contact us)',line,re.I):break
                if active and line and not line.startswith(('Image:','[Button','[Input','[Select')):segments.append((line,f'web text line {n}'))
        if segments and not re.search(r'Internal Error|Access Denied|Robot or human|Page Not Found|Just a moment',title,re.I):
            # Include title, but never treat the provider's old card as newly retrieved page evidence.
            # Scalar specification labels are not affirmative claims (e.g. Integrated Grinder: No).
            for ii,(n,line) in enumerate(lines):
                if re.fullmatch(r'Integrated (?:Coffee )?Grinder',line,re.I):
                    nxt=next(((nn,ss) for nn,ss in lines[ii+1:ii+5] if ss),None)
                    if nxt and nxt[1].lower() in ['yes','no'] and any(loc==f'web text line {n}' for _,loc in segments):
                        segments.append(('Integrated grinder explicit value: '+nxt[1],f'web text lines {n}-{nxt[0]}'))
            scalar_fields={
                'integrated grinder':('grinding','integrated_grinder',None),
                'automatic milk frother':('milk','automatic_frothing_explicit',None),
                'manual milk frother':('milk','manual_frothing_explicit',None),
                'removable water tank':('physical','removable_water_tank',None),
                'number of grind settings':('grinding','grind_settings',None),
                'bars of pressure':('brewing','advertised_pressure_bar','bar'),
                'pump pressure (bars)':('brewing','advertised_pressure_bar','bar'),
                'depth (inches)':('physical','depth','in'),
                'height (inches)':('physical','height','in'),
                'width (inches)':('physical','width','in'),
                'weight (lbs.)':('physical','weight','lb'),
                'water reservoir size (oz.)':('physical','water_tank_capacity','fl oz'),
                'bean container size (grams)':('grinding','bean_hopper_capacity','g'),
            }
            for ii,(n,line) in enumerate(lines):
                label=re.sub(r'^[#* ]+','',line).lower()
                if label not in scalar_fields or not any(loc==f'web text line {n}' for _,loc in segments):continue
                nxt=next(((nn,ss.strip(' |')) for nn,ss in lines[ii+1:ii+6] if ss.strip(' |') and ss.strip(' |')!='---'),None)
                if not nxt:continue
                value=nxt[1];cat,name,unit=scalar_fields[label]
                if value.lower() in ['yes','no']:value=value.lower()=='yes'
                elif not re.fullmatch(r'\d+(?:\.\d+)?',value):continue
                segments.append(('SCALAR:'+json.dumps({'category':cat,'name':name,'value':value,'unit':unit}),f'web text lines {n}-{nxt[0]}'))
            segments.insert(0,(title,'page title'))
            sources.append({'title':title,'segments':segments,'object':{},'object_locator':None,'meta':{'url':url,'retrieved_at':d['retrieved_at'],'method':d.get('method','web.open'),'status':'retrieved','content_sha256':sha(raw.encode()),**({'parent_response_sha256':d['parent_response_sha256']} if d.get('parent_response_sha256') else {})},'representation':d.get('representation','web_tool_text')})
    return sources

def build(cache,out):
    if (out/'manifest.json').exists():raise ValueError('Frozen release exists; build into a new directory/version.')
    base=ROOT/'scenarios/scenario-1';vr=base/'versions/1.3.0'
    records=[r for provider in ['bing','google'] for r in read(vr/f'recommendations/{provider}.json')['records']]
    plan=read(ROOT/'scenarios/scenario-1/product-facts/versions/1.0.0/collection/resolution-plan.json') if not (cache/'page-jobs.json').exists() else None
    jobs={j['record_id']:j for j in (read(cache/'page-jobs.json') if plan is None else plan['page_jobs'])};dec=read(cache/'identity-decisions.json') if plan is None else plan['identity_decisions'];source_map={};index=[]
    def save_source(meta,rep,title,kind):
        url=clean_url(meta['url'])
        host=urlparse(url).hostname or ''
        if kind=='merchant_or_manufacturer_product_page':
            makers=['breville.com','delonghi.com','espresso-works.com','gevi.com','vevor.com','gemilai.com','hibrew.com','encalife.com','garvee.com']
            kind='manufacturer_product_page' if any(host==m or host.endswith('.'+m) for m in makers) else 'merchant_product_page'
            if host.endswith('findthedeal.org'):kind='shopping_affiliate_product_page'
            if '/pages/help-' in url:kind='product_specific_manufacturer_guide'
        sid='src-'+sha((url+'|'+meta['content_sha256']).encode())[:24]
        source_map[sid]={'source_id':sid,'url':url,'retrieved_at':meta['retrieved_at'],'method':meta['method'],'representation':rep,'content_sha256':meta['content_sha256'],'hash_scope':'original response bytes' if rep=='raw_http_html' else 'UTF-8 cached web tool text; concatenated page-range responses when needed','source_kind':kind,'page_title':title}
        if rep=='indexed_product_document_text':source_map[sid]['hash_scope']='UTF-8 numbered primary document representation extracted from a search-tool response'
        if meta.get('parent_response_sha256'):source_map[sid]['parent_response_sha256']=meta['parent_response_sha256']
        return sid
    for record in records:
        rid=record['record_id'];facts=[];attempts=[];res={'status':'unresolved','method':'title_and_merchant_search','reasons':[]};offer=[];conflicts=[]
        discovery=cache/'google-search-v2'/f'{rid}.json'
        if discovery.exists():
            search=read(discovery);attempts.append({'method':'web.search title and merchant domain','query':search['query'],'domain_filter':search.get('domain_filter'),'retrieved_at':search['retrieved_at'],'candidate_count':len(search['candidates']),'status':'URL discovery only; no search snippet treated as a fact'})
        j=jobs.get(rid)
        if j:
            url=j['url'];key=sha(url.encode())
            for folder,ext in [('merchant-pages','.meta.json'),('web-pages','.json'),('indexed-rendered','.json')]:
                p=cache/folder/(key+ext)
                if p.exists():
                    d=read(p);a={'url':clean_url(url),'method':d.get('method','web.open'),'retrieved_at':d['retrieved_at']}
                    if folder=='merchant-pages':a.update({k:d[k] for k in ['status','http_status','error_type'] if k in d})
                    else:a['status']='page_text_returned' if 'Total lines:' in d['result'] and 'Internal Error' not in d['result'] else 'unavailable'
                    attempts.append(a)
            pages=load_page(url,cache)
            ranked=[]
            for page in pages:
                identity_title=page['title']
                host=urlparse(url).hostname or ''
                brand=next((b for b in ['breville','delonghi','gemilai','encalife','hibrew'] if host.endswith(b+'.com')),None)
                if brand:identity_title+=' '+brand
                objbrand=page['object'].get('brand')
                if isinstance(objbrand,dict):identity_title+=' '+str(objbrand.get('name',''))
                match=identity(record,identity_title,j['method']);match['page_title']=page['title']
                review=dec.get(rid,{})
                if review.get('decision')=='matched_after_review' and clean_url(url)==review.get('url') and page['title']==review.get('expected_page_title'):
                    match['status']='matched_listing';match['reasons']=[];match['review_note']=review['note']
                ranked.append((match,page))
            matched=[(m,p) for m,p in ranked if m['status']=='matched_listing']
            if matched:
                # JSON-LD first, visible product sections as supplemental evidence.
                res=matched[0][0];res['product_url']=clean_url(url);res['note']=j.get('identity_note','Matched using product title and retained URL lineage or merchant-scoped search; not independently verified SKU identity.')
                for m,p in matched:
                    sid=save_source(p['meta'],p['representation'],p['title'],'merchant_or_manufacturer_product_page')
                    facts.extend(extract_claims(p['segments'],sid))
                    obj=p['object'];loc=p['object_locator']
                    for field in ['model','sku','mpn','gtin','gtin12','gtin13','color','material','weight','height','width','depth']:
                        val=obj.get(field)
                        if val is not None and not isinstance(val,(dict,list)) and len(str(val))<120:
                            facts.append({'category':'identity' if field in ['model','sku','mpn','gtin','gtin12','gtin13'] else 'physical','name':field,'value':val,'evidence':[{'source_id':sid,'locator':loc+'.'+field}]})
                    os=obj.get('offers',[]);os=os if isinstance(os,list) else [os]
                    for oi,o in enumerate(os):
                        if not isinstance(o,dict):continue
                        obs={k:o[k] for k in ['price','priceCurrency','availability','itemCondition','sku'] if k in o and not isinstance(o[k],(list,dict))}
                        if isinstance(o.get('seller'),dict) and o['seller'].get('name'):obs['seller']=o['seller']['name']
                        # Variant prices remain observations, not substituted frozen prices.
                        if obs:offer.append({'observations':obs,'scope':'landing-page offer; may differ from original frozen seller/variant','source_id':sid,'locator':loc+f'.offers[{oi}]'})
                if not facts:res['status']='matched_page_without_extracted_specs'
            elif ranked:
                res=ranked[0][0];res['candidate_url']=clean_url(url)
            else:res={'status':'unavailable','method':j['method'],'candidate_url':clean_url(url),'reasons':['Product page could not be retrieved with usable, scoped product details.']}
        elif rid in dec:res['reasons']=[dec[rid]['note']]
        else:res['reasons']=['Search did not establish an unambiguous product landing-page URL.']
        # Bing provider PDP specifications are a separately labeled fallback, never manufacturer verification.
        if record['provider']=='bing':
            d=read(cache/'bing-resolved'/f'{rid}.json');meta=d['source']
            attempts.insert(0,{k:meta[k] for k in ['url','retrieved_at','method','status','http_status','error_type'] if k in meta})
            match=identity(record,d.get('page_product_title') or '', 'retained_bing_product_id')
            if meta['status']=='retrieved' and match['status']=='matched_listing' and d['page_specifications']:
                sid=save_source(meta,'raw_http_html',d['page_product_title'],'shopping_provider_product_page')
                for spec in d['page_specifications']:
                    facts.append({'category':'provider_specification','name':spec['name'],'value':spec['value'],'evidence':[{'source_id':sid,'locator':spec['locator']}]})
                if res['status']!='matched_listing':
                    res['merchant_resolution']=dict(res);res['status']='provider_page_only';res['product_url']=meta['url'];res['note']='Only shopping-provider product-page specifications are established; merchant match or access remains unresolved.'
        # Consolidate same claim and preserve competing values rather than arbitrating them.
        unique={}
        for f in facts:
            k=json.dumps({x:f[x] for x in ['category','name','value','unit'] if x in f},sort_keys=True)
            if k in unique:unique[k]['evidence'].extend(e for e in f['evidence'] if e not in unique[k]['evidence'])
            else:unique[k]=f
        facts=list(unique.values())
        milk={f['name'] for f in facts if f['category']=='milk' and f['value'] is True}
        if {'manual_frothing_explicit','automatic_frothing_explicit'}<=milk:conflicts.append({'topic':'milk_system','note':'Source text describes both manual and automatic frothing. This may indicate dual capability or inconsistent copy; automatic operation is not resolved by these claims alone.'})
        fields={}
        for f in facts:fields.setdefault((f['category'],f['name'],f.get('unit')),set()).add(str(f['value']))
        for (cat,name,unit),values in fields.items():
            if len(values)>1 and cat not in ['identity','provider_specification'] and name not in ['dimensions','advertised_pressure_bar']:conflicts.append({'topic':cat+'.'+name,'note':'Multiple values appear in the scoped evidence; they may describe different operating settings, variants, or inconsistent copy.','values':sorted(values),'unit':unit})
        categories={f['category'] for f in facts}
        missing=[x for x in ['electrical','included_items','maintenance','physical','milk','grinding'] if x not in categories]
        for attempt in attempts:
            if 'aliexpress.com' in str(attempt.get('url','')) and 's.click.' in str(attempt.get('url','')):
                attempt.pop('url',None);attempt['note']='Unresolved affiliate redirect; canonical product URL not established.'
        if 's.click.aliexpress.com' in str(res.get('candidate_url','')):
            res.pop('candidate_url',None);res['reasons']=['Unresolved affiliate redirect; canonical product URL not established.']
        product={'schema_version':'1.0.0','facts_version':'1.0.0','scenario_version':'1.3.0','record_id':rid,'provider':record['provider'],'frozen_record_sha256':record['record_sha256'],'frozen_title':record['title'],'resolution':res,'facts':facts,'offer_observations':offer,'conflicts':conflicts,'not_established_categories':missing,'attempts':attempts,'limits':['Page-supported claims, not independent physical testing.','Missing facts mean unknown, not absent.','Frozen price and merchant text remain in the recommendation record; current observations do not replace them.']}
        write(out/'products'/f'{rid}.json',product)
        index.append({'record_id':rid,'file':f'products/{rid}.json','status':res['status'],'fact_count':len(facts),'conflict_count':len(conflicts)})
    for sid,s in source_map.items():write(out/'sources'/f'{sid}.json',s)
    counts=Counter(x['status'] for x in index)
    write(out/'index.json',{'schema_version':'1.0.0','facts_version':'1.0.0','scenario_version':'1.3.0','record_count':len(index),'source_count':len(source_map),'coverage':dict(counts),'products':index})
    print(json.dumps({'coverage':dict(counts),'sources':len(source_map),'facts':sum(i['fact_count'] for i in index)},indent=2))

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cache-dir',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();build(args.cache_dir,args.output)
if __name__=='__main__':main()
