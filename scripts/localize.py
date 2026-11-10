"""Content-addressed Korean localization; never reuse translations after source edits."""
from __future__ import annotations
import hashlib, html, json, re, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

def fingerprint(text): return hashlib.sha256(text.encode('utf-8')).hexdigest()

class KoreanLocalizer:
    def __init__(self, catalog, cache=None, enabled=False, time_budget=60):
        self.catalog=catalog if isinstance(catalog,dict) else {}
        self.cache=cache if isinstance(cache,dict) else {}
        if not isinstance(self.cache.get('entries'),dict): self.cache['entries']={}
        day=datetime.now(timezone.utc).date().isoformat()
        used=self.cache.get('usedCharacters')
        if self.cache.get('usageDay')!=day or type(used) is not int or used<0:
            self.cache.update(usageDay=day,usedCharacters=0)
        self.enabled=enabled
        self.deadline=time.monotonic()+time_budget

    def translate(self,text,kind='descriptions'):
        if not text: return '', 'unavailable'
        key=fingerprint(text)
        section=self.catalog.get(kind)
        known=section.get(key if kind=='descriptions' else text) if isinstance(section,dict) else None
        if isinstance(known,str) and known.strip(): return known,'reviewed'
        if re.search('[가-힣]',text) and not re.search('[A-Za-z]{6,}',text): return text,'source-ko'
        prior=self.cache['entries'].get(key)
        if isinstance(prior,dict) and isinstance(prior.get('text'),str) and re.search('[가-힣]',prior['text']): return prior['text'],'automatic'
        if not self.enabled or time.monotonic()>=self.deadline or self.cache['usedCharacters']+len(text)>4500: return None,'pending'
        # The documented anonymous quota is 5,000 chars/day; leave headroom and cache all successes.
        self.cache['usedCharacters']+=len(text)
        try:
            chunks=[]
            for line in text.splitlines():
                current=''
                for word in line.split():
                    proposed=(current+' '+word).strip()
                    if len(proposed.encode('utf-8'))>450:
                        if not current or len(word.encode('utf-8'))>450: raise ValueError('translation segment too long')
                        chunks.append(current);current=word
                    else: current=proposed
                if current: chunks.append(current)
            translated=[]
            for chunk in chunks:
                remaining=self.deadline-time.monotonic()
                if remaining<=0: return None,'pending'
                url='https://api.mymemory.translated.net/get?'+urlencode({'q':chunk,'langpair':'en|ko'})
                with urlopen(Request(url,headers={'User-Agent':'GO-CAL/1.1'}),timeout=min(10,remaining)) as response: payload=json.load(response)
                if payload.get('responseStatus')!=200 or payload.get('quotaFinished'):
                    self.enabled=False
                    return None,'pending'
                value=html.unescape(payload.get('responseData',{}).get('translatedText','')).strip()
                if not value or value==chunk: raise ValueError('untranslated response')
                translated.append(value)
            result='\n'.join(translated)
            if not re.search('[가-힣]',result): raise ValueError('not Korean')
            self.cache['entries'][key]={'text':result,'provider':'MyMemory','sourceHash':key}
            return result,'automatic'
        except (OSError, ValueError, AttributeError, TypeError):
            # Stop network retries in this run when the provider cannot answer.
            # Exact cached and reviewed translations are still usable.
            self.enabled=False
            return None,'pending'

    def apply(self,event):
        original=event.get('description','')
        text,state=self.translate(original)
        event['descriptionKo']=text
        event['descriptionTranslation']={'state':state,'sourceHash':fingerprint(original)}
        event['bonusesKo']=[self.translate(b,'bonuses')[0] for b in event.get('bonuses',[])]
        return event
