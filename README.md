# frame-doctor

Steam Frame の **調子を 1 コマンドで点検** します。
「なんだか重い」「アプリが動いていない気がする」ときに打つと、**いまの状態** を確かめて 1 行ずつ教えてくれます。見るだけで、何も変えません。

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

## アンインストール

```sh
curl -fsSL https://raw.githubusercontent.com/cympfh/frame-doctor/main/install.sh | bash -s -- --uninstall
```

外したファイルは消さずに `~/.local/share/frame-doctor-uninstalled/` へ移します。

<details>
<summary>くわしい情報（開発者向け）</summary>

- `frame-doctor --verbose` で各項目のくわしい値、`--history` で過去 24 時間のログのエラー（参考。今の状態とは関係ありません）、`--json` で JSON
- 終了コード: すべて OK なら 0、WARN があれば 1、ERROR があれば 2
- 何を見ているかは [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)

</details>

ほかの Steam Frame 用ツール: [frame-tools](https://github.com/cympfh/frame-tools)
