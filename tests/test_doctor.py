#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""本物の /sys やコマンドの代わりに作りものの値を渡して、判定を確かめる。 python3 tests/test_doctor.py"""
import importlib.machinery
import importlib.util
import json
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

    def logs_run(self, started, recent_lines):
        """journalctl は --since の時刻より後の行だけ返すふりをする。recent_lines: [(UNIX 秒, 行)]"""
        calls = []

        def run(cmd, **k):
            if cmd[:2] == ["systemctl", "--user"] and "show" in cmd:
                return 0, f"@{started}"
            if cmd[0] == "journalctl":
                since = int(cmd[cmd.index("--since") + 1].lstrip("@"))
                calls.append(since)
                if "-p" in cmd:
                    return 0, ""
                return 0, "\n".join(l for t, l in recent_lines if t >= since)
            return 0, ""
        return run, calls

    def test_logs_only_current(self):
        now = 1_000_000
        cases = [
            # 起動時（起動から 18 秒後）のエラーだけ: 30 分前に起動 → 数えない
            (now - 1800, [(now - 1782, "Can't read eye data; failed")], "OK"),
            # 今もエラーが出ている（30 秒前）→ 警告
            (now - 1800, [(now - 1782, "failed"), (now - 30, "failed to open device")], "WARN"),
            # 起動して 90 秒: 起動後 60 秒までのエラーは数えない
            (now - 90, [(now - 80, "error at startup")], "OK"),
            # 起動して 40 秒: まだ見ない
            (now - 40, [(now - 10, "error")], "OK"),
        ]
        for started, lines, want in cases:
            run, calls = self.logs_run(started, lines)
            r = fd.Report()
            with mock.patch.object(fd.shutil, "which", return_value="/usr/bin/journalctl"), \
                    mock.patch.object(fd.os.path, "exists", return_value=False), mock.patch.object(fd, "run", side_effect=run):
                fd.check_logs(r, now=now)
            self.assertEqual(levels(r), [("steamvr", want)], (started, lines))
            for since in calls:
                self.assertGreaterEqual(since, now - fd.RECENT_SECONDS)

    def test_history_is_past_only(self):
        run, _ = self.logs_run(0, [(5, "failed to open device")])
        r = fd.Report()
        with mock.patch.object(fd.shutil, "which", return_value="/usr/bin/journalctl"), \
                mock.patch.object(fd.os.path, "exists", return_value=False), mock.patch.object(fd, "run", side_effect=run):
            fd.check_history(r, "@0")
        self.assertEqual([(i["level"], i["data"]["past"]) for i in r.items], [("INFO", True)])

    def test_audio(self):
        outs = {"@DEFAULT_AUDIO_SOURCE@": (0, "Volume: 1.00"), "@DEFAULT_AUDIO_SINK@": (1, "Object '-1' not found")}
        r = fd.Report()
        with mock.patch.object(fd.shutil, "which", return_value="/usr/bin/wpctl"), \
                mock.patch.object(fd, "run", side_effect=lambda cmd, **k: outs[cmd[-1]]):
            fd.check_audio(r)
        self.assertEqual([fd.brief_line(i) for i in r.items],
                         ["マイク：正常", "スピーカー：警告（既定のスピーカーが見つかりません）"])

    def eye(self, status, mmap=True):
        import tempfile
        d = tempfile.mkdtemp()
        os.makedirs(os.path.join(d, "frameeyeosc"))
        with open(os.path.join(d, "frameeyeosc", "status.json"), "w") as f:
            json.dump(status, f)
        exists = lambda p: p.endswith("frameeyeosc.service") or (p == fd.EYE_MMAP and mmap)
        r = fd.Report()
        with mock.patch.dict(os.environ, {"XDG_RUNTIME_DIR": d}), mock.patch.object(fd.os.path, "exists", side_effect=exists), \
                mock.patch.object(fd, "unit_state", return_value=("active", "enabled")):
            fd.check_eye(r, True)
        return fd.brief_line(r.items[0])

    def test_eye(self):
        import time as t
        now = t.time()
        boot_err = {"text": "Can't read eye data (/dev/shm/eye-server.mmap: No such file)", "time": now - 1500}
        ok = {"time": now, "started": now - 1500, "source_error": None, "last_error": boot_err, "tracking": False}
        self.assertEqual(self.eye(ok), "視線データ：正常")   # 起動時のエラーは昔のことなので気にしない
        self.assertIn("警告（目のデータが読めません", self.eye(dict(ok, source_error="Can't read eye data")))
        self.assertIn("警告（目のデータが読めません", self.eye(ok, mmap=False))
        self.assertIn("更新されていません", self.eye(dict(ok, time=now - 60)))
        recent = dict(ok, last_error={"text": "camera lost", "time": now - 10})
        self.assertIn("いまエラーが出ています", self.eye(recent))

    def test_network(self):
        r = fd.Report()
        with mock.patch.object(fd.socket, "getaddrinfo", side_effect=OSError("no dns")):
            fd.check_network(r, timeout=1)
        self.assertEqual(fd.brief_line(r.items[0]), "ネット：警告（インターネットにつながりません（名前解決ができません））")


class BriefTest(unittest.TestCase):
    def test_tools_brief(self):
        def run(cmd, **k):
            return (1, "") if cmd[0] == "pgrep" else (0, "")
        states = {"frameeyeosc": ("active", "enabled"), "frame-vitals-osc": ("inactive", "disabled")}
        r = fd.Report()
        with mock.patch.object(fd, "TOOLS", [("frameeyeosc", "frameeyeosc", ("bin", "x"), None, False),
                                             ("frame-vitals-osc", "frame-vitals-osc", ("py", "y"), None, False)]), \
                mock.patch.object(fd, "tool_version", return_value=("1.0.0", True)), \
                mock.patch.object(fd, "unit_state", side_effect=lambda u: states[u]), \
                mock.patch.object(fd, "stale_processes", return_value=[123]), mock.patch.object(fd, "run", side_effect=run):
            fd.check_tools(r, True)
        # 更新前の版のまま動いていても、動いているので正常。自動起動オフで止まっているものは、ふだんは出さない
        self.assertEqual([fd.brief_line(i) for i in r.items if i["brief"]], ["frameeyeosc：正常"])
        self.assertEqual([i["level"] for i in r.items], ["OK", "INFO"])

    def test_brief_render(self):
        import io, contextlib
        r = fd.Report()
        r.add("本体", "OK", "温度", "55 °C", brief="温度")
        r.add("本体", "INFO", "起動してから", "1 日", )
        r.add("ツール", "WARN", "視線データ", "x", brief="視線データ", reason="目のデータが読めません")
        r.add("過去のログ", "INFO", "steamvr", "3 行", past=True)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            fd.render_brief(r, False, "24h")
        self.assertEqual(out.getvalue().splitlines(),
                         ["温度：正常", "視線データ：警告（目のデータが読めません）", "（くわしくは frame-doctor --verbose）",
                          "", "■ 過去のログ（直近 24h。参考です。今の状態とは関係ありません）", "  steamvr: 3 行"])


class HelperTest(unittest.TestCase):
    def test_error_words(self):
        self.assertTrue(fd.looks_like_error("failed to open device"))
        self.assertTrue(fd.looks_like_error("Error: no such file"))
        self.assertFalse(fd.looks_like_error("[VR] SetOverlayFlag -> VROverlayError_None（読み返し: VROverlayError_None, true）"))
        self.assertFalse(fd.looks_like_error("finished, errors=0"))

    def test_ansi_stripped(self):
        with mock.patch.object(fd, "run", side_effect=lambda cmd, **k: (0, "" if "-p" in cmd else "\x1b[0;93m2026 [W:onnxruntime] GPU device discovery failed\x1b[m")):
            self.assertEqual(fd.error_lines("steamvr", "@0"), ["2026 [W:onnxruntime] GPU device discovery failed"])

    def test_size(self):
        self.assertEqual(fd.size(224 * 1024 * 1024), "235 MB")
        self.assertEqual(fd.size(6.3e9), "6.3 GB")
        self.assertEqual(fd.size(997e9), "997 GB")



class ToolVersionTest(unittest.TestCase):
    def test_opt_binary(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "vrc-wrist-notifier"))
            exe = os.path.join(d, "vrc-wrist-notifier", "wrist-toast")
            with open(exe, "w") as f:
                f.write("#!/bin/sh\necho 'wrist-toast 0.1.0'\n")
            os.chmod(exe, 0o755)
            with mock.patch.object(fd, "OPT", d):
                self.assertEqual(fd.tool_version(("opt", "vrc-wrist-notifier/wrist-toast")), ("0.1.0", True))
                self.assertEqual(fd.tool_version(("opt", "nothing/here")), (None, False))
        self.assertIn("vrc-wrist-notifier", [t[0] for t in fd.TOOLS])


if __name__ == "__main__":
    unittest.main()
