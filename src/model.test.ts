import {describe,it,expect} from 'vitest';
import {formatTime,isSnapshot,kstDate,phase,score,wallTime,defaults,GoEvent} from './model';
const event={start:'2026-10-24T14:00:00+09:00',end:'2026-10-24T17:00:00+09:00',lifecycle:'scheduled',category:'레이드'} as GoEvent;
describe('KST and event logic',()=>{
 it('converts UTC even across Korean midnight',()=>{expect(kstDate('2026-10-24T18:00:00Z')).toBe('2026-10-25');expect(wallTime('2026-10-25T02:30:00Z')).toBe('2026-10-25T11:30:00');expect(formatTime('2026-10-25T02:30:00Z')).toContain('11:30')});
 it('uses exclusive end and inclusive start',()=>{expect(phase(event,Date.parse(event.start!))).toBe('active');expect(phase(event,Date.parse(event.end!))).toBe('ended')});
 it('does not invent missing timestamps or unconfirmed events',()=>{expect(phase({...event,end:null})).toBe('unknown');expect(phase({...event,lifecycle:'unconfirmed'})).toBe('unknown')});
 it('keeps personal score separate from facts',()=>{expect(score(event,defaults).value).toBe(4);expect(score(event,{...defaults,scores:{'레이드':1}}).value).toBe(1)});
 it('rejects invalid snapshot',()=>{expect(isSnapshot({events:[]})).toBe(false);expect(isSnapshot(null)).toBe(false)});
});
