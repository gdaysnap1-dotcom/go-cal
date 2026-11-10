import json, tempfile, unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch
import collect
from localize import KoreanLocalizer,fingerprint

class KoreanTests(unittest.TestCase):
    def test_known_and_untranslated_content_can_coexist(self):
        source='A new battle event'
        localizer=KoreanLocalizer({
            'descriptions':{fingerprint(source):'새 배틀 이벤트'},
            'bonuses':{'Double XP':'경험치 두 배'},
        })
        event={'description':source,'bonuses':['Double XP','An unreviewed bonus']}
        localizer.apply(event)
        self.assertEqual(event['descriptionKo'],'새 배틀 이벤트')
        self.assertEqual(event['descriptionTranslation']['sourceHash'],fingerprint(source))
        self.assertEqual(event['bonusesKo'],['경험치 두 배',None])
        self.assertEqual(event['bonuses'],['Double XP','An unreviewed bonus'])

    def test_changed_source_never_reuses_old_translation(self):
        old='Ends on October 24.'
        localizer=KoreanLocalizer({'descriptions':{fingerprint(old):'10월 24일 종료됩니다.'}})
        self.assertEqual(localizer.translate(old)[1],'reviewed')
        self.assertEqual(localizer.translate('Ends on October 25.'),(None,'pending'))

    def test_exact_cache_and_offline(self):
        source='New battle event'
        cache={'entries':{fingerprint(source):{'text':'새 배틀 이벤트'}}}
        self.assertEqual(KoreanLocalizer({},cache).translate(source),('새 배틀 이벤트','automatic'))

    def test_failed_service_does_not_replace_original(self):
        event={'description':'A new event starts on November 8.','bonuses':[]}
        with patch('localize.urlopen',side_effect=OSError('offline')):
            KoreanLocalizer({},enabled=True).apply(event)
        self.assertIsNone(event['descriptionKo'])
        self.assertEqual(event['descriptionTranslation']['state'],'pending')
        self.assertEqual(event['description'],'A new event starts on November 8.')

    def test_fresh_schedule_survives_translation_outage(self):
        description='A new five-star raid announced after the catalog was published.'
        row={'title':'New raid','article_url':'https://leekduck.com/events/new-raid',
             'is_local_time':True,'start_time':'2026-11-18T18:00:00',
             'end_time':'2026-11-18T19:00:00','description':description}
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'events.json'
            # Simulate an incomplete cache left by an earlier run.
            output.with_name('translations-ko.json').write_text('{"entries":[]}',encoding='utf-8')
            with patch.object(collect,'fetch',side_effect=[{'Raid Hour':[row]},OSError('secondary offline')]), \
                 patch('localize.urlopen',side_effect=OSError('translation offline')) as provider:
                collect.run(Namespace(output=str(output),raw=None))
                provider.assert_not_called()
                before=json.loads(output.read_text(encoding='utf-8'))
                collect.enrich(output)
                provider.assert_called_once()
            after=json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(before,after)
            self.assertEqual(after['events'][0]['description'],description)
            self.assertEqual(after['events'][0]['start'],'2026-11-18T18:00:00+09:00')
            self.assertEqual(after['translationPending'],1)
            self.assertEqual(after['state'],'degraded')

    def test_expired_budget_still_allows_cached_translation(self):
        source='A known cached event'
        cache={'entries':{fingerprint(source):{'text':'저장된 이벤트'}}}
        localizer=KoreanLocalizer({},cache,enabled=True,time_budget=0)
        with patch('localize.urlopen') as provider:
            self.assertEqual(localizer.translate('An unseen event'),(None,'pending'))
            self.assertEqual(localizer.translate(source),('저장된 이벤트','automatic'))
            provider.assert_not_called()

    def test_translation_is_not_official_verification(self):
        source='New event'; event={'description':source,'bonuses':[],'officialVerification':None}
        KoreanLocalizer({'descriptions':{fingerprint(source):'새 이벤트'}}).apply(event)
        self.assertIsNone(event['officialVerification'])

if __name__=='__main__':unittest.main()
