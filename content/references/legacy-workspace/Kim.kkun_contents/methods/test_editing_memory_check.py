import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from editing_memory_check import run, CURRENT, HISTORY


class HealthTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'repo'
        self.episode = '2026-09-19_test'
        self.library = self.root / '김꾼_영상보관' / self.episode
        for folder in [self.repo/'drafts', self.repo/'methods', self.repo/'context',
                       self.library/'02_결과보기', self.library/'03_수정기록']:
            folder.mkdir(parents=True, exist_ok=True)
        self.record = self.repo/'drafts'/f'{self.episode}_video-comparison.md'
        (self.library/'03_수정기록/README.md').write_text(self.record.name)
        for name, text in {
            'methods/workflow.md': '## 영상 편집 세션\n절차\n## 발행 후',
            'methods/capcut-caption-style.md': '## 적용할 기준과 과거 사례 구분\n## 확정 규칙\n## 최신 연출 참조',
            'methods/automation.md': '### 단계별 실행 확인 — 2026-09-19\n검사\n### 글씨 크기',
            'context/kimkkun-mind.md': '관점', 'context/audience.md': '청자'
        }.items():
            (self.repo/name).write_text(text)
        self.bundle = self.repo/'drafts/baseline.zip'
        with zipfile.ZipFile(self.bundle, 'w') as z:
            z.writestr('draft_info.json', '{"tracks": []}')
        self.state = {'review_state': 'awaiting_user', 'baseline': {
            'path': 'baseline.zip', 'sha256': hashlib.sha256(self.bundle.read_bytes()).hexdigest()},
            'feedback': [{'id': 'stickers', 'source': '사용자 발언', 'status': 'pending', 'scope': 'episode'}]}
        self.write()

    def write(self, extra=''):
        self.record.write_text(CURRENT+'\n'+extra+'\n```editing-state\n'+json.dumps(self.state)+
                               '\n```\n## 기록 갱신 방법\n방법\n'+HISTORY+'\n이력')

    def codes(self, **kwargs):
        return {f['code'] for f in run(self.repo, self.episode, **kwargs)['findings']}

    def test_waiting_is_normal_and_checker_is_read_only(self):
        before = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(self.codes(), set())
        self.assertEqual(before, {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_pending_at_delivery(self):
        self.state['review_state'] = 'ready'; self.write()
        self.assertIn('pending_at_delivery', self.codes())
        self.assertIn('missing_results', self.codes())

    def test_baseline_changes(self):
        self.bundle.write_bytes(b'changed')
        self.assertIn('baseline_changed', self.codes())
        self.assertIn('baseline_unreadable', self.codes())

    def test_broken_link_duplicate_current_and_growth(self):
        self.write('[없음](missing.mov)\n'+CURRENT)
        codes = self.codes(current_limit=5, reading_limit=5, history_limit=1)
        self.assertTrue({'broken_link', 'current_sections', 'current_growth', 'reading_growth', 'history_growth'} <= codes)

    def test_applied_without_evidence_and_unconfirmed_promotion(self):
        self.state['feedback'][0].update(status='applied', scope='common', confirmed=False)
        self.write()
        self.assertTrue({'applied_without_evidence', 'unconfirmed_promotion', 'rule_not_linked'} <= self.codes())

    def test_conflicting_confirmed_values(self):
        self.state['feedback'] = [{'id': str(i), 'source': '승인', 'status': 'pending',
            'scope': 'common', 'confirmed': True, 'property': 'caption.lines', 'value': i} for i in [1, 2]]
        self.write(); self.assertIn('conflicting_feedback', self.codes())

    def test_result_clutter_and_pointer(self):
        (self.library/'02_결과보기/extra.zip').write_bytes(b'x')
        (self.library/'03_수정기록/README.md').write_text('다른 문서')
        self.assertTrue({'result_clutter', 'record_pointer'} <= self.codes())

    def test_completed_review_can_pass(self):
        evidence = self.repo/'drafts/comparison.md'; evidence.write_text('실제 차이 근거')
        self.state['feedback'][0].update(status='applied', evidence='comparison.md', scope='common',
                                        confirmed=True, rule_anchor='## 확정 규칙')
        self.state['review_state'] = 'ready'; self.write()
        (self.library/'02_결과보기/latest.mov').write_bytes(b'fixture')
        (self.library/'02_결과보기/thumbnail.png').write_bytes(b'fixture')
        self.assertEqual(self.codes(), set())


if __name__ == '__main__':
    unittest.main()
