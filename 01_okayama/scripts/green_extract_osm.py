# -*- coding: utf-8 -*-
"""
green_extract_osm.py

目的：
  OSM Overpass APIから、人中心空間（緑）の構成要素を一括取得して面化し、
  folium地図に描画する。

  対象タグ：
    - leisure=park    （公園）
    - leisure=garden  （緑地・庭園）
    - place=square    （広場）
    - highway=pedestrian （歩行者専用道路。線データなので一律幅でバッファして面化）
        - covered=arcade が付くものはアーケード商店街として別扱い（バッファ幅を太めに）
    - highway=footway （歩道・遊歩道。線データをバッファして面化）
    - highway=path    （小道・公園内通路等。線データをバッファして面化）

  公園・広場（park/garden/square）はOSM上、ポリゴン（way closed / relation）として
  登録されていることが多いのでそのまま面として使う。
  歩行者専用道路（pedestrian）・歩道（footway）・小道（path）は線として登録されている
  ことが多いので、一律の仮定幅でバッファして面にする。

  墓地（landuse=cemetery）・運動場（leisure=pitch等）は対象タグに含めていないため、
  この時点で自然に除外される。

検証：
  既存の green_plateau_217.geojson（PLATEAU公共空地、墓園・運動場を含む全部入り）の
  合計面積と、ここで取得したOSM緑面積を比較表示する。
  OSMの面積が217よりかなり小さい場合は、公園・広場の登録漏れを疑うこと
  （駐車場分析で起きた「小規模コインパーキングの登録漏れ」と同種の問題）。

前提：
  requests, folium がインストール済みであること（前回の駐車場分析と同じ環境）。
  ネットワーク接続があること（Overpass APIに問い合わせるため）。

使い方：
  python green_extract_osm.py
"""

import os
import json
import math
import time

import requests
import folium

# ---- 設定 ---------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 岡山市まちなか周辺のバウンディングボックス（south, west, north, east）
# 駐車場分析プロジェクトと同じ範囲を想定。違う場合はここを調整してください。
BBOX = (34.62, 133.89, 34.69, 133.95)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
CACHE_PATH = os.path.join(SCRIPT_DIR, "_overpass_green_full_cache.json")
USE_CACHE = True

# 線データを面化する際の片側バッファ幅[m]（全幅 = 値 × 2）
WIDTH_PEDESTRIAN_M = 4.0   # 歩行者専用道路：全幅 約8m
WIDTH_ARCADE_M = 6.0       # アーケード商店街：全幅 約12m（表町・奉還町等）
WIDTH_FOOTWAY_M = 1.5      # 歩道・遊歩道：全幅 約3m
WIDTH_PATH_M = 1.0         # 小道・公園内通路：全幅 約2m

PLATEAU_217_GEOJSON = os.path.join(SCRIPT_DIR, "green_plateau_217.geojson")

OUT_HTML = os.path.join(SCRIPT_DIR, "green_osm.html")
OUT_GEOJSON = os.path.join(SCRIPT_DIR, "green_osm.geojson")

CENTER_LAT, CENTER_LON = 34.6551, 133.9195


# ---- Overpass取得 --------------------------------------------------------
def build_query(bbox):
    s, w, n, e = bbox
    bbox_str = f"{s},{w},{n},{e}"
    # way/relationの面データ（park, garden, square）と、線データ（pedestrian）を一括取得
    query = f"""
    [out:json][timeout:90];
    (
      way["leisure"="park"]({bbox_str});
      relation["leisure"="park"]({bbox_str});
      way["leisure"="garden"]({bbox_str});
      relation["leisure"="garden"]({bbox_str});
      way["place"="square"]({bbox_str});
      relation["place"="square"]({bbox_str});
      way["highway"="pedestrian"]({bbox_str});
      way["highway"="footway"]({bbox_str});
      way["highway"="path"]({bbox_str});
    );
    out body;
    >;
    out skel qt;
    """
    return query


def fetch_overpass(bbox):
    if USE_CACHE and os.path.exists(CACHE_PATH):
        print(f"[キャッシュ使用] {CACHE_PATH}")
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    query = build_query(bbox)
    print("Overpass APIに問い合わせ中...")
    headers = {"User-Agent": "GIS_personspace_study/1.0 (educational)"}
    resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=90, headers=headers)
    resp.raise_for_status()
    data = resp.json()

    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    print(f"取得完了。キャッシュに保存: {CACHE_PATH}")
    return data


# ---- 線のバッファ処理（簡易・緯度経度ベース） -----------------------------
def meters_to_deg_lat(m):
    return m / 111_000.0


def meters_to_deg_lon(m, at_lat):
    return m / (111_000.0 * math.cos(math.radians(at_lat)))


def buffer_line_to_polygon(coords, width_m):
    """
    coords: [(lat, lon), ...] の線
    width_m: 片側バッファ幅[m]
    戻り値: [(lat, lon), ...] のポリゴン（線の両側にオフセットした帯）

    簡易実装：各セグメントの法線方向にオフセットし、往路（左側）と
    復路（右側を逆順）をつなげて帯状ポリゴンを作る。
    厳密なマイター処理はせず、可視化目的の近似として扱う。
    """
    if len(coords) < 2:
        return None

    left_side = []
    right_side = []

    for i in range(len(coords) - 1):
        lat1, lon1 = coords[i]
        lat2, lon2 = coords[i + 1]

        # 経度方向はcos(lat)で補正してメートル近似のベクトルにする
        mid_lat = (lat1 + lat2) / 2
        dx = (lon2 - lon1) * math.cos(math.radians(mid_lat))
        dy = (lat2 - lat1)
        length = math.hypot(dx, dy)
        if length == 0:
            continue

        # 法線ベクトル（単位ベクトルを90度回転）
        nx = -dy / length
        ny = dx / length

        off_lat_val = meters_to_deg_lat(width_m) * ny
        off_lon_val = meters_to_deg_lon(width_m, mid_lat) * nx

        left_side.append((lat1 + off_lat_val, lon1 + off_lon_val))
        right_side.append((lat1 - off_lat_val, lon1 - off_lon_val))

        if i == len(coords) - 2:
            left_side.append((lat2 + off_lat_val, lon2 + off_lon_val))
            right_side.append((lat2 - off_lat_val, lon2 - off_lon_val))

    polygon = left_side + right_side[::-1]
    if len(polygon) < 3:
        return None
    return polygon


# ---- OSM要素のパース ------------------------------------------------------
def parse_osm_elements(data):
    """
    Overpassの結果から、ノード座標を引いてway/relationを実座標リストに変換する。
    戻り値: {
      "park": [polygon(coords), ...],
      "garden": [...],
      "square": [...],
      "pedestrian": [{"coords": [...], "is_arcade": bool}, ...],
    }
    """
    nodes = {}
    ways = []

    for el in data.get("elements", []):
        if el["type"] == "node":
            nodes[el["id"]] = (el["lat"], el["lon"])

    for el in data.get("elements", []):
        if el["type"] == "way":
            coords = [nodes[nid] for nid in el.get("nodes", []) if nid in nodes]
            if len(coords) >= 2:
                ways.append({"tags": el.get("tags", {}), "coords": coords})

    result = {"park": [], "garden": [], "square": [], "pedestrian": [], "footway": [], "path": []}

    for w in ways:
        tags = w["tags"]
        coords = w["coords"]
        closed = len(coords) >= 3 and coords[0] == coords[-1]

        if tags.get("leisure") == "park" and closed:
            result["park"].append(coords)
        elif tags.get("leisure") == "garden" and closed:
            result["garden"].append(coords)
        elif tags.get("place") == "square" and closed:
            result["square"].append(coords)
        elif tags.get("highway") == "pedestrian":
            is_arcade = tags.get("covered") == "arcade"
            result["pedestrian"].append({
                "coords": coords,
                "is_arcade": is_arcade,
                "name": tags.get("name", ""),
            })
        elif tags.get("highway") == "footway":
            result["footway"].append(coords)
        elif tags.get("highway") == "path":
            result["path"].append(coords)

    return result


# ---- 面積計算（簡易：緯度経度→メートル近似のshoelace） ---------------------
def polygon_area_m2(coords):
    if len(coords) < 3:
        return 0.0
    lat0 = coords[0][0]
    pts = []
    for lat, lon in coords:
        x = (lon - coords[0][1]) * 111_000.0 * math.cos(math.radians(lat0))
        y = (lat - lat0) * 111_000.0
        pts.append((x, y))
    area = 0.0
    for i in range(len(pts) - 1):
        x1, y1 = pts[i]
        x2, y2 = pts[i + 1]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0


# ---- 地図とGeoJSON出力 ----------------------------------------------------
def build_outputs(parsed):
    m = folium.Map(location=[CENTER_LAT, CENTER_LON], zoom_start=14, tiles="cartodbpositron")
    features = []
    total_area = 0.0

    def add_polygon(coords, category, name=""):
        nonlocal total_area
        folium.Polygon(
            locations=coords,
            color="#1D9E75",
            weight=1,
            fill=True,
            fill_color="#1D9E75",
            fill_opacity=0.5,
            tooltip=f"{category} {name}".strip(),
        ).add_to(m)
        area = polygon_area_m2(coords)
        total_area += area
        ring = [[lon, lat] for (lat, lon) in coords]
        if ring[0] != ring[-1]:
            ring.append(ring[0])
        features.append({
            "type": "Feature",
            "properties": {"category": category, "area_m2": round(area, 1), "name": name},
            "geometry": {"type": "Polygon", "coordinates": [ring]},
        })

    for coords in parsed["park"]:
        add_polygon(coords, "park")
    for coords in parsed["garden"]:
        add_polygon(coords, "garden")
    for coords in parsed["square"]:
        add_polygon(coords, "square")

    for item in parsed["pedestrian"]:
        width = WIDTH_ARCADE_M if item["is_arcade"] else WIDTH_PEDESTRIAN_M
        poly = buffer_line_to_polygon(item["coords"], width)
        if poly:
            category = "arcade" if item["is_arcade"] else "pedestrian"
            add_polygon(poly, category, name=item.get("name", ""))

    for coords in parsed["footway"]:
        poly = buffer_line_to_polygon(coords, WIDTH_FOOTWAY_M)
        if poly:
            add_polygon(poly, "footway")

    for coords in parsed["path"]:
        poly = buffer_line_to_polygon(coords, WIDTH_PATH_M)
        if poly:
            add_polygon(poly, "path")

    m.save(OUT_HTML)
    with open(OUT_GEOJSON, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": features}, f, ensure_ascii=False)

    print(f"地図を保存しました: {OUT_HTML}")
    print(f"GeoJSONを保存しました: {OUT_GEOJSON}")
    print()
    print(f"OSM緑面積 合計: {total_area:,.0f} m2  ({total_area/10000:.2f} ha)")

    return total_area


def compare_with_plateau_217(osm_total_area):
    if not os.path.exists(PLATEAU_217_GEOJSON):
        print("(参考比較スキップ：green_plateau_217.geojson が見つかりません)")
        return

    with open(PLATEAU_217_GEOJSON, "r", encoding="utf-8") as f:
        geo = json.load(f)

    total_217 = 0.0
    for feat in geo["features"]:
        ring = feat["geometry"]["coordinates"][0]
        coords = [(lat, lon) for lon, lat in ring]
        total_217 += polygon_area_m2(coords)

    print()
    print("=== PLATEAU 217（公園・緑地・広場・運動場・墓園 全部入り）との比較 ===")
    print(f"  PLATEAU 217 合計面積: {total_217:,.0f} m2 ({total_217/10000:.2f} ha)")
    print(f"  OSM緑 合計面積      : {osm_total_area:,.0f} m2 ({osm_total_area/10000:.2f} ha)")
    if total_217 > 0:
        ratio = osm_total_area / total_217 * 100
        print(f"  OSM / PLATEAU217 比 : {ratio:.1f}%")
        if ratio < 50:
            print("  [注意] OSMの方がかなり小さいです。公園・広場の登録漏れがある可能性があります。")
            print("         （217には運動場・墓園も含まれるため、ある程度の差は当然出ます）")


def main():
    data = fetch_overpass(BBOX)
    parsed = parse_osm_elements(data)

    print(f"取得件数: park={len(parsed['park'])}, garden={len(parsed['garden'])}, "
          f"square={len(parsed['square'])}, pedestrian={len(parsed['pedestrian'])}, "
          f"footway={len(parsed['footway'])}, path={len(parsed['path'])}")
    n_arcade = sum(1 for p in parsed["pedestrian"] if p["is_arcade"])
    print(f"  うちアーケード(covered=arcade): {n_arcade}件")
    print()

    osm_total_area = build_outputs(parsed)
    compare_with_plateau_217(osm_total_area)


if __name__ == "__main__":
    main()
