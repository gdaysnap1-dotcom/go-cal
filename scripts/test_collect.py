import copy, json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from argparse import Namespace
import collect as c

def row(**kwargs):
    return dict(title='Palkia Raid Hour',article_url='https://leekduck.com/events/test/',category='Raid Hour',is_local_time=True,start_time='2026-10-24T18:00:00',end_time='2026-10-24T19:00:00',details={},**kwargs)

class CollectorTests(unittest.TestCase):
    def test_local_kst(self): self.assertEqual(c.parse_time('2026-10-24T18:00:00','local'),'2026-10-24T18:00:00+09:00')
    def test_absolute(self): self.assertEqual(c.parse_time('2026-10-25T02:30:00Z','absolute'),'2026-10-25T02:30:00+00:00')
    def test_epoch(self): self.assertEqual(c.parse_time(0,'absolute'),'1970-01-01T00:00:00+00:00')
    def test_unknown_times(self):
        self.assertIsNone(c.parse_time(None,'local')); self.assertIsNone(c.parse_time('bad','local')); self.assertIsNone(c.parse_time('2026-01-01T00:00:00','absolute'))
    def test_missing_end_not_generated(self):
        r=row(); r['end_time']=None; self.assertIsNone(c.normalize(r,'primary')['end'])
    def test_description_end_unknown_beats_numeric_field(self):
        r=row(description='The broadcast end time and expiration dates have not been announced.')
        secondary={'name':r['title'],'link':r['article_url'],'heading':'Raid Hour','start':'2026-10-24T18:00:00','end':'2026-10-24T19:00:00'}
        self.assertIsNone(c.merge_events([r],[secondary])[0]['end'])
    def test_region_does_not_become_kst(self):
        r=row(); r['category']='City Safari'; r['title']='City Safari Boston'
        e=c.normalize(r,'primary'); self.assertIsNone(e['start']); self.assertTrue(e['regional'])
    def test_duplicate_and_conflict(self):
        r=row(); other={'name':r['title'],'link':r['article_url']+'?a=1','heading':'Raid Hour','start':'2026-10-24T17:00:00','end':'2026-10-24T19:00:00'}
        events=c.merge_events([r],[other]); self.assertEqual(len(events),1); self.assertEqual(len(events[0]['sources']),2); self.assertEqual(events[0]['conflicts'][0]['field'],'start')
    def test_changed_time_stable_id(self):
        first=c.normalize(row(),'primary'); r=row(); r['start_time']='2026-10-24T17:00:00'
        changed=c.normalize(r,'primary'); self.assertEqual(first['id'],changed['id'])
        old=c.reconcile([first],{},'2026-10-20T00:00:00+00:00',{'primary'})
        result=c.reconcile([changed],{'events':old},'2026-10-21T00:00:00+00:00',{'primary'})
        self.assertEqual(result[0]['change'],'modified')
    def test_unchanged(self):
        e=c.normalize(row(),'primary'); old=c.reconcile([copy.deepcopy(e)],{},'2026-10-20T00:00:00+00:00',{'primary'})
        result=c.reconcile([e],{'events':old},'2026-10-21T00:00:00+00:00',{'primary'})
        self.assertEqual(result[0]['change'],'unchanged'); self.assertEqual(result[0]['firstSeen'],old[0]['firstSeen'])
    def test_absence_is_not_cancellation(self):
        e=c.normalize(row(),'primary'); old=c.reconcile([e],{},'2026-10-20T00:00:00+00:00',{'primary'})
        result=c.reconcile([],{'events':old},'2026-10-21T00:00:00+00:00',{'primary'})
        self.assertEqual(result[0]['lifecycle'],'unconfirmed')
    def test_ended(self):
        result=c.reconcile([c.normalize(row(),'primary')],{},'2026-10-25T00:00:00+00:00',{'primary'})
        self.assertEqual(result[0]['lifecycle'],'ended')
    def test_translation_fallback(self): self.assertEqual(c.translate('Unknown Pokémon Event'),'Unknown Pokémon Event')
    def test_invalid_schema(self):
        with self.assertRaises(ValueError): c.flatten_primary([])
        with self.assertRaises(ValueError): c.normalize({'title':'bad'},'primary')
        r=row(); r['details']={'bonuses':'not an array'}
        with self.assertRaises(ValueError): c.normalize(r,'primary')
    def test_failure_preserves_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/'events.json'; out.write_text('{"lastSuccess":"yesterday","events":[]}',encoding='utf-8'); before=out.read_bytes()
            with patch.object(c,'fetch',side_effect=OSError('offline')):
                with self.assertRaises(RuntimeError): c.run(Namespace(output=str(out),raw=None))
            self.assertEqual(out.read_bytes(),before)
            self.assertEqual(json.loads(out.with_name('status.json').read_text())['state'],'failed')
    def test_secondary_failure_valid_primary(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/'events.json'
            with patch.object(c,'fetch',side_effect=[{'Raid Hour':[row()]},OSError('offline')]): c.run(Namespace(output=str(out),raw=None))
            self.assertEqual(json.loads(out.read_text(encoding='utf-8'))['state'],'degraded')

if __name__=='__main__': unittest.main()
