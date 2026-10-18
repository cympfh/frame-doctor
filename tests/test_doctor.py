#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""本物の /sys やコマンドの代わりに作りものの値を渡して、判定を確かめる。 python3 tests/test_doctor.py"""
import importlib.machinery
import importlib.util
import os
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
loader = importlib.machinery.SourceFileLoader("frame_doctor", os.path.join(ROOT, "frame-doctor"))
spec = importlib.util.spec_from_loader("frame_doctor", loader)
fd = importlib.util.module_from_spec(spec)
loader.exec_module(fd)


def fake_fs(files):
    globs = lambda pattern: sorted({p.rsplit("/", 1)[0] for p in files if __import__("fnmatch").fnmatch(p.rsplit("/", 1)[0], pattern)})
    return mock.patch.multiple(fd, read=lambda p: files.get(p), glob=mock.Mock(glob=globs))


def levels(r):
    return [(i["title"], i["level"]) for i in r.items]


class SensorTest(unittest.TestCase):
    def zones(self, cpu_c):
        return {"/sys/class/thermal/thermal_zone0/type": "cpu3-top-thermal",
                "/sys/class/thermal/thermal_zone0/temp": str(int(cpu_c * 1000)),
                "/sys/class/thermal/thermal_zone1/type": "gpuss-0-thermal",
                "/sys/class/thermal/thermal_zone1/temp": "50000",
                "/sys/class/thermal/thermal_zone2/type": "pm8550-thermal",
                "/sys/class/thermal/thermal_zone2/temp": "99000"}   # 電源 IC は数えない

    def test_temp_levels(self):
        for c, want in ((55, "OK"), (85, "WARN"), (93, "ERROR")):
            r = fd.Report()
            with fake_fs(self.zones(c)):
                fd.check_temps(r, 80, 90)
            self.assertEqual(r.items[0]["level"], want, c)
            self.assertEqual(r.items[0]["data"]["hottest_zone"], "cpu3-top-thermal")

    def battery(self, cap, status):
        b = "/sys/class/power_supply/max1720x_bat"
        return {b + "/type": "Battery", b + "/capacity": str(cap), b + "/status": status, b + "/temp": "263"}

    def test_battery_levels(self):
        for cap, st, want in ((73, "Discharging", "OK"), (15, "Discharging", "WARN"), (5, "Discharging", "ERROR"),
                              (5, "Charging", "OK")):
            r = fd.Report()
            with fake_fs(self.battery(cap, st)):
                fd.check_battery(r)
            self.assertEqual(r.items[0]["level"], want, (cap, st))

    def test_throttling(self):
        files = {"/sys/class/thermal/cooling_device0/type": "cpufreq-cpu7",
                 "/sys/class/thermal/cooling_device0/cur_state": "3",
                 "/sys/class/thermal/cooling_device0/max_state": "31"}
        r = fd.Report()
        with fake_fs(files):
            fd.check_throttling(r)
        self.assertEqual(r.items[0]["level"], "WARN")


class CommandTest(unittest.TestCase):
    def test_mic_settings(self):
        outs = {"frame-mic.echo-cancel": (0, "Value: true (Saved: true)"),
                "frame-mic.noise-suppression": (0, "Value: false (Saved: false)")}
        r = fd.Report()
        with mock.patch.object(fd.shutil, "which", return_value="/usr/bin/wpctl"), \
                mock.patch.object(fd, "run", side_effect=lambda cmd, **k: outs[cmd[-1]]):
            fd.check_mic(r)
        self.assertEqual([i["message"] for i in r.items], ["オン", "オフ"])

    def test_passthrough(self):
        r = fd.Report()
        with mock.patch.object(fd.os.path, "exists", return_value=True), \
                mock.patch.object(fd, "run", return_value=(0, "camera.roomViewStyle=3")):
            fd.check_passthrough(r, True)
        self.assertIn("半透明", r.items[0]["message"])
        self.assertEqual(r.items[0]["data"]["value"], 3)

    def test_logs(self):
        def run(cmd, **k):
            if "-p" in cmd:
                return 0, ""
            return 0, "started\nSending OSC to x\nfailed to open device\nok"
        r = fd.Report()
        with mock.patch.object(fd.shutil, "which", return_value="/usr/bin/journalctl"), \
                mock.patch.object(fd.os.path, "exists", return_value=False), mock.patch.object(fd, "run", side_effect=run):
            fd.check_logs(r, "-24h")
        self.assertEqual(levels(r), [("steamvr", "WARN")])
        self.assertEqual(r.items[0]["data"]["count"], 1)


class HelperTest(unittest.TestCase):
    def test_error_words(self):
        self.assertTrue(fd.looks_like_error("failed to open device"))
        self.assertTrue(fd.looks_like_error("Error: no such file"))
        self.assertFalse(fd.looks_like_error("[VR] SetOverlayFlag -> VROverlayError_None（読み返し: VROverlayError_None, true）"))
        self.assertFalse(fd.looks_like_error("finished, errors=0"))

    def test_size(self):
        self.assertEqual(fd.size(224 * 1024 * 1024), "235 MB")
        self.assertEqual(fd.size(6.3e9), "6.3 GB")
        self.assertEqual(fd.size(997e9), "997 GB")


if __name__ == "__main__":
    unittest.main(verbosity=2)
