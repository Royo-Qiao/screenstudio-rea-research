"""Synthetic, offline checks for privacy, parser boundaries and media failures."""
import importlib.util
import json
import plistlib
import struct
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


app = load_module("inspect_app")
project = load_module("project_stats")
export = load_module("verify_export")


def thin_macho(cpu=0x100000c, minimum=0x000c0000):
    command = struct.pack("<6I", 0x32, 24, 1, minimum, 0x000f0000, 0)
    header = struct.pack("<8I", 0xfeedfacf, cpu, 0, 2, 1, len(command), 0, 0)
    return header + command


class AppTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_thin_and_fat_minimums(self):
        binary = self.root / "binary"
        binary.write_bytes(thin_macho())
        result = app.macho_slices(binary)
        self.assertEqual(result[0]["architecture"], "arm64")
        self.assertEqual(result[0]["minimum_macos_declared"], "12.0.0")
        first, second = thin_macho(), thin_macho(0x1000007, 0x000d0500)
        table = struct.pack(">II", 0xcafebabe, 2)
        table += struct.pack(">5I", 0x100000c, 0, 48, len(first), 0)
        table += struct.pack(">5I", 0x1000007, 0, 48 + len(first), len(second), 0)
        binary.write_bytes(table + first + second)
        result = app.macho_slices(binary)
        self.assertEqual([x["architecture"] for x in result], ["arm64", "x86_64"])
        self.assertEqual(result[1]["minimum_macos_declared"], "13.5.0")

    def test_truncated_and_invalid_command_sizes_fail(self):
        binary = self.root / "binary"
        binary.write_bytes(thin_macho()[:-1])
        with self.assertRaises(ValueError):
            app.macho_slices(binary)
        broken = bytearray(thin_macho())
        struct.pack_into("<I", broken, 36, 4)
        binary.write_bytes(broken)
        with self.assertRaises(ValueError):
            app.macho_slices(binary)

    def test_bundle_does_not_launch_and_packed_hash_stays_distinct(self):
        root = self.root / "Example.app"
        (root / "Contents/MacOS").mkdir(parents=True)
        (root / "Contents/Resources").mkdir()
        (root / "Contents/MacOS/Example").write_bytes(thin_macho())
        (root / "Contents/Info.plist").write_bytes(plistlib.dumps({
            "CFBundleExecutable": "Example", "CFBundleShortVersionString": "1.0",
            "CFBundleVersion": "100", "LSMinimumSystemVersion": "12.0"}))
        (root / "Contents/Resources/app.asar").write_bytes(b"synthetic archive bytes")
        with patch.object(app.subprocess, "run", side_effect=AssertionError("No execution")):
            result = app.inspect_app(root, verify_signature=False)
        self.assertFalse(result["target_app_executed"])
        self.assertEqual(result["resource_layout"], "packed")
        self.assertIsNone(result["main_js_sha256"])
        self.assertIsNotNone(result["asar_sha256"])
        self.assertNotIn(str(root), json.dumps(result))

    def test_bundle_symlink_escape_rejected(self):
        (self.root / "outside").write_text("private", encoding="utf-8")
        bundle = self.root / "bundle"
        bundle.mkdir()
        (bundle / "escaped").symlink_to(self.root / "outside")
        with self.assertRaises(ValueError):
            app.inside(bundle.resolve(), "escaped")


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "project.json").write_text(json.dumps({"json": {
            "name": "PRIVATE TITLE", "scenes": [{"zoomRanges": [{"isSystem": False}]}]}}))

    def test_only_counts_are_emitted_and_missing_is_not_zero_evidence(self):
        (self.root / "recording").mkdir()
        (self.root / "recording/keystrokes-0.json").write_text(json.dumps([{"key": "SECRET KEYS"}]))
        (self.root / "recording/mouseclicks-0.json").write_text("[]")
        result = project.project_stats(self.root)
        self.assertEqual(result["event_counts"]["keystrokes"], 1)
        self.assertEqual(result["event_counts"]["mouseclicks"], 0)
        self.assertIsNone(result["event_counts"]["mousemoves"])
        self.assertEqual(result["missing_event_kinds"], ["mousemoves"])
        self.assertEqual(result["zoom_is_system_false"], 1)
        self.assertFalse(result["automatic_zoom_proven"])
        encoded = json.dumps(result)
        for secret in ("SECRET KEYS", "PRIVATE TITLE", str(self.root)):
            self.assertNotIn(secret, encoded)

    def test_unknown_event_schema_is_not_reported_as_empty(self):
        (self.root / "mousemoves-0.json").write_text('{"events": []}')
        with self.assertRaises(ValueError):
            project.project_stats(self.root)

    def test_symlinked_event_rejected(self):
        (self.root / "private.json").write_text("[]")
        (self.root / "mousemoves-0.json").symlink_to(self.root / "private.json")
        with self.assertRaises(ValueError):
            project.project_stats(self.root)

    def test_oversized_json_is_rejected_before_read(self):
        with patch.object(project, "MAX_JSON_BYTES", 1):
            with self.assertRaises(ValueError):
                project.project_stats(self.root)

    def test_unknown_zoom_origin_stays_unknown(self):
        (self.root / "project.json").write_text('{"scenes":[{"zoomRanges":[{}]}]}')
        result = project.project_stats(self.root)
        self.assertEqual(result["zoom_origin_unknown"], 1)
        self.assertEqual(result["zoom_is_system_true"], 0)


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "PRIVATE VIDEO.mp4"
        self.path.write_bytes(b"synthetic media fixture")
        self.metadata = {"streams": [{"codec_name": "h264", "width": 640, "height": 480,
                                      "avg_frame_rate": "60/1", "nb_read_frames": "120"}],
                         "format": {"duration": "2"}}

    def probe(self, **changes):
        return SimpleNamespace(returncode=0, stdout=json.dumps(self.metadata), stderr="", **changes)

    def test_valid_export_needs_full_decode_and_no_path_leaks(self):
        with patch.object(export.shutil, "which", side_effect=lambda x: x), patch.object(
                export.subprocess, "run", side_effect=[self.probe(), SimpleNamespace(returncode=0, stderr="")]) as run:
            result = export.verify_export(self.path)
        args = run.call_args_list[1].args[0]
        self.assertIn("-xerror", args)
        self.assertIn("0:v", args)
        self.assertIn("0:a?", args)
        self.assertFalse(result["native_recording_proven"])
        self.assertEqual(result["decoded_primary_video_frames"], 120)
        self.assertEqual(len(result["sha256"]), 64)
        self.assertNotIn("PRIVATE", json.dumps(result))

    def test_probe_success_does_not_hide_decode_failure(self):
        with patch.object(export.shutil, "which", side_effect=lambda x: x), patch.object(
                export.subprocess, "run", side_effect=[self.probe(), SimpleNamespace(returncode=1, stderr="broken")]):
            with self.assertRaises(ValueError):
                export.verify_export(self.path)

    def test_zero_exit_decode_errors_still_fail(self):
        with patch.object(export.shutil, "which", side_effect=lambda x: x), patch.object(
                export.subprocess, "run", side_effect=[self.probe(), SimpleNamespace(returncode=0, stderr="corrupt frame")]):
            with self.assertRaises(ValueError):
                export.verify_export(self.path)

    def test_invalid_metadata_rejected(self):
        for duration in ("0", "nan", "inf"):
            with self.subTest(duration=duration):
                self.metadata["format"]["duration"] = duration
                with patch.object(export.shutil, "which", side_effect=lambda x: x), patch.object(
                        export.subprocess, "run", return_value=self.probe()) as run:
                    with self.assertRaises(ValueError):
                        export.verify_export(self.path)
                    self.assertEqual(run.call_count, 1)

    def test_changing_file_fails(self):
        with patch.object(export.shutil, "which", side_effect=lambda x: x), patch.object(
                export.subprocess, "run", side_effect=[self.probe(), SimpleNamespace(returncode=0, stderr="")]), patch.object(
                export, "fingerprint", side_effect=[(1, 2, 3, 4), (1, 2, 4, 5)]):
            with self.assertRaises(ValueError):
                export.verify_export(self.path)

    def test_no_media_tools_and_empty_file_fail(self):
        with patch.object(export.shutil, "which", return_value=None):
            with self.assertRaises(ValueError):
                export.verify_export(self.path)
        self.path.write_bytes(b"")
        with self.assertRaises(ValueError):
            export.verify_export(self.path)


if __name__ == "__main__":
    unittest.main()
