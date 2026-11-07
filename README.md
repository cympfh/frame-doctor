# frame-doctor

Steam Frame の **調子を 1 コマンドで点検** します。
「なんだか重い」「アプリが動いていない気がする」ときに打つと、**いまの状態** を確かめて 1 行ずつ教えてくれます。既定は見るだけで、何も変えません。

```
温度：正常
バッテリー：正常
SteamVR：正常
frameeyeosc：正常
視線データ：正常
マイク：正常
ネット：正常
```

調子が悪いところは「視線データ：警告（目のデータが読めません）」のように理由つきで出ます。
起動したときの一時的なエラーなど、もう直っている過去のことは出しません。

## インストール

Frame の Konsole に貼り付けて Enter:

```sh
curl -fsSL https://raw.githubusercontent.com/cympfh/frame-doctor/main/install.sh | bash
```

## 使い方

```sh
frame-doctor
```

（見つからないと言われたら `~/.local/bin/frame-doctor`）

画面が真っ紺で操作できないときは、SteamVR の項目が警告になります。直すときだけ:

```sh
frame-doctor --fix
```

SteamVR だけ再起動します（本体は再起動しません。Steam と gamescope も一緒に立ち上がり直すことがあります）。Steam や SteamOS の更新中は実行しません。止めてある動画プレイヤーなどは勝手に起動しません。

## アンインストール

```sh
curl -fsSL https://raw.githubusercontent.com/cympfh/frame-doctor/main/install.sh | bash -s -- --uninstall
```

外したファイルは消さずに `~/.local/share/frame-doctor-uninstalled/` へ移します。

<details>
<summary>くわしい情報（開発者向け）</summary>

- `frame-doctor --verbose` で各項目のくわしい値、`--history` で過去 24 時間のログのエラー（参考。今の状態とは関係ありません）、`--json` で JSON、`--fix` で画面 UI が落ちていたときだけ SteamVR を再起動
- 終了コード: すべて OK なら 0、WARN があれば 1、ERROR があれば 2
- 何を見ているかは [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)

</details>

ほかの Steam Frame 用ツール: [frame-tools](https://github.com/cympfh/frame-tools)
