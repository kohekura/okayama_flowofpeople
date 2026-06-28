# -*- coding: utf-8 -*-
"""
build_overlay_map.py  v3

メッセージ:「人中心であるべき通りに駐車場が張り付きすぎている」

レイヤー構成:
  水色（太め）: highway=pedestrian / arcade の通り  → 人中心軸
  橙色        : その通りから 30m 以内の駐車場       → 問題の主役
  薄緑        : その他の緑地・歩道                  → 背景
  薄灰        : 遠い駐車場                           → 参考
  ベース      : 地図 / 航空写真 切り替え

出力: overlay_parking_green.html（01_personspace）
"""

import os, json, math, csv, folium, requests

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
PARKING_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, r"..\00_parking"))

GTFS_DIR    = r"C:\Users\rd006\Downloads\0kayama_GTFS"
JINRYU_CSV  = r"C:\Users\rd006\Downloads\zinryu_okayama\kobetsuarea_time.csv"

# エリア名 → (lat, lon) 岡山市人流オープンデータ対応
JINRYU_COORDS = {
    "奉還町エリア":               (34.6555, 133.9115),
    "寿町エリア":                 (34.6570, 133.9150),
    "駅元町エリア":               (34.6545, 133.9215),
    "岡山駅エリア":               (34.6549, 133.9183),
    "下石井エリア":               (34.6513, 133.9220),
    "桑田町エリア":               (34.6600, 133.9235),
    "岩田町・駅前町エリア":       (34.6563, 133.9200),
    "中心市街地①（本町）":        (34.6621, 133.9200),
    "中心市街地②（幸町ほか）":    (34.6600, 133.9225),
    "中心市街地③（柳町ほか）":    (34.6617, 133.9255),
    "富田町・野田屋町エリア":      (34.6575, 133.9250),
    "中心市街地④（磨屋町ほか）":  (34.6593, 133.9280),
    "中心市街地⑤（田町ほか）":    (34.6610, 133.9290),
    "中心市街地⑥（中央町ほか）":  (34.6632, 133.9255),
    "弓之町・天神町・蕃山町エリア":(34.6585, 133.9160),
    "中心市街地⑦（中山下ほか）":  (34.6562, 133.9260),
    "中心市街地⑧（表町ほか）":    (34.6593, 133.9305),
    "中心市街地⑨（西大寺町ほか）":(34.6590, 133.9348),
    "出石・石関町エリア":          (34.6620, 133.9315),
    "後楽園エリア":                (34.6657, 133.9342),
    "岡山城・丸の内エリア":        (34.6625, 133.9370),
    "内山下・京橋町エリア":        (34.6555, 133.9330),
}

# エリア分類: name → (カテゴリ, 色, ラベル)  ラベルは空文字でも可
AREA_CATEGORIES = {
    # ── 大規模商業施設 ─────────────────────
    "下石井エリア":              ("大規模商業施設", "#FF5722", "イオンモール岡山"),
    "駅元町エリア":              ("大規模商業施設", "#FF5722", "さんすて岡山"),
    # ── 商店街・街商業 ────────────────────
    "奉還町エリア":              ("商店街・街商業",  "#FF9800", "奉還町商店街"),
    "中心市街地⑧（表町ほか）":   ("商店街・街商業",  "#FF9800", "表町商店街・天満屋"),
    "中心市街地③（柳町ほか）":   ("商店街・街商業",  "#FF9800", ""),
    "中心市街地⑤（田町ほか）":   ("商店街・街商業",  "#FF9800", ""),
    "富田町・野田屋町エリア":     ("商店街・街商業",  "#FF9800", ""),
    # ── 業務・オフィス ────────────────────
    "桑田町エリア":              ("業務・オフィス",   "#5C6BC0", "オフィス・業務集積"),
    "岩田町・駅前町エリア":      ("業務・オフィス",   "#5C6BC0", ""),
    "中心市街地①（本町）":       ("業務・オフィス",   "#5C6BC0", "業務地区"),
    "中心市街地②（幸町ほか）":   ("業務・オフィス",   "#5C6BC0", ""),
    "中心市街地④（磨屋町ほか）":  ("業務・オフィス",   "#5C6BC0", ""),
    "中心市街地⑦（中山下ほか）":  ("業務・オフィス",   "#5C6BC0", ""),
    "弓之町・天神町・蕃山町エリア":("業務・オフィス",   "#5C6BC0", ""),
    "寿町エリア":                ("業務・オフィス",   "#5C6BC0", ""),
    # ── 交通ハブ ──────────────────────────
    "岡山駅エリア":              ("交通ハブ",         "#00BCD4", "鉄道ハブ"),
    # ── 官公庁・行政 ──────────────────────
    "中心市街地⑥（中央町ほか）":  ("官公庁・行政",     "#78909C", ""),
    "内山下・京橋町エリア":      ("官公庁・行政",     "#78909C", "官公庁・旧城下町"),
    # ── 観光・文化 ────────────────────────
    "後楽園エリア":              ("観光・文化",        "#4CAF50", "後楽園・岡山城"),
    "岡山城・丸の内エリア":      ("観光・文化",        "#4CAF50", ""),
    "出石・石関町エリア":        ("観光・文化",        "#4CAF50", ""),
    "中心市街地⑨（西大寺町ほか）":("観光・文化",        "#4CAF50", ""),
}
# ラベルのみ（後方互換）
JINRYU_REASONS = {k: v[2] for k, v in AREA_CATEGORIES.items()}
CAT_DEFAULT = ("その他", "#90A4AE", "")

GREEN_GEOJSON   = os.path.join(SCRIPT_DIR, "green_osm.geojson")
PARKING_GEOJSON = os.path.join(PARKING_DIR, "parking.geojson")
OUT_HTML        = os.path.join(SCRIPT_DIR, "overlay_parking_green.html")

CENTER_LAT, CENTER_LON = 34.6551, 133.9195

# 人中心軸とみなすカテゴリ（pedestrian / arcade のみ）
HUMAN_AXIS_CATS = {"pedestrian", "arcade"}

# 駐車場が「張り付いている」とみなす距離（度）≈ 30m
TOUCH_DEG = 0.0003

# 色
COLOR_AXIS  = "#F1C40F"   # 黄色：人中心軸
COLOR_CLING = "#E67E22"   # 橙：張り付き駐車場（赤枠）
COLOR_GREEN = "#1D9E75"   # 薄緑：その他緑地
COLOR_FAR   = "#E67E22"   # 橙：遠い駐車場（枠なし）
COLOR_CLING_BORDER = "#C0392B"  # 赤：張り付き駐車場の枠線


# ---- ユーティリティ -------------------------------------------------------

def load_json(path):
    if not os.path.exists(path):
        print(f"  [SKIP] {path}")
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_outer_ring(feat):
    """GeoJSON Feature の外周リング座標リストを返す（Polygon/MultiPolygon 対応）"""
    geom  = feat.get("geometry") or {}
    gtype = geom.get("type", "")
    if gtype == "Polygon":
        return [geom["coordinates"][0]]
    if gtype == "MultiPolygon":
        return [p[0] for p in geom["coordinates"]]
    return []


def ring_bbox(ring):
    """ring: [[lon,lat],...] → (min_lat, min_lon, max_lat, max_lon)"""
    lats = [c[1] for c in ring]
    lons = [c[0] for c in ring]
    return min(lats), min(lons), max(lats), max(lons)


def bboxes_near(b1, b2, buf):
    return not (b1[2]+buf < b2[0] or b2[2]+buf < b1[0] or
                b1[3]+buf < b2[1] or b2[3]+buf < b1[1])


def add_polygon(fg, ring, color, weight, opacity, tooltip=None, fill_color=None):
    ll = [(c[1], c[0]) for c in ring]
    if len(ll) < 3:
        return
    folium.Polygon(ll, color=color, weight=weight,
                   fill=True, fill_color=fill_color or color, fill_opacity=opacity,
                   tooltip=tooltip).add_to(fg)


# ---- バッファ（線 → 帯状ポリゴン）---------------------------------------

def meters_to_deg_lat(m):
    return m / 111_000.0

def meters_to_deg_lon(m, lat):
    return m / (111_000.0 * math.cos(math.radians(lat)))

def buffer_line(latlons, width_m):
    """[(lat,lon),...] の中心線を片側 width_m でバッファしたポリゴンを返す"""
    if len(latlons) < 2:
        return None
    left, right = [], []
    for i in range(len(latlons) - 1):
        lat1, lon1 = latlons[i]
        lat2, lon2 = latlons[i + 1]
        mid = (lat1 + lat2) / 2
        dx  = (lon2 - lon1) * math.cos(math.radians(mid))
        dy  = lat2 - lat1
        L   = math.hypot(dx, dy)
        if L == 0:
            continue
        nx = -dy / L;  ny = dx / L
        dlat = meters_to_deg_lat(width_m) * ny
        dlon = meters_to_deg_lon(width_m, mid) * nx
        left.append( (lat1+dlat, lon1+dlon))
        right.append((lat1-dlat, lon1-dlon))
        if i == len(latlons) - 2:
            left.append( (lat2+dlat, lon2+dlon))
            right.append((lat2-dlat, lon2-dlon))
    poly = left + right[::-1]
    return poly if len(poly) >= 3 else None


# ---- 賑わい・対流人口レイヤー -------------------------------------------

def add_vitality_layer(m):
    """shop密度ティアで賑わいエリアを追加（対流人口のプロキシ）。"""
    if not os.path.exists(VITALITY_CACHE):
        print("  [SKIP] 賑わいキャッシュなし (_overpass_vitality_cache.json)")
        return
    with open(VITALITY_CACHE, encoding="utf-8") as f:
        data = json.load(f)

    nodes, shop_locs, ways = {}, [], []
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

    SHOP_DEG = 0.001  # ≈100m
    COLOR_VIT = "#D4AC0D"   # 金色（暖かみ＆他レイヤーと重複なし）
    fg = folium.FeatureGroup(name="賑わい・対流人口エリア（shop密度）", show=False)
    cnt = 0
    for w in ways:
        coords = w["coords"]
        hw = w["tags"].get("highway", "")
        if hw == "pedestrian":
            shops = 99
        else:
            clat = sum(c[0] for c in coords) / len(coords)
            clon = sum(c[1] for c in coords) / len(coords)
            shops = sum(1 for slat, slon in shop_locs
                        if abs(slat - clat) <= SHOP_DEG and abs(slon - clon) <= SHOP_DEG)
        if shops >= 8:
            opacity, weight = 0.55, 2.5
        elif shops >= 4:
            opacity, weight = 0.35, 1.5
        elif shops >= 2:
            opacity, weight = 0.18, 1.0
        else:
            continue
        poly = buffer_line(coords, 6.0)
        if poly:
            folium.Polygon(
                poly, color=COLOR_VIT, weight=weight,
                fill=True, fill_color=COLOR_VIT, fill_opacity=opacity,
                tooltip=f"shop密度: {min(shops, 99)}件",
            ).add_to(fg)
            cnt += 1
    fg.add_to(m)
    print(f"  賑わいエリア: {cnt} セグメント（shop {len(shop_locs)} 件参照）")


# ---- 人流レイヤー（岡山市人流オープンデータ）------------------------------

# 時間ラベル表示用（25時→1時 等に変換）
_HOUR_DISP = {
    f"{h}時": f"{h}時" if h <= 24 else f"{h-24}時(翌)" for h in range(5, 29)
}

def _load_jinryu_hourly(year="2023"):
    """指定年の全時間帯・全エリア平均滞在人口を返す。
    Returns: {area_name: {hour_label: avg_value}}
    """
    with open(JINRYU_CSV, encoding="cp932") as f:
        lines = f.readlines()
    years = lines[1].strip().split(",")
    months_row = lines[2].strip().split(",")
    hours = lines[3].strip().split(",")
    # 対象年の全列インデックス
    cols_year = [i for i, y in enumerate(years) if y.strip() == year]
    if not cols_year:
        return {}
    # 24時間帯
    hour_labels = ["5時","6時","7時","8時","9時","10時","11時","12時",
                   "13時","14時","15時","16時","17時","18時","19時","20時",
                   "21時","22時","23時","24時","25時","26時","27時","28時"]
    result = {}
    for line in lines[4:]:
        parts = line.strip().split(",")
        name = parts[0].strip()
        if not name:
            continue
        h_avgs = {}
        for h_label in hour_labels:
            h_cols = [i for i in cols_year if hours[i].strip() == h_label]
            vals = []
            for i in h_cols:
                if i < len(parts) and parts[i].strip():
                    try:
                        vals.append(float(parts[i]))
                    except ValueError:
                        pass
            if vals:
                h_avgs[h_label] = sum(vals) / len(vals)
        if h_avgs:
            result[name] = h_avgs
    return result


def _make_popup_html(name, hourly):
    """エリアの時間帯別人口をバーチャートHTMLで返す。"""
    hour_labels = ["5時","6時","7時","8時","9時","10時","11時","12時",
                   "13時","14時","15時","16時","17時","18時","19時","20時",
                   "21時","22時","23時","24時","25時","26時","27時","28時"]
    max_v = max(hourly.values()) if hourly else 1
    rows = ""
    for h in hour_labels:
        v = hourly.get(h)
        if v is None:
            continue
        pct = int(v / max_v * 100)
        disp = _HOUR_DISP.get(h, h)
        # 昼間帯（10-17時）を強調
        bar_color = "#29B6F6" if h in {"10時","11時","12時","13時","14時","15時","16時","17時"} \
                    else "#90CAF9" if h in {"18時","19時","20時","21時","22時","23時","24時","25時","26時","27時","28時"} \
                    else "#B0BEC5"
        rows += (
            f'<tr>'
            f'<td style="width:32px;color:#666;font-size:9px;padding:1px 3px 1px 0">{disp}</td>'
            f'<td style="padding:1px 4px 1px 0"><div style="background:{bar_color};'
            f'height:6px;width:{pct}%;min-width:2px;border-radius:2px"></div></td>'
            f'<td style="color:#333;font-size:9px;text-align:right;white-space:nowrap">{v:.0f}</td>'
            f'</tr>'
        )
    html = (
        f'<div style="min-width:200px;font-family:sans-serif;padding:2px">'
        f'<b style="font-size:11px">{name}</b><br>'
        f'<span style="font-size:9px;color:#888">2023年 時間帯別滞在人口（千人）</span>'
        f'<table style="width:100%;margin-top:4px;border-collapse:collapse">{rows}</table>'
        f'</div>'
    )
    return html


def add_jinryu_layer(m):
    """2023年 昼間平均滞在人口を円サイズで表示（岡山市人流オープンデータ）。
    円クリックで全時間帯バーチャートのポップアップを表示。
    """
    if not os.path.exists(JINRYU_CSV):
        print("  [SKIP] 人流CSVなし")
        return
    with open(JINRYU_CSV, encoding="cp932") as f:
        lines = f.readlines()

    years = lines[1].strip().split(",")
    hours = lines[3].strip().split(",")
    day_h = {"10時","11時","12時","13時","14時","15時","16時","17時"}
    cols  = [i for i, y in enumerate(years)
             if y.strip() == "2023" and hours[i].strip() in day_h]

    pop = {}
    for line in lines[4:]:
        parts = line.strip().split(",")
        name = parts[0].strip()
        if not name:
            continue
        vals = []
        for i in cols:
            if i < len(parts) and parts[i].strip():
                try:
                    vals.append(float(parts[i]))
                except ValueError:
                    pass
        if vals:
            pop[name] = sum(vals) / len(vals)

    if not pop:
        return

    # 全時間帯データをロード（ポップアップ用）
    hourly_all = _load_jinryu_hourly("2023")

    max_p = max(pop.values())
    COLOR = "#29B6F6"   # 水色（人流・単色）
    fg = folium.FeatureGroup(name="人流・昼間滞在人口（2023年）", show=True)

    for name, p in pop.items():
        coord = JINRYU_COORDS.get(name)
        if not coord:
            continue
        _, _, reason = AREA_CATEGORIES.get(name, CAT_DEFAULT)
        t   = math.sqrt(p / max_p)
        r   = 5 + 22 * t          # 5〜27 px
        op  = 0.25 + 0.45 * t     # 0.25〜0.70
        tip = f"<b>{name}</b><br>昼間滞在: {p:.0f}千人 (2023年平均)"
        if reason:
            tip += f"<br><span style='color:#555'>{reason}</span>"
        # ポップアップ（クリック）に24時間プロファイル
        popup_html = _make_popup_html(name, hourly_all.get(name, {}))
        folium.CircleMarker(
            coord,
            radius=r,
            color=COLOR, weight=0.5,
            fill=True, fill_color=COLOR, fill_opacity=op,
            tooltip=tip,
            popup=folium.Popup(popup_html, max_width=240),
        ).add_to(fg)

        # ラベルあり → pill 表示（水色縁・中立色）
        if reason:
            offset_y   = int(r) + 5
            label_html = (
                '<div style="'
                'font-size:9.5px;font-family:sans-serif;font-weight:500;'
                'color:#0a4060;'
                'background:rgba(255,255,255,0.88);'
                'border:1px solid rgba(41,182,246,0.55);'
                'border-radius:10px;'
                'padding:1px 6px;'
                'white-space:nowrap;'
                'pointer-events:none;'
                'box-shadow:0 1px 2px rgba(0,0,0,0.08);'
                f'">{reason}</div>'
            )
            est_w  = len(reason) * 8 + 14
            pill_h = 18
            folium.Marker(
                coord,
                icon=folium.DivIcon(
                    html=label_html,
                    icon_size=(est_w, pill_h),
                    icon_anchor=(est_w // 2, pill_h + offset_y),
                )
            ).add_to(fg)

    fg.add_to(m)
    print(f"  人流レイヤー: {len(pop)} エリア")


# ---- GTFS 路線・停留所読み込み -------------------------------------------

BBOX_S, BBOX_W, BBOX_N, BBOX_E = 34.62, 133.89, 34.69, 133.95

def _load_shapes_in_bbox(gtfs_folder):
    path = os.path.join(gtfs_folder, "shapes.txt")
    if not os.path.exists(path):
        return {}
    raw = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            sid = row["shape_id"].strip('"')
            lat = float(row["shape_pt_lat"].strip('"'))
            lon = float(row["shape_pt_lon"].strip('"'))
            seq = int(row["shape_pt_sequence"].strip('"'))
            raw.setdefault(sid, []).append((seq, lat, lon))
    result = {}
    for sid, pts in raw.items():
        pts.sort()
        coords = [(la, lo) for _, la, lo in pts]
        if any(BBOX_S <= la <= BBOX_N and BBOX_W <= lo <= BBOX_E
               for la, lo in coords):
            result[sid] = coords
    return result


def _load_stops_with_freq(gtfs_folder):
    """BBOX内停留所を返す。trips = 1日あたりのユニーク便数。"""
    stops = {}
    with open(os.path.join(gtfs_folder, "stops.txt"),
              encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            try:
                lat = float(row["stop_lat"])
                lon = float(row["stop_lon"])
            except ValueError:
                continue
            if BBOX_S <= lat <= BBOX_N and BBOX_W <= lon <= BBOX_E:
                stops[row["stop_id"]] = {
                    "name": row.get("stop_name", ""),
                    "lat": lat, "lon": lon, "trips": 0
                }
    # stop_times から便数カウント
    stop_trips = {}
    with open(os.path.join(gtfs_folder, "stop_times.txt"),
              encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            sid = row.get("stop_id", "")
            if sid in stops:
                stop_trips.setdefault(sid, set()).add(row.get("trip_id", ""))
    for sid, tset in stop_trips.items():
        stops[sid]["trips"] = len(tset)
    return stops


def add_gtfs_bus_layer(m, gtfs_folder, name, color, show):
    """バス停（頻度→円サイズ）＋極細路線を1レイヤーで追加。"""
    shapes = _load_shapes_in_bbox(gtfs_folder)
    stops  = _load_stops_with_freq(gtfs_folder)

    max_t = max((s["trips"] for s in stops.values()), default=1) or 1
    fg = folium.FeatureGroup(name=name, show=show)

    # 極細路線（繋ぎ用）
    for coords in shapes.values():
        folium.PolyLine(coords, color=color, weight=0.5,
                        opacity=0.2).add_to(fg)

    # 停留所（頻度∝サイズ）
    for s in stops.values():
        t = math.sqrt(s["trips"] / max_t)   # 0〜1 (sqrt スケール)
        radius      = 1.5 + 4.5 * t         # 1.5〜6 px
        fill_op     = 0.45 + 0.45 * t       # 0.45〜0.90
        folium.CircleMarker(
            [s["lat"], s["lon"]],
            radius=radius,
            color=color, weight=0.3,
            fill=True, fill_color=color, fill_opacity=fill_op,
            tooltip=f"{s['name']} ({s['trips']}便/日)",
        ).add_to(fg)

    fg.add_to(m)
    print(f"  {name}: {len(stops)} 停留所, {len(shapes)} 路線")


def add_tram_layer(m, gtfs_folder, name, color, show):
    """路面電車：太めの路線＋停留所（固定サイズ）。"""
    shapes = _load_shapes_in_bbox(gtfs_folder)
    stops  = _load_stops_with_freq(gtfs_folder)
    fg = folium.FeatureGroup(name=name, show=show)
    for coords in shapes.values():
        folium.PolyLine(coords, color=color, weight=3.5,
                        opacity=0.85).add_to(fg)
    for s in stops.values():
        folium.CircleMarker(
            [s["lat"], s["lon"]],
            radius=5, color=color, weight=1,
            fill=True, fill_color="white", fill_opacity=0.9,
            tooltip=s["name"],
        ).add_to(fg)
    fg.add_to(m)
    print(f"  {name}: {len(stops)} 停留所")


# ---- 大規模商業施設レイヤー -----------------------------------------------

COMMERCIAL_CACHE  = os.path.join(SCRIPT_DIR, "_overpass_commercial_cache.json")
OFFICE_CACHE      = os.path.join(SCRIPT_DIR, "_overpass_office_cache.json")
RESTAURANT_CACHE  = os.path.join(SCRIPT_DIR, "_overpass_restaurant_cache.json")
OVERPASS_URL      = "https://overpass-api.de/api/interpreter"

# カテゴリ: OSMの shop= 値 or 独自キー → (表示名, 色, 半径)
POI_CAT = {
    "mall":             ("大規模SC",   "#E91E63", 13),
    "department_store": ("百貨店",     "#E91E63", 11),
    "shopping_street":  ("商店街",     "#FF9800", 10),
    "tourism":          ("観光・文化", "#4CAF50",  9),
}

# OSMに単体エントリがない施設・観光地を手動追加
EXTRA_POIS = [
    ("表町商店街",   34.6617, 133.9305, "shopping_street"),
    ("奉還町商店街", 34.6555, 133.9115, "shopping_street"),
    ("後楽園",       34.6657, 133.9342, "tourism"),
    ("岡山城",       34.6625, 133.9370, "tourism"),
]

def _fetch_commercial_overpass():
    """Overpass から mall / department_store / supermarket を取得（キャッシュあり）。"""
    if os.path.exists(COMMERCIAL_CACHE):
        print(f"  [キャッシュ使用] {COMMERCIAL_CACHE}")
        with open(COMMERCIAL_CACHE, encoding="utf-8") as f:
            return json.load(f)
    s, w, n, e = BBOX_S, BBOX_W, BBOX_N, BBOX_E
    query = f"""
[out:json][timeout:90];
(
  node["shop"~"^(mall|department_store|supermarket)$"]({s},{w},{n},{e});
  way["shop"~"^(mall|department_store|supermarket)$"]({s},{w},{n},{e});
  relation["shop"~"^(mall|department_store|supermarket)$"]({s},{w},{n},{e});
);
out center tags;
"""
    headers = {"User-Agent": "GIS_personspace_study/1.0 (educational)"}
    print("  Overpass API に商業施設を問い合わせ中...")
    resp = requests.post(OVERPASS_URL, data={"data": query},
                         timeout=120, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    with open(COMMERCIAL_CACHE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    print(f"  取得完了 → {COMMERCIAL_CACHE}")
    return data


def _draw_poi(fg, lat, lon, name, cat_key):
    """POI を白縁 + カテゴリ色の CircleMarker で描く。"""
    cat_name, color, r = POI_CAT.get(cat_key, ("その他", "#90A4AE", 8))
    tip = f"<b>{name}</b><br><span style='color:{color}'>{cat_name}</span>"
    folium.CircleMarker(
        [lat, lon], radius=r + 2,
        color="white", weight=3,
        fill=True, fill_color="white", fill_opacity=1.0,
    ).add_to(fg)
    folium.CircleMarker(
        [lat, lon], radius=r,
        color=color, weight=2,
        fill=True, fill_color=color, fill_opacity=0.88,
        tooltip=tip,
    ).add_to(fg)


def _fetch_office_overpass():
    """Overpass からオフィスビル・業務施設を取得（キャッシュあり）。"""
    if os.path.exists(OFFICE_CACHE):
        print(f"  [キャッシュ使用] {OFFICE_CACHE}")
        with open(OFFICE_CACHE, encoding="utf-8") as f:
            return json.load(f)
    s, w, n, e = BBOX_S, BBOX_W, BBOX_N, BBOX_E
    query = f"""
[out:json][timeout:90];
(
  way["building"="office"]({s},{w},{n},{e});
  node["office"~"^(company|financial|insurance|government|estate_agent|ngo)$"]({s},{w},{n},{e});
  way["office"~"^(company|financial|insurance|government|estate_agent|ngo)$"]({s},{w},{n},{e});
);
out center tags;
"""
    headers = {"User-Agent": "GIS_personspace_study/1.0 (educational)"}
    print("  Overpass API にオフィスビルを問い合わせ中...")
    try:
        resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=120, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        with open(OFFICE_CACHE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        print(f"  取得完了 → {OFFICE_CACHE}")
        return data
    except Exception as e:
        print(f"  [警告] Overpass オフィス取得失敗: {e}")
        return {"elements": []}


def add_supermarket_layer(m):
    """スーパー（shop=supermarket）を独立レイヤーで表示。"""
    data  = _fetch_commercial_overpass()   # 既存キャッシュ再利用
    fg    = folium.FeatureGroup(name="スーパー", show=False)
    COLOR = "#26A69A"   # teal
    cnt   = 0
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        name = tags.get("name") or tags.get("name:ja", "")
        if not name or tags.get("shop") != "supermarket":
            continue
        if el["type"] == "node":
            lat, lon = el["lat"], el["lon"]
        else:
            c = el.get("center", {})
            lat, lon = c.get("lat"), c.get("lon")
            if lat is None:
                continue
        folium.CircleMarker(
            [lat, lon], radius=7,
            color=COLOR, weight=1.5,
            fill=True, fill_color=COLOR, fill_opacity=0.80,
            tooltip=f"<b>{name}</b><br>スーパー",
        ).add_to(fg)
        cnt += 1
    fg.add_to(m)
    print(f"  スーパーレイヤー: {cnt} 件")


def add_office_layer(m):
    """オフィスビル・業務施設を独立レイヤーで表示。"""
    data  = _fetch_office_overpass()
    fg    = folium.FeatureGroup(name="オフィスビル・業務施設", show=False)
    COLOR = "#7986CB"   # light indigo
    cnt   = 0
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        name = tags.get("name") or tags.get("name:ja", "")
        if not name:
            continue
        if el["type"] == "node":
            lat, lon = el["lat"], el["lon"]
        else:
            c = el.get("center", {})
            lat, lon = c.get("lat"), c.get("lon")
            if lat is None:
                continue
        otype = tags.get("office") or tags.get("building", "office")
        folium.CircleMarker(
            [lat, lon], radius=6,
            color=COLOR, weight=1.5,
            fill=True, fill_color=COLOR, fill_opacity=0.75,
            tooltip=f"<b>{name}</b><br>{otype}",
        ).add_to(fg)
        cnt += 1
    fg.add_to(m)
    print(f"  オフィスレイヤー: {cnt} 件")


def _fetch_restaurant_overpass():
    """Overpass から飲食店・カフェを取得（キャッシュあり）。"""
    if os.path.exists(RESTAURANT_CACHE):
        print(f"  [キャッシュ使用] {RESTAURANT_CACHE}")
        with open(RESTAURANT_CACHE, encoding="utf-8") as f:
            return json.load(f)
    s, w, n, e = BBOX_S, BBOX_W, BBOX_N, BBOX_E
    query = f"""
[out:json][timeout:90];
(
  node["amenity"~"^(restaurant|cafe|fast_food|bar|pub|food_court)$"]({s},{w},{n},{e});
  way["amenity"~"^(restaurant|cafe|fast_food|bar|pub|food_court)$"]({s},{w},{n},{e});
);
out center tags;
"""
    headers = {"User-Agent": "GIS_personspace_study/1.0 (educational)"}
    print("  Overpass API に飲食店を問い合わせ中...")
    try:
        resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=120, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        with open(RESTAURANT_CACHE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        print(f"  取得完了 → {RESTAURANT_CACHE}")
        return data
    except Exception as exc:
        print(f"  [警告] Overpass 飲食店取得失敗: {exc}")
        return {"elements": []}


# 飲食店タイプ → 表示名
_FOOD_TYPE_NAMES = {
    "restaurant": "レストラン",
    "cafe":       "カフェ",
    "fast_food":  "ファストフード",
    "bar":        "バー",
    "pub":        "パブ",
    "food_court": "フードコート",
}


def add_restaurant_layer(m):
    """飲食店・カフェをドットで表示する独立レイヤー。"""
    data  = _fetch_restaurant_overpass()
    fg    = folium.FeatureGroup(name="飲食店・カフェ", show=False)
    COLOR = "#EF5350"   # 赤
    cnt   = 0
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        name = tags.get("name") or tags.get("name:ja", "")
        if not name:
            continue
        atype = tags.get("amenity", "")
        if el["type"] == "node":
            lat, lon = el["lat"], el["lon"]
        else:
            c = el.get("center", {})
            lat, lon = c.get("lat"), c.get("lon")
            if lat is None:
                continue
        type_name = _FOOD_TYPE_NAMES.get(atype, atype)
        folium.CircleMarker(
            [lat, lon], radius=4,
            color=COLOR, weight=1,
            fill=True, fill_color=COLOR, fill_opacity=0.75,
            tooltip=f"<b>{name}</b><br>{type_name}",
        ).add_to(fg)
        cnt += 1
    fg.add_to(m)
    print(f"  飲食店レイヤー: {cnt} 件")


def add_yakkan_layer(m):
    """夜間人口（22〜28時 2023年平均）を円サイズで表示する独立レイヤー。"""
    if not os.path.exists(JINRYU_CSV):
        print("  [SKIP] 夜間人口: CSVなし")
        return
    hourly_all = _load_jinryu_hourly("2023")
    night_h = {"22時","23時","24時","25時","26時","27時","28時"}
    pop = {}
    for name, h_data in hourly_all.items():
        vals = [v for h, v in h_data.items() if h in night_h]
        if vals:
            pop[name] = sum(vals) / len(vals)
    if not pop:
        return
    max_p = max(pop.values())
    COLOR = "#5C6BC0"   # インディゴ（夜間）
    fg    = folium.FeatureGroup(name="人流・夜間滞在人口（2023年）", show=False)
    for name, p in pop.items():
        coord = JINRYU_COORDS.get(name)
        if not coord:
            continue
        t  = math.sqrt(p / max_p)
        r  = 5 + 22 * t
        op = 0.25 + 0.45 * t
        tip = f"<b>{name}</b><br>夜間滞在: {p:.0f}千人 (2023年 22〜4時平均)"
        popup_html = _make_popup_html(name, hourly_all.get(name, {}))
        folium.CircleMarker(
            coord, radius=r,
            color=COLOR, weight=0.5,
            fill=True, fill_color=COLOR, fill_opacity=op,
            tooltip=tip,
            popup=folium.Popup(popup_html, max_width=240),
        ).add_to(fg)
    fg.add_to(m)
    print(f"  夜間人口レイヤー: {len(pop)} エリア")


def add_commercial_layer(m):
    """大規模SC・百貨店（Overpass）＋商店街・観光地（手動）をカテゴリ色で表示。"""
    data = _fetch_commercial_overpass()
    fg   = folium.FeatureGroup(name="商業施設・観光地", show=True)
    cnt  = 0

    # Overpass: mall / department_store のみ（supermarketは除外）
    for el in data.get("elements", []):
        tags      = el.get("tags", {})
        name      = tags.get("name") or tags.get("name:ja", "")
        shop_type = tags.get("shop", "")
        if not name or shop_type not in ("mall", "department_store"):
            continue
        if el["type"] == "node":
            lat, lon = el["lat"], el["lon"]
        else:
            center = el.get("center", {})
            lat = center.get("lat")
            lon = center.get("lon")
            if lat is None:
                continue
        _draw_poi(fg, lat, lon, name, shop_type)
        cnt += 1

    # 手動追加（商店街・観光地）
    for name, lat, lon, cat_key in EXTRA_POIS:
        _draw_poi(fg, lat, lon, name, cat_key)
        cnt += 1

    fg.add_to(m)
    print(f"  商業施設・観光地レイヤー: {cnt} 件")


# ---- 凡例 ----------------------------------------------------------------

LEGEND_HTML = """
<div style="position:fixed;bottom:30px;left:30px;z-index:1000;
  background:rgba(255,255,255,0.94);border-radius:8px;padding:12px 16px;
  font-family:sans-serif;font-size:12px;line-height:1.9;
  box-shadow:0 1px 6px rgba(0,0,0,0.2);min-width:230px;">
  <div style="font-weight:bold;font-size:13px;margin-bottom:6px;">
    人中心空間と駐車場
  </div>
  <div><span style="display:inline-block;width:16px;height:5px;
    background:#F1C40F;border-radius:2px;vertical-align:middle;
    margin-right:8px;"></span>歩行者専用通り（人中心軸）</div>
  <div><span style="display:inline-block;width:14px;height:14px;
    background:#E67E22;border:2px solid #C0392B;border-radius:2px;vertical-align:middle;
    margin-right:8px;opacity:0.9"></span>軸に張り付く駐車場（赤枠・30m以内）</div>
  <div><span style="display:inline-block;width:14px;height:14px;
    background:#E67E22;border-radius:2px;vertical-align:middle;
    margin-right:8px;opacity:0.5"></span>その他の駐車場</div>
  <div><span style="display:inline-block;width:14px;height:14px;
    background:#1D9E75;border-radius:2px;vertical-align:middle;
    margin-right:8px;opacity:0.5"></span>その他の緑地・歩道</div>
  <div><span style="display:inline-block;width:14px;height:14px;
    background:#29B6F6;border-radius:50%;vertical-align:middle;
    margin-right:8px;opacity:0.6"></span>昼間滞在人口（円＝規模、2023年）</div>
  <div style="border-top:1px solid #e0e0e0;margin-top:6px;padding-top:6px;
    font-size:11px;font-weight:bold;color:#444;">施設・観光地</div>
  <div><span style="display:inline-block;width:12px;height:12px;background:#E91E63;border-radius:50%;vertical-align:middle;margin-right:6px;"></span>大規模SC・百貨店</div>
  <div><span style="display:inline-block;width:12px;height:12px;background:#FF9800;border-radius:50%;vertical-align:middle;margin-right:6px;"></span>商店街</div>
  <div><span style="display:inline-block;width:12px;height:12px;background:#4CAF50;border-radius:50%;vertical-align:middle;margin-right:6px;"></span>観光・文化</div>
  <div><span style="display:inline-block;width:12px;height:12px;background:#26A69A;border-radius:50%;vertical-align:middle;margin-right:6px;"></span>スーパー（右上でON/OFF）</div>
  <div><span style="display:inline-block;width:12px;height:12px;background:#7986CB;border-radius:50%;vertical-align:middle;margin-right:6px;"></span>オフィスビル・業務（右上でON/OFF）</div>
  <div><span style="display:inline-block;width:12px;height:12px;background:#EF5350;border-radius:50%;vertical-align:middle;margin-right:6px;"></span>飲食店・カフェ（右上でON/OFF）</div>
  <div><span style="display:inline-block;width:14px;height:14px;background:#5C6BC0;border-radius:50%;vertical-align:middle;margin-right:6px;opacity:0.6"></span>夜間滞在人口 22-4時（右上でON/OFF）</div>
  <div style="font-size:10px;color:#888;margin-top:2px;">※円をクリックで時間帯別グラフ表示</div>
  <div style="border-top:1px solid #e0e0e0;margin-top:8px;padding-top:4px;">
  <div><span style="display:inline-block;width:16px;height:4px;
    background:#cc0022;border-radius:1px;vertical-align:middle;
    margin-right:8px;"></span>路面電車（岡電）</div>
  <div style="font-size:11px;color:#888;margin-top:2px;">
    ●円サイズ＝バス停の運行頻度（右上で切替）</div>
  </div>
  <div style="border-top:1px solid #e0e0e0;margin-top:6px;padding-top:6px;
    font-size:11px;color:#555;">{summary}</div>
</div>
"""


# ---- メイン --------------------------------------------------------------

def main():
    geo_green = load_json(GREEN_GEOJSON)
    geo_park  = load_json(PARKING_GEOJSON)

    if not geo_green or not geo_park:
        print("ファイルが読み込めませんでした。"); return

    green_feats = geo_green.get("features", [])
    park_feats  = geo_park.get("features", [])

    # ---- 人中心軸の抽出（pedestrian / arcade、かつ名前付きのみ）-----------
    axis_feats = [f for f in green_feats
                  if (f.get("properties") or {}).get("category") in HUMAN_AXIS_CATS
                  and (f.get("properties") or {}).get("name", "")]
    print(f"人中心軸フィーチャ: {len(axis_feats)} 件 (名前付き pedestrian/arcade)")

    axis_bboxes = []
    for feat in axis_feats:
        for ring in get_outer_ring(feat):
            axis_bboxes.append(ring_bbox(ring))

    # ---- 駐車場を「張り付き」/「それ以外」に分類 -----------------------
    print("駐車場の近接判定中...")
    cling_feats = []
    far_feats   = []
    for feat in park_feats:
        rings = get_outer_ring(feat)
        if not rings:
            continue
        near = any(
            bboxes_near(ring_bbox(pr), ab, TOUCH_DEG)
            for pr in rings
            for ab in axis_bboxes
        )
        (cling_feats if near else far_feats).append(feat)

    n_total = len(cling_feats) + len(far_feats)
    pct = len(cling_feats) / n_total * 100 if n_total else 0
    print(f"  軸に張り付く駐車場: {len(cling_feats)} 件 ({pct:.1f}%)")
    print(f"  その他            : {len(far_feats)} 件")

    # ---- 地図 ------------------------------------------------------------
    m = folium.Map(location=[CENTER_LAT, CENTER_LON], zoom_start=15, tiles=None)

    folium.TileLayer("cartodbpositron",   name="地図 (CartoDB)").add_to(m)
    folium.TileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri", name="航空写真 (Esri)",
    ).add_to(m)

    # レイヤー①: その他緑地（背景）
    fg_green = folium.FeatureGroup(name="緑地・歩道（背景）", show=True)
    other_green = [f for f in green_feats
                   if (f.get("properties") or {}).get("category") not in HUMAN_AXIS_CATS]
    for feat in other_green:
        for ring in get_outer_ring(feat):
            add_polygon(fg_green, ring, COLOR_GREEN, 0.3, 0.25)
    fg_green.add_to(m)

    # レイヤー②: その他駐車場（背景）
    fg_far = folium.FeatureGroup(name="その他の駐車場", show=True)
    for feat in far_feats:
        for ring in get_outer_ring(feat):
            add_polygon(fg_far, ring, COLOR_FAR, 0.3, 0.45)
    fg_far.add_to(m)

    # レイヤー③: 張り付き駐車場（主役）
    fg_cling = folium.FeatureGroup(
        name=f"人中心軸に張り付く駐車場（{len(cling_feats)} 件）", show=True)
    for feat in cling_feats:
        props = feat.get("properties") or {}
        tip   = " | ".join(f"{k}: {v}" for k, v in list(props.items())[:4] if v)
        for ring in get_outer_ring(feat):
            add_polygon(fg_cling, ring, COLOR_CLING_BORDER, 2.0, 0.75,
                        tip or None, fill_color=COLOR_CLING)
    fg_cling.add_to(m)

    # レイヤー④: 人中心軸（最前面・最も目立たせる）
    fg_axis = folium.FeatureGroup(name="歩行者専用通り（人中心軸）", show=True)
    for feat in axis_feats:
        cat = (feat.get("properties") or {}).get("category", "")
        for ring in get_outer_ring(feat):
            latlons = [(c[1], c[0]) for c in ring]
            folium.Polygon(
                latlons, color=COLOR_AXIS, weight=2,
                fill=True, fill_color=COLOR_AXIS, fill_opacity=0.65,
                tooltip=cat,
            ).add_to(fg_axis)
    fg_axis.add_to(m)

    # レイヤー⑤: 人流（昼間滞在人口）
    print("人流レイヤーを追加中...")
    add_jinryu_layer(m)

    # レイヤー⑤b: 商業施設・観光地・スーパー・オフィス
    print("商業施設レイヤーを追加中...")
    add_commercial_layer(m)
    add_supermarket_layer(m)
    print("オフィスレイヤーを追加中...")
    add_office_layer(m)

    # レイヤー⑤c: 飲食店・夜間人口
    print("飲食店レイヤーを追加中...")
    add_restaurant_layer(m)
    print("夜間人口レイヤーを追加中...")
    add_yakkan_layer(m)

    # レイヤー⑥〜⑧: 公共交通
    print("公共交通を追加中...")
    add_tram_layer(m, os.path.join(GTFS_DIR, "gtfs"),
                   "路面電車（岡電）", "#cc0022", True)
    add_gtfs_bus_layer(m, os.path.join(GTFS_DIR, "okaden"),
                       "岡電バス（停留所・路線）", "#9B59B6", False)
    add_gtfs_bus_layer(m, os.path.join(GTFS_DIR, "ryobi"),
                       "両備バス（停留所・路線）", "#0077cc", False)

    # 凡例 & コントロール
    summary = (f"歩行者専用通り: {len(axis_feats)} フィーチャ<br>"
               f"張り付く駐車場: {len(cling_feats)} 件 ({pct:.0f}%) "
               f"／ 総駐車場 {n_total} 件")
    m.get_root().html.add_child(folium.Element(LEGEND_HTML.format(summary=summary)))
    folium.LayerControl(collapsed=False, position="topright").add_to(m)

    m.save(OUT_HTML)
    print(f"\n保存完了: {OUT_HTML}")


if __name__ == "__main__":
    main()
