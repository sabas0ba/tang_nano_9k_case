# Tang Nano 9K + 4.3-inch LCD panel case

Tang Nano 9KとSipeedが例示している4.3インチ480×272 RGB LCDを、既設パネルへ
組み込むための3Dプリントケースです。外部からUSB-C、HDMI、microSDへアクセス
できます。

## 収録STL

| ファイル | 用途 |
| --- | --- |
| `front_chassis_panel_1p5mm.stl` | 厚さ1.5 mmパネル用の前面シャーシ |
| `front_chassis_panel_2p0mm.stl` | 厚さ2.0 mmパネル用の前面シャーシ |
| `front_chassis_panel_3p0mm.stl` | 厚さ3.0 mmパネル用の前面シャーシ |
| `lcd_retainer.stl` | LCD背面の押さえ枠 |
| `rear_cover.stl` | Tang Nano 9K保持レール付き背面カバー |
| `rear_cover_clearance_20mm.stl` | 基板背面から20 mmの増設空間を持つ背面カバー |
| `rear_cover_clearance_30mm.stl` | 基板背面から30 mmの増設空間を持つ背面カバー |
| `assembly_reference_clearance_20mm.stl` | 20 mm版の組立状態確認用。印刷禁止 |
| `assembly_reference_clearance_30mm.stl` | 30 mm版の組立状態確認用。印刷禁止 |

`assembly_reference_*.stl`は、フロントシャーシ、LCD外形、LCDリテーナー、PCB外形、
リアカバーを組立座標へ配置した複数シェルの参照モデルです。部品間には意図的な接触・
スナップ掛かりがあるため、単一部品としてスライスまたは印刷しないでください。

## レンダリング・図面

`make visuals`で以下を生成します。

| ファイル | 内容 |
| --- | --- |
| `output/images/assembly_render.png` | 内部構成を示す半透明組立レンダリング |
| `output/images/exploded_render.png` | 前面から背面への分解レンダリング |
| `output/images/orthographic_three_view.png` | 前面・上面・右側面の三面図 |
| `output/pdf/tang-nano-9k-panel-case-drawing.pdf` | 三面図、レンダリング、主要寸法をまとめたPDF |
| `output/pdf/tang-nano-9k-panel-case-1to1.pdf` | A4横・原寸1:1の部品、実機照合、組立断面図（100 mm校正線付き） |
| `output/pdf/tang-nano-9k-panel-case-retention-design.pdf` | スナップ固定、荷重経路、組立・分解方法の図解設計書 |
| `docs/retention-design.md` | 固定構造、公差、検証項目を記載した日本語設計書 |

原寸PDFの5〜10ページと固定設計PDFの6〜10ページには、STLと同じCSG形状から生成した
A-A〜E-E断面を収録しています。塗りつぶし形状は印刷モデルの正確な断面、橙色破線は
実基板で確認が必要なコネクタ・実装部品エンベロープです。

原寸図は`make scale-drawing`で生成します。印刷時は「実際のサイズ / 100%」を選び、
「ページに合わせる」を無効にして、各ページの100 mm校正線を定規で確認してください。

## 基準寸法

- LCD: `105.50 × 67.15 × 2.90 mm`
- LCD表示領域: `95.04 × 53.856 mm`
- Tang Nano 9K PCB: `70.00 × 26.00 × 1.60 mm`
- 前面ベゼル: `118.00 × 81.00 mm`
- パネル角穴: `112.6 × 75.6 mm`を初期値とし、プリンタに応じて調整
- 標準版全奥行き: `27.0 mm`
- 20 mm増設空間版の全奥行き: `42.0 mm`
- 30 mm増設空間版の全奥行き: `52.0 mm`
- Tang Nano 9K取付穴: HDMI側の2穴、中心間隔`20.80 mm`

LCD外周には片側約0.5 mm、PCB外周には片側約0.5 mmの空間があります。LCD
表示窓は表示領域に対して全周0.3 mm広げています。

## 組立

1. 使用するパネル厚に対応した前面シャーシを、パネル前面から角穴へ挿入します。
2. LCDのFPC側をケース下側へ向け、前面窓に合わせます。
3. `lcd_retainer.stl`のFPC切欠きを合わせ、左右4本のフックがシャーシ受け穴へ
   掛かるまで押し込みます。リアカバーなしでリテーナーが外れないことを確認します。
4. Tang Nano 9Kの左長辺を背面カバーの固定リップ下へ差し込み、右長辺を2本の
   弾性爪へ押し込みます。部品面をLCD側、microSDソケット面を背面カバー側へ向けます。
5. 基板両端がUSB-C側とHDMI側のストッパー間に入っていることを確認します。
6. 必要に応じて、HDMI側2穴をM2x8セルフタッピングねじでボスへ固定します。
   スナップのみで使用する場合、このねじは不要です。
7. FPCを接続し、USB-C側をケース下側、HDMI側を上側に合わせて背面カバーを
   スナップ固定します。

2.54 mmピンヘッダを実装した基板は、背面カバーの保持レールと干渉する可能性が
あります。未実装基板を基準にしています。

背面カバーの左右非荷重領域には、材料使用量を抑えるため8.0 x 6.0 mmの貫通スロットを
格子状に配置しています。外周リム、PCB保持レール、M2ボスおよびコネクタストッパーの
周囲はソリッドのままです。スライサーで内部充填を指定できる場合も、保持部周辺の強度を
下げないでください。

## 推奨印刷条件

- 材料: PETG推奨。PLAを使う場合はスナップ爪の繰返し着脱を避ける
- ノズル: 0.4 mm
- 積層: 0.20 mm
- 外周: 4周
- 充填: 25%以上
- 前面シャーシ: ベゼル面をビルドプレートへ向ける
- LCD押さえ・背面カバー: 平板面をビルドプレートへ向ける
- サポート: 原則不要。ブリッジ設定を有効化

最初にパネル角穴を小さめに加工し、現物合わせで片側0.1 mmずつ拡張してください。
LCDへ局所的な荷重を掛けないよう、押さえ枠が強く嵌る場合は外周を研磨します。

## 再生成と検証

開発環境は`sabas0ba/dotfiles`のcommit
`fc4cdecc02a6a95c81a259549d3fb9e7df18bb8f`を基準とし、同じnixpkgs revisionを
`flake.lock`で固定しています。Python、図面生成ライブラリおよびフォントはflakeだけで
定義し、ホストへパッケージを追加しません。

Nixを利用する場合は、開発シェル内で環境検査と全生成・テストを実行します。

```sh
nix develop
make check
```

PodmanまたはDockerでは、同じflakeから開発profileを構築します。実行時はネットワークを
無効化しても生成・テストできます。

```sh
make container-check
# Dockerを使用する場合
make container-check CONTAINER_ENGINE=docker
```

`make package`は、STL、レンダリング、三面図、PDF設計書をまとめた決定的ZIPと
`SHA256SUMS`を`dist/`へ生成します。

環境定義と更新手順は[`docs/development.md`](docs/development.md)に記載しています。

## CI Artifact

GitHub Actionsの`Build design artifacts` workflowは、`main`へのpush、Pull Request、
手動実行時に全成果物を再生成してテストします。成功したrunのArtifactsから
`tang-nano-9k-panel-case-<commit SHA>`を取得できます。Artifactには次の2ファイルが
含まれます。

- `tang-nano-9k-panel-case-r4.zip`: STL、PNG、PDF、設計書、README
- `SHA256SUMS`: ZIPのSHA-256検証値

生成済みファイルはGit管理せず、flake、Containerfile、workflowおよび生成スクリプトを
正本とします。CIもローカルと同じコンテナ内で`make check`を実行します。

## GitHub Release

`v<major>.<minor>.<patch>`形式のtagをpushすると、`Publish release` workflowが同じ
生成・テスト・パッケージ処理を実行し、GitHub Releaseを作成します。

```sh
git tag -a v1.0.0 -m "v1.0.0"
git push origin v1.0.0
```

Release Assetsには`dist/`から次のファイルが登録されます。

- `tang-nano-9k-panel-case-r4.zip`
- `SHA256SUMS`

`v1.0.0-rc.1`のようにハイフンを含むtagはpre-releaseとして作成されます。同じtagの
workflowを再実行した場合は、既存Releaseの同名assetsを再生成結果で更新します。

テストは全STLについて、バイナリ形式、境界寸法、有限座標、正の体積、全エッジが
ちょうど2面に共有される閉じた2-manifoldメッシュであり、単一の連結成分だけを持つことを
確認します。さらに、
B-Bが基板固定リップと弾性爪、C-CがLCDフックと受け穴、D-DがmicroSD開口、
E-EがHDMI側2本のM2ボスを実際に通過することを座標で検証します。

## 出典と前提

- [Sipeed Tang Nano 9K公式ページ](https://wiki.sipeed.com/hardware/en/tang/Tang-Nano-9K/Nano-9K.html): HDMI、RGB LCD、SPI LCD、TFカード、USB-C
- [Sipeed Tang Nano 9K公式寸法図](https://dl.sipeed.com/fileList/TANG/Nano%209K/4_Dimensional_drawing/Tang_Nano_9K_3672_size.pdf): PCB `70.0 × 26.0 mm`
- [Sipeed配布LCD資料 HT043DA-V.0](https://dl.sipeed.com/Accessories/LCD/HT043DA-V.0-%E5%8D%95%E5%B1%8F%E6%9B%B4%E6%96%B0%E7%89%88%E6%9C%AC.pdf): 外形、表示領域、FPC位置

LCDは公式資料上で互換例が複数あるため、本設計は4.3インチ480×272モデルを対象に
しています。5インチまたは1.14インチLCDには適合しません。量産前にLCD外形、FPC
位置、Tang Nano 9Kのコネクタ高さを実測してください。
