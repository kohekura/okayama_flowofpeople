import csv
import json
import math
import argparse
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
DATA_DIR = ROOT / "data"
POIS_PATH = DATA_DIR / "analysis" / "_map_pois_full.json"
GREEN_PATH = DATA_DIR / "analysis" / "green_osm.geojson"
OUTPUT_PATH = ROOT / "okayama_osm_all.html"
OSM_EXTRA_CACHE = DATA_DIR / "analysis" / "_osm_extra_layers.json"
PARKING_ROOT = ROOT.parent / "00_parking"
PARKING_OSM_PATH = PARKING_ROOT / "parking_osm_flagged.geojson"
PARKING_PLATEAU_PATH = PARKING_ROOT / "parking_plateau.geojson"
PARKING_CANDIDATES_PATH = PARKING_ROOT / "parking_plateau_candidates.geojson"
BUILDING_AGE_PATH = DATA_DIR / "plateau" / "_plateau_building_age.geojson"
PLATEAU_LUSE_CORE_PATH = DATA_DIR / "plateau" / "_plateau_luse_core.geojson"
FLOW_DRIVER_NOTES_PATH = DATA_DIR / "flow" / "_flow_driver_notes.geojson"
FLOW_AREA_APPROX_PATH = DATA_DIR / "flow" / "_flow_area_approx.geojson"
GTFS_ROOT = Path(r"C:\Users\rd006\Downloads\0kayama_GTFS")
JINRYU_PATH = Path(r"C:\Users\rd006\Downloads\zinryu_okayama\kobetsuarea_time.csv")
BBOX = (34.62, 133.89, 34.69, 133.95)
parser = argparse.ArgumentParser(
    description="岡山市中心部OSM分析マップを生成します。"
)
parser.add_argument(
    "--light",
    action="store_true",
    help="重いPLATEAU系レイヤーを埋め込まない軽量版HTMLを生成します。",
)
parser.add_argument(
    "--output",
    type=Path,
    default=None,
    help="出力HTMLパス。省略時は通常版/軽量版の既定名を使います。",
)
ARGS = parser.parse_args()
LIGHTWEIGHT = ARGS.light
OUTPUT_PATH = ARGS.output or (
    ROOT / "okayama_osm_light.html" if LIGHTWEIGHT else OUTPUT_PATH
)
EMPTY_FEATURE_COLLECTION = {"type": "FeatureCollection", "features": []}
RAIL_STATION_FALLBACK = [
    {"name": "岡山駅", "position": [34.6663, 133.9186], "tags": {"railway": "station"}},
    {"name": "備前三門駅", "position": [34.6741, 133.9024], "tags": {"railway": "station"}},
    {"name": "法界院駅", "position": [34.6852, 133.9210], "tags": {"railway": "station"}},
    {"name": "西川原駅", "position": [34.6790, 133.9375], "tags": {"railway": "station"}},
]
JINRYU_COORDS = {
    # 人流CSVにはエリア形状がないため、地図上では町名・地区名に合わせた代表点で表示する。
    # 以前の代表点は駅南側へ大きくズレていたため、岡山駅〜表町〜後楽園の実位置へ補正。
    "奉還町エリア": [34.6687, 133.9124],
    "寿町エリア": [34.6710, 133.9140],
    "駅元町エリア": [34.6668, 133.9160],
    "岡山駅エリア": [34.6663, 133.9187],
    "下石井エリア": [34.6618, 133.9198],
    "桑田町エリア": [34.6570, 133.9158],
    "岩田町・駅前町エリア": [34.6670, 133.9215],
    "中心市街地①（本町）": [34.6650, 133.9218],
    "中心市街地②（幸町ほか）": [34.6622, 133.9214],
    "中心市街地③（柳町ほか）": [34.6593, 133.9225],
    "富田町・野田屋町エリア": [34.6665, 133.9248],
    "中心市街地④（磨屋町ほか）": [34.6638, 133.9258],
    "中心市街地⑤（田町ほか）": [34.6608, 133.9264],
    "中心市街地⑥（中央町ほか）": [34.6592, 133.9258],
    "弓之町・天神町・蕃山町エリア": [34.6686, 133.9290],
    "中心市街地⑦（中山下ほか）": [34.6633, 133.9287],
    "中心市街地⑧（表町ほか）": [34.6610, 133.9305],
    "中心市街地⑨（西大寺町ほか）": [34.6589, 133.9331],
    "出石・石関町エリア": [34.6659, 133.9318],
    "後楽園エリア": [34.6699, 133.9350],
    "岡山城・丸の内エリア": [34.6650, 133.9356],
    "内山下・京橋町エリア": [34.6620, 133.9328],
}


def compact_json(path: Path) -> str:
    with path.open("r", encoding="utf-8") as f:
        return json.dumps(json.load(f), ensure_ascii=False, separators=(",", ":"))


def geometry_points(coordinates):
    if not isinstance(coordinates, list):
        return
    if len(coordinates) >= 2 and all(
        isinstance(value, (int, float)) for value in coordinates[:2]
    ):
        yield coordinates[0], coordinates[1]
        return
    for child in coordinates:
        yield from geometry_points(child)


def feature_in_bbox(feature):
    south, west, north, east = BBOX
    for lon, lat in geometry_points(feature.get("geometry", {}).get("coordinates")):
        if south <= lat <= north and west <= lon <= east:
            return True
    properties = feature.get("properties", {})
    lat, lon = properties.get("rep_lat"), properties.get("rep_lon")
    return (
        isinstance(lat, (int, float))
        and isinstance(lon, (int, float))
        and south <= lat <= north
        and west <= lon <= east
    )


def load_parking(path):
    if not path.exists():
        return {"type": "FeatureCollection", "features": []}
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return {
        "type": "FeatureCollection",
        "features": [
            feature
            for feature in data.get("features", [])
            if feature_in_bbox(feature)
        ],
    }


def load_gtfs_stops():
    sources = [
        ("路面電車", GTFS_ROOT / "gtfs"),
        ("岡電バス", GTFS_ROOT / "okaden"),
        ("両備バス", GTFS_ROOT / "ryobi"),
    ]
    south, west, north, east = BBOX
    merged = {}
    for operator, folder in sources:
        stops_path = folder / "stops.txt"
        times_path = folder / "stop_times.txt"
        if not stops_path.exists() or not times_path.exists():
            continue
        stops = {}
        with stops_path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                try:
                    lat, lon = float(row["stop_lat"]), float(row["stop_lon"])
                except (ValueError, KeyError):
                    continue
                if south <= lat <= north and west <= lon <= east:
                    stops[row["stop_id"]] = {
                        "name": row.get("stop_name", "") or "名称なし",
                        "lat": lat,
                        "lon": lon,
                    }
        trips = {}
        with times_path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                stop_id = row.get("stop_id", "")
                if stop_id in stops:
                    trips.setdefault(stop_id, set()).add(row.get("trip_id", ""))
        for stop_id, stop in stops.items():
            count = len(trips.get(stop_id, ()))
            key = (
                stop["name"],
                round(stop["lat"], 3),
                round(stop["lon"], 3),
            )
            item = merged.setdefault(
                key,
                {
                    "name": stop["name"],
                    "lat_sum": 0.0,
                    "lon_sum": 0.0,
                    "positions": 0,
                    "trips": 0,
                    "operators": set(),
                },
            )
            item["lat_sum"] += stop["lat"]
            item["lon_sum"] += stop["lon"]
            item["positions"] += 1
            item["trips"] += count
            item["operators"].add(operator)
    result = []
    for item in merged.values():
        n = item["positions"]
        result.append(
            {
                "name": item["name"],
                "lat": item["lat_sum"] / n,
                "lon": item["lon_sum"] / n,
                "trips": item["trips"],
                "operators": sorted(item["operators"]),
            }
        )
    return result


def load_gtfs_routes():
    sources = [
        ("路面電車", GTFS_ROOT / "gtfs", "#d32f2f"),
        ("岡電バス", GTFS_ROOT / "okaden", "#8e44ad"),
        ("両備バス", GTFS_ROOT / "ryobi", "#1565c0"),
    ]
    south, west, north, east = BBOX
    margin = 0.006
    result = []
    signatures = set()

    def perpendicular_distance(point, start, end):
        x, y = point[1], point[0]
        x1, y1 = start[1], start[0]
        x2, y2 = end[1], end[0]
        if x1 == x2 and y1 == y2:
            return math.hypot(x - x1, y - y1)
        return abs((y2 - y1) * x - (x2 - x1) * y + x2 * y1 - y2 * x1) / math.hypot(
            y2 - y1, x2 - x1
        )

    def simplify(points, tolerance=0.00008):
        if len(points) <= 2:
            return points
        max_distance = 0.0
        index = 0
        for i in range(1, len(points) - 1):
            distance = perpendicular_distance(points[i], points[0], points[-1])
            if distance > max_distance:
                index, max_distance = i, distance
        if max_distance > tolerance:
            left = simplify(points[: index + 1], tolerance)
            right = simplify(points[index:], tolerance)
            return left[:-1] + right
        return [points[0], points[-1]]

    def append_route(operator, color, shape_id, geometry):
        simplified = simplify(geometry)
        signature = (
            operator,
            tuple((round(point[0], 4), round(point[1], 4)) for point in simplified),
        )
        reverse_signature = (operator, tuple(reversed(signature[1])))
        if signature in signatures or reverse_signature in signatures:
            return
        signatures.add(signature)
        result.append(
            {
                "operator": operator,
                "color": color,
                "shape_id": shape_id,
                "geometry": simplified,
            }
        )

    for operator, folder, color in sources:
        path = folder / "shapes.txt"
        if not path.exists():
            continue
        shapes = {}
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                try:
                    lat = float(row["shape_pt_lat"])
                    lon = float(row["shape_pt_lon"])
                    sequence = int(float(row["shape_pt_sequence"]))
                except (ValueError, KeyError):
                    continue
                shape_id = row.get("shape_id", "")
                shapes.setdefault(shape_id, []).append((sequence, lat, lon))
        for shape_id, points in shapes.items():
            points.sort()
            segment = []
            for _, lat, lon in points:
                inside = (
                    south - margin <= lat <= north + margin
                    and west - margin <= lon <= east + margin
                )
                if inside:
                    segment.append([lat, lon])
                elif len(segment) >= 2:
                    append_route(operator, color, shape_id, segment)
                    segment = []
                else:
                    segment = []
            if len(segment) >= 2:
                append_route(operator, color, shape_id, segment)
    return result


def load_jinryu(year="2023"):
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
        if name not in JINRYU_COORDS:
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
            result.append(
                {
                    "name": name,
                    "lat": JINRYU_COORDS[name][0],
                    "lon": JINRYU_COORDS[name][1],
                    "hourly": hourly,
                }
            )
    return result


def fetch_osm_extra():
    if OSM_EXTRA_CACHE.exists():
        with OSM_EXTRA_CACHE.open("r", encoding="utf-8") as f:
            cached = json.load(f)
        if cached.get("_schema") == 3:
            return cached
    south, west, north, east = BBOX
    bbox = f"{south},{west},{north},{east}"
    query = f"""
[out:json][timeout:90];
(
  nwr["tourism"]({bbox});
  nwr["historic"~"^(castle|monument|memorial)$"]({bbox});
  nwr["shop"~"^(mall|department_store)$"]({bbox});
  way["highway"="cycleway"]({bbox});
  way["cycleway"]({bbox});
  way["cycleway:left"]({bbox});
  way["cycleway:right"]({bbox});
  way["bicycle_road"="yes"]({bbox});
  nwr["amenity"="bicycle_parking"]({bbox});
  nwr["amenity"="bicycle_rental"]({bbox});
  nwr["bicycle_rental"]({bbox});
  nwr["railway"~"^(station|halt)$"]({bbox});
  nwr["public_transport"="station"]["train"="yes"]({bbox});
);
out center geom tags;
"""
    request = Request(
        "https://overpass-api.de/api/interpreter",
        data=urlencode({"data": query}).encode("utf-8"),
        headers={"User-Agent": "okayama-osm-overview/1.0"},
    )
    with urlopen(request, timeout=120) as response:
        data = json.load(response)
    data["_schema"] = 3
    OSM_EXTRA_CACHE.write_text(
        json.dumps(data, ensure_ascii=False), encoding="utf-8"
    )
    return data


def element_position(element):
    if "lat" in element and "lon" in element:
        return element["lat"], element["lon"]
    center = element.get("center", {})
    if "lat" in center and "lon" in center:
        return center["lat"], center["lon"]
    geometry = element.get("geometry") or []
    if geometry:
        return (
            sum(p["lat"] for p in geometry) / len(geometry),
            sum(p["lon"] for p in geometry) / len(geometry),
        )
    return None


def prepare_osm_extra(raw):
    data = {
        "tourism": [],
        "commercial": [],
        "cycleways": [],
        "bike_parking": [],
        "bike_share": [],
        "rail_stations": [],
    }
    seen = set()
    for element in raw.get("elements", []):
        key = (element.get("type"), element.get("id"))
        if key in seen:
            continue
        seen.add(key)
        tags = element.get("tags", {})
        position = element_position(element)
        geometry = [
            [point["lat"], point["lon"]]
            for point in (element.get("geometry") or [])
            if "lat" in point and "lon" in point
        ]
        name = tags.get("name") or tags.get("name:ja") or "名称なし"
        common = {
            "name": name,
            "tags": tags,
            "position": list(position) if position else None,
            "geometry": geometry,
        }
        if tags.get("tourism") or tags.get("historic") in {
            "castle",
            "monument",
            "memorial",
        }:
            data["tourism"].append(common)
        if tags.get("shop") in {"mall", "department_store"}:
            data["commercial"].append(common)
        if (
            tags.get("highway") == "cycleway"
            or tags.get("cycleway")
            or tags.get("cycleway:left")
            or tags.get("cycleway:right")
            or tags.get("bicycle_road") == "yes"
        ) and len(geometry) >= 2:
            data["cycleways"].append(common)
        if tags.get("amenity") == "bicycle_parking":
            data["bike_parking"].append(common)
        if tags.get("amenity") == "bicycle_rental" or tags.get("bicycle_rental"):
            data["bike_share"].append(common)
        if tags.get("railway") in {"station", "halt"} or (
            tags.get("public_transport") == "station"
            and tags.get("train") == "yes"
        ):
            data["rail_stations"].append(common)
    return data


with POIS_PATH.open("r", encoding="utf-8") as f:
    pois = json.load(f)

with GREEN_PATH.open("r", encoding="utf-8") as f:
    green_source = json.load(f)

parking_osm = load_parking(PARKING_OSM_PATH)
parking_osm["features"] = [
    feature
    for feature in parking_osm["features"]
    if feature.get("geometry", {}).get("type") in {"Polygon", "MultiPolygon"}
]
parking_plateau = load_parking(PARKING_PLATEAU_PATH)
parking_candidates = load_parking(PARKING_CANDIDATES_PATH)
building_age = load_parking(BUILDING_AGE_PATH)
plateau_luse_core = load_parking(PLATEAU_LUSE_CORE_PATH)
flow_driver_notes = load_parking(FLOW_DRIVER_NOTES_PATH)
flow_area_approx = load_parking(FLOW_AREA_APPROX_PATH)
if LIGHTWEIGHT:
    parking_plateau = EMPTY_FEATURE_COLLECTION
    parking_candidates = EMPTY_FEATURE_COLLECTION
    building_age = EMPTY_FEATURE_COLLECTION

green_areas = {
    "type": "FeatureCollection",
    "features": [
        feature
        for feature in green_source.get("features", [])
        if feature.get("properties", {}).get("category") in {"park", "garden", "square"}
    ],
}

pedestrian_areas = {
    "type": "FeatureCollection",
    "features": [
        feature
        for feature in green_source.get("features", [])
        if feature.get("properties", {}).get("category")
        in {"pedestrian", "arcade", "footway", "path"}
    ],
}

shopping_areas = {
    "type": "FeatureCollection",
    "features": [
        feature
        for feature in green_source.get("features", [])
        if feature.get("properties", {}).get("category") == "arcade"
        or "商店街" in (feature.get("properties", {}).get("name") or "")
    ],
}

transit_stops_all = load_gtfs_stops()
transit_routes_all = load_gtfs_routes()
tram_stops = [
    stop for stop in transit_stops_all if "路面電車" in stop.get("operators", [])
]
tram_routes = [
    route for route in transit_routes_all if route.get("operator") == "路面電車"
]
transit_stops = [
    stop
    for stop in transit_stops_all
    if any(operator != "路面電車" for operator in stop.get("operators", []))
]
transit_routes = [
    route for route in transit_routes_all if route.get("operator") != "路面電車"
]
max_bus_trips = max((stop.get("trips", 0) for stop in transit_stops), default=0)
high_freq_bus_count = sum(
    1 for stop in transit_stops if stop.get("trips", 0) >= max_bus_trips * 0.45
)
jinryu = load_jinryu()
top_flow_areas = sorted(
    [
        {
            "name": item["name"],
            "lat": item["lat"],
            "lon": item["lon"],
            "score": max((float(v) for v in item.get("hourly", {}).values()), default=0.0),
        }
        for item in jinryu
    ],
    key=lambda item: item["score"],
    reverse=True,
)[:8]
osm_extra = prepare_osm_extra(fetch_osm_extra())
if not osm_extra["rail_stations"]:
    osm_extra["rail_stations"] = RAIL_STATION_FALLBACK
shopping_streets = [
    {
        "name": "表町商店街",
        "lat": 34.6617,
        "lon": 133.9305,
        "note": "アーケードの実形状は歩行者道路ポリゴンでも表示",
    },
    {
        "name": "奉還町商店街",
        "lat": 34.6555,
        "lon": 133.9115,
        "note": "アーケードの実形状は歩行者道路ポリゴンでも表示",
    },
]


def build_grid(points, lat_step=0.0025, lon_step=0.003):
    cells = {}
    for point in points:
        if not isinstance(point, list) or len(point) < 2:
            continue
        lat, lon = point[0], point[1]
        row = int((lat - 34.62) // lat_step)
        col = int((lon - 133.89) // lon_step)
        key = (row, col)
        cells[key] = cells.get(key, 0) + 1
    return [
        [
            round(34.62 + row * lat_step, 6),
            round(133.89 + col * lon_step, 6),
            round(34.62 + (row + 1) * lat_step, 6),
            round(133.89 + (col + 1) * lon_step, 6),
            count,
        ]
        for (row, col), count in cells.items()
    ]


grid_sources = dict(pois)
grid_sources["urban"] = []
for category in ("food", "cafe", "bar", "convenience", "shop", "office"):
    grid_sources["urban"].extend(pois.get(category, []))

grids = {key: build_grid(points) for key, points in grid_sources.items()}

pois_json = json.dumps(pois, ensure_ascii=False, separators=(",", ":"))
grids_json = json.dumps(grids, ensure_ascii=False, separators=(",", ":"))
green_json = json.dumps(green_areas, ensure_ascii=False, separators=(",", ":"))
pedestrian_json = json.dumps(
    pedestrian_areas, ensure_ascii=False, separators=(",", ":")
)
transit_json = json.dumps(transit_stops, ensure_ascii=False, separators=(",", ":"))
tram_stops_json = json.dumps(tram_stops, ensure_ascii=False, separators=(",", ":"))
tram_routes_json = json.dumps(tram_routes, ensure_ascii=False, separators=(",", ":"))
extra_json = json.dumps(osm_extra, ensure_ascii=False, separators=(",", ":"))
shopping_json = json.dumps(
    shopping_streets, ensure_ascii=False, separators=(",", ":")
)
shopping_areas_json = json.dumps(
    shopping_areas, ensure_ascii=False, separators=(",", ":")
)
transit_routes_json = json.dumps(
    transit_routes, ensure_ascii=False, separators=(",", ":")
)
jinryu_json = json.dumps(jinryu, ensure_ascii=False, separators=(",", ":"))
top_flow_areas_json = json.dumps(
    top_flow_areas, ensure_ascii=False, separators=(",", ":")
)
parking_osm_json = json.dumps(
    parking_osm, ensure_ascii=False, separators=(",", ":")
)
parking_plateau_json = json.dumps(
    parking_plateau, ensure_ascii=False, separators=(",", ":")
)
parking_candidates_json = json.dumps(
    parking_candidates, ensure_ascii=False, separators=(",", ":")
)
building_age_json = json.dumps(
    building_age, ensure_ascii=False, separators=(",", ":")
)
plateau_luse_core_json = json.dumps(
    plateau_luse_core, ensure_ascii=False, separators=(",", ":")
)
flow_driver_notes_json = json.dumps(
    flow_driver_notes, ensure_ascii=False, separators=(",", ":")
)
flow_area_approx_json = json.dumps(
    flow_area_approx, ensure_ascii=False, separators=(",", ":")
)
html_title = "岡山市中心部 OSMデータ総覧（軽量版）" if LIGHTWEIGHT else "岡山市中心部 OSMデータ総覧"
html_subtitle = (
    "航空写真で見る、岡山市中心部の都市空間とOpenStreetMapデータ（PLATEAU重レイヤー除外）"
    if LIGHTWEIGHT
    else "航空写真で見る、岡山市中心部の都市空間とOpenStreetMapデータ"
)
html = r"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>__HTML_TITLE__</title>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
  <style>
    :root{--ink:#17212b;--muted:#687582;--line:#dbe2e8;--paper:#fff;--bg:#eef2f4;--accent:#176b87}
    *{box-sizing:border-box} html,body{height:100%;margin:0;font-family:"Yu Gothic UI","Hiragino Kaku Gothic ProN",sans-serif;color:var(--ink)}
    body{display:grid;grid-template-rows:auto 1fr;background:var(--bg)}
    header{display:flex;align-items:center;gap:14px;padding:11px 16px;
      background:linear-gradient(100deg,#102d3a,#176476);color:#fff;
      box-shadow:0 2px 10px rgba(0,0,0,.22);z-index:1000}
    header h1{font-size:16px;margin:0;white-space:nowrap}
    header p{font-size:12px;margin:0;color:#cfe0e8}
    #layout{min-height:0;display:grid;grid-template-columns:290px 1fr}
    aside{overflow:auto;background:var(--paper);border-right:1px solid var(--line);padding:14px}
    #map{min-width:0}
    .actions{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:7px;margin-bottom:13px}
    button,select{font:inherit}
    button{border:1px solid #bdc9d1;background:#fff;border-radius:7px;padding:8px;cursor:pointer}
    button:hover{background:#edf5f7;border-color:#6f9baa}
    .section{border-top:1px solid var(--line);padding-top:9px;margin-top:9px}
    .section h2{font-size:12px;margin:0;color:#344854;letter-spacing:.04em;cursor:pointer;
      padding:3px 20px 7px 1px;position:relative;user-select:none}
    .section h2:after{content:"−";position:absolute;right:2px;top:1px;color:#71808b;font-size:15px}
    .section.collapsed h2:after{content:"＋"}
    .section.collapsed>:not(h2){display:none}
    .section h2:hover{color:#176b87}
    .row{display:grid;grid-template-columns:18px 14px 1fr auto;align-items:center;gap:7px;padding:5px 1px;font-size:13px}
    .row input{margin:0}.dot{width:11px;height:11px;border-radius:50%}.count{color:var(--muted);font-variant-numeric:tabular-nums}
    .metric{width:100%;padding:7px;border:1px solid #bdc9d1;border-radius:7px;background:#fff}
    .note{font-size:11px;line-height:1.55;color:var(--muted);margin:9px 0 0}
    .flow-rank-label{width:26px!important;height:26px!important;border-radius:50%;color:#fff;
      display:flex;align-items:center;justify-content:center;font-weight:800;font-size:13px;
      line-height:1;border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.35)}
    .total{font-size:12px;background:#edf5f7;border-radius:8px;padding:9px 10px;margin-bottom:12px}
    .guide{font-size:12px;line-height:1.55;background:#f7fbfc;border:1px solid #d7e6eb;border-radius:10px;
      padding:10px 11px;margin-bottom:12px;color:#344854}
    .guide b{color:#164c63}.guide .mini{display:block;color:#687582;font-size:11px;margin-top:4px}
    .area-label{background:rgba(255,255,255,.88);border:1px solid #71808b;border-radius:4px;color:#26343e;
      box-shadow:none;font-size:11px;font-weight:700;padding:2px 5px}
    .area-label:before{display:none}
    .rail-station-icon{font-size:20px;line-height:24px;text-align:center;text-shadow:0 2px 5px rgba(0,0,0,.65)}
    .station-label{background:rgba(255,255,255,.92);border:1px solid #1d2730;border-radius:4px;color:#111;
      box-shadow:0 1px 4px rgba(0,0,0,.18);font-size:11px;font-weight:800;padding:2px 5px}
    .station-label:before{display:none}
    .popup{font-size:12px;line-height:1.55;min-width:190px}.popup b{font-size:14px;color:#164c63}
    .popup table{border-collapse:collapse;width:100%;margin-top:6px}.popup td{padding:2px 4px;border-bottom:1px solid #edf0f2}
    .popup td:last-child{text-align:right;font-variant-numeric:tabular-nums;font-weight:600}
    @media(max-width:760px){
      header{align-items:flex-start;flex-direction:column;gap:3px} header p{font-size:10px}
      #layout{grid-template-columns:1fr;grid-template-rows:210px 1fr}
      aside{border-right:0;border-bottom:1px solid var(--line);padding:10px}
      .section{margin-top:8px;padding-top:8px}.row{padding:3px 1px}
    }
  </style>
</head>
<body>
<header>
  <h1>__HTML_TITLE__</h1>
  <p>__HTML_SUBTITLE__</p>
</header>
<div id="layout">
  <aside>
    <div class="total" id="total"></div>
    <div class="guide">
      <b>まず見るもの</b>：航空写真＋歩行者空間・緑地・商店街・路面電車・駐車場。
      <span class="mini">人流、建物年代、バス、密度メッシュは必要な時だけONにすると読みやすいです。</span>
    </div>
    <div class="actions">
      <button id="showAll">詳細OSM点を表示</button>
      <button id="hideAll">詳細OSM点を隠す</button>
      <button id="hideThemeLayers">全レイヤーOFF</button>
    </div>
    <div class="section" style="border-top:0;margin-top:8px;padding-top:0">
      <h2>分析メモ</h2>
      <label class="row" style="grid-template-columns:18px 14px 1fr auto">
        <input id="flowDriverDayToggle" type="checkbox">
        <span class="dot" style="background:#d95f5f"></span>
        <span>分析「昼に人流が多いエリア」</span>
        <span class="count">上位10</span>
      </label>
      <label class="row" style="grid-template-columns:18px 14px 1fr auto">
        <input id="flowDriverNightToggle" type="checkbox">
        <span class="dot" style="background:#6a3d9a"></span>
        <span>分析「夜に人流が多いエリア」</span>
        <span class="count">上位10</span>
      </label>
      <p class="note">ONにすると、人流ランキング、概略エリア、商業、歩行者空間、緑地、駐車場、主要交通などを表示します。概略エリアは正式な125mメッシュ境界ではありません。</p>
    </div>
    <div class="section" style="border-top:0;margin-top:0;padding-top:0">
      <h2>背景地図</h2>
      <select id="basemap" class="metric">
        <option value="simple">地理院地図（淡色）</option>
        <option value="osm">OpenStreetMap</option>
      </select>
      <label class="row" style="grid-template-columns:18px 1fr auto;margin-top:5px">
        <input id="aerialToggle" type="checkbox">
        <span>地図を航空写真に重ねる</span>
        <span class="count" id="aerialPct">0%</span>
      </label>
      <input id="aerialOpacity" type="range" min="0" max="100" value="0"
        style="width:100%;accent-color:#176b87" aria-label="重ねる地図の濃さ">
    </div>
    <div class="section">
      <h2>OSMレイヤー</h2>
      <div id="layers"></div>
    </div>
    <div class="section">
      <h2>歩行者空間・緑地</h2>
      <label class="row" style="grid-template-columns:18px 14px 1fr auto">
        <input id="greenPolygonToggle" type="checkbox" checked>
        <span class="dot" style="background:#62a744"></span>
        <span>公園・緑地ポリゴン</span>
        <span class="count">__GREEN_COUNT__面</span>
      </label>
      <label class="row" style="grid-template-columns:18px 14px 1fr auto">
        <input id="pedestrianPolygonToggle" type="checkbox" checked>
        <span class="dot" style="background:#00a69a"></span>
        <span>歩行者道路・歩道ポリゴン</span>
        <span class="count">__PEDESTRIAN_COUNT__面</span>
      </label>
      <p class="note">面で囲うことで、歩ける場所・滞留できる場所を直感的に見られます。商店街の通りとも重ねて読むと分かりやすいです。</p>
    </div>
    <div class="section">
      <h2>観光・商業</h2>
      <label class="row">
        <input id="tourismToggle" type="checkbox">
        <span class="dot" style="background:#e59a28"></span>
        <span>観光・文化施設</span>
        <span class="count">__TOURISM_COUNT__件</span>
      </label>
      <label class="row">
        <input id="commercialToggle" type="checkbox" checked>
        <span class="dot" style="background:#f2b84b"></span>
        <span>大規模商業施設</span>
        <span class="count">__COMMERCIAL_COUNT__件</span>
      </label>
      <label class="row">
        <input id="shoppingStreetToggle" type="checkbox" checked>
        <span class="dot" style="background:#f07822"></span>
        <span>商店街の通り全体</span>
        <span class="count">__SHOPPING_AREA_COUNT__面</span>
      </label>
    </div>
    <div class="section">
      <h2>自転車・公共交通</h2>
      <label class="row">
        <input id="cyclewayToggle" type="checkbox" checked>
        <span class="dot" style="background:#1476d4"></span>
        <span>自転車レーン・自転車道</span>
        <span class="count">__CYCLEWAY_COUNT__本</span>
      </label>
      <label class="row">
        <input id="bikeParkingToggle" type="checkbox">
        <span class="dot" style="background:#596b79"></span>
        <span>駐輪場</span>
        <span class="count">__BIKE_PARKING_COUNT__件</span>
      </label>
      <label class="row">
        <input id="bikeShareToggle" type="checkbox" checked>
        <span class="dot" style="background:#16a085"></span>
        <span>シェアサイクルポート</span>
        <span class="count">__BIKE_SHARE_COUNT__件</span>
      </label>
      <label class="row">
        <input id="tramToggle" type="checkbox" checked>
        <span class="dot" style="background:#2f4858"></span>
        <span>路面電車の軌道</span>
        <span class="count">__TRAM_ROUTE_COUNT__本</span>
      </label>
      <label class="row">
        <input id="tramStopToggle" type="checkbox" checked>
        <span class="dot" style="background:#fff;border:2px solid #2f4858"></span>
        <span>路面電車の電停</span>
        <span class="count">__TRAM_STOP_COUNT__件</span>
      </label>
      <label class="row">
        <input id="tramWalkToggle" type="checkbox">
        <span class="dot" style="background:#d6e2e6"></span>
        <span>電停から徒歩圏（約250m）</span>
        <span class="count">__TRAM_STOP_COUNT__面</span>
      </label>
      <label class="row">
        <input id="transitStopsToggle" type="checkbox">
        <span class="dot" style="background:#f4511e"></span>
        <span>バス停留所・頻度</span>
        <span class="count">__TRANSIT_COUNT__件</span>
      </label>
      <label class="row">
        <input id="transitRoutesToggle" type="checkbox">
        <span class="dot" style="background:#1565c0"></span>
        <span>バス路線</span>
        <span class="count">__TRANSIT_ROUTE_COUNT__本</span>
      </label>
      <p class="note">路面電車は中心市街地の骨格なので初期ONです。バス路線・バス停は量が多いため、必要な時だけONにして見ます。停留所は円が大きく、赤いほど収録便数が多い場所です。</p>
    </div>
    <div class="section">
      <h2>分析補助レイヤー</h2>
      <label class="row">
        <input id="railWalkToggle" type="checkbox">
        <span class="dot" style="background:#cfd8dc"></span>
        <span>鉄道駅徒歩圏（約500m）</span>
        <span class="count">__RAIL_STATION_COUNT__面</span>
      </label>
      <label class="row">
        <input id="tramWalk500Toggle" type="checkbox">
        <span class="dot" style="background:#d6e2e6"></span>
        <span>電停徒歩圏（約500m）</span>
        <span class="count">__TRAM_STOP_COUNT__面</span>
      </label>
      <label class="row">
        <input id="highFreqBusWalkToggle" type="checkbox">
        <span class="dot" style="background:#ffe082"></span>
        <span>高頻度バス停徒歩圏（約300m）</span>
        <span class="count">__HIGH_FREQ_BUS_COUNT__面</span>
      </label>
      <p class="note">人流・商店街・駐車場・低未利用地と重ねると、「交通が近いのに弱い場所」「交通から遠いのに人が多い場所」が見つけやすくなります。人流エリアの正式境界は未確認のため、分析範囲円は表示しません。</p>
    </div>
    <div class="section">
      <h2>建物年代・鉄道駅</h2>
      <label class="row">
        <input id="buildingAgeToggle" type="checkbox">
        <span class="dot" style="background:#7e57c2"></span>
        <span>建物年代（PLATEAU）</span>
        <span class="count">__BUILDING_AGE_COUNT__棟</span>
      </label>
      <label class="row">
        <input id="railStationToggle" type="checkbox" checked>
        <span class="dot" style="background:#111"></span>
        <span>鉄道駅</span>
        <span class="count">__RAIL_STATION_COUNT__駅</span>
      </label>
      <p class="note">建物年代は古い建物を茶色、新しい建物を青系で表示します。重めなので初期OFFです。鉄道駅は地図の目印になるよう初期ONにしています。</p>
    </div>
    <div class="section">
      <h2>駐車場・低未利用地</h2>
      <label class="row">
        <input id="parkingOsmToggle" type="checkbox" checked>
        <span class="dot" style="background:#8a6f5a"></span>
        <span>OSM駐車場</span>
        <span class="count">__PARKING_OSM_COUNT__件</span>
      </label>
      <label class="row">
        <input id="parkingCandidatesToggle" type="checkbox">
        <span class="dot" style="background:#d5a07a"></span>
        <span>PLATEAU低未利用地候補</span>
        <span class="count">__PARKING_CANDIDATES_COUNT__面</span>
      </label>
      <p class="note">赤系の面が駐車場です。低未利用地は駐車場と確定していないため、薄い破線で初期OFFにしています。</p>
    </div>
    <div class="section">
      <h2>PLATEAU商業用地</h2>
      <label class="row">
        <input id="plateauLuseToggle" type="checkbox">
        <span class="dot" style="background:#f6c85f"></span>
        <span>中心部の商業用地</span>
        <span class="count">__PLATEAU_LUSE_COUNT__面</span>
      </label>
      <p class="note">岡山駅〜表町周辺に絞り、人流との関係を見やすくするためPLATEAU土地利用は商業用地だけを表示します。</p>
    </div>
    <div class="section">
      <h2>人流（2023年平均）</h2>
      <label class="row" style="grid-template-columns:18px 14px 1fr auto">
        <input id="flowToggle" type="checkbox">
        <span class="dot" style="background:#20aee8"></span>
        <span>時間帯別の滞在人口</span>
        <span class="count">__FLOW_COUNT__エリア</span>
      </label>
      <label class="row" style="grid-template-columns:18px 14px 1fr auto">
        <input id="flowTypeToggle" type="checkbox">
        <span class="dot" style="background:#7e57c2"></span>
        <span>人流タイプ分類</span>
        <span class="count">__FLOW_COUNT__エリア</span>
      </label>
      <select id="flowHour" class="metric">
        <option value="8時">8時</option>
        <option value="10時">10時</option>
        <option value="12時">12時</option>
        <option value="13時" selected>13時</option>
        <option value="15時">15時</option>
        <option value="18時">18時</option>
        <option value="20時">20時</option>
        <option value="22時">22時</option>
        <option value="24時">24時</option>
        <option value="26時">翌2時</option>
      </select>
      <p class="note">円が大きく濃いほど、その時間帯の推計滞在人口が多いエリアです。タイプ分類は、昼型・夕夜型・夜型・終日型のざっくり判定です。</p>
    </div>
    <div class="section">
      <h2>密度ポリゴン（約250mメッシュ）</h2>
      <select id="density" class="metric">
        <option value="none" selected>表示しない</option>
        <option value="urban">店舗・施設の総密度</option>
        <option value="food">飲食店</option>
        <option value="cafe">カフェ</option>
        <option value="bar">バー・夜間飲食</option>
        <option value="convenience">コンビニ等</option>
        <option value="shop">店舗</option>
        <option value="office">オフィス</option>
        <option value="pedestrian">歩行者系道路・地点</option>
        <option value="green">公園・緑地</option>
      </select>
      <p class="note">濃いマスほど、そのカテゴリのOSMデータが多い場所です。マスをクリックすると件数を表示します。</p>
    </div>
    <div class="section">
      <h2>表示の考え方</h2>
      <p class="note">分析値や評価は入れていません。色付きメッシュで分布をつかみ、必要なカテゴリだけ元の点を重ねて確認できます。</p>
    </div>
  </aside>
  <div id="map"></div>
</div>
<script>
const POIS=__POIS__;
const GRIDS=__GRIDS__;
const GREEN_AREAS=__GREEN_AREAS__;
const PEDESTRIAN_AREAS=__PEDESTRIAN_AREAS__;
const TRANSIT_STOPS=__TRANSIT_STOPS__;
const TRANSIT_ROUTES=__TRANSIT_ROUTES__;
const TRAM_STOPS=__TRAM_STOPS__;
const TRAM_ROUTES=__TRAM_ROUTES__;
const OSM_EXTRA=__OSM_EXTRA__;
const SHOPPING_STREETS=__SHOPPING_STREETS__;
const SHOPPING_AREAS=__SHOPPING_AREAS__;
const JINRYU=__JINRYU__;
const TOP_FLOW_AREAS=__TOP_FLOW_AREAS__;
const PARKING_OSM=__PARKING_OSM__;
const PARKING_PLATEAU=__PARKING_PLATEAU__;
const PARKING_CANDIDATES=__PARKING_CANDIDATES__;
const BUILDING_AGE=__BUILDING_AGE__;
const PLATEAU_LUSE_CORE=__PLATEAU_LUSE_CORE__;
const FLOW_DRIVER_NOTES=__FLOW_DRIVER_NOTES__;
const FLOW_AREA_APPROX=__FLOW_AREA_APPROX__;
const RAIL_STATIONS=OSM_EXTRA.rail_stations||[];

// 凡例をカテゴリ別の折りたたみ表示にする。
const initiallyClosed=new Set([
  "OSMレイヤー",
  "分析補助レイヤー",
  "建物年代・鉄道駅",
  "密度ポリゴン（約250mメッシュ）",
  "人流（2023年平均）",
  "表示の考え方"
]);
document.querySelectorAll(".section").forEach(section=>{
  const heading=section.querySelector(":scope > h2");
  if(!heading)return;
  heading.setAttribute("role","button");
  heading.setAttribute("tabindex","0");
  const setState=collapsed=>{
    section.classList.toggle("collapsed",collapsed);
    heading.setAttribute("aria-expanded",String(!collapsed));
  };
  setState(initiallyClosed.has(heading.textContent.trim()));
  const toggle=()=>setState(!section.classList.contains("collapsed"));
  heading.addEventListener("click",toggle);
  heading.addEventListener("keydown",event=>{
    if(event.key==="Enter"||event.key===" "){event.preventDefault();toggle();}
  });
});

const CONFIG={
  food:{label:"飲食店",color:"#e34f5f"},
  cafe:{label:"カフェ",color:"#a96b32"},
  bar:{label:"バー・夜間飲食",color:"#7845b5"},
  convenience:{label:"コンビニ等",color:"#18a36f"},
  shop:{label:"店舗",color:"#347cc1"},
  office:{label:"オフィス",color:"#6b7785"},
  pedestrian:{label:"歩行者系道路・地点",color:"#00a69a"},
  green:{label:"公園・緑地",color:"#5c9f38"}
};

// 初見では、岡山駅・西川緑道・表町が一画面に入り、
// 商業、歩行者空間、駐車場などが重なる中心部を見せる。
const map=L.map("map",{preferCanvas:true,zoomControl:true}).setView([34.6632,133.9248],16);
const simpleBase=L.tileLayer("https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png",{
  maxZoom:18,opacity:.65,attribution:'<a href="https://maps.gsi.go.jp/development/ichiran.html">地理院タイル</a>'
});
const osmBase=L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",{
  maxZoom:19,opacity:.65,attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
});
const aerial=L.tileLayer("https://cyberjapandata.gsi.go.jp/xyz/seamlessphoto/{z}/{x}/{y}.jpg",{
  maxZoom:18,opacity:1,attribution:'<a href="https://maps.gsi.go.jp/development/ichiran.html">地理院タイル（全国最新写真）</a>'
}).addTo(map);
let currentBase=simpleBase;
document.getElementById("basemap").onchange=e=>{
  map.removeLayer(currentBase);
  currentBase=e.target.value==="osm"?osmBase:simpleBase;
  const value=Number(document.getElementById("aerialOpacity").value);
  currentBase.setOpacity(value/100);
  if(document.getElementById("aerialToggle").checked)currentBase.addTo(map);
  aerial.bringToBack();
};
document.getElementById("aerialToggle").onchange=e=>{
  e.target.checked?currentBase.addTo(map):map.removeLayer(currentBase);
  aerial.bringToBack();
};
document.getElementById("aerialOpacity").oninput=e=>{
  const value=Number(e.target.value);
  currentBase.setOpacity(value/100);
  document.getElementById("aerialPct").textContent=`${value}%`;
};
L.control.scale({imperial:false}).addTo(map);

const canvas=L.canvas({padding:.5});
const groups={};
const layerBox=document.getElementById("layers");
let grandTotal=0;

Object.entries(CONFIG).forEach(([key,cfg])=>{
  const points=Array.isArray(POIS[key])?POIS[key]:[];
  grandTotal+=points.length;
  const group=L.layerGroup();
  points.forEach(p=>{
    if(!Array.isArray(p)||p.length<2)return;
    L.circleMarker([p[0],p[1]],{
      renderer:canvas,radius:key==="green"?4:2.5,color:cfg.color,weight:.6,
      fillColor:cfg.color,fillOpacity:key==="pedestrian"?.35:.68
    }).bindTooltip(cfg.label,{direction:"top",opacity:.9}).addTo(group);
  });
  groups[key]=group;
  const row=document.createElement("label");
  row.className="row";
  row.innerHTML=`<input type="checkbox" data-layer="${key}">
    <span class="dot" style="background:${cfg.color}"></span>
    <span>${cfg.label}</span><span class="count">${points.length.toLocaleString()}件</span>`;
  layerBox.appendChild(row);
});
document.getElementById("total").textContent=`取得済みOSMデータ：延べ ${grandTotal.toLocaleString()} 件`;

layerBox.addEventListener("change",e=>{
  const key=e.target.dataset.layer;if(!key)return;
  e.target.checked?groups[key].addTo(map):map.removeLayer(groups[key]);
});
document.getElementById("showAll").onclick=()=>{
  layerBox.querySelectorAll("input").forEach(cb=>{cb.checked=true;groups[cb.dataset.layer].addTo(map)});
};
document.getElementById("hideAll").onclick=()=>{
  layerBox.querySelectorAll("input").forEach(cb=>{cb.checked=false;map.removeLayer(groups[cb.dataset.layer])});
};
document.getElementById("hideThemeLayers").onclick=()=>{
  document.querySelectorAll('aside input[type="checkbox"]').forEach(cb=>{
    cb.checked=false;
    cb.dispatchEvent(new Event("change",{bubbles:true}));
  });
  const density=document.getElementById("density");
  density.value="none";
  drawDensity();
};

const densityGroup=L.layerGroup().addTo(map);
const densityLabels={urban:"店舗・施設の総密度",food:"飲食店",cafe:"カフェ",bar:"バー・夜間飲食",
  convenience:"コンビニ等",shop:"店舗",office:"オフィス",pedestrian:"歩行者系道路・地点",green:"公園・緑地"};
const densityColors={urban:"#e04f2f",food:"#e34f5f",cafe:"#a96b32",bar:"#7845b5",
  convenience:"#18a36f",shop:"#347cc1",office:"#6b7785",pedestrian:"#00a69a",green:"#5c9f38"};
function drawDensity(){
  densityGroup.clearLayers();
  const key=document.getElementById("density").value;
  if(key==="none")return;
  const cells=GRIDS[key]||[];
  const max=Math.max(...cells.map(c=>c[4]),1);
  cells.forEach(c=>{
    const strength=Math.sqrt(c[4]/max);
    L.rectangle([[c[0],c[1]],[c[2],c[3]]],{
      renderer:canvas,color:densityColors[key],weight:.45,fillColor:densityColors[key],
      fillOpacity:.08+.64*strength
    }).bindPopup(`<b>${densityLabels[key]}</b><br>このメッシュ：${c[4].toLocaleString()}件`)
      .bindTooltip(`${c[4].toLocaleString()}件`,{sticky:true}).addTo(densityGroup);
  });
}
drawDensity();
document.getElementById("density").onchange=drawDensity;

const greenPolygonGroup=L.geoJSON(GREEN_AREAS,{
  renderer:canvas,
  style:f=>({color:"#3f812b",weight:.8,fillColor:f.properties.category==="garden"?"#82b95a":"#67a847",fillOpacity:.42}),
  onEachFeature:(f,l)=>l.bindPopup(`<b>${f.properties.name||"公園・緑地"}</b><br>種別：${f.properties.category}<br>面積：約${Math.round(f.properties.area_m2||0).toLocaleString()}㎡`)
}).addTo(map);
document.getElementById("greenPolygonToggle").onchange=e=>e.target.checked?greenPolygonGroup.addTo(map):map.removeLayer(greenPolygonGroup);

const pedestrianNames={
  pedestrian:"歩行者専用道路",arcade:"アーケード",footway:"歩道・歩行者道",path:"小径・遊歩道"
};
const pedestrianPolygonGroup=L.geoJSON(PEDESTRIAN_AREAS,{
  renderer:canvas,
  style:f=>{
    const category=f.properties.category;
    const major=category==="pedestrian"||category==="arcade";
    return {
      color:major?"#007f78":"#1c918c",
      weight:major?1.1:.45,
      fillColor:major?"#00a69a":"#55bbb4",
      fillOpacity:major?.68:.42
    };
  },
  onEachFeature:(f,l)=>l.bindPopup(
    `<b>${f.properties.name||pedestrianNames[f.properties.category]||"歩行者空間"}</b>`+
    `<br>種別：${pedestrianNames[f.properties.category]||f.properties.category}`+
    `<br>面積：約${Math.round(f.properties.area_m2||0).toLocaleString()}㎡`
  )
}).addTo(map);
document.getElementById("pedestrianPolygonToggle").onchange=e=>
  e.target.checked?pedestrianPolygonGroup.addTo(map):map.removeLayer(pedestrianPolygonGroup);

function featureLayer(items,color,label,fillOpacity=.35){
  const group=L.layerGroup();
  items.forEach(item=>{
    const tags=item.tags||{};
    const details=Object.entries(tags).filter(([k])=>["tourism","historic","shop","operator","brand"].includes(k))
      .map(([k,v])=>`${k}: ${v}`).join("<br>");
    const popup=`<b>${item.name||label}</b><br>${label}${details?`<br>${details}`:""}`;
    if(Array.isArray(item.geometry)&&item.geometry.length>=3){
      L.polygon(item.geometry,{renderer:canvas,color,weight:1.2,fillColor:color,fillOpacity})
        .bindPopup(popup).bindTooltip(item.name||label).addTo(group);
    }else if(item.position){
      L.circleMarker(item.position,{renderer:canvas,radius:7,color,weight:1.5,fillColor:color,fillOpacity:.8})
        .bindPopup(popup).bindTooltip(item.name||label).addTo(group);
    }
  });
  return group;
}

const tourismGroup=featureLayer(OSM_EXTRA.tourism,"#e59a28","観光・文化施設",.3);
document.getElementById("tourismToggle").onchange=e=>e.target.checked?tourismGroup.addTo(map):map.removeLayer(tourismGroup);

const commercialGroup=featureLayer(OSM_EXTRA.commercial,"#f2b84b","大規模商業施設",.5).addTo(map);
document.getElementById("commercialToggle").onchange=e=>e.target.checked?commercialGroup.addTo(map):map.removeLayer(commercialGroup);

const shoppingStreetGroup=L.geoJSON(SHOPPING_AREAS,{
  renderer:canvas,
  style:{color:"#b94c08",fillColor:"#f07822",weight:2.2,fillOpacity:.72},
  onEachFeature:(feature,layer)=>layer.bindPopup(
    `<b>${feature.properties.name||"商店街"}</b><br>商店街の通り・アーケード範囲`
  ).bindTooltip(feature.properties.name||"商店街")
}).addTo(map);
document.getElementById("shoppingStreetToggle").onchange=e=>
  e.target.checked?shoppingStreetGroup.addTo(map):map.removeLayer(shoppingStreetGroup);

const cyclewayGroup=L.layerGroup().addTo(map);
OSM_EXTRA.cycleways.forEach(item=>{
  L.polyline(item.geometry,{renderer:canvas,color:"#1476d4",weight:4,opacity:.82})
    .bindPopup(`<b>${item.name==="名称なし"?"自転車レーン・自転車道":item.name}</b>`)
    .bindTooltip("自転車レーン・自転車道").addTo(cyclewayGroup);
});
document.getElementById("cyclewayToggle").onchange=e=>e.target.checked?cyclewayGroup.addTo(map):map.removeLayer(cyclewayGroup);

function pointGroup(items,color,label,radius){
  const group=L.layerGroup();
  items.forEach(item=>{
    if(!item.position)return;
    const operator=(item.tags||{}).operator||(item.tags||{}).brand||"";
    L.circleMarker(item.position,{renderer:canvas,radius,color,weight:1.4,fillColor:color,fillOpacity:.82})
      .bindPopup(`<b>${item.name==="名称なし"?label:item.name}</b>${operator?`<br>運営: ${operator}`:""}`)
      .bindTooltip(item.name==="名称なし"?label:item.name).addTo(group);
  });
  return group;
}
const bikeParkingGroup=pointGroup(OSM_EXTRA.bike_parking,"#596b79","駐輪場",4);
document.getElementById("bikeParkingToggle").onchange=e=>e.target.checked?bikeParkingGroup.addTo(map):map.removeLayer(bikeParkingGroup);
const bikeShareGroup=pointGroup(OSM_EXTRA.bike_share,"#16a085","シェアサイクルポート",7).addTo(map);
document.getElementById("bikeShareToggle").onchange=e=>e.target.checked?bikeShareGroup.addTo(map):map.removeLayer(bikeShareGroup);

const tramGroup=L.layerGroup().addTo(map);
TRAM_ROUTES.forEach(route=>{
  L.polyline(route.geometry,{
    renderer:canvas,color:"#ffffff",weight:8,opacity:.9,lineCap:"round",lineJoin:"round"
  }).addTo(tramGroup);
  L.polyline(route.geometry,{
    renderer:canvas,color:"#2f4858",weight:4.4,opacity:.95,lineCap:"round",lineJoin:"round"
  }).bindPopup(`<b>路面電車</b><br>GTFS軌道`)
    .bindTooltip("路面電車",{sticky:true}).addTo(tramGroup);
});
document.getElementById("tramToggle").onchange=e=>
  e.target.checked?tramGroup.addTo(map):map.removeLayer(tramGroup);

const tramStopGroup=L.layerGroup().addTo(map);
const maxTramTrips=Math.max(...TRAM_STOPS.map(s=>s.trips),1);
TRAM_STOPS.forEach(stop=>{
  const ratio=Math.sqrt(stop.trips/maxTramTrips);
  L.circleMarker([stop.lat,stop.lon],{
    renderer:canvas,radius:4+4*ratio,color:"#2f4858",weight:2,
    fillColor:"#fff",fillOpacity:.96
  }).bindPopup(`<b>${stop.name}</b><br>路面電車の電停<br>${stop.trips.toLocaleString()}便（GTFS収録）`)
    .bindTooltip(stop.name,{sticky:true}).addTo(tramStopGroup);
});
document.getElementById("tramStopToggle").onchange=e=>
  e.target.checked?tramStopGroup.addTo(map):map.removeLayer(tramStopGroup);

const tramWalkGroup=L.layerGroup();
TRAM_STOPS.forEach(stop=>{
  L.circle([stop.lat,stop.lon],{
    renderer:canvas,radius:250,color:"#2f4858",weight:.8,fillColor:"#d6e2e6",
    fillOpacity:.18,opacity:.55
  }).bindPopup(`<b>${stop.name}</b><br>電停から約250mの徒歩圏`)
    .bindTooltip("電停徒歩圏 約250m",{sticky:true}).addTo(tramWalkGroup);
});
document.getElementById("tramWalkToggle").onchange=e=>
  e.target.checked?tramWalkGroup.addTo(map):map.removeLayer(tramWalkGroup);

const tramWalk500Group=L.layerGroup();
TRAM_STOPS.forEach(stop=>{
  L.circle([stop.lat,stop.lon],{
    renderer:canvas,radius:500,color:"#2f4858",weight:.9,fillColor:"#d6e2e6",
    fillOpacity:.12,opacity:.5,dashArray:"5 4"
  }).bindPopup(`<b>${stop.name}</b><br>電停から約500mの徒歩圏`)
    .bindTooltip("電停徒歩圏 約500m",{sticky:true}).addTo(tramWalk500Group);
});
document.getElementById("tramWalk500Toggle").onchange=e=>
  e.target.checked?tramWalk500Group.addTo(map):map.removeLayer(tramWalk500Group);

function buildingAgeColor(year){
  if(!Number.isFinite(year))return "#8e8e8e";
  if(year<=1945)return "#6d3d22";
  if(year<=1970)return "#b8672f";
  if(year<=1990)return "#d99b2b";
  if(year<=2010)return "#7e57c2";
  return "#2c8fd6";
}
function buildingAgeLabel(year){
  if(!Number.isFinite(year))return "年代不明";
  if(year<=1945)return "1945年以前";
  if(year<=1970)return "1946〜1970年";
  if(year<=1990)return "1971〜1990年";
  if(year<=2010)return "1991〜2010年";
  return "2011年以降";
}
const buildingAgeGroup=L.geoJSON(BUILDING_AGE,{
  renderer:canvas,
  style:feature=>{
    const year=Number((feature.properties||{}).year);
    const color=buildingAgeColor(year);
    return {color,weight:.45,fillColor:color,fillOpacity:Number.isFinite(year)?.46:.18};
  },
  onEachFeature:(feature,layer)=>{
    const p=feature.properties||{};
    const year=Number(p.year);
    layer.bindPopup(
      `<b>建物年代（PLATEAU）</b><br>${buildingAgeLabel(year)}`+
      `${Number.isFinite(year)?`<br>建築年: ${year}年`:""}`+
      `${p.height?`<br>高さ: ${p.height}m`:""}`+
      `${p.usage?`<br>用途コード: ${p.usage}`:""}`
    ).bindTooltip(buildingAgeLabel(year),{sticky:true});
  }
});
document.getElementById("buildingAgeToggle").onchange=e=>
  e.target.checked?buildingAgeGroup.addTo(map):map.removeLayer(buildingAgeGroup);

const railStationGroup=L.layerGroup().addTo(map);
RAIL_STATIONS.forEach(item=>{
  if(!item.position)return;
  const icon=L.divIcon({className:"rail-station-icon",html:"🚉",iconSize:[26,26],iconAnchor:[13,13]});
  const tags=item.tags||{};
  L.marker(item.position,{icon,zIndexOffset:900})
    .bindPopup(`<b>${item.name||"鉄道駅"}</b><br>OSM鉄道駅${tags.operator?`<br>運営: ${tags.operator}`:""}`)
    .bindTooltip(item.name||"鉄道駅",{permanent:true,direction:"right",className:"station-label",offset:[8,0]})
    .addTo(railStationGroup);
});
document.getElementById("railStationToggle").onchange=e=>
  e.target.checked?railStationGroup.addTo(map):map.removeLayer(railStationGroup);

const railWalkGroup=L.layerGroup();
RAIL_STATIONS.forEach(item=>{
  if(!item.position)return;
  L.circle(item.position,{
    renderer:canvas,radius:500,color:"#263238",weight:.9,fillColor:"#cfd8dc",
    fillOpacity:.14,opacity:.55,dashArray:"6 4"
  }).bindPopup(`<b>${item.name||"鉄道駅"}</b><br>駅から約500mの徒歩圏`)
    .bindTooltip("鉄道駅徒歩圏 約500m",{sticky:true}).addTo(railWalkGroup);
});
document.getElementById("railWalkToggle").onchange=e=>
  e.target.checked?railWalkGroup.addTo(map):map.removeLayer(railWalkGroup);

const transitRoutesGroup=L.layerGroup();
TRANSIT_ROUTES.forEach(route=>{
  const isTram=route.operator==="路面電車";
  L.polyline(route.geometry,{
    renderer:canvas,color:route.color,weight:isTram?4:2.2,
    opacity:isTram?.9:.48,lineCap:"round",lineJoin:"round"
  }).bindPopup(`<b>${route.operator}</b><br>GTFS路線`)
    .bindTooltip(route.operator,{sticky:true}).addTo(transitRoutesGroup);
});
document.getElementById("transitRoutesToggle").onchange=e=>
  e.target.checked?transitRoutesGroup.addTo(map):map.removeLayer(transitRoutesGroup);

const transitStopsGroup=L.layerGroup();
const maxTrips=Math.max(...TRANSIT_STOPS.map(s=>s.trips),1);
function transitColor(value){
  const ratio=value/maxTrips;
  return ratio>.65?"#b71c1c":ratio>.35?"#e64a19":ratio>.15?"#f9a825":"#fdd835";
}
TRANSIT_STOPS.forEach(stop=>{
  const ratio=Math.sqrt(stop.trips/maxTrips);
  const radius=3+11*ratio;
  const color=transitColor(stop.trips);
  L.circleMarker([stop.lat,stop.lon],{renderer:canvas,radius,color:"#7a3300",weight:.7,fillColor:color,fillOpacity:.82})
    .bindPopup(`<b>${stop.name}</b><br>${stop.trips.toLocaleString()}便（GTFS収録便）<br>${stop.operators.join("・")}`)
    .bindTooltip(`${stop.name}: ${stop.trips.toLocaleString()}便`).addTo(transitStopsGroup);
});
document.getElementById("transitStopsToggle").onchange=e=>
  e.target.checked?transitStopsGroup.addTo(map):map.removeLayer(transitStopsGroup);

const highFreqBusThreshold=maxTrips*.45;
const highFreqBusStops=TRANSIT_STOPS.filter(stop=>stop.trips>=highFreqBusThreshold);
const highFreqBusWalkGroup=L.layerGroup();
highFreqBusStops.forEach(stop=>{
  L.circle([stop.lat,stop.lon],{
    renderer:canvas,radius:300,color:"#f9a825",weight:.9,fillColor:"#ffe082",
    fillOpacity:.14,opacity:.55,dashArray:"5 4"
  }).bindPopup(`<b>${stop.name}</b><br>高頻度バス停から約300m<br>${stop.trips.toLocaleString()}便（GTFS収録）`)
    .bindTooltip("高頻度バス停徒歩圏 約300m",{sticky:true}).addTo(highFreqBusWalkGroup);
});
document.getElementById("highFreqBusWalkToggle").onchange=e=>
  e.target.checked?highFreqBusWalkGroup.addTo(map):map.removeLayer(highFreqBusWalkGroup);

const topFlowAreaGroup=L.layerGroup();
TOP_FLOW_AREAS.forEach((area,index)=>{
  L.circle([area.lat,area.lon],{
    renderer:canvas,radius:500,color:"#00838f",weight:1.2,fillColor:"#26c6da",
    fillOpacity:.12,opacity:.7,dashArray:"6 4"
  }).bindPopup(`<b>${index+1}. ${area.name}</b><br>人流上位エリアの分析範囲<br>ピーク推計: ${area.score.toFixed(1)}千人<br><span style="color:#687582">※今後のPLATEAU土地利用・建物・駐車場分析はこの周辺に絞る方針</span>`)
    .bindTooltip(`${index+1}. ${area.name} 分析範囲`,{sticky:true}).addTo(topFlowAreaGroup);
});
const topFlowAreaToggle=document.getElementById("topFlowAreaToggle");
if(topFlowAreaToggle){
  topFlowAreaToggle.onchange=e=>
    e.target.checked?topFlowAreaGroup.addTo(map):map.removeLayer(topFlowAreaGroup);
}

const parkingTypeNames={
  surface:"平面駐車場",underground:"地下駐車場",multi_storey:"立体駐車場",
  "multi-storey":"立体駐車場",street_side:"路上・沿道駐車場",lane:"路上駐車帯",
  rooftop:"屋上駐車場",unknown:"種別不明"
};
function parkingStyle(feature){
  const type=(feature.properties||{}).type_key||"unknown";
  if(type==="underground")return {color:"#54257d",fillColor:"#9b77bd",weight:1.6,fillOpacity:.42,dashArray:"5 3"};
  if(type==="multi_storey"||type==="multi-storey"||type==="rooftop")
    return {color:"#62331d",fillColor:"#a76b42",weight:1.7,fillOpacity:.55};
  const overlap=(feature.properties||{}).overlap_status==="overlap_224";
  return {color:overlap?"#5f4633":"#6f5a48",fillColor:overlap?"#a78363":"#8a6f5a",weight:overlap?2:1.35,fillOpacity:.5};
}
function parkingPopup(feature,source){
  const p=feature.properties||{};
  const type=parkingTypeNames[p.type_key]||p.luse_class_label||"駐車場";
  const overlap=p.overlap_status==="overlap_224"?"PLATEAU低未利用地と重複":"重複なし／未判定";
  return `<b>${p.name||type}</b><br>データ: ${source}<br>種別: ${type}`+
    `<br>土地利用との関係: ${overlap}`+
    `${p.capacity?`<br>収容台数: ${p.capacity}`:""}`+
    `${p.fee?`<br>有料: ${p.fee}`:""}`+
    `${p.operator?`<br>運営: ${p.operator}`:""}`;
}
const parkingOsmGroup=L.geoJSON(PARKING_OSM,{
  renderer:canvas,
  style:parkingStyle,
  onEachFeature:(feature,layer)=>layer.bindPopup(parkingPopup(feature,"OpenStreetMap"))
    .bindTooltip(feature.properties.name||parkingTypeNames[feature.properties.type_key]||"駐車場")
}).addTo(map);
document.getElementById("parkingOsmToggle").onchange=e=>
  e.target.checked?parkingOsmGroup.addTo(map):map.removeLayer(parkingOsmGroup);

const parkingCandidatesGroup=L.geoJSON(PARKING_CANDIDATES,{
  renderer:canvas,
  style:{color:"#9b603b",fillColor:"#d5a07a",weight:1.25,fillOpacity:.2,dashArray:"5 3"},
  onEachFeature:(feature,layer)=>layer.bindPopup(
    `<b>PLATEAU低未利用地候補</b><br>駐車場とは限りません<br>${feature.properties.luse_class_label||""}`
  ).bindTooltip("低未利用地候補")
});
document.getElementById("parkingCandidatesToggle").onchange=e=>
  e.target.checked?parkingCandidatesGroup.addTo(map):map.removeLayer(parkingCandidatesGroup);

const plateauLuseColors={
  commercial:"#f6c85f"
};
const plateauLuseNames={
  commercial:"商業用地"
};
const plateauLuseGroup=L.geoJSON(PLATEAU_LUSE_CORE,{
  renderer:canvas,
  style:feature=>{
    const group=(feature.properties||{}).luse_group||"";
    const color=plateauLuseColors[group]||"#88939b";
    return {color,fillColor:color,weight:.8,fillOpacity:.28};
  },
  onEachFeature:(feature,layer)=>{
    const p=feature.properties||{};
    const label=p.luse_class_label||plateauLuseNames[p.luse_group]||"土地利用";
    layer.bindPopup(`<b>PLATEAU土地利用</b><br>${label}<br>コード: ${p.luse_class_code||""}`)
      .bindTooltip(label,{sticky:true});
  }
});
document.getElementById("plateauLuseToggle").onchange=e=>
  e.target.checked?plateauLuseGroup.addTo(map):map.removeLayer(plateauLuseGroup);

const flowGroup=L.layerGroup();
const flowTypeColors={
  "昼型":"#2c7fb8",
  "夕夜型":"#f57c00",
  "夜型":"#6a3d9a",
  "朝型":"#43a047",
  "終日型":"#455a64"
};
function flowProfile(item){
  const h=item.hourly||{};
  const avg=hours=>{
    const vals=hours.map(hour=>Number(h[`${hour}時`])||0).filter(v=>v>0);
    return vals.length?vals.reduce((a,b)=>a+b,0)/vals.length:0;
  };
  const morning=avg([7,8,9,10]);
  const day=avg([11,12,13,14,15,16]);
  const evening=avg([17,18,19,20,21]);
  const night=avg([22,23,24,25,26]);
  const all=[morning,day,evening,night];
  const max=Math.max(...all,1);
  const min=Math.min(...all);
  let type="終日型";
  if(max-min>max*.22){
    if(max===morning)type="朝型";
    else if(max===day)type="昼型";
    else if(max===evening)type="夕夜型";
    else type="夜型";
  }
  const peak=Object.entries(h).reduce((best,[hour,value])=>
    Number(value)>Number(best[1]||0)?[hour,value]:best,["",0]);
  return {type,peakHour:peak[0],peakValue:Number(peak[1]||0),morning,day,evening,night};
}
function drawFlow(){
  flowGroup.clearLayers();
  const hour=document.getElementById("flowHour").value;
  const values=JINRYU.map(item=>Number(item.hourly[hour])||0);
  const max=Math.max(...values,1);
  JINRYU.forEach(item=>{
    const value=Number(item.hourly[hour])||0;
    const ratio=Math.sqrt(value/max);
    L.circleMarker([item.lat,item.lon],{
      renderer:canvas,radius:5+22*ratio,color:"#0577a8",weight:1,
      fillColor:"#20aee8",fillOpacity:.18+.48*ratio
    }).bindPopup(`<b>${item.name}</b><br>${hour.replace("26時","翌2時")}：${value.toFixed(1)}千人<br>2023年平均推計<br><span style="color:#687582">※町名に合わせた代表点表示</span>`)
      .bindTooltip(`${item.name}: ${value.toFixed(1)}千人`).addTo(flowGroup);
  });
}
drawFlow();
document.getElementById("flowHour").onchange=drawFlow;
document.getElementById("flowToggle").onchange=e=>e.target.checked?flowGroup.addTo(map):map.removeLayer(flowGroup);

const flowTypeGroup=L.layerGroup();
const flowProfiles=JINRYU.map(item=>({item,profile:flowProfile(item)}));
const maxPeak=Math.max(...flowProfiles.map(d=>d.profile.peakValue),1);
flowProfiles.forEach(({item,profile})=>{
  const ratio=Math.sqrt(profile.peakValue/maxPeak);
  const color=flowTypeColors[profile.type]||"#455a64";
  L.circleMarker([item.lat,item.lon],{
    renderer:canvas,radius:6+17*ratio,color:"#263238",weight:.8,
    fillColor:color,fillOpacity:.72
  }).bindPopup(
    `<b>${item.name}</b><br>人流タイプ: ${profile.type}`+
    `<br>ピーク: ${profile.peakHour} / ${profile.peakValue.toFixed(1)}千人`+
    `<br><span style="color:#687582">朝 ${profile.morning.toFixed(1)} / 昼 ${profile.day.toFixed(1)} / 夕夜 ${profile.evening.toFixed(1)} / 夜 ${profile.night.toFixed(1)}</span>`+
    `<br><span style="color:#687582">※町名に合わせた代表点表示</span>`
  ).bindTooltip(`${item.name}: ${profile.type}`).addTo(flowTypeGroup);
});
document.getElementById("flowTypeToggle").onchange=e=>
  e.target.checked?flowTypeGroup.addTo(map):map.removeLayer(flowTypeGroup);

function buildFlowApproxAreaGroup(mode){
  const color=mode==="night"?"#6a3d9a":"#d95f5f";
  return L.geoJSON(FLOW_AREA_APPROX,{
    renderer:canvas,
    filter:feature=>{
      const p=feature.properties||{};
      const rank=Number(mode==="night"?p.rank_20:p.rank_13);
      return rank&&rank<=10;
    },
    style:{
      color,
      weight:2.4,
      opacity:.9,
      fill:false,
      dashArray:"8 6"
    },
    onEachFeature:(feature,layer)=>{
      const p=feature.properties||{};
      layer.bindPopup(
        `<b>${p.name||"概略エリア"}</b>`+
        `<br>昼順位: ${p.rank_13||"-"} / 夜順位: ${p.rank_20||"-"}`+
        `<br><span style="color:#687582">${p.note||"正式な境界ではありません。"}</span>`
      ).bindTooltip(`${p.name||""}: 概略エリア`,{sticky:true});
    }
  });
}
const flowApproxAreaDayGroup=buildFlowApproxAreaGroup("day");
const flowApproxAreaNightGroup=buildFlowApproxAreaGroup("night");

function driverText(drivers){
  return Array.isArray(drivers)&&drivers.length?drivers.join(" / "):"要因整理中";
}
const areaAnalysisNotes={
  "下石井エリア":{
    overview:"岡山駅南側からイオンモール岡山、杜の街グレース方面にかけての大規模商業・複合開発系エリア。",
    mobility:"交通面では、岡山駅徒歩圏にありつつ、バス停、シェアサイクル、駐車場も近い。公共交通と車来訪の両方を受け止める拠点と読める。",
    users:"昼は買物客、家族連れ、学生・若者、駅周辺で用事を済ませる人、業務ついでの来訪者が含まれると考えられる。駅からの徒歩・公共交通に加え、周辺駐車場を使った車来訪も多い可能性がある。",
    policy:"大規模商業、駐車場、歩行者空間を接続し、車から歩行へ切り替わる場所をつくることが人流に効いている。",
    day:"昼は大規模商業施設が明確な目的地になり、買物、食事、待ち合わせ、滞在が同時に発生する。駐車場も多く、郊外・周辺市街地から車で来る来訪を吸収しやすい。",
    night:"夜は昼ほどではないが、飲食と商業施設周辺の滞留が残るため、20時でも上位に残る。"
  },
  "桑田町エリア":{
    overview:"駅南側の業務・駐車場・複合施設周辺エリア。店舗件数だけでは説明しにくいが、駐車場が非常に多く、杜の街グレースなどにも近い。",
    mobility:"交通面では、駅・電停・高頻度バスへの近接は強くない。夜の人流は、公共交通よりも駐車場、車アクセス、複合施設利用で説明する必要がある。",
    users:"昼は業務目的の人、周辺施設への来訪者、車で中心部に来て用事を済ませる人が多い可能性がある。夜は仕事帰りの食事、複合施設利用、車で来て短時間滞在する人が含まれると考えられる。",
    policy:"駐車場を単なる空地ではなく、目的地への入口、歩行者ネットワークへの接続点として設計できるかが重要になる。",
    day:"昼は業務・買物・周辺施設利用、車アクセスが重なり、人流を押し上げていると考えられる。",
    night:"20時で最上位になる点が特徴的。公共交通だけでは説明しきれない、地方都市らしい車アクセス型の夜間人流を示す。"
  },
  "岡山駅エリア":{
    overview:"JR岡山駅、駅ビル、さんすて岡山、駅前商業、バス・路面電車が集中する交通結節点。",
    mobility:"交通面では、鉄道、バス、路面電車、シェアサイクルが重なる最も強いマルチモーダル拠点である。乗換人流をまちの滞在人流へ変えられるかが重要になる。",
    users:"通勤・通学者、買物客、観光客、出張者、乗換客、待ち合わせ利用者が混在していると考えられる。移動手段は鉄道、バス、路面電車、徒歩が中心とみられる。",
    policy:"駅は乗降場所だけでなく、駅ビル、バス、路面電車、商店街、カフェ、日常買物が重なると滞在と回遊を生む。",
    day:"昼は駅利用と商業利用が重なり、乗換、待ち合わせ、買物、飲食が同時に発生しやすい。",
    night:"夜は帰宅動線と飲食利用が中心になり、駅としての基礎的な人流が残る。"
  },
  "中心市街地①（本町）":{
    overview:"岡山駅東側の駅前繁華街・商業飲食混在エリア。商業、飲食、バー等、オフィス、駐車場が高密度に重なる。",
    mobility:"交通面では、岡山駅から歩けるうえ、電停・バス停のサービス密度も高い。公共交通で来て、徒歩で飲食・商業へ回遊する構造が人流を支えている可能性がある。",
    users:"昼は買物客、会社員、駅利用者、飲食利用者が重なっていると考えられる。夜は仕事帰りの飲食、会食、二次会、駅へ戻る前の滞在が多い可能性がある。",
    policy:"昼だけの商業地、夜だけの飲食街ではなく、業務、買物、飲食、交通が重なる混合用途が時間帯をまたいだ人流を生む。",
    day:"昼は商業・業務・飲食、駅前からの回遊、ランチ需要、買物・用務が重なる。",
    night:"20時でも非常に高い。昼の商業中心から夜の飲食・回遊中心へ役割を変える場所と考えられる。"
  },
  "中心市街地⑧（表町ほか）":{
    overview:"表町商店街、天満屋、クレド岡山、西大寺町商店街などがある、百貨店・アーケード商店街型の中心商業地。",
    mobility:"交通面では、鉄道駅からは少し離れるが、路面電車とバスの近さが商店街・百貨店利用を支えている。アーケードは公共交通から降りた後の徒歩回遊を受け止める装置になる。",
    users:"昼は百貨店・商店街の買物客、カフェ利用者、高齢者を含む日常利用者、近隣勤務者が含まれると考えられる。",
    policy:"アーケードや歩行者空間は、天候に左右されにくい回遊を生む。夜の人流を残すには、夜に開いている飲食、文化施設、イベント、公共空間の使い方も必要になる。",
    day:"昼は買物、カフェ、日常利用、商店街回遊が重なって強い。歩いて回れる空間がエリア内回遊を生む。",
    night:"夜は昼ほど強くない。商店街・百貨店型の集客は昼に寄りやすく、夜間は飲食集積が強い駅前・本町・磨屋町側へ重心が移ると読める。"
  },
  "中心市街地⑦（中山下ほか）":{
    overview:"表町・天満屋周辺と連続する商業・飲食・カフェ混在エリア。大型店やアーケードの影響を受けつつ、周辺に駐車場も多い。",
    mobility:"交通面では、電停・バス停のサービス密度が高く、表町方面からの徒歩回遊も受ける。公共交通で近くまで来て、商業・カフェへ歩く利用が想定される。",
    users:"昼は表町・天満屋方面から回遊する買物客、カフェ利用者、周辺で用事を済ませる人が多いと考えられる。夜は本町・磨屋町より目的的な夜間来訪は少ない可能性がある。",
    policy:"中心商業地の周辺部は、核施設だけでなく、カフェ、日常買物、駐車場、歩きやすい道があることで回遊を受け止める。",
    day:"昼は表町方面の商業回遊、カフェ利用、用事型の来訪を受ける。",
    night:"夜も上位に残るが昼よりは弱く、昼夜の中間的な性格を持つエリアとして見られる。"
  },
  "岩田町・駅前町エリア":{
    overview:"岡山駅東側・北東側に近い、駅前商業、飲食、オフィス、駐車場が混在するエリア。",
    mobility:"交通面では、岡山駅に近く、バス・路面電車、シェアサイクル、駐車場も重なる。駅から出た人流を飲食・商業の滞留へ変えやすい場所である。",
    users:"昼は駅から歩いて来る買物客、周辺オフィスの勤務者、飲食利用者が含まれると考えられる。夜は駅近くで飲食する会社員、友人同士の会食、駅へ戻る前の滞在が多い可能性がある。",
    policy:"駅前の歩行者動線を周辺街区に自然につなげられると、交通人流をまちの滞在人流へ変えやすい。",
    day:"昼は駅利用、業務、買物、飲食が重なる。駅から中心市街地へ出る入口として人の流れを受け止める。",
    night:"夜順位が高い。飲食・待ち合わせ・帰宅動線が残り、夜の滞留拠点としても機能していると考えられる。"
  },
  "駅元町エリア":{
    overview:"岡山駅西側・駅周辺の日常利用エリア。駅施設、奉還町商店街、日常買物、宿泊・居住系の利用が重なる。",
    mobility:"交通面では、鉄道駅に近く、シェアサイクルポートの容量も大きい。駅西側の生活動線や短距離移動を補完するモビリティが効いている可能性がある。",
    users:"通勤・通学者、駅西側の住民・宿泊者、奉還町方面の商店街利用者、日常買物客が含まれると考えられる。夜は帰宅、宿泊、駅利用、日常的な食事・買物が中心である可能性がある。",
    policy:"派手な大規模集客だけでなく、商店街、スーパー、宿泊、駅への安全な歩行動線が安定した人流を支える。",
    day:"昼は駅利用と周辺商業・日常買物が効く。東口側の商業回遊とは少し異なる交通結節型の人流と考えられる。",
    night:"夜も上位に残る。歓楽街的な強さではなく、帰宅、宿泊、駅利用、日常的な飲食・買物が人流を支える。"
  },
  "中心市街地②（幸町ほか）":{
    overview:"下石井・本町・表町の中間に位置する商業・飲食・業務混在エリア。大規模商業や駐車場に近く、バー等・飲食・オフィスも多い。",
    mobility:"交通面では、駅・電停・バス停・シェアサイクル・駐車場が周辺に重なる。大規模商業や飲食地へ、徒歩や短距離モビリティでにじむ人流を読む必要がある。",
    users:"昼は買物・業務・飲食のついでに周辺を移動する人が多いと考えられる。夜は飲食・バー等を目的に来る人、仕事帰りの滞在、駐車場から周辺目的地へ歩く人が含まれる可能性がある。",
    policy:"大型商業施設と周辺街区を分断せず、歩いて移動できる関係にすることで、人流が施設内部だけで完結せず周辺に広がる。",
    day:"下石井エリアに近接するが、元データでは別エリアとして集計されている。大規模商業周辺の人流を一部共有しつつ、幸町側の飲食・業務・回遊を拾う。",
    night:"夜も中位に残る。昼の大規模商業寄りの人流から、夜は飲食・駅方面への回遊・帰宅前後の滞留に性格が変わる可能性がある。"
  },
  "内山下・京橋町エリア":{
    overview:"表町から東側、水辺・緑地・公共施設方面へつながるエリア。緑地面積が大きく、駅前や本町の高密度飲食繁華街とは性格が異なる。",
    mobility:"交通面では、路面電車・バスで近づけるが、夜の目的地性は弱い。公共交通から緑地・水辺・公共施設へ歩かせる昼の回遊設計が重要になる。",
    users:"昼は買物客、公共施設利用者、散策する人、緑地や水辺へ向かう人が含まれると考えられる。夜は目的地となる飲食・娯楽の厚みが相対的に弱いため、滞在者は減りやすい可能性がある。",
    policy:"緑地や水辺、公共施設は昼の回遊や滞在には効くが、夜も人を残すには照明、安全性、夜間営業施設、イベント、公共空間の使い方をセットで考える必要がある。",
    day:"昼は買物、公共施設利用、散策、水辺・緑地利用などが重なり上位に入る。",
    night:"夜順位は下がる。中心部の夜間飲食軸からやや外れるため、夜の滞留は相対的に弱いと考えられる。"
  },
  "中心市街地④（磨屋町ほか）":{
    overview:"駅前・本町・表町の間に位置する飲食・バー等・駐車場が厚いエリア。西川沿いやNISHIGAWA TERRACE周辺、表町方面とのつながりもある。",
    mobility:"交通面では、電停・バス停の密度が高く、シェアサイクルや駐車場も近い。夜の飲食地に、公共交通・徒歩・車アクセスが複合して効いている可能性がある。",
    users:"夜は会社員、友人同士、飲食・バー等を目的に来る人が中心に含まれると考えられる。駅やオフィスから徒歩で来る人に加え、周辺駐車場を使って来る人も一定程度いる可能性がある。",
    policy:"夜の人流は、飲食店の数だけでなく、駅・オフィスから歩けること、駐車場が近いこと、夜に歩いても不安が少ない通りがあることに左右される。",
    day:"昼の順位は高くないが、中心商業地と飲食集積の間に位置する。通過・業務・飲食利用が中心と考えられる。",
    night:"夜に順位が上がる。飲食店・バー等の集積が効き、岡山のまちが昼の買物中心から夜の飲食中心へ表情を変える場所として重要。"
  }
};
function flowAnalysisText(p,mode){
  const drivers=driverText(p.drivers);
  const note=areaAnalysisNotes[p.name]||{};
  const specific=note[mode];
  const paragraphs=[
    note.overview,
    note.mobility,
    specific,
    note.users,
    note.policy
  ].filter(Boolean);
  return `${paragraphs.join("<br><br>")}<br><br>`+
    `<span style="color:#4f5d66">主な手がかり: ${drivers}</span><br>`+
    `<span style="color:#687582">※利用者像や滞在内容は、施設立地・交通条件・時間帯からの推測を含みます。</span>`;
}
function addFlowAnalysisFeature(group,feature,mode){
  const p=feature.properties||{};
  const coords=(feature.geometry||{}).coordinates||[];
  if(coords.length<2)return;
  const rank=Number(mode==="day"?p.rank_13:p.rank_20);
  if(!rank||rank>10)return;
  const color=mode==="day"?"#d95f5f":"#6a3d9a";
  const value=Number(mode==="day"?p.flow_13:p.flow_20).toFixed(1);
  const otherValue=Number(mode==="day"?p.flow_20:p.flow_13).toFixed(1);
  const mainTime=mode==="day"?"13時":"20時";
  const otherTime=mode==="day"?"20時":"13時";
  const latlng=[coords[1],coords[0]];
  L.marker(latlng,{
    icon:L.divIcon({
      className:"",
      html:`<div class="flow-rank-label" style="background:${color}">${rank}</div>`,
      iconSize:[26,26],
      iconAnchor:[13,13]
    }),
    zIndexOffset:1200
  }).bindPopup(
    `<b>${rank}位 ${p.name||"人流上位エリア"}</b>`+
    `<br>${mainTime}: ${value}千人 / ${otherTime}: ${otherValue}千人`+
    `<br><b>なぜ人流が集まるのか</b><br>${flowAnalysisText(p,mode)}`
  ).bindTooltip(`${rank}位 ${p.name||""}：${mainTime} ${value}千人`,{sticky:true})
    .addTo(group);
}
const flowDriverDayGroup=L.layerGroup();
const flowDriverNightGroup=L.layerGroup();
FLOW_DRIVER_NOTES.features.forEach(feature=>{
  addFlowAnalysisFeature(flowDriverDayGroup,feature,"day");
  addFlowAnalysisFeature(flowDriverNightGroup,feature,"night");
});
function setLayerCheckbox(id,checked=true){
  const cb=document.getElementById(id);
  if(!cb)return;
  if(cb.checked===checked)return;
  cb.checked=checked;
  cb.dispatchEvent(new Event("change",{bubbles:true}));
}
function showFlowDriverContextLayers(mode){
  const flowHour=document.getElementById("flowHour");
  const targetHour=mode==="night"?"20時":"13時";
  if(flowHour&&[...flowHour.options].some(option=>option.value===targetHour)){
    flowHour.value=targetHour;
    drawFlow();
  }
  [
    "plateauLuseToggle",
    "commercialToggle",
    "shoppingStreetToggle",
    "pedestrianPolygonToggle",
    "greenPolygonToggle",
    "parkingOsmToggle",
    "tramToggle",
    "tramStopToggle",
    "transitStopsToggle",
    "railStationToggle"
  ].forEach(id=>setLayerCheckbox(id,true));
}
function toggleAnalysisLayer(mode,checked){
  const group=mode==="night"?flowDriverNightGroup:flowDriverDayGroup;
  const areaGroup=mode==="night"?flowApproxAreaNightGroup:flowApproxAreaDayGroup;
  if(checked){
    showFlowDriverContextLayers(mode);
    areaGroup.addTo(map);
    group.addTo(map);
    bringGroupToFront(areaGroup);
    bringGroupToFront(group);
  }else{
    map.removeLayer(areaGroup);
    map.removeLayer(group);
  }
}
document.getElementById("flowDriverDayToggle").onchange=e=>{
  toggleAnalysisLayer("day",e.target.checked);
};
document.getElementById("flowDriverNightToggle").onchange=e=>{
  toggleAnalysisLayer("night",e.target.checked);
};

function bringGroupToFront(group){
  group.eachLayer(layer=>{
    if(layer.bringToFront)layer.bringToFront();
  });
}
function refreshVisualOrder(){
  [flowApproxAreaDayGroup,flowApproxAreaNightGroup,railWalkGroup,tramWalk500Group,highFreqBusWalkGroup,topFlowAreaGroup,shoppingStreetGroup,cyclewayGroup,tramGroup,tramStopGroup,bikeShareGroup,railStationGroup,flowTypeGroup,flowDriverDayGroup,flowDriverNightGroup].forEach(group=>{
    if(map.hasLayer(group))bringGroupToFront(group);
  });
}
refreshVisualOrder();
map.on("overlayadd overlayremove zoomend moveend",refreshVisualOrder);

const bounds=[];
Object.values(POIS).forEach(arr=>Array.isArray(arr)&&arr.forEach(p=>Array.isArray(p)&&p.length>1&&bounds.push([p[0],p[1]])));
</script>
</body>
</html>
"""

html = (
    html.replace("__POIS__", pois_json)
    .replace("__HTML_TITLE__", html_title)
    .replace("__HTML_SUBTITLE__", html_subtitle)
    .replace("__GRIDS__", grids_json)
    .replace("__GREEN_AREAS__", green_json)
    .replace("__PEDESTRIAN_AREAS__", pedestrian_json)
    .replace("__TRANSIT_STOPS__", transit_json)
    .replace("__TRANSIT_ROUTES__", transit_routes_json)
    .replace("__TRAM_STOPS__", tram_stops_json)
    .replace("__TRAM_ROUTES__", tram_routes_json)
    .replace("__OSM_EXTRA__", extra_json)
    .replace("__SHOPPING_STREETS__", shopping_json)
    .replace("__SHOPPING_AREAS__", shopping_areas_json)
    .replace("__JINRYU__", jinryu_json)
    .replace("__TOP_FLOW_AREAS__", top_flow_areas_json)
    .replace("__PARKING_OSM__", parking_osm_json)
    .replace("__PARKING_PLATEAU__", parking_plateau_json)
    .replace("__PARKING_CANDIDATES__", parking_candidates_json)
    .replace("__BUILDING_AGE__", building_age_json)
    .replace("__PLATEAU_LUSE_CORE__", plateau_luse_core_json)
    .replace("__FLOW_DRIVER_NOTES__", flow_driver_notes_json)
    .replace("__FLOW_AREA_APPROX__", flow_area_approx_json)
    .replace("__GREEN_COUNT__", str(len(green_areas["features"])))
    .replace("__PEDESTRIAN_COUNT__", str(len(pedestrian_areas["features"])))
    .replace("__TOURISM_COUNT__", str(len(osm_extra["tourism"])))
    .replace("__COMMERCIAL_COUNT__", str(len(osm_extra["commercial"])))
    .replace("__SHOPPING_COUNT__", str(len(shopping_streets)))
    .replace("__SHOPPING_AREA_COUNT__", str(len(shopping_areas["features"])))
    .replace("__CYCLEWAY_COUNT__", str(len(osm_extra["cycleways"])))
    .replace("__BIKE_PARKING_COUNT__", str(len(osm_extra["bike_parking"])))
    .replace("__BIKE_SHARE_COUNT__", str(len(osm_extra["bike_share"])))
    .replace("__TRAM_STOP_COUNT__", str(len(tram_stops)))
    .replace("__TRAM_ROUTE_COUNT__", str(len(tram_routes)))
    .replace("__HIGH_FREQ_BUS_COUNT__", str(high_freq_bus_count))
    .replace("__TOP_FLOW_AREA_COUNT__", str(len(top_flow_areas)))
    .replace("__TRANSIT_COUNT__", str(len(transit_stops)))
    .replace("__TRANSIT_ROUTE_COUNT__", str(len(transit_routes)))
    .replace("__BUILDING_AGE_COUNT__", str(len(building_age["features"])))
    .replace("__PLATEAU_LUSE_COUNT__", str(len(plateau_luse_core["features"])))
    .replace("__FLOW_DRIVER_NOTE_COUNT__", str(len(flow_driver_notes["features"])))
    .replace("__FLOW_AREA_APPROX_COUNT__", str(len(flow_area_approx["features"])))
    .replace("__RAIL_STATION_COUNT__", str(len(osm_extra["rail_stations"])))
    .replace("__FLOW_COUNT__", str(len(jinryu)))
    .replace("__PARKING_OSM_COUNT__", str(len(parking_osm["features"])))
    .replace("__PARKING_PLATEAU_COUNT__", str(len(parking_plateau["features"])))
    .replace(
        "__PARKING_CANDIDATES_COUNT__",
        str(len(parking_candidates["features"])),
    )
)
OUTPUT_PATH.write_text(html, encoding="utf-8")
print(f"created: {OUTPUT_PATH}")
