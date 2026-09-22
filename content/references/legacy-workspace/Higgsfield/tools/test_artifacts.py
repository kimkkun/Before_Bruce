import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import unicodedata
import artifacts as a


class ArtifactsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = a.init_episode(Path(self.tmp.name) / 'episode')

    def request(self, inputs=None):
        inputs = inputs or []
        return {'kind': 'image', 'params': {'model': 'test', 'prompt': 'test', 'medias': [{'role': 'image', 'value': i['job_id']} for i in inputs]}, 'inputs': inputs, 'request_note': 'User requested test; no paid service invoked.'}

    def reserve(self, shot='S01_test', inputs=None):
        return a.reserve(self.root, shot, '03_인물기반 생성', self.request(inputs))

    def completed(self, shot='S01_test', job='job1'):
        record = self.reserve(shot)
        a.update(record, 'bind', job)
        out = record.parent / 'image.png'
        out.write_bytes(b'local test fixture')
        a.update(record, 'finish', str(out))
        return record, {'job_id': job, 'path': str(out.relative_to(self.root)), 'sha256': a._hash(out)}

    def test_normal_and_cross_shot_reference(self):
        _, source = self.completed()
        next_record = self.reserve('S02_other', [source])
        self.assertEqual(next_record.parent.name, 'v001')
        self.assertEqual(a.validate_episode(self.root), [])

    def test_missing_record(self):
        record = self.reserve()
        record.rename(record.with_suffix('.backup'))
        self.assertTrue(any('missing' in x for x in a.validate_episode(self.root)))

    def test_input_job_vs_path_mismatch(self):
        _, source = self.completed()
        source['job_id'] = 'wrong'
        with self.assertRaisesRegex(ValueError, 'provenance'):
            self.reserve('S02_wrong', [source])
        self.assertFalse((self.root / a.BASE / '03_인물기반 생성/S02_wrong').exists())

    def test_pending_duplicate(self):
        self.reserve()
        with self.assertRaisesRegex(ValueError, 'pending'):
            self.reserve()

    def test_traversal(self):
        with self.assertRaises(ValueError):
            self.reserve('../escape')
        _, source = self.completed()
        source['path'] = '../escape.png'
        with self.assertRaisesRegex(ValueError, 'traversal'):
            self.reserve('S02_escape', [source])

    def test_output_wrong_folder(self):
        record = self.reserve()
        a.update(record, 'bind', 'job1')
        outside = self.root / 'outside.png'
        outside.write_bytes(b'x')
        with self.assertRaisesRegex(ValueError, 'own version'):
            a.update(record, 'finish', str(outside))

    def test_hash_changed(self):
        record, source = self.completed()
        (self.root / source['path']).write_bytes(b'changed')
        self.assertTrue(any('hash mismatch' in x for x in a.validate_episode(self.root)))

    def test_duplicate_jobs(self):
        self.completed()
        second = self.reserve('S02_other')
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            a.update(second, 'bind', 'job1')
        self.assertEqual(a.read_record(second)['status'], 'reserved')

    def test_media_id_mismatch(self):
        _, source = self.completed()
        request = self.request([source])
        request['params']['medias'][0]['value'] = 'different'
        with self.assertRaisesRegex(ValueError, 'IDs mismatch'):
            a.reserve(self.root, 'S02_other', '03_인물기반 생성', request)

    def test_symlink_escape(self):
        other = Path(self.tmp.name) / 'outside'
        other.mkdir()
        (self.root / 'escape').symlink_to(other, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'escapes'):
            a._inside(self.root, 'escape/file.png')

    def test_bind_idempotent_and_version_increment(self):
        record = self.reserve()
        a.update(record, 'bind', 'job1')
        a.update(record, 'bind', 'job1')
        with self.assertRaises(ValueError):
            a.update(record, 'bind', 'job2')
        a.update(record, 'fail', 'Service reports terminal failure; checked by operator.', confirmed_failed=True)
        self.assertEqual(self.reserve().parent.name, 'v002')

    def test_duplicate_shot_id_name_or_method_rejected(self):
        self.completed()
        with self.assertRaisesRegex(ValueError, 'shot ID already'):
            self.reserve('S01_renamed')
        with self.assertRaisesRegex(ValueError, 'shot ID already'):
            a.reserve(self.root, 'S01_test', '02_상황 장면 생성', self.request())
        self.assertEqual(self.reserve().parent.name, 'v002')

    def test_existing_missing_metadata_blocks_reserve(self):
        record = self.reserve()
        record.rename(record.with_suffix('.backup'))
        with self.assertRaisesRegex(ValueError, 'existing episode'):
            self.reserve('S02_other')

    def test_missing_links_and_external_project_reference(self):
        outside = self.root.parent / 'script with space.md'
        outside.write_text('script')
        readme = self.root / 'README.md'
        readme.write_text('[script](../script%20with%20space.md) [site](https://example.com)')
        self.assertEqual(a.validate_episode(self.root), [])
        readme.write_text('[missing](missing.md)')
        self.assertTrue(any('missing linked file' in e for e in a.validate_episode(self.root)))
        with self.assertRaisesRegex(ValueError, 'existing episode'):
            self.reserve()

    def test_orphan_completed_asset_and_pending_download(self):
        record = self.reserve()
        stray = record.parent / 'pending.png'
        stray.write_bytes(b'pending')
        self.assertEqual(a.validate_episode(self.root), [])
        a.update(record, 'bind', 'job1')
        a.update(record, 'finish', str(stray))
        (record.parent / 'unregistered.mp4').write_bytes(b'wrong')
        self.assertTrue(any('orphan' in e for e in a.validate_episode(self.root)))

    def test_missing_cut_link_and_png_in_feedback(self):
        record = self.reserve()
        cut_record = record.parent.parent.parent / a.CUT_RECORD
        cut_record.write_text('[missing](absent.png)')
        (self.root / '03_수정기록/frame.png').write_bytes(b'image')
        errors = a.validate_episode(self.root)
        self.assertTrue(any('missing linked file' in e for e in errors))
        self.assertTrue(any('technical artifact' in e for e in errors))

    def test_unicode_path_variants_follow_actual_filesystem(self):
        record = self.reserve()
        a.update(record, 'bind', 'unicode-job')
        out = record.parent / unicodedata.normalize('NFD', '기준이미지.png')
        out.write_bytes(b'unicode fixture')
        a.update(record, 'finish', str(out))
        data = a.read_record(record)
        nfc_path = unicodedata.normalize('NFC', data['output']['path'])
        nfc_file = self.root / nfc_path
        if not nfc_file.exists():
            # Linux treats names as distinct: do not collapse different files.
            nfc_file.write_bytes(b'different file')
            self.assertTrue(any('orphan' in e for e in a.validate_episode(self.root)))
            return
        self.assertTrue(nfc_file.samefile(out))
        data['output']['path'] = nfc_path
        a.write_record(record, data)
        source = {'job_id': 'unicode-job', 'path': str(out.relative_to(self.root)), 'sha256': a._hash(out)}
        self.reserve('S02_unicode', [source])
        self.assertEqual(a.validate_episode(self.root), [])

    def test_unknown_service_status_cannot_be_failed(self):
        record = self.reserve()
        a.update(record, 'bind', 'job1')
        with self.assertRaisesRegex(ValueError, 'terminal failure'):
            a.update(record, 'fail', 'timeout')
        self.assertEqual(a.read_record(record)['status'], 'submitted')

    def test_preserve_review_and_no_overwrite_create(self):
        record = self.reserve()
        with record.open('a') as f:
            f.write('\nHuman review retained.\n')
        a.update(record, 'bind', 'job1')
        self.assertIn('Human review retained.', record.read_text())
        with self.assertRaises(FileExistsError):
            a.write_record(record, a.read_record(record), create=True)

    def test_technical_file_in_feedback(self):
        (self.root / '03_수정기록/debug.json').write_text('{}')
        self.assertTrue(any('technical artifact' in x for x in a.validate_episode(self.root)))

    def test_external_reference_explicit(self):
        source = self.root / '01_자료넣는곳/ref.png'
        source.write_bytes(b'external source')
        inp = {'job_id': 'remote-upload-id', 'path': str(source.relative_to(self.root)), 'sha256': a._hash(source), 'external': True}
        self.reserve(inputs=[inp])
        self.assertEqual(a.validate_episode(self.root), [])


if __name__ == '__main__':
    unittest.main()
