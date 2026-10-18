#!/bin/bash
# SPDX-License-Identifier: MIT
# frame-doctor を Steam Frame に入れる・外す。Frame の Konsole で、ふつうのユーザーで実行する（sudo 不要）。
#
#   curl -fsSL https://raw.githubusercontent.com/cympfh/frame-doctor/main/install.sh | bash
#   curl -fsSL https://raw.githubusercontent.com/cympfh/frame-doctor/main/install.sh | bash -s -- --uninstall
#
# 入れるのは ~/.local/bin/frame-doctor の 1 ファイルだけ。外すときは消さずに ~/.local/share/frame-doctor-uninstalled/<日時>/ に移す。
set -euo pipefail

name=frame-doctor
ref=${FRAME_TOOL_REF:-main}
bin="$HOME/.local/bin/$name"

[[ "$(id -u)" != 0 ]] || { echo "root では動かしません。sudo なしで実行してください。" >&2; exit 1; }

if [[ "${1:-}" == "--uninstall" ]]; then
    aside="$HOME/.local/share/$name-uninstalled/$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$aside"
    if [[ -e "$bin" ]]; then mv "$bin" "$aside/"; fi
    echo "$name を外しました（$aside に移してあります。要らなければ消してOK）。"
    exit 0
fi

mkdir -p "$(dirname "$bin")"
here=""
if [[ -n "${BASH_SOURCE[0]:-}" && -f "${BASH_SOURCE[0]}" ]]; then
    here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi
if [[ -n "$here" && -f "$here/$name" ]]; then
    install -m755 "$here/$name" "$bin.new"
else
    echo "ダウンロード中: https://github.com/cympfh/$name ($ref)"
    curl -fsSL "https://raw.githubusercontent.com/cympfh/$name/$ref/$name" -o "$bin.new"
    chmod 755 "$bin.new"
fi
mv -f "$bin.new" "$bin"

echo
echo "frame-doctor を入れました。Konsole で frame-doctor と打つとチェックします。"
case ":$PATH:" in *":$HOME/.local/bin:"*) ;; *) echo "（見つからないときは ~/.local/bin/frame-doctor で動かしてください）" ;; esac
