# -*- coding: utf-8 -*-
"""
build_vitality_map.py

「賑わい軸」地図の生成。

方針:
  - Overpass から shop=* ノード + 道路 way を取得
  - 各道路重心から 100m 以内の shop 数でティア分類
      Tier S (>=8店): 濃水色 opacity 0.70
      Tier A (>=4店): 中水色 opacity 0.50
      Tier B (>=2店): 薄水色 opacity 0.30
  - highway=pedestrian/arcade は無条件で Tier S
  - 片側 4m バッファで帯状ポリゴン化（green_extract_osm.py と同じ方式）
  - 既存 green_osm.geojson（緑地）を背景に、駐車場と重ねて表示
  - 地図 / 航空写真切り替え対応

出力: vitality_map.html（01_personspace）
"""

import os, json, math, requests, folium

# ---- 設定 -----------------------------------------------------------------
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
PARKING_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, r"..\00_parking"))

BBOX         = (34.62, 133.89, 34.69, 133.95)
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
CACHE_PATH   = os.path.join(SCRIPT_DIR, "_overpass_vitality_cache.json")
USE_CACHE    = True

GREEN_GEOJSON   = os.path.join(SCRIPT_DIR, "green_osm.geojson")
PARKING_GEOJSON = os.path.join(PARKING_DIR, "parking.geojson")
OUT_HTML        = os.path.join(SCRIPT_DIR, "vitality_map.html")

CENTER_LAT, CENTER_LON = 34.6551, 133.9195

# 店密度ティア閾値（各道路重心 100m 以内の shop 数）
TIER_S_MIN = 8
TIER_A_MIN = 4
TIER_B_MIN = 2
SHOP_SEARCH_DEG = 0.001   # ≈100m

# 色・太さ（水色グラデーション）
COLOR_VIT   = "#0096C7"
OPACITY_S   = 0.70
OPACITY_A   = 0.50
OPACITY_B   = 0.30
WEIGHT_S    = 2
WEIGHT_AB   = 1
BUFFER_M    = 4.0   # 片側バッファ幅 [m]

# 緑地・駐車場の色（既存レイヤーの色）
COLOR_GREEN = "#1D9E75"
COLOR_PARK  = "#7F8C8D"


# ---- Overpass 取得 --------------------------------------------------------
def build_query(bbox):
    s, w, n, e = bbox
    bb = f"{s},{w},{n},{e}"
    return f"""
[out:json][timeout:120];
(
  node["shop"]({bb});
  way["highway"~"^(primary|secondary|tertiary|residential|unclassified|pedestrian|living_street)$"]({bb});
);
out body;
>;
out skel qt;
"""

def fetch_overpass():
    if USE_CACHE and os.path.exists(CACHE_PATH):
        print(f"[キャッシュ使用] {CACHE_PATH}")
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    print("Overpass API に問い合わせ中（shop + 道路）...")
    headers = {"User-Agent": "GIS_personspace_study/1.0 (educational)"}
    resp = requests.post(OVERPASS_URL, data={"data": build_query(BBOX)},
                         timeout=120, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    print(f"  取得完了 → {CACHE_PATH}")
    return data


# ---- パース ---------------------------------------------------------------
def parse(data):
    nodes     = {}
    shop_locs = []
    ways      = []

    for el in data.get("elements", []):
        if el["type"] == "node":
            nodes[el["id"]] = (el["lat"], el["lon"])
            if "shop" in el.get("tags", {}):
                shop_locs.append((el["lat"], el["lon"]))

    for el in data.get("elements", []):
        if el["type"] == "way":
            coords = [nodes[nid] for nid in el.get("nodes", []) if nid in nodes]
            if len(coords) >= 2:
                ways.append({"tags": el.get("tags", {}), "coords": coords})

    return shop_locs, ways


# ---- 密度計算 -------------------------------------------------------------
def centroid(coords):
    lat = sum(c[0] for c in coords) / len(coords)
    lon = sum(c[1] for c in coords) / len(coords)
    return lat, lon

def shop_count_near(coords, shops, deg):
    clat, clon = centroid(coords)
    cnt = 0
    for slat, slon in shops:
        if (abs(slat - clat) <= deg and abs(slon - clon) <= deg):
            cnt += 1
    return cnt


# ---- バッファ（green_extract_osm.py と同じ方式）--------------------------
def meters_to_deg_lat(m):
    return m / 111_000.0

def meters_to_deg_lon(m, lat):
    return m / (111_000.0 * math.cos(math.radians(lat)))

def buffer_line(coords, width_m):
    if len(coords) < 2:
        return None
    left, right = [], []
    for i in range(len(coords) - 1):
        lat1, lon1 = coords[i]
        lat2, lon2 = coords[i + 1]
        mid = (lat1 + lat2) / 2
        dx = (lon2 - lon1) * math.cos(math.radians(mid))
        dy = lat2 - lat1
        L  = math.hypot(dx, dy)
        if L == 0:
            continue
        nx = -dy / L
        ny =  dx / L
        dlat = meters_to_deg_lat(width_m) * ny
        dlon = meters_to_deg_lon(width_m, mid) * nx
        left.append( (lat1 + dlat, lon1 + dlon))
        right.append((lat1 - dlat, lon1 - dlon))
        if i == len(coords) - 2:
            left.append( (lat2 + dlat, lon2 + dlon))
            right.append((lat2 - dlat, lon2 - dlon))
    poly = left + right[::-1]
    return poly if len(poly) >= 3 else None


# ---- GeoJSON ユーティリティ -----------------------------------------------
def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def get_rings(feat):
    geom  = feat.get("geometry") or {}
    gtype = geom.get("type", "")
    if gtype == "Polygon":
        return geom["coordinates"][:1]
    if gtype == "MultiPolygon":
        return [p[0] for p in geom["coordinates"]]
    return []


# ---- 凡例 HTML ------------------------------------------------------------
LEGEND_HTML = """
<div style="position:fixed;bottom:30px;left:30px;z-index:1000;
  background:rgba(255,255,255,0.93);border-radius:8px;padding:10px 14px;
  font-family:sans-serif;font-size:12px;line-height:1.8;
  box-shadow:0 1px 5px rgba(0,0,0,0.2);min-width:210px;">
  <div style="font-weight:bold;font-size:13px;margin-bottom:4px;">凡例</div>
  <div><span style="display:inline-block;width:14px;height:14px;
    background:#0096C7;opacity:0.9;border-radius:2px;vertical-align:middle;
    margin-right:6px;"></span>賑わい軸 S（密集 ≥8店）</div>
  <div><span style="display:inline-block;width:14px;height:14px;
    background:#0096C7;opacity:0.6;border-radius:2px;vertical-align:middle;
    margin-right:6px;"></span>賑わい軸 A（≥4店）</div>
  <div><span style="display:inline-block;width:14px;height:14px;
    background:#0096C7;opacity:0.4;border-radius:2px;vertical-align:middle;
    margin-right:6px;"></span>賑わい軸 B（≥2店）</div>
  <div><span style="display:inline-block;width:14px;height:14px;
    background:#1D9E75;opacity:0.6;border-radius:2px;vertical-align:middle;
    margin-right:6px;"></span>緑地・歩行者空間</div>
  <div><span style="display:inline-block;width:14px;height:14px;
    background:#7F8C8D;opacity:0.5;border-radius:2px;vertical-align:middle;
    margin-right:6px;"></span>駐車場</div>
  <div style="border-top:1px solid #e0e0e0;margin-top:6px;padding-top:4px;
    color:#555;font-size:11px;">{summary}</div>
</div>
"""


# ---- メイン ---------------------------------------------------------------
def main():
    # 1. データ取得
    data = fetch_overpass()
    shop_locs, ways = parse(data)
    print(f"shop ノード: {len(shop_locs)} 件")
    print(f"道路 way   : {len(ways)} 件")

    # 2. 既存データ読み込み
    geo_green = load_json(GREEN_GEOJSON)
    geo_park  = load_json(PARKING_GEOJSON)

    # 3. ティア分類
    print("店密度でティア分類中...")
    tier_s, tier_a, tier_b = [], [], []

    for w in ways:
        tags   = w["tags"]
        coords = w["coords"]
        hw     = tags.get("highway", "")

        # pedestrian / arcade は無条件で S
        if hw == "pedestrian":
            tier_s.append((coords, tags))
            continue

        cnt = shop_count_near(coords, shop_locs, SHOP_SEARCH_DEG)
        if   cnt >= TIER_S_MIN: tier_s.append((coords, tags))
        elif cnt >= TIER_A_MIN: tier_a.append((coords, tags))
        elif cnt >= TIER_B_MIN: tier_b.append((coords, tags))

    print(f"  Tier S: {len(tier_s)} way")
    print(f"  Tier A: {len(tier_a)} way")
    print(f"  Tier B: {len(tier_b)} way")

    # 4. 地図作成
    m = folium.Map(location=[CENTER_LAT, CENTER_LON], zoom_start=14, tiles=None)

    folium.TileLayer("cartodbpositron", name="地図 (CartoDB)").add_to(m)
    folium.TileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri",
        name="航空写真 (Esri)",
    ).add_to(m)

    # ---- 緑地（背景）-----------------------------------------------------
    if geo_green:
        fg_green = folium.FeatureGroup(name="緑地・歩行者空間", show=True)
        for feat in geo_green.get("features", []):
            cat = (feat.get("properties") or {}).get("category", "")
            for ring in get_rings(feat):
                ll = [(c[1], c[0]) for c in ring]
                if len(ll) >= 3:
                    folium.Polygon(ll, color=COLOR_GREEN, weight=0.5,
                                   fill=True, fill_color=COLOR_GREEN,
                                   fill_opacity=0.35, tooltip=cat).add_to(fg_green)
        fg_green.add_to(m)

    # ---- 駐車場（背景）---------------------------------------------------
    if geo_park:
        fg_park = folium.FeatureGroup(name="駐車場", show=False)
        for feat in geo_park.get("features", []):
            for ring in get_rings(feat):
                ll = [(c[1], c[0]) for c in ring]
                if len(ll) >= 3:
                    folium.Polygon(ll, color=COLOR_PARK, weight=0.5,
                                   fill=True, fill_color=COLOR_PARK,
                                   fill_opacity=0.30).add_to(fg_park)
        fg_park.add_to(m)

    # ---- 賑わい軸（水色）-------------------------------------------------
    def add_vitality_layer(tier_ways, name, opacity, weight):
        fg = folium.FeatureGroup(name=name, show=True)
        cnt = 0
        for coords, tags in tier_ways:
            poly = buffer_line(coords, BUFFER_M)
            if poly:
                shop_name = tags.get("name", "")
                hw        = tags.get("highway", "")
                tip       = f"{hw}" + (f" / {shop_name}" if shop_name else "")
                folium.Polygon(poly, color=COLOR_VIT, weight=weight,
                               fill=True, fill_color=COLOR_VIT,
                               fill_opacity=opacity, tooltip=tip).add_to(fg)
                cnt += 1
        fg.add_to(m)
        return cnt

    n_s = add_vitality_layer(tier_s, f"賑わい軸 S（≥{TIER_S_MIN}店 / pedestrian）", OPACITY_S, WEIGHT_S)
    n_a = add_vitality_layer(tier_a, f"賑わい軸 A（≥{TIER_A_MIN}店）",              OPACITY_A, WEIGHT_AB)
    n_b = add_vitality_layer(tier_b, f"賑わい軸 B（≥{TIER_B_MIN}店）",              OPACITY_B, WEIGHT_AB)

    # ---- 凡例 & コントロール ---------------------------------------------
    summary = (f"Tier S: {len(tier_s)}通り　A: {len(tier_a)}通り　B: {len(tier_b)}通り<br>"
               f"shop ノード {len(shop_locs)} 件を参照")
    m.get_root().html.add_child(folium.Element(LEGEND_HTML.format(summary=summary)))
    folium.LayerControl(collapsed=False, position="topright").add_to(m)

    m.save(OUT_HTML)
    print(f"\n保存完了: {OUT_HTML}")
    print(f"  Tier S バッファ: {n_s} ポリゴン")
    print(f"  Tier A バッファ: {n_a} ポリゴン")
    print(f"  Tier B バッファ: {n_b} ポリゴン")


if __name__ == "__main__":
    main()
