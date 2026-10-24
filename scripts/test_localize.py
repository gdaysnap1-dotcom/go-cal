import json,unittest
from pathlib import Path
from unittest.mock import patch
from localize import KoreanLocalizer,fingerprint

class KoreanTests(unittest.TestCase):
    def test_current_description_and_bonus_coverage(self):
        root=Path(__file__).resolve().parents[1]
        catalog=json.loads((root/'scripts/korean.json').read_text(encoding='utf-8'))
        events=json.loads((root/'public/data/events.json').read_text(encoding='utf-8'))['events']
        localizer=KoreanLocalizer(catalog)
        for event in events:
            localizer.apply(event)
            if event['description']:
                self.assertTrue(event['descriptionKo'],event['id'])
                self.assertEqual(event['descriptionTranslation']['sourceHash'],fingerprint(event['description']))
            self.assertTrue(all(event['bonusesKo']),event['id'])

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

    def test_translation_is_not_official_verification(self):
        source='New event'; event={'description':source,'bonuses':[],'officialVerification':None}
        KoreanLocalizer({'descriptions':{fingerprint(source):'새 이벤트'}}).apply(event)
        self.assertIsNone(event['officialVerification'])

if __name__=='__main__':unittest.main()
