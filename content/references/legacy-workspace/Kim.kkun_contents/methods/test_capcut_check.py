import json
import tempfile
import unittest
from pathlib import Path

from capcut_check import check


class CheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / "draft_info.json"
        self.episode = "2026-09-19_owner-emotions"

    def save(self, paths):
        self.project.write_text(json.dumps({"tracks": [], "materials": paths}))

    def test_placeholder_absolute_relative_and_no_write(self):
        media = self.root / "video.mov"
        media.write_bytes(b"fixture")
        self.save([{"path": str(media)}, {"path": "video.mov"},
                   {"font_path": "##_draftpath_placeholder_ABC_##/video.mov"}])
        before = {p.name: p.read_bytes() for p in self.root.iterdir()}
        result = check(self.project, self.episode)
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["references"]), 1)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.root.iterdir()})

    def test_missing_and_remote_are_not_passed(self):
        self.save([{"path": "missing.mov"}, {"path": "https://example.com/a"}])
        result = check(self.project, self.episode)
        self.assertFalse(result["ok"])
        self.assertEqual(len(result["missing"]), 1)
        self.assertEqual(len(result["unresolved"]), 1)

    def test_actual_mistyped_export_is_rejected(self):
        self.save([])
        output = self.root / "09192026-09-19_owne-emotions_v002.mov"
        output.write_bytes(b"fixture")
        self.assertFalse(check(self.project, self.episode, output)["ok"])

    def test_correct_name_and_missing_or_empty_output(self):
        self.save([])
        output = self.root / (self.episode + "_v002.mov")
        self.assertFalse(check(self.project, self.episode, output)["ok"])
        output.touch()
        self.assertFalse(check(self.project, self.episode, output)["ok"])
        output.write_bytes(b"fixture")
        self.assertTrue(check(self.project, self.episode, output)["ok"])

    def test_wrong_json_and_episode(self):
        self.project.write_text('{}')
        with self.assertRaises(ValueError):
            check(self.project, self.episode)
        self.save([])
        with self.assertRaises(ValueError):
            check(self.project, "../../wrong")

    def test_reused_click_identity_for_bgm_is_flagged(self):
        self.project.write_text(json.dumps({"tracks": [], "materials": {"audios": [
            {"name": "click.mp3", "effect_id": "click-id"},
            {"name": "bgm.wav", "effect_id": "click-id"}]}}))
        self.assertFalse(check(self.project, self.episode)["ok"])


if __name__ == "__main__":
    unittest.main()
