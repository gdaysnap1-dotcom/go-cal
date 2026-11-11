import type {GoEvent} from './model';

type Guide = {title: string; summary: string; action?: string; source?: string};

const specialDays = new Set(['와일드 에리어', 'GO 투어', 'GO 페스트', '커뮤니티 데이', '레이드 데이', '시티 사파리']);
const wildWeekSource = 'https://pokemongo.com/ko/news/into-the-wild-2026';
const guides: Record<string, Guide> = {
 'Into the Wild 2026': {
  title: '와일드 위크',
  summary: '강철·드래곤타입 포켓몬을 만나는 주간이에요. 다이맥스 레지드래고가 처음 나와요.',
  action: '지도에서 파워스폿을 찾아 별 5개짜리 맥스배틀에 도전해 보세요.',
  source: wildWeekSource,
 },
 'Zacian (Crowned Sword) and Zamazenta (Crowned Shield) in 5-star Raid Battles': {
  title: '자시안(검왕)·자마젠타(방패왕) 레이드',
  summary: '별 5개짜리 레이드에 자시안과 자마젠타가 나와요. 이기면 모습을 바꾸는 데 쓰는 에너지를 받을 수 있어요.',
  action: '지도에서 별 5개짜리 레이드가 열린 체육관을 찾아 친구들과 도전해 보세요.',
  source: wildWeekSource,
 },
 'Pokémon GO Wild Area 2026: Global': {
  title: 'GO 와일드 에리어 2026',
  summary: '강철·드래곤타입 포켓몬을 만나는 이틀짜리 행사예요. 거다이맥스 두랄루돈도 처음 나와요.',
  action: '야생 포켓몬은 GO사파리볼로 잡아 보세요. 두랄루돈에 도전하려면 파워스폿의 맥스배틀을 찾아요.',
  source: 'https://pokemongo.com/ko/gowildarea/global',
 },
 'Eternamax Eternatus Returns': {
  title: '무한다이노 귀환',
  summary: '파워스폿에서 무한다이노(무한다이맥스)와 싸워요. 이기면 무한다이노의 사탕을 받을 수 있어요.',
  action: '친구들과 맥스배틀에 도전해 보세요. 무한다이노와의 만남은 GO패스 보상에서 확인해요.',
  source: 'https://pokemongo.com/ko/news/dynamax-trails-eternamax-eternatus-2026',
 },
 'Pawniard Community Day': {
  title: '자망칼 커뮤니티 데이',
  summary: '평소보다 자망칼이 야생에 많이 나오는 날이에요. 운이 좋으면 색이 다른 자망칼도 만날 수 있어요.',
  action: '게임 지도에서 자망칼을 찾아 잡아 보세요.',
  source: 'https://pokemongo.com/ko/news/communityday-november-2026-pawniard',
 },
 'Clefable Super Mega Raid Day': {
  title: '픽시 슈퍼 메가 레이드 데이',
  summary: '메가픽시가 처음 나와요. 일부 체육관에서 열리는 슈퍼 메가 레이드에서 만날 수 있어요.',
  action: '지도에서 슈퍼 메가 레이드가 열린 체육관을 찾고 친구들과 도전해 보세요.',
  source: 'https://pokemongo.com/ko/news/clefable-super-mega-raid-day-2026',
 },
};

export function isBigEvent(event: GoEvent): boolean {
 return specialDays.has(event.category) ||
  (event.category === '맥스배틀' && (/\b(?:Max Battle Day|Gigantamax)\b|맥스배틀 데이/i.test(event.originalName + ' ' + event.name) ||
   event.originalName === 'Eternamax Eternatus Returns')) ||
  (event.category === '이벤트' && event.officialVerification?.debut === true);
}

export function isFeaturedEvent(event: GoEvent): boolean {
 return isBigEvent(event) || event.originalName === 'Into the Wild 2026' ||
  (event.category === '레이드' && event.raidType === '전설');
}

export function calendarLabel(event: GoEvent, title: string): string {
 if (event.category==='와일드 에리어') return '와일드';
 if (event.originalName==='Clefable Super Mega Raid Day') return '메가픽시';
 if (event.category==='커뮤니티 데이') return title.replace(/ 커뮤니티 데이$/, '') || '커뮤데이';
 if (event.category==='레이드 데이') return '레이드';
 return title.split(' ')[0];
}

export function eventGuide(event: GoEvent): Guide {
 const written = guides[event.originalName];
 if (Object.hasOwn(guides,event.originalName)) return written;
 const names = [...new Set(event.pokemon.filter(p=>/[가-힣]/.test(p.nameKo)).map(p=>p.nameKo))];
 const subject = names.length === 1 ? names[0] : names.length === 2 ? names.join('·') : '';
 const localizedTitle = /^[^A-Za-z]*[가-힣][^A-Za-z]*$/.test(event.name) ? event.name : '';
 const title = localizedTitle || [subject, event.category].filter(Boolean).join(' ');
 const known = (name: string, generic: string) => subject ? name : generic;

 switch(event.category){
  case '커뮤니티 데이':
   return {title,summary:names.length===1?`주인공은 ${subject}! 평소보다 야생에 자주 나와요.`:'한 포켓몬이 평소보다 자주 나오는 날이에요. 주인공은 아래 상세 안내에서 확인할 수 있어요.',action:'게임 지도에 나타난 포켓몬을 눌러 잡아 보세요.'};
  case '레이드 데이':
  case '레이드':
   return {title,summary:known(`체육관의 레이드에서 ${subject}에 도전할 수 있어요.`,'체육관에서 강한 포켓몬과 싸우는 레이드 일정이에요.'),action:'지도에서 레이드가 열린 체육관을 찾아 친구들과 도전해 보세요.'};
  case '맥스배틀':
   return {title,summary:known(`파워스폿에서 ${subject}에 도전할 수 있어요.`,'파워스폿에서 커진 포켓몬과 싸우는 맥스배틀 일정이에요.'),action:'지도에서 맥스배틀이 열린 파워스폿을 찾아보세요.'};
  case 'GO 투어':
   return {title,summary:'포켓몬 세계의 한 지방을 주제로 열리는 큰 행사예요. 등장 포켓몬과 참가 방법은 아래 안내에서 확인해요.'};
  case '와일드 에리어':
  case 'GO 페스트':
  case '시티 사파리':
   return {title,summary:'평소와 다른 포켓몬을 만날 수 있는 특별 행사예요. 참가할 수 있는 장소와 조건을 아래에서 확인해요.'};
  default:
   return {title,summary:event.descriptionKo ? event.descriptionKo.split(/\n/)[0] : '자세한 한국어 안내를 준비하고 있어요. 아래에서 원문을 볼 수 있어요.'};
 }
}
