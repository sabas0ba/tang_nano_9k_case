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

## 成果物

生成物は`build/`、`output/`、`dist/`へ出力し、Git管理しない。Releaseへ登録する成果物は
`dist/tang-nano-9k-panel-case-r4.zip`と`dist/SHA256SUMS`である。
