# frame-doctor

Steam Frame の **調子を 1 コマンドで点検** します。
「なんだか重い」「アプリが動いていない気がする」ときに打つと、温度・電池・空き容量・SteamVR・入れたツールの状態をまとめて教えてくれます。見るだけで、何も変えません。

```
■ 本体
  [ OK  ] 温度: SoC 最高 55.5 °C（cpu1-thermal）、GPU 51.8 °C
  [ OK  ] 熱による制限: 制限なし（CPU・GPU とも最大クロックまで使えます）
  [ OK  ] バッテリー: 90%（充電中）、27.1 °C
■ ツール
  [ OK  ] frameeyeosc: 0.7.10、動作中、自動起動オン
  [WARN ] frame-mic-tuner: 0.3.1、動作中、自動起動オン。古い版のまま動いています（終了するか SteamVR を再起動すると新しい版になります）
■ マイク
  [INFO ] エコー除去: オン
まとめ: OK 20 / INFO 5 / WARN 1 / ERROR 0
```

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

- `frame-doctor --json` で JSON、`--no-color` で色なし、`--since 6h` でログを見る範囲を変えられます
- 終了コード: すべて OK なら 0、WARN があれば 1、ERROR があれば 2
- 何を見ているかは [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)

</details>

ほかの Steam Frame 用ツール: [frame-tools](https://github.com/cympfh/frame-tools)
