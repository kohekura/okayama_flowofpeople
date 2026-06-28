# projectGIS_2026 フォルダ構成（2026-06-28 更新）

## 全体構造

```
projectGIS_2026/
├── 01_okayama/          岡山市中心市街地 人流GIS分析
├── 02_geinintasaku/     芸人探索MAP（Next.jsアプリ）
└── 99_sonota/           その他・旧プロジェクト
```

---

## 01_okayama/

岡山市中心市街地の人流分析プロジェクト。Pythonスクリプト＋Leaflet地図。

```
01_okayama/
├── okayama_osm_light.html    ★ 正規地図（これが正）
├── okayama_analysis_story.html  分析総括HTML
│
├── data/
│   ├── osm_cache/   Overpass APIキャッシュ（_overpass_*.json 6件）
│   ├── plateau/     PLATEAUデータ（建物・土地利用 geojson）
│   ├── flow/        人流系データ（_flow_*.json/geojson 7件）
│   └── analysis/    分析中間データ（_cycle*.json 等 15件）
│
├── scripts/         Pythonスクリプト（build_osm_overview.py 等 16件）
├── charts/          グラフPNG（cycle2_sensitivity.png 等 10件）
├── reports/         レポート（DOCX 5件・MD 9件）
├── _archive/        旧HTML地図（okayama_osm_all.html 等 9件）
└── _runners/        バッチ・VBS・ログ（15件）
```

**重要ファイル:**
- 正規地図: `01_okayama/okayama_osm_light.html`
- 人流CSV（元データ）: `../Downloads/zinryu_okayama/kobetsuarea_time.csv`（別フォルダ）
- GTFSデータ: `../Downloads/0kayama_GTFS/`（別フォルダ）

---

## 02_geinintasaku/

芸人探索MAP。「芸人の行きつけ・通った店を地図で楽しむ」Next.jsアプリ。

```
02_geinintasaku/
├── app/             Next.js ページ（page.tsx 等）
├── components/      Reactコンポーネント（MapView.tsx, PinCard.tsx 等）
├── lib/             型定義（types.ts, categoryEmoji.ts）
│
├── public/data/
│   ├── places.geojson   ★ 店舗データ（現在65件）← 主な編集対象
│   ├── areas.json       エリア定義
│   └── heat.geojson     ヒートマップ用
│
├── scripts/
│   ├── add/   add-*.cjs（データ追加スクリプト 8件）
│   └── util/  apply, enrich, raise 等（ユーティリティ 6件）
│
└── docs/
    ├── research-playbook.md   調査基準・採用条件
    └── notes/
        ├── research-notes-2026-06-27.md  前回調査メモ
        └── research-notes-2026-06-28.md  最新調査メモ（追加候補7件）
```

**重要ファイル:**
- メインデータ: `02_geinintasaku/public/data/places.geojson`
- 調査基準: `02_geinintasaku/docs/research-playbook.md`
- 開発起動: `cd 02_geinintasaku && npm run dev`（※移動前はルートから実行していた）

---

## 99_sonota/

完成・休止中のサブプロジェクト。

```
99_sonota/
├── 00_parking/      岡山市駐車場GIS分析（Python＋Leaflet、完了済み）
└── plateau_citygml/ PLATEAU CityGML 生データ（大容量）
```

---

## 変更履歴（2026-06-28）

- `01_personspace/` → `01_okayama/` にリネーム
- 芸人探索MAPのNext.jsアプリ一式をルートから `02_geinintasaku/` に移動
- `00_parking/`・`plateau_citygml/` を `99_sonota/` に移動
- `02_geinintasaku/scripts/` を `add/` と `util/` に整理
- `02_geinintasaku/docs/notes/` フォルダ作成、リサーチノートを集約
