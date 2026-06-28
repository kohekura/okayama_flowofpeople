# 岡山市まちなかOSM分析マップ 引き継ぎメモ

最終更新: 2026-06-26

## 主要ファイル

- 地図HTML: `C:\Users\rd006\Documents\projectGIS_2026\01_personspace\okayama_osm_all.html`
- 軽量版HTML: `C:\Users\rd006\Documents\projectGIS_2026\01_personspace\okayama_osm_light.html`
- 生成スクリプト: `C:\Users\rd006\Documents\projectGIS_2026\01_personspace\build_osm_overview.py`
- OSM追加キャッシュ: `C:\Users\rd006\Documents\projectGIS_2026\01_personspace\_osm_extra_layers.json`
- PLATEAU建物年代: `C:\Users\rd006\Documents\projectGIS_2026\01_personspace\_plateau_building_age.geojson`
- PLATEAU土地利用軽量版: `C:\Users\rd006\Documents\projectGIS_2026\01_personspace\_plateau_luse_core.geojson`
- PLATEAU土地利用抽出: `C:\Users\rd006\Documents\projectGIS_2026\01_personspace\extract_plateau_luse_core.py`
- 人流一次分析: `C:\Users\rd006\Documents\projectGIS_2026\01_personspace\人流と都市条件_一次分析.md`
- 人流重点考察: `C:\Users\rd006\Documents\projectGIS_2026\01_personspace\人流重点エリア_比較考察.md`
- 人流昼夜比較: `C:\Users\rd006\Documents\projectGIS_2026\01_personspace\人流昼夜比較_要点.md`
- 人流要因分析: `C:\Users\rd006\Documents\projectGIS_2026\01_personspace\人流要因分析_昼夜別.md`
- 人流要因JSON: `C:\Users\rd006\Documents\projectGIS_2026\01_personspace\_flow_driver_context.json`
- 人流要因注釈GeoJSON: `C:\Users\rd006\Documents\projectGIS_2026\01_personspace\_flow_driver_notes.geojson`
- 人流昼夜注釈GeoJSON: `C:\Users\rd006\Documents\projectGIS_2026\01_personspace\_flow_day_night_notes.geojson`
- 都心細密人流ベースGeoJSON: `C:\Users\rd006\Documents\projectGIS_2026\01_personspace\_toshin_fine_flow_base.geojson`
- 地図確認手順: `C:\Users\rd006\Documents\projectGIS_2026\01_personspace\地図確認チェックリスト.md`
- 人流条件集計JSON: `C:\Users\rd006\Documents\projectGIS_2026\01_personspace\_flow_context_summary.json`

## 現在の方針

- Codex上限・HTML重量を避けるため、大きいデータはそのままHTMLへ追加しない。
- 軽量版は `python build_osm_overview.py --light` で生成する。
- 軽量版では建物年代とPLATEAU低未利用地候補をHTMLへ埋め込まない。
- PLATEAU土地利用は、まちづくり・人流分析に割り切って商業用地だけを `_plateau_luse_core.geojson` に抽出して使う。
- 駐車場はOSMレイヤーを優先し、PLATEAU低未利用地・平面駐車場は軽量版では外す。
- 軽量版には「全レイヤーOFF」ボタンを追加済み。背景地図だけ残して主題レイヤーを消せる。
- 人流一次分析は、代表点から約500m圏で商業用地・歩行者空間・OSM駐車場・公共交通を集計している。
- 13時/20時の昼夜比較は個別エリア時間帯別データ、細密ポリゴンは2023年平均の人流地形として扱う。
- 今後の分析は「まちなかの人流がある場所」に絞る。
- PLATEAU土地利用は、フル投入ではなく商業用地など目的に直結する分類だけを抽出して使う。
- 重いレイヤーは初期OFF。
- なるべく `build_osm_overview.py` を編集し、HTML全文の読み込みは避ける。

## 現在入っている主なレイヤー

初期ON寄り:

- 航空写真
- 公園・緑地ポリゴン
- 歩行者道路・歩道ポリゴン
- 観光・文化施設
- 大規模商業施設
- 商店街の通り
- 自転車レーン
- シェアサイクルポート
- 路面電車軌道・電停
- 鉄道駅
- OSM駐車場ポリゴン

初期OFF寄り:

- 詳細OSM点
- バス停・バス路線
- 電停・駅・高頻度バス停の徒歩圏
- 人流
- 人流タイプ分類
- 人流上位エリア分析範囲
- 建物年代
- PLATEAU低未利用地候補
- 密度メッシュ

## 人流データの注意

- 元データ: `C:\Users\rd006\Downloads\zinryu_okayama\kobetsuarea_time.csv`
- CSVはCP932で読める。
- CSVにはエリア形状がなく、地図では町名・地区名に合わせた代表点で表示している。
- 岡山駅エリアなどは駅周辺に補正済み。
- 桑田町エリアはCSV上でも人流値が高い。表示バグというより、エリア定義・周辺用途の確認が必要。
- 今後は「人流上位エリア分析範囲（約500m）」を使い、その周辺だけPLATEAU土地利用等を追加するのが安全。

## 次にやるとよいこと

1. PLATEAU土地利用は有用だが重い。必要になった場合のみ入れる。
2. PLATEAU土地利用を扱う前には、必ずユーザーに確認する。
3. 入れる場合も、フル投入ではなく「人流上位エリア周辺」や「中心部の主要分類だけ」に限定する。
4. 人流上位エリアごとに、徒歩圏・商店街・駐車場・低未利用地・建物年代を比較する。
5. 追加データは、軽い集計レイヤーまたは小さい補助レイヤーを優先する。
6. 必要なら分析結果はHTMLに直接大きなポリゴンで入れず、小さな集計JSONや別GeoJSONに分ける。

## 上限回避ルール

- `okayama_osm_all.html` は大きいので、必要時以外は全文表示しない。
- 検索は `Select-String` や小範囲読み取りで済ませる。
- PLATEAU GMLは巨大なので、対象範囲を先に決めてから抽出する。
- 1回の作業で追加するレイヤーは少数にする。
- 節目ごとにこのメモを更新する。

## 2026-06-27 追記: 人流要因メモを軽量版地図に追加

- `okayama_osm_light.html` に「分析メモ > 人流要因メモ」レイヤーを追加済み。
- データ元は `_flow_driver_notes.geojson`。約6KBの小さな注釈GeoJSONだけをHTMLに埋め込むため、軽量版のサイズ増加はごく小さい。
- 表示内容は、13時・20時の上位人流エリアごとの順位、推計人流、主な要因、短い考察。
- ポップアップで「大規模商業」「スーパー・日常買物」「飲食集積」「夜間飲食」「カフェ」「業務・オフィス」「商店街・アーケード」「駐車場アクセス」などを確認できる。
- 再生成コマンドは `python 01_personspace/build_osm_overview.py --light`。
