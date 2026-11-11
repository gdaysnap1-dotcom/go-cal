import {describe,it,expect} from 'vitest';
import {endsToday,formatTime,isSnapshot,kstDate,phase,score,timeHint,wallTime,defaults,GoEvent} from './model';
import {eventGuide,isBigEvent,isFeaturedEvent} from './eventGuide';
const event={start:'2026-10-24T14:00:00+09:00',end:'2026-10-24T17:00:00+09:00',lifecycle:'scheduled',category:'레이드'} as GoEvent;
describe('KST and event logic',()=>{
 it('converts UTC even across Korean midnight',()=>{expect(kstDate('2026-10-24T18:00:00Z')).toBe('2026-10-25');expect(wallTime('2026-10-25T02:30:00Z')).toBe('2026-10-25T11:30:00');expect(formatTime('2026-10-25T02:30:00Z')).toContain('11:30')});
 it('uses exclusive end and inclusive start',()=>{expect(phase(event,Date.parse(event.start!))).toBe('active');expect(phase(event,Date.parse(event.end!))).toBe('ended')});
 it('does not invent missing timestamps or unconfirmed events',()=>{expect(phase({...event,end:null})).toBe('unknown');expect(phase({...event,lifecycle:'unconfirmed'})).toBe('unknown')});
 it('keeps personal score separate from facts',()=>{expect(score(event,defaults).value).toBe(4);expect(score(event,{...defaults,scores:{'레이드':1}}).value).toBe(1)});
 it('rejects invalid snapshot',()=>{expect(isSnapshot({events:[]})).toBe(false);expect(isSnapshot(null)).toBe(false)});
 it('groups only remaining events ending on the current Korean date',()=>{
  const now=Date.parse('2026-10-24T14:55:00Z');
  const late={...event,start:'2026-10-24T14:57:00Z',end:'2026-10-24T14:59:00Z'};
  expect(endsToday(late,now)).toBe(true);
  expect(endsToday({...late,end:'2026-10-24T15:00:00Z'},now)).toBe(false);
  expect(endsToday({...late,lifecycle:'unconfirmed'},now)).toBe(false);
  expect(endsToday(late,Date.parse(late.end))).toBe(false);
 });
 it('only counts down confirmed start or end times',()=>{
  expect(timeHint(event,Date.parse(event.start!)-120000)).toBe('2분 후 시작');
  expect(timeHint(event,Date.parse(event.start!))).toBe('종료까지 3시간');
  expect(timeHint(event,Date.parse(event.end!)-1)).toBe('종료까지 1분');
  expect(timeHint({...event,end:null},Date.parse(event.start!))).toBe('');
  expect(timeHint({...event,lifecycle:'unconfirmed'},Date.parse(event.start!))).toBe('');
  expect(timeHint(event,Date.parse(event.end!))).toBe('');
 });
 it('shows the next Wild Area session during the overnight break',()=>{
  const wild={...event,originalName:'Pokémon GO Wild Area 2026: Global',start:'2026-11-14T10:00:00+09:00',end:'2026-11-15T18:00:00+09:00'};
  const night=Date.parse('2026-11-14T18:00:00+09:00');
  expect(phase(wild,night)).toBe('upcoming');
  expect(timeHint(wild,night)).toBe('16시간 후 시작');
  expect(endsToday(wild,night)).toBe(false);
  expect(phase(wild,Date.parse('2026-11-15T10:00:00+09:00'))).toBe('active');
 });
 it('keeps regular raids off the big event calendar and creates an honest fallback',()=>{
  const raid={...event,name:'Unannounced',originalName:'Unannounced',raidType:'전설',pokemon:[]};
  expect(isFeaturedEvent(raid)).toBe(true);
  expect(isBigEvent(raid)).toBe(false);
  expect(isFeaturedEvent({...raid,category:'레이드 아워'})).toBe(false);
  expect(isBigEvent({...raid,category:'커뮤니티 데이'})).toBe(true);
  expect(eventGuide(raid).title).toBe('레이드');
  expect(eventGuide({...raid,originalName:'Pawniard Community Day'}).summary).toContain('자망칼');
 });
});
