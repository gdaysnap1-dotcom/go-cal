"""Content-addressed Korean localization; never reuse translations after source edits."""
from __future__ import annotations
import hashlib, html, json, re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

def fingerprint(text): return hashlib.sha256(text.encode('utf-8')).hexdigest()

class KoreanLocalizer:
    def __init__(self, catalog, cache=None, enabled=False):
        self.catalog=catalog; self.cache=cache if isinstance(cache,dict) else {}
        self.cache.setdefault('entries',{})
        day=datetime.now(timezone.utc).date().isoformat()
        if self.cache.get('usageDay')!=day: self.cache.update(usageDay=day,usedCharacters=0)
        self.enabled=enabled

    def translate(self,text,kind='descriptions'):
        if not text: return '', 'unavailable'
        key=fingerprint(text)
        known=self.catalog.get(kind,{}).get(key) if kind=='descriptions' else self.catalog.get(kind,{}).get(text)
        if known: return known,'reviewed'
        if re.search('[가-힣]',text) and not re.search('[A-Za-z]{6,}',text): return text,'source-ko'
        prior=self.cache['entries'].get(key)
        if isinstance(prior,dict) and isinstance(prior.get('text'),str) and re.search('[가-힣]',prior['text']): return prior['text'],'automatic'
        if not self.enabled or self.cache['usedCharacters']+len(text)>4500: return None,'pending'
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
                url='https://api.mymemory.translated.net/get?'+urlencode({'q':chunk,'langpair':'en|ko'})
                with urlopen(Request(url,headers={'User-Agent':'GO-CAL/1.1'}),timeout=12) as response: payload=json.load(response)
                if payload.get('responseStatus')!=200 or payload.get('quotaFinished'): raise ValueError('translation service unavailable')
                value=html.unescape(payload.get('responseData',{}).get('translatedText','')).strip()
                if not value or value==chunk: raise ValueError('untranslated response')
                translated.append(value)
            result='\n'.join(translated)
            if not re.search('[가-힣]',result): raise ValueError('not Korean')
            self.cache['entries'][key]={'text':result,'provider':'MyMemory','sourceHash':key}
            return result,'automatic'
        except Exception:
            return None,'pending'

    def apply(self,event):
        original=event.get('description','')
        text,state=self.translate(original)
        event['descriptionKo']=text
        event['descriptionTranslation']={'state':state,'sourceHash':fingerprint(original)}
        event['bonusesKo']=[self.translate(b,'bonuses')[0] for b in event.get('bonuses',[])]
        return event
