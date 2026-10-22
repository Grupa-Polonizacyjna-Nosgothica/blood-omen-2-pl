#!/usr/bin/env python3
"""Tests of build_patch.py (manifest) and the Bo2Patcher executable, on synthetic game files.

    cmake -S tools -B build && cmake --build build
    python3 -m unittest discover -s tools           # or: python3 tools/test_patcher.py

The patcher binary is looked up in $BO2_PATCHER, then build/Bo2Patcher(.exe), build/Release/Bo2Patcher.exe;
the tests that need it are skipped when it is not built. A final test runs against the real game files
when GameData/bo2.exe exists (it only works on copies in a temp dir).
"""
import os
import random
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import build_patch  # noqa: E402


def find_patcher():
    candidates = [os.environ.get("BO2_PATCHER", "")] + [
        os.path.join(ROOT, "build", n) for n in ("Bo2Patcher", "Bo2Patcher.exe", os.path.join("Release", "Bo2Patcher.exe"))]
    return next((c for c in candidates if c and os.path.isfile(c)), None)


PATCHER = find_patcher()


def blob(seed, n):
    return bytes(random.Random(seed).randrange(256) for _ in range(n))


class ManifestTests(unittest.TestCase):
    def test_ranges_merge_close_changes_and_keep_far_ones_apart(self):
        orig = bytes(200)
        new = bytearray(orig)
        new[10] = 1
        new[20] = 2          # 9 identical bytes in between: merged
        new[150] = 3         # far away: separate
        rs = build_patch.ranges(orig, bytes(new))
        self.assertEqual(rs, [(10, 21), (150, 151)])

    def test_manifest_has_checksums_not_original_bytes(self):
        orig = blob(1, 300)
        new = bytearray(orig)
        new[5:8] = b"\xaa\xbb\xcc"
        text = build_patch.manifest([("bo2.exe", orig, bytes(new))])
        self.assertIn("file bo2.exe size 300 crc32 %08x" % build_patch.crc32(orig), text)
        self.assertIn("range 5 3 %08x aabbcc" % build_patch.crc32(orig[5:8]), text)
        self.assertNotIn(orig[5:8].hex(), text.split("range", 1)[1])

    def test_size_change_is_rejected(self):
        with self.assertRaises(SystemExit):
            build_patch.ranges(b"abc", b"abcd")


@unittest.skipUnless(PATCHER, "Bo2Patcher is not built")
class PatcherTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.game = os.path.join(self.tmp, "game")
        os.makedirs(os.path.join(self.game, "data"))
        self.exe = blob(2, 5000)
        self.big = blob(3, 3000)
        new_exe = bytearray(self.exe)
        new_exe[100:104] = b"\x90\x90\x90\x90"
        new_exe[4000:4010] = bytes(range(10))
        new_big = bytearray(self.big)
        new_big[1000:1100] = bytes(100)
        self.patched = {"bo2.exe": bytes(new_exe), "data/PreCode.big": bytes(new_big)}
        self.originals = {"bo2.exe": self.exe, "data/PreCode.big": self.big}
        self.manifest = os.path.join(self.tmp, "bo2pl.patch")
        with open(self.manifest, "w", newline="\n") as f:
            f.write(build_patch.manifest([(k, self.originals[k], self.patched[k]) for k in self.originals]))
        # the real files have mixed case names; the patcher must find them anyway
        self.write("bo2.exe", self.exe)
        self.write("data/precode.big", self.big)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def path(self, rel):
        return os.path.join(self.game, *rel.split("/"))

    def write(self, rel, data):
        with open(self.path(rel), "wb") as f:
            f.write(data)

    def read(self, rel):
        with open(self.path(rel), "rb") as f:
            return f.read()

    def run_patcher(self, *args):
        return subprocess.run([PATCHER, *args], capture_output=True, text=True).returncode

    def cmd(self, name, *extra):
        return self.run_patcher(name, self.game, self.manifest, *extra)

    def test_patch_is_idempotent_and_restore_is_byte_identical(self):
        self.assertEqual(self.cmd("check"), 0)
        self.assertEqual(self.cmd("patch"), 0)
        self.assertEqual(self.read("bo2.exe"), self.patched["bo2.exe"])
        self.assertEqual(self.read("data/precode.big"), self.patched["data/PreCode.big"])
        self.assertTrue(os.path.exists(self.path("bo2.exe") + ".plbackup"))
        self.assertEqual(self.cmd("patch"), 0)                     # second run changes nothing
        self.assertEqual(self.read("bo2.exe"), self.patched["bo2.exe"])
        self.assertEqual(self.cmd("check"), 0)
        self.assertEqual(self.cmd("restore"), 0)
        self.assertEqual(self.read("bo2.exe"), self.exe)
        self.assertEqual(self.read("data/precode.big"), self.big)
        self.assertFalse(os.path.exists(self.path("bo2.exe") + ".plbackup"))

    def test_unsupported_build_is_refused_and_nothing_is_written(self):
        bad = bytearray(self.exe)
        bad[0] ^= 1                      # outside every range: right size, wrong build
        self.write("bo2.exe", bytes(bad))
        self.assertEqual(self.cmd("check"), 3)
        self.assertEqual(self.cmd("patch"), 3)
        self.assertEqual(self.read("bo2.exe"), bytes(bad))
        self.assertEqual(self.read("data/precode.big"), self.big)    # the other file was not touched either

    def test_wrong_size_is_unsupported(self):
        self.write("bo2.exe", self.exe + b"x")
        self.assertEqual(self.cmd("check"), 3)

    def test_file_changed_after_patching_is_refused_but_restorable(self):
        self.assertEqual(self.cmd("patch"), 0)
        tampered = bytearray(self.read("bo2.exe"))
        tampered[4003] ^= 1              # inside a patched range
        self.write("bo2.exe", bytes(tampered))
        self.assertEqual(self.cmd("patch"), 6)
        self.assertEqual(self.cmd("restore"), 0)
        self.assertEqual(self.read("bo2.exe"), self.exe)

    def test_restore_without_backup_is_refused(self):
        self.assertEqual(self.cmd("patch"), 0)
        os.remove(self.path("bo2.exe") + ".plbackup")
        self.assertEqual(self.cmd("restore"), 6)

    @unittest.skipIf(os.name == "nt" or os.geteuid() == 0, "needs a non-root POSIX user")
    def test_read_only_file_reports_write_error(self):
        os.chmod(self.path("bo2.exe"), 0o444)
        self.assertEqual(self.cmd("check"), 7)
        self.assertEqual(self.cmd("patch"), 7)
        os.chmod(self.path("bo2.exe"), 0o644)

    @unittest.skipUnless(sys.platform.startswith("linux"), "process scan is Linux-specific here")
    def test_running_game_is_detected(self):
        fake = os.path.join(self.tmp, "bo2.exe")
        os.symlink(shutil.which("sleep"), fake)
        proc = subprocess.Popen([fake, "5"])           # argv[0] ends in bo2.exe, like a Wine process
        try:
            self.assertEqual(self.cmd("check"), 4)
            self.assertEqual(self.cmd("patch"), 4)
            self.assertEqual(self.cmd("restore"), 4)
        finally:
            proc.kill()
            proc.wait()

    def test_usage_errors(self):
        self.assertEqual(self.run_patcher(), 1)
        self.assertEqual(self.run_patcher("frobnicate", self.game, self.manifest), 1)


@unittest.skipUnless(PATCHER and os.path.isfile(os.path.join(ROOT, "GameData", "bo2.exe")), "no real game files")
class RealGameTests(unittest.TestCase):
    def test_patch_the_real_exe_copy_and_restore(self):
        manifest = os.path.join(ROOT, "patch", "bo2pl.patch")
        original = os.path.join(ROOT, "GameData", "bo2.exe")
        with open(original, "rb") as f:
            original_bytes = f.read()
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copy(original, tmp)
            run = lambda c: subprocess.run([PATCHER, c, tmp, manifest], capture_output=True, text=True).returncode
            self.assertEqual(run("patch"), 0)
            with open(os.path.join(tmp, "bo2.exe"), "rb") as f:
                self.assertNotEqual(f.read(), original_bytes)
            self.assertEqual(run("restore"), 0)
            with open(os.path.join(tmp, "bo2.exe"), "rb") as f:
                self.assertEqual(f.read(), original_bytes)

if __name__ == "__main__":
    unittest.main()
