"""Standard-library only collector. Writes validated snapshots atomically."""
from __future__ import annotations
import argparse, copy, hashlib, json, re, sys, time, os
from localize import KoreanLocalizer
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {'primary': 'https://raw.githubusercontent.com/zhenga8533/leak-duck/data/events.json', 'secondary': 'https://raw.githubusercontent.com/bigfoott/ScrapedDuck/data/events.json'}
KST = timezone(timedelta(hours=9))
CATEGORIES = {'Raid Battles':'레이드','Raid Hour':'레이드 아워','Raid Day':'레이드 데이','Max Battles':'맥스배틀','Max Mondays':'맥스 먼데이','Pokémon Spotlight Hour':'스포트라이트 아워','Community Day':'커뮤니티 데이','GO Battle League':'GO배틀리그','Event':'이벤트','Season':'시즌','Research':'리서치','Wild Area':'와일드 에리어','City Safari':'시티 사파리','GO Pass':'GO패스','Twitch Drops':'트위치 드롭스','Pokémon GO Tour':'GO 투어'}
NAMES = {'Mega Charizard X':'메가리자몽 X','Mega Charizard Y':'메가리자몽 Y','Charizard':'리자몽','Palkia':'펄기아','Giratina (Origin Forme)':'기라티나 오리진폼','Giratina (Altered Forme)':'기라티나 어나더폼','Shadow Landorus (Incarnate Forme)':'그림자 랜드로스 화신폼','Shadow Tornadus (Incarnate Forme)':'그림자 토네로스 화신폼','Cresselia':'크레세리아','Darkrai':'다크라이','Mega Metagross':'메가메타그로스','Mega Banette':'메가다크펫','Mega Sableye':'메가깜까미','Sableye':'깜까미','Uxie':'유크시','Mesprit':'엠라이트','Azelf':'아그놈','Pawniard':'자망칼','Gastly':'고오스','Morelull':'자마슈','Noibat':'음뱃','Chandelure':'샹델라','Machop':'알통몬','Espurr':'냐스퍼','Cryogonal':'프리지오','Minior':'메테노'}

def now_iso(): return datetime.now(timezone.utc).isoformat()
def read(path, default):
    try: return json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError): return default
def atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(path)
def fetch(url):
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers={'User-Agent':'GO-CAL/1.0 (personal event calendar)'}), timeout=30) as r:
                return json.load(r)
        except Exception:
            if attempt == 2: raise
            time.sleep(2 ** attempt)
def translate(text):
    result = text
    for en, ko in sorted(NAMES.items(), key=lambda x:-len(x[0])): result = result.replace(en, ko)
    for en, ko in [('Pokémon GO Halloween','포켓몬 GO 핼러윈'),('Part II','파트 2'),('Part I','파트 1'),('Spotlight Hour','스포트라이트 아워'),('Community Day','커뮤니티 데이'),('Raid Hour','레이드 아워'),('Super Mega Raid Day','슈퍼 메가 레이드 데이'),('in 5-star Raid Battles','전설 레이드'),('in Mega Raids','메가 레이드'),('in Shadow Raids','그림자 레이드'),('during Max Monday','맥스 먼데이'),('Dynamax','다이맥스'),('Max Battle Day','맥스배틀 데이'),('GO Pass: October','GO패스: 10월'),('GO Pass: November','GO패스: 11월'),('Twilight Trails','황혼의 여정')]: result=result.replace(en,ko)
    return result
def canonical(url): return str(url or '').split('?')[0].rstrip('/')
def parse_time(value, mode):
    if value is None or value == '': return None
    try:
        if isinstance(value,(int,float)):
            return datetime.fromtimestamp(value,timezone.utc).isoformat() if mode=='absolute' else None
        d=datetime.fromisoformat(str(value).replace('Z','+00:00'))
        if d.tzinfo: return d.astimezone(timezone.utc).isoformat()
        if mode=='local': return d.replace(tzinfo=KST).isoformat()
        return None
    except (ValueError,TypeError,OverflowError,OSError): return None
def flatten_primary(data):
    if not isinstance(data,dict) or not data: raise ValueError('primary schema: nonempty category object required')
    rows=[]
    for cat, items in data.items():
        if not isinstance(items,list): raise ValueError('primary category must be list')
        for item in items:
            if not isinstance(item,dict): raise ValueError('primary event must be object')
            rows.append(dict(item,category=item.get('category',cat)))
    return rows
def pokemon_from(details):
    result={}
    def walk(value):
        if isinstance(value,list):
            for v in value: walk(v)
        elif isinstance(value,dict):
            if value.get('name') and (value.get('asset_url') or value.get('image')):
                name=value['name']; image=value.get('asset_url',value.get('image'))
                if '_shiny' not in str(image): result[name]={'name':name,'nameKo':NAMES.get(name,name),'image':image,'shiny':value.get('shiny_available',value.get('canBeShiny'))}
            for v in value.values():
                if isinstance(v,(list,dict)): walk(v)
    walk(details)
    return list(result.values())
def normalize(row, source):
    primary=source=='primary'
    title=row.get('title' if primary else 'name')
    url=canonical(row.get('article_url' if primary else 'link'))
    if not isinstance(title,str) or not title.strip() or not url.startswith('https://leekduck.com/events/'): raise ValueError('invalid event name or source URL')
    category=row.get('category' if primary else 'heading','Event')
    if not isinstance(category,str): raise ValueError('invalid category')
    start=row.get('start_time' if primary else 'start'); end=row.get('end_time' if primary else 'end')
    if primary: mode='local' if row.get('is_local_time') is True else 'absolute' if row.get('is_local_time') is False else 'unknown'
    else: mode='absolute' if any(isinstance(v,str) and re.search(r'(Z|[+-]\d\d:\d\d)$',v) for v in [start,end]) else 'local'
    regional = (category in ['City Safari'] or (category in ['Wild Area','Pokémon GO Tour'] and 'Global' not in title) or ('Night Out' in title and 'Twitch' not in title))
    details=row.get('details' if primary else 'extraData') or {}
    if not isinstance(details,dict): raise ValueError('details must be object')
    bonuses=details.get('bonuses',[])
    if not isinstance(bonuses,list) or any(not isinstance(b,str) for b in bonuses): raise ValueError('bonuses must be string array')
    start_kst=parse_time(start,mode) if not (regional and mode=='local') else None
    end_kst=parse_time(end,mode) if not (regional and mode=='local') else None
    if start_kst and end_kst and datetime.fromisoformat(end_kst)<=datetime.fromisoformat(start_kst): raise ValueError('end before start')
    warnings=[]
    description=row.get('description','')
    if not isinstance(description,str): raise ValueError('description must be text')
    if re.search(r'(?:end time|end date)[^.\n]{0,120}(?:not been announced|unannounced|not announced|to be announced)',description,re.I):
        end_kst=None; warnings.append('소스 설명에 종료 시각 미정으로 명시되어 종료값을 사용하지 않았습니다.')
    lower=title.lower()
    raid_type='거다이맥스' if 'gigantamax' in lower else '다이맥스' if ('dynamax' in lower or category in ['Max Battles','Max Mondays']) else '그림자' if 'shadow' in lower else '메가' if 'mega' in lower and 'raid' in lower else '전설' if '5-star' in lower or category=='Raid Hour' else '기타'
    return {'id':hashlib.sha256(url.encode()).hexdigest()[:16], 'name':translate(title),'originalName':title,'translationComplete':not bool(re.search('[A-Za-z]{4,}',translate(title).replace('Pokémon','').replace('Dynamax',''))),'category':CATEGORIES.get(category,category),'categoryOriginal':category,'raidType':raid_type,'start':start_kst,'end':end_kst,'rawStart':start,'rawEnd':end,'timeZoneType':mode,'timeZone':'Asia/Seoul' if mode=='local' and not regional else 'UTC' if mode=='absolute' else None,'region':'현장 한정 · '+title if regional else '글로벌 / 한국','regional':regional,'description':description,'bonuses':details.get('bonuses',[]),'pokemon':pokemon_from(details),'image':row.get('banner_url' if primary else 'image'),'sources':[{'name':source,'url':url,'official':False}],'officialVerification':None,'warnings':warnings,'conflicts':[]}

def merge_events(primary,secondary):
    merged={}
    for source, rows in [('primary',primary),('secondary',secondary)]:
        for row in rows:
            event=normalize(row,source); key=event['id']
            if key not in merged: merged[key]=event; continue
            old=merged[key]; old['sources']+=event['sources']
            for field in ['start','end']:
                if old[field] and event[field] and datetime.fromisoformat(old[field])!=datetime.fromisoformat(event[field]):
                    old['conflicts'].append({'field':field,'primary':old[field],'secondary':event[field]})
                elif not old[field] and event[field] and old['timeZoneType']==event['timeZoneType'] and not old['regional'] and not (field=='end' and old['warnings']): old[field]=event[field]
            for field in ['bonuses','pokemon','image','description']:
                if not old[field] and event[field]: old[field]=event[field]
    return list(merged.values())

def content_hash(e):
    return hashlib.sha256(json.dumps({k:v for k,v in e.items() if k not in ['firstSeen','updatedAt','change','lifecycle','lastSeen','descriptionKo','descriptionTranslation','bonusesKo']},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def reconcile(events, previous, timestamp, healthy_sources):
    old={e['id']:e for e in previous.get('events',[])}
    for e in events:
        prior=old.pop(e['id'],None)
        # Keep richer primary facts when only fallback is healthy; never overwrite known facts with absence.
        if prior and 'primary' not in healthy_sources:
            for k in ['description','bonuses','pokemon','officialVerification','name','originalName','translationComplete','region','regional']:
                if not e.get(k) or k in ['name','originalName','region','regional']: e[k]=copy.deepcopy(prior.get(k,e.get(k)))
            e['warnings'].append('주 소스 연결 실패 · 보조 소스로 확인한 일정입니다.')
        e['firstSeen']=prior['firstSeen'] if prior else timestamp
        changed=prior is not None and content_hash(e)!=content_hash(prior)
        e['updatedAt']=timestamp if not prior or changed else prior['updatedAt']
        e['change']='new' if not prior else 'modified' if changed else 'unchanged'
        e['lastSeen']=timestamp
        e['lifecycle']='ended' if e['end'] and datetime.fromisoformat(e['end'])<=datetime.fromisoformat(timestamp) else 'scheduled'
    for e in old.values():
        e=copy.deepcopy(e)
        e['lifecycle']='ended' if e['end'] and datetime.fromisoformat(e['end'])<=datetime.fromisoformat(timestamp) else 'unconfirmed'
        e['change']='unchanged'
        e['warnings']=list(dict.fromkeys(e.get('warnings',[])+['최신 소스에서 확인되지 않음 · 취소로 단정할 수 없습니다.']))
        events.append(e)
    return events

def run(args):
    output=Path(args.output); previous=read(output,{})
    timestamp=now_iso(); states={}; data={}
    for source,url in SOURCES.items():
        try:
            raw=read(Path(args.raw)/f'{source}.json',None) if args.raw else fetch(url)
            rows=flatten_primary(raw) if source=='primary' else raw
            if not isinstance(rows,list) or not rows: raise ValueError('empty or invalid source')
            for row in rows: normalize(row,source)
            data[source]=rows; states[source]={'ok':True,'count':len(rows),'url':url,'checkedAt':timestamp}
        except Exception as ex: states[source]={'ok':False,'url':url,'error':str(ex)[:250],'checkedAt':timestamp}
    status_path=output.with_name('status.json')
    if not data:
        atomic(status_path,{'lastAttempt':timestamp,'lastSuccess':previous.get('lastSuccess'),'state':'failed','sources':states})
        raise RuntimeError('Both sources failed. Existing event data preserved.')
    events=merge_events(data.get('primary',[]),data.get('secondary',[]))
    # A catastrophic source shrink is quarantined instead of silently dropping schedules.
    baseline=sum(e.get('lifecycle')!='ended' for e in previous.get('events',[]))
    if baseline>10 and len(events)<baseline*.3:
        atomic(status_path,{'lastAttempt':timestamp,'lastSuccess':previous.get('lastSuccess'),'state':'failed','sources':states,'error':'Unexpected source shrink; snapshot preserved'})
        raise RuntimeError('Unexpected source shrink')
    verifications=read(ROOT/'scripts/official-verifications.json',{})
    for e in events:
        slug=e['sources'][0]['url'].split('/')[-1]
        if slug in verifications:
            v=verifications[slug]; e['officialVerification']=v
            if not e['start'] or not e['end'] or datetime.fromisoformat(e['start'])!=datetime.fromisoformat(v['start']) or datetime.fromisoformat(e['end'])!=datetime.fromisoformat(v['end']): e['warnings'].append('공식 검증 기록과 현재 소스의 시각이 다릅니다. 원문을 확인하세요.')
            if v.get('nameKo'): e['name']=v['nameKo']; e['translationComplete']=True
            e['region']=v.get('region',e['region'])
            if v.get('preferredPokemon'):
                e['pokemon'].sort(key=lambda p:p['name']!=v['preferredPokemon'])
    events=reconcile(events,previous,timestamp,set(data))
    localizer=KoreanLocalizer(read(ROOT/'scripts/korean.json',{}),read(output.with_name('translations-ko.json'),{}),enabled=os.environ.get('GO_CAL_TRANSLATE')=='1')
    for event in events: localizer.apply(event)
    atomic(output.with_name('translations-ko.json'),localizer.cache)
    result={'schemaVersion':1,'lastSuccess':timestamp,'lastAttempt':timestamp,'state':'ok' if len(data)==2 else 'degraded','sources':states,'events':sorted(events,key=lambda e:e['start'] or '9999')}
    # Roundtrip validation before replacement.
    assert len({e['id'] for e in events})==len(events)
    atomic(output,result)
    atomic(status_path,{k:v for k,v in result.items() if k!='events'})
    print(f"Validated {len(events)} real events; state={result['state']}")

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--raw'); parser.add_argument('--output',default=str(ROOT/'public/data/events.json'))
    try: run(parser.parse_args())
    except Exception as ex: print(str(ex),file=sys.stderr); sys.exit(1)
