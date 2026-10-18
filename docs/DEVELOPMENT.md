# 開発者向けメモ

見るだけで、何も書き込みません。Python 3 の標準ライブラリだけで動きます。

| 項目 | 見ているもの | 判定 |
|---|---|---|
| 温度 | `/sys/class/thermal/thermal_zone*` のうち `cpu*` / `cpuss*` / `gpuss*` の最大値 | 80 °C 以上 WARN、90 °C 以上 ERROR（`--warn-temp` / `--error-temp`） |
| 熱による制限 | `cooling_device*`（`cpufreq-*`、GPU）の `cur_state`、`cpufreq/policy*` の `scaling_max_freq` < `cpuinfo_max_freq` | 制限があれば WARN |
| バッテリー | `/sys/class/power_supply/*`（`type` が `Battery`） | 充電していないとき 20% 未満 WARN、10% 未満 ERROR |
| 空き容量 | `/`、`/home`、`/var` | 10% 未満 WARN、5% 未満 ERROR |
| 起動してから | `/proc/uptime` | 情報 |
| SteamVR | `systemctl --user is-active steamvr.service`、`vrserver` のプロセス | 動いていなければ WARN |
| パススルーの表示 | `vrcmd --settings-int camera.roomViewStyle`（`/opt/steamvr/bin/linuxarm64`、`LD_LIBRARY_PATH=.`） | 情報 |
| ツール | frameeyeosc（+パネル）、frame-aux-shortcuts、frame-mic-tuner、frame-perf-overlay、frame-vitals-osc、frame-gaze-gestures、vrc-wrist-notifier の `--version`、unit の状態、プロセス。更新後も古い実行ファイル（`/proc/<pid>/exe` が `(deleted)`）のまま動いていれば WARN | 自動起動オンで SteamVR が動いているのに止まっていれば WARN（パネルで閉じられるものは INFO） |
| マイク | `wpctl settings frame-mic.echo-cancel` / `frame-mic.noise-suppression` | 情報 |
| ログ | `journalctl --user -u <unit> --since -24h` の重要度 err 以上の行と、error / failed / panic などを含む行（`VROverlayError_None` のような「エラーなし」は除く） | あれば WARN |

## テスト

```sh
python3 tests/test_doctor.py
```
