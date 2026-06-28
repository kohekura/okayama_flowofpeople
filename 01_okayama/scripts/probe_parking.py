# -*- coding: utf-8 -*-
"""parking GeoJSON のプロパティ構造を確認する"""
import json, sys

files = {
    "parking": r"C:\Users\rd006\Documents\projectGIS_2026\00_parking\parking.geojson",
    "parking_osm_flagged": r"C:\Users\rd006\Documents\projectGIS_2026\00_parking\parking_osm_flagged.geojson",
}

for name, path in files.items():
    try:
        with open(path, encoding="utf-8") as f:
            geo = json.load(f)
        feats = geo.get("features", [])
        print(f"=== {name} ===")
        print(f"  件数: {len(feats)}")
        if feats:
            props = feats[0].get("properties", {})
            print(f"  プロパティキー: {list(props.keys())}")
            print(f"  最初の要素: {json.dumps(props, ensure_ascii=False)[:300]}")
            geom_type = feats[0].get("geometry", {}).get("type", "?")
            print(f"  ジオメトリ型: {geom_type}")
        print()
    except Exception as e:
        print(f"  ERROR: {e}")
        print()
