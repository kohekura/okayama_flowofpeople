import ast
import csv
import json
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BUILD_SCRIPT = ROOT / "build_osm_overview.py"
JINRYU_PATH = Path(r"C:\Users\rd006\Downloads\zinryu_okayama\kobetsuarea_time.csv")
GTFS_ROOT = Path(r"C:\Users\rd006\Downloads\0kayama_GTFS")
GREEN_PATH = ROOT / "green_osm.geojson"
LUSE_PATH = ROOT / "_plateau_luse_core.geojson"
OSM_EXTRA_PATH = ROOT / "_osm_extra_layers.json"
PARKING_PATH = ROOT.parent / "00_parking" / "parking_osm_flagged.geojson"
OUT_JSON = ROOT / "_flow_context_summary.json"
OUT_MD = ROOT / "人流と都市条件_一次分析.md"

RADIUS_M = 500
HIGH_FREQ_RATIO = 0.45


def load_jinryu_coords():
    text = BUILD_SCRIPT.read_text(encoding="utf-8")
    match = re.search(r"JINRYU_COORDS\s*=\s*(\{.*?\n\})", text, re.S)
    if not match:
        raise RuntimeError("JINRYU_COORDS not found")
    return ast.literal_eval(match.group(1))


def load_fallback_rail_stations():
    text = BUILD_SCRIPT.read_text(encoding="utf-8")
    match = re.search(r"RAIL_STATION_FALLBACK\s*=\s*(\[.*?\n\])", text, re.S)
    if not match:
        return []
    return ast.literal_eval(match.group(1))


def distance_m(lat1, lon1, lat2, lon2):
    r = 6371000
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def geometry_points(coordinates):
    if not isinstance(coordinates, list):
        return
    if len(coordinates) >= 2 and all(isinstance(v, (int, float)) for v in coordinates[:2]):
        yield coordinates[1], coordinates[0]
        return
    for child in coordinates:
        yield from geometry_points(child)


def feature_center(feature):
    points = list(geometry_points(feature.get("geometry", {}).get("coordinates")))
    if not points:
        props = feature.get("properties", {})
        lat, lon = props.get("rep_lat"), props.get("rep_lon")
        if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
            return lat, lon
        return None
    return sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points)


def count_features_near(features, lat, lon, radius=RADIUS_M):
    count = 0
    for feature in features:
        center = feature_center(feature)
        if center and distance_m(lat, lon, center[0], center[1]) <= radius:
            count += 1
    return count


def load_jinryu(year="2023"):
    coords = load_jinryu_coords()
    if not JINRYU_PATH.exists():
        return []
    with JINRYU_PATH.open("r", encoding="cp932") as f:
        lines = f.readlines()
    years = lines[1].strip().split(",")
    hours = lines[3].strip().split(",")
    hour_labels = [f"{hour}時" for hour in range(5, 29)]
    year_columns = [i for i, value in enumerate(years) if value.strip() == year]
    result = []
    for line in lines[4:]:
        parts = line.strip().split(",")
        name = parts[0].strip()
        if name not in coords:
            continue
        hourly = {}
        for hour in hour_labels:
            columns = [i for i in year_columns if i < len(hours) and hours[i].strip() == hour]
            values = []
            for index in columns:
                if index < len(parts) and parts[index].strip():
                    try:
                        values.append(float(parts[index]))
                    except ValueError:
                        pass
            if values:
                hourly[hour] = sum(values) / len(values)
        if hourly:
            peak_hour, peak_value = max(hourly.items(), key=lambda item: item[1])
            result.append(
                {
                    "name": name,
                    "lat": coords[name][0],
                    "lon": coords[name][1],
                    "hourly": hourly,
                    "peak_hour": peak_hour,
                    "peak": peak_value,
                    "day_avg": sum(hourly.get(f"{h}時", 0) for h in range(10, 19)) / 9,
                    "night_avg": sum(hourly.get(f"{h}時", 0) for h in range(18, 25)) / 7,
                }
            )
    return sorted(result, key=lambda item: item["peak"], reverse=True)


def load_json(path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_gtfs_stops():
    sources = [
        ("路面電車", GTFS_ROOT / "gtfs"),
        ("岡電バス", GTFS_ROOT / "okaden"),
        ("両備バス", GTFS_ROOT / "ryobi"),
    ]
    stops_by_key = {}
    for operator, folder in sources:
        stops_path = folder / "stops.txt"
        times_path = folder / "stop_times.txt"
        if not stops_path.exists() or not times_path.exists():
            continue
        stops = {}
        with stops_path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                try:
                    stops[row["stop_id"]] = {
                        "name": row.get("stop_name", "") or "名称なし",
                        "lat": float(row["stop_lat"]),
                        "lon": float(row["stop_lon"]),
                    }
                except (ValueError, KeyError):
                    continue
        trips = {}
        with times_path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                stop_id = row.get("stop_id", "")
                if stop_id in stops:
                    trips.setdefault(stop_id, set()).add(row.get("trip_id", ""))
        for stop_id, stop in stops.items():
            key = (round(stop["lat"], 4), round(stop["lon"], 4), stop["name"])
            item = stops_by_key.setdefault(
                key,
                {"name": stop["name"], "lat": stop["lat"], "lon": stop["lon"], "operators": set(), "trips": 0},
            )
            item["operators"].add(operator)
            item["trips"] += len(trips.get(stop_id, ()))
    return [
        {**item, "operators": sorted(item["operators"])}
        for item in stops_by_key.values()
    ]


def near_points(points, lat, lon, radius=RADIUS_M):
    return [p for p in points if distance_m(lat, lon, p["lat"], p["lon"]) <= radius]


def score_level(value, high, mid):
    if value >= high:
        return "高"
    if value >= mid:
        return "中"
    return "低"


def classify(row):
    commercial = row["commercial_land"] >= 40 or row["osm_shops"] >= 20
    pedestrian = row["pedestrian_spaces"] >= 15 or row["shopping_arcade"] > 0
    transit = row["high_freq_bus_stops"] >= 2 or row["tram_stops"] >= 1 or row["rail_stations"] >= 1
    parking = row["parking"] >= 18
    if commercial and pedestrian and transit:
        return "中心商業・回遊型"
    if commercial and parking and not pedestrian:
        return "車アクセス商業型"
    if transit and not commercial:
        return "交通結節・通過型"
    if commercial and not transit:
        return "目的地商業型"
    if pedestrian and not commercial:
        return "歩行空間先行型"
    return "条件探索型"


def main():
    flows = load_jinryu()
    green = load_json(GREEN_PATH).get("features", [])
    luse = load_json(LUSE_PATH).get("features", [])
    parking = load_json(PARKING_PATH).get("features", [])
    osm_extra = load_json(OSM_EXTRA_PATH)
    gtfs_stops = load_gtfs_stops()
    rail_sources = osm_extra.get("rail_stations", []) or load_fallback_rail_stations()
    max_trips = max((stop["trips"] for stop in gtfs_stops), default=0)

    pedestrian = [
        f for f in green
        if f.get("properties", {}).get("category") in {"pedestrian", "arcade", "footway", "path"}
    ]
    shopping_arcade = [
        f for f in green
        if f.get("properties", {}).get("category") == "arcade"
        or "商店街" in (f.get("properties", {}).get("name") or "")
    ]

    rows = []
    for flow in flows:
        lat, lon = flow["lat"], flow["lon"]
        nearby_stops = near_points(gtfs_stops, lat, lon)
        tram_stops = [s for s in nearby_stops if "路面電車" in s["operators"]]
        bus_stops = [s for s in nearby_stops if any(op != "路面電車" for op in s["operators"])]
        high_freq = [
            s for s in bus_stops
            if max_trips and s["trips"] >= max_trips * HIGH_FREQ_RATIO
        ]
        rail = []
        for item in rail_sources:
            pos = item.get("position") or []
            if len(pos) >= 2 and distance_m(lat, lon, pos[0], pos[1]) <= RADIUS_M:
                rail.append(item)

        row = {
            "name": flow["name"],
            "peak": round(flow["peak"], 1),
            "peak_hour": flow["peak_hour"],
            "day_avg": round(flow["day_avg"], 1),
            "night_avg": round(flow["night_avg"], 1),
            "commercial_land": count_features_near(luse, lat, lon),
            "pedestrian_spaces": count_features_near(pedestrian, lat, lon),
            "shopping_arcade": count_features_near(shopping_arcade, lat, lon),
            "parking": count_features_near(parking, lat, lon),
            "rail_stations": len(rail),
            "tram_stops": len(tram_stops),
            "bus_stops": len(bus_stops),
            "high_freq_bus_stops": len(high_freq),
            "tourism": len([
                item for item in osm_extra.get("tourism", [])
                if len(item.get("position") or []) >= 2
                and distance_m(lat, lon, item["position"][0], item["position"][1]) <= RADIUS_M
            ]),
            "large_commercial": len([
                item for item in osm_extra.get("commercial", [])
                if len(item.get("position") or []) >= 2
                and distance_m(lat, lon, item["position"][0], item["position"][1]) <= RADIUS_M
            ]),
        }
        row["type"] = classify(row)
        row["commercial_level"] = score_level(row["commercial_land"], 120, 40)
        row["pedestrian_level"] = score_level(row["pedestrian_spaces"], 30, 15)
        row["parking_level"] = score_level(row["parking"], 30, 12)
        row["transit_level"] = score_level(
            row["rail_stations"] * 3 + row["tram_stops"] + row["high_freq_bus_stops"],
            5,
            2,
        )
        rows.append(row)

    OUT_JSON.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    top = rows[:12]
    md = []
    md.append("# 人流と都市条件の一次分析\n")
    md.append("対象: 岡山市中心部の人流代表点から半径約500m。PLATEAU土地利用は商業用地のみ、駐車場はOSMを使用。\n")
    md.append("## 人流上位エリアの都市条件\n")
    md.append("|順位|エリア|ピーク|時間|類型|商業地|歩行者空間|駐車場|公共交通|\n")
    md.append("|---:|---|---:|---|---|---:|---:|---:|---:|\n")
    for index, row in enumerate(top, 1):
        transit_text = f"駅{row['rail_stations']} 電停{row['tram_stops']} 高頻度バス{row['high_freq_bus_stops']}"
        md.append(
            f"|{index}|{row['name']}|{row['peak']}|{row['peak_hour']}|{row['type']}|"
            f"{row['commercial_land']}|{row['pedestrian_spaces']}|{row['parking']}|{transit_text}|\n"
        )

    md.append("\n## 読み取りの仮説\n")
    md.append("- 駅・表町周辺は、商業用地、歩行者空間、公共交通が重なるほど人流が強くなる「中心商業・回遊型」として読める。\n")
    md.append("- 駐車場が多いエリアは、地方都市らしい車アクセスの受け皿になりうる。一方で、駐車場が面として増えると歩行者の連続性を切り、人流を点で止める可能性がある。\n")
    md.append("- 商業用地があるのに人流が弱い場所は、商業の密度、歩行者導線、公共交通との接続、夜間目的地性のどれが不足しているかを見るとよい。\n")
    md.append("- 歩行者空間や公共交通があるのに人流が伸びない場所は、空間整備だけでなく目的地となる店舗・施設の不足が疑われる。\n")
    md.append("- 商業用地が薄いのに人流が高い場所は、通勤・通学、病院・公共施設、観光、乗換など、商業以外の目的地性を確認する価値がある。\n")

    md.append("\n## 地図で確認したいズレ\n")
    focus_notes = []
    for row in rows:
        notes = []
        rank = rows.index(row) + 1
        if row["commercial_level"] == "低" and row["peak"] >= top[10]["peak"]:
            notes.append("商業地が薄いのに人流が高い")
        if row["commercial_level"] == "高" and row["pedestrian_level"] == "低":
            notes.append("商業地は濃いが歩行者空間が弱い")
        if row["parking_level"] == "高" and row["pedestrian_level"] == "低":
            notes.append("駐車場依存の可能性")
        if row["transit_level"] == "高" and row["commercial_level"] == "低":
            notes.append("交通結節・通過型の可能性")
        if rank >= 13 and row["commercial_land"] >= 280 and row["pedestrian_spaces"] >= 400:
            notes.append("商業・歩行者条件の割に人流が相対的に弱い")
        if notes:
            focus_notes.append((rank, row, notes))
    if focus_notes:
        for rank, row, notes in focus_notes:
            md.append(f"- {rank}位 {row['name']}: {'、'.join(notes)}。\n")
    else:
        md.append("- 上位だけでは条件差が出にくいため、13位以下の相対的に弱いエリアと比較する。\n")

    md.append("\n## まず面白そうな考察ポイント\n")
    md.append("1. 下石井・岡山駅・本町は、商業地、歩行者空間、交通が重なる素直な集積である。特に歩行者空間の密度が高く、単なる目的地ではなく回遊の受け皿がある。\n")
    md.append("2. 桑田町は人流が非常に高い一方、電停・高頻度バスが弱く、駐車場が多い。地方都市らしい車アクセス型の目的地人流、または代表点・エリア定義の影響を確認したい。\n")
    md.append("3. 奉還町は商業用地の量は中心部ほど多くないが、駐車場と商店街的な目的地性で一定の人流がある。駅裏・生活商業型の可能性がある。\n")
    md.append("4. 田町・中央町・柳町などは商業地や歩行者空間がある割に、人流順位が中下位に落ちる。夜間飲食、駐車場、歩行回遊の切れ目、昼夜ピークの違いを見るとよい。\n")
    md.append("5. 後楽園・岡山城周辺は観光・公共空地の目的地性があるが、商業地とは違う人流の出方をする。商業回遊型とは分けて読むべきである。\n")

    md.append("\n## まとめの方向性\n")
    md.append("岡山市中心部の人流は、単純に公共交通だけ、商業だけ、駐車場だけで決まるというより、商業目的地・歩行者空間・交通結節・車アクセスの重なりで説明するのが自然である。地方都市では車が主流であるため駐車場は人流を支える入口になりやすいが、駐車場が多すぎると沿道の連続性を弱め、回遊を切る可能性もある。したがって、駐車場を起点に商業地や歩行者空間へどう人を流すかが、まちなか再生の論点になる。\n")
    OUT_MD.write_text("".join(md), encoding="utf-8")
    print(f"created: {OUT_JSON}")
    print(f"created: {OUT_MD}")
    print(f"rows: {len(rows)}")


if __name__ == "__main__":
    main()
