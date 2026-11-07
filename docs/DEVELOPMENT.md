# 開発者向けメモ

既定は見るだけで、何も書き込みません。`--fix` を付けたときだけ、画面の UI が落ちていれば `systemctl --user restart steamvr.service` を実行します（更新中はしない。他のユニットは触らない）。Python 3 の標準ライブラリだけで動きます。

**いまの状態だけで判定します**（0.3.0 から）。過去のログは判定に使いません。ログで警告にするのは、直近 2 分に同じサービスがまだエラーを出しているときだけです。サービスが起動してから 1 分以内の行は、起動時によくある一時的なものとして数えません。

ふだんの表示は「項目：正常」「項目：警告（理由）」を 1 行ずつ。`--verbose` で各項目の値、`--json` で全部、`--history [24h]` で過去のログを「参考」として別に出します（判定には使いません）。

| 項目（ふだんの表示） | 見ているもの | 判定 |
|---|---|---|
| 温度 | `/sys/class/thermal/thermal_zone*` のうち `cpu*` / `cpuss*` / `gpuss*` の最大値 | 80 °C 以上 WARN、90 °C 以上 ERROR（`--warn-temp` / `--error-temp`） |
| 熱による制限 | `cooling_device*`（`cpufreq-*`、GPU）の `cur_state`、`cpufreq/policy*` の `scaling_max_freq` < `cpuinfo_max_freq` | 制限があれば WARN |
| バッテリー | `/sys/class/power_supply/*`（`type` が `Battery`） | 充電していないとき 20% 未満 WARN、10% 未満 ERROR |
| 空き容量 | `/`、`/home`、`/var`（ふだんの表示は 1 行にまとめる） | 10% 未満 WARN、5% 未満 ERROR |
| SteamVR | `systemctl --user is-active steamvr.service`、`vrserver` と `vrwebhelper` のプロセス（pgrep は 0=いる / 1=いない / それ以外=不明）。起動後 1 分以内、起動時刻が取れないとき、プロセス確認が失敗したときは異常にしない。今回の SteamVR 起動以降の `vrwebhelper` コアダンプ（プロセスがいないときの理由）。`WaitForPendingPresent` だけでは異常にしない | 止まっていれば「停止中」（デスクトップモードでは普通なので警告にしない）。動いているのに画面 UI がいなければ WARN |
| 各ツール | frameeyeosc（+パネル）、frame-aux-shortcuts、frame-mic-tuner、frame-perf-overlay、frame-vitals-osc、frame-gaze-gestures、vrc-wrist-notifier の unit の状態とプロセス | 自動起動オンで SteamVR が動いているのに止まっていれば WARN（パネルで閉じられるものは除く）。動いているものだけふだんの表示に出す。更新前の版のまま動いているのは、--verbose で知らせるだけ |
| 視線データ | frameeyeosc が動いているとき: `$XDG_RUNTIME_DIR/frameeyeosc/status.json` の更新時刻・`source_error`・`config_error`・`last_error`、`/dev/shm/eye-server.mmap` があるか | 10 秒以上更新されていない、読み込みエラーが今ある、ファイルが無い、直近 2 分に新しいエラー（起動後 1 分以内は除く）なら WARN |
| マイク / スピーカー | `wpctl get-volume @DEFAULT_AUDIO_SOURCE@` / `@DEFAULT_AUDIO_SINK@` | 既定の機器が見つからなければ WARN |
| ネット | `github.com` の名前解決と TCP 443 への接続（何も送らない。`--no-network` で省略） | できなければ WARN |
| ＜サービス＞ のログ | `journalctl --user -u <unit> --since @<max(今-2分, 起動+1分)>` の重要度 err 以上の行と、error / failed / panic などを含む行（`VROverlayError_None` のような「エラーなし」は除く） | あれば WARN（正常なときはふだんの表示に出さない） |
| （--verbose だけ） | 起動してからの時間、パススルーの表示（`vrcmd`）、マイクのフィルター（`wpctl settings frame-mic.*`）、各ツールの版 | 情報 |

`--fix`: 画面 UI が落ちていて、Steam / SteamOS の更新中でなければ `steamvr.service` だけ再起動する。起動時刻が取れない、pgrep が失敗した、更新中かを判定できない、`steamvr.service` が active でない、ときは再起動しない。成功して UI が戻れば、その WARN は正常扱いにする。`frame-video-player` など他のユニットは有効化も起動もしない。

終了コード: すべて正常なら 0、WARN があれば 1、ERROR があれば 2（過去のログは関係なし）。

## テスト

```sh
python3 tests/test_doctor.py
```
