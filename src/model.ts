export interface Pokemon {name:string;nameKo:string;image:string;shiny:boolean|null}
export interface GoEvent {id:string;name:string;originalName:string;translationComplete:boolean;category:string;categoryOriginal:string;raidType:string;start:string|null;end:string|null;rawStart:string|number|null;rawEnd:string|number|null;timeZoneType:string;timeZone:string|null;region:string;regional:boolean;description:string;descriptionKo?:string|null;descriptionTranslation?:{state:string;sourceHash:string};bonusesKo?:(string|null)[];bonuses:string[];pokemon:Pokemon[];image:string|null;sources:{name:string;url:string;official:boolean}[];officialVerification:{url:string;checkedAt:string;note:string;debut?:boolean;verifiedFields:string[]}|null;warnings:string[];conflicts:{field:string;primary:string;secondary:string}[];firstSeen:string;updatedAt:string;lastSeen:string;change:string;lifecycle:string}
export interface SourceState {ok:boolean;count?:number;error?:string;url:string;checkedAt:string}
export interface Snapshot {schemaVersion:number;lastSuccess:string;lastAttempt:string;state:string;sources:Record<string,SourceState>;events:GoEvent[]}
export interface Settings {minScore:number;regional:boolean;categories:string[];scores:Record<string,number>}
export const defaults:Settings={minScore:1,regional:false,categories:[],scores:{'레이드':4,'레이드 아워':4,'레이드 데이':4,'맥스배틀':4,'맥스 먼데이':2,'스포트라이트 아워':2,'커뮤니티 데이':4}};
export function loadStored<T>(key:string,fallback:T):T {try {const v=localStorage.getItem(key);return v?JSON.parse(v):fallback}catch{return fallback}}
export function saveStored(key:string,value:unknown):boolean {try{localStorage.setItem(key,JSON.stringify(value));return true}catch{return false}}
export function isSnapshot(v:unknown):v is Snapshot {const s=v as Snapshot;return !!s&&s.schemaVersion===1&&Number.isFinite(Date.parse(s.lastSuccess))&&Array.isArray(s.events)&&s.events.every(e=>typeof e.id==='string'&&typeof e.name==='string'&&Array.isArray(e.sources)&&Array.isArray(e.pokemon)&&Array.isArray(e.bonuses)&&(!e.start||Number.isFinite(Date.parse(e.start)))&&(!e.end||Number.isFinite(Date.parse(e.end))));}
export function score(e:GoEvent,s:Settings):{value:number;reason:string} {if(e.officialVerification?.debut)return {value:5,reason:'공식 발표에서 신규 등장 확인 · 개인 추천 기준'};return {value:s.scores[e.category]??3,reason:`${e.category}에 설정한 개인 추천 점수`}}
export function eventWindows(event: GoEvent): {start:string;end:string}[] {
 if (event.lifecycle === 'unconfirmed' || !event.start || !event.end) return [];
 // The official 2026 global Wild Area has two daytime sessions in Korea.
 if (event.originalName === 'Pokémon GO Wild Area 2026: Global' &&
     Date.parse(event.start) === Date.parse('2026-11-14T10:00:00+09:00') &&
     Date.parse(event.end) === Date.parse('2026-11-15T18:00:00+09:00')) {
  return [
   {start:event.start,end:'2026-11-14T18:00:00+09:00'},
   {start:'2026-11-15T10:00:00+09:00',end:event.end},
  ];
 }
 return [{start:event.start,end:event.end}];
}

export function nextWindow(event: GoEvent, now: number) {
 return eventWindows(event).find(window=>Date.parse(window.end)>now);
}

export function phase(e:GoEvent,now=Date.now()):'active'|'upcoming'|'ended'|'unknown' {
 if(e.lifecycle==='unconfirmed'||!e.start||!e.end)return 'unknown';
 const window=nextWindow(e,now);
 if(!window)return 'ended';
 return Date.parse(window.start)<=now?'active':'upcoming';
}
export function kstDate(input:Date|string|number=Date.now()):string {return new Intl.DateTimeFormat('sv-SE',{timeZone:'Asia/Seoul',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(input))}
export function wallTime(value:string):string {const d=new Date(Date.parse(value)+9*3600000);return d.toISOString().slice(0,19)}
export function formatTime(value:string|null,full=false):string {if(!value)return '시각 미확인';return new Intl.DateTimeFormat('ko-KR',{timeZone:'Asia/Seoul',month:'numeric',day:'numeric',...(full?{year:'numeric' as const}:{}),hour:'2-digit',minute:'2-digit',hour12:false}).format(new Date(value))}
export function interval(e:GoEvent):string {if(eventWindows(e).length===2)return '11월 14일·15일, 매일 10:00~18:00';if(!e.start&&!e.end)return '한국 시각 미확인 · 원문 확인';return `${e.start?formatTime(e.start):'시작 미확인'} → ${e.end?formatTime(e.end):'종료 미확인'}`}
export function tone(e:GoEvent):string {if(e.raidType==='다이맥스'||e.raidType==='거다이맥스')return 'pink';if(/레이드/.test(e.category))return 'violet';if(/스포트|커뮤니티/.test(e.category))return 'amber';return 'lime'}

export function endsToday(event: GoEvent, now: number): boolean {
 const window = nextWindow(event,now);
 return !!window && kstDate(window.end) === kstDate(now);
}

export function timeHint(event: GoEvent, now: number): string {
 const state = phase(event, now);
 if (state !== 'active' && state !== 'upcoming') return '';

 const window = nextWindow(event,now)!;
 const target = state === 'active' ? window.end : window.start;
 const minutes = Math.ceil((Date.parse(target) - now) / 60000);
 const days = Math.floor(minutes / 1440);
 const hours = Math.floor((minutes % 1440) / 60);
 const remainder = minutes % 60;
 const duration = days ? `${days}일${hours ? ` ${hours}시간` : ''}`
  : [hours && `${hours}시간`, remainder && `${remainder}분`].filter(Boolean).join(' ');
 return state === 'active' ? `종료까지 ${duration}` : `${duration} 후 시작`;
}
