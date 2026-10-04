# 開発環境

## 基準環境

本リポジトリの開発環境は`sabas0ba/dotfiles`のcommit
`fc4cdecc02a6a95c81a259549d3fb9e7df18bb8f`を基準とする。次の値をdotfilesと一致させている。

- nixpkgs: `597283ad8aa0b331c788e97c4c262d58877074ef`
- Nixコンテナ: `nixos/nix:2.35.1`
- ベースイメージdigest:
  `sha256:377d4887aca98f0dfa12971c1ea6d6a625a435d8b610d4c95a436843da6fbfd1`

`flake.nix`はPythonと生成依存をnixpkgsから構成し、`flake.lock`は入力revisionとNAR hashを
固定する。依存を更新する場合は、dotfiles側の更新を確認してから独立したcommitで
`flake.nix`、`flake.lock`、`Containerfile`の整合を保つ。

## Nix

```sh
nix develop
scripts/check-env.sh
make check
```

`make check`は環境検査、STL単一連結成分を含むユニットテスト、STL・PNG・PDF生成、
決定的ZIPとSHA-256の作成を行う。MatplotlibとPythonのキャッシュはgit ignoreされた
`tmp/`以下へ置く。PDFのページ情報確認とPNGレンダリングには、同じflakeに含まれる
`pdfinfo`と`pdftoppm`を使用する。

## Container

```sh
podman build -f Containerfile -t tang-nano-9k-case-dev .
podman run --rm --network none \
  -v "$PWD:/project" -w /project \
  tang-nano-9k-case-dev make check
```

`make container-check`は上記操作の入口である。Dockerを使う場合は
`CONTAINER_ENGINE=docker`を指定する。Containerfileはビルド時にflakeをprofileへ実体化し、
実行時には入力取得を行わない。CIとRelease workflowも同じ経路を使用する。

## LCDプロファイル

LCDに依存する寸法は`tools/profiles.py`の`CaseProfile`に定義する。STL生成、断面図、レンダリング、原寸図および固定設計書は、すべて同じプロファイルから寸法を取得する。共通の機構寸法（壁厚、スナップ形状、基板保持、奥行き基準）は`tools/generate_stl.py`に置く。

座標系は背面から見た向きで、ベゼル左下を原点とし、USB-C側を下（y小）とする。データシートの外形図は通常前面から見た向きで描かれているため、表示領域とFPCの左右方向の位置は鏡像変換して登録する。

プロファイルを追加する手順は次のとおりである。

1. データシートの外形図から、LCD外形、表示領域とその位置、FPCの出る辺と範囲を`LcdModule`へ登録する。出典の版とページを注記する。
2. `CaseProfile`に本体外形、リテーナー開口、各スナップの位置、コネクタ開口、背面板スロット位置を定義する。基板端と壁内面の距離が1 mmを超える場合は、`PortBulkhead`でリアカバーのコネクタ隔壁を定義する。
3. `PROFILES`へ登録し、`tests/test_stl.py`の`EXPECTED_BOUNDS`へ各STLの外形境界を追加する。
4. `make check`で、メッシュ、組立干渉、断面位置、図面レイアウトの各テストを通す。

生成物は`build/<profile>/`と`output/<profile>/`へ出力され、`make package`は登録済みの全プロファイルをZIPへ含める。

## 成果物

生成物は`build/`、`output/`、`dist/`へ出力し、Git管理しない。Releaseへ登録する成果物は
`dist/tang-nano-9k-panel-case-r5.zip`と`dist/SHA256SUMS`である。
