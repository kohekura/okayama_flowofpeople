import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SUMMARY_PATH = ROOT / "_flow_day_night_summary.json"
GREEN_PATH = ROOT / "green_osm.geojson"
PARKING_PATH = ROOT.parent / "00_parking" / "parking_osm_flagged.geojson"
COMMERCIAL_CACHE = ROOT / "_overpass_commercial_cache.json"
RESTAURANT_CACHE = ROOT / "_overpass_restaurant_cache.json"
OFFICE_CACHE = ROOT / "_overpass_office_cache.json"
OSM_EXTRA_CACHE = ROOT / "_osm_extra_layers.json"
POIS_PATH = ROOT / "_map_pois_full.json"

OUT_JSON = ROOT / "_flow_driver_context.json"
OUT_NOTES = ROOT / "_flow_driver_notes.geojson"
OUT_MD = ROOT / "人流要因分析_昼夜別.md"

RADIUS_M = 500


def distance_m(lat1, lon1, lat2, lon2):
    r = 6371000
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def load_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def element_point(element):
    if "lat" in element and "lon" in element:
        return element["lat"], element["lon"]
    center = element.get("center") or {}
    if "lat" in center and "lon" in center:
        return center["lat"], center["lon"]
    bounds = element.get("bounds") or {}
    if {"minlat", "maxlat", "minlon", "maxlon"} <= set(bounds):
        return (bounds["minlat"] + bounds["maxlat"]) / 2, (bounds["minlon"] + bounds["maxlon"]) / 2
    return None


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


def within(lat, lon, point, radius=RADIUS_M):
    return point and distance_m(lat, lon, point[0], point[1]) <= radius


def sum_area_near(features, lat, lon, categories):
    total = 0.0
    count = 0
    named = []
    for feature in features:
        props = feature.get("properties", {})
        if props.get("category") not in categories:
            continue
        center = feature_center(feature)
        if not within(lat, lon, center):
            continue
        area = float(props.get("area_m2") or 0)
        total += area
        count += 1
        if props.get("name"):
            named.append(props["name"])
    return round(total), count, named[:5]


def count_features_near(features, lat, lon):
    count = 0
    for feature in features:
        if within(lat, lon, feature_center(feature)):
            count += 1
    return count


def load_tagged_points():
    points = []
    for path in [COMMERCIAL_CACHE, RESTAURANT_CACHE, OFFICE_CACHE, OSM_EXTRA_CACHE]:
        data = load_json(path, {})
        for element in data.get("elements", []):
            point = element_point(element)
            if not point:
                continue
            tags = element.get("tags", {})
            points.append({"lat": point[0], "lon": point[1], "tags": tags})
    return points


def unique_name(tags):
    name = tags.get("name") or tags.get("brand") or tags.get("operator") or ""
    return name.strip()


def count_tagged(points, lat, lon, predicate):
    keys = set()
    names = []
    for point in points:
        if not within(lat, lon, (point["lat"], point["lon"])):
            continue
        tags = point["tags"]
        if predicate(tags):
            name = unique_name(tags)
            key = name or f"{round(point['lat'], 5)},{round(point['lon'], 5)},{tags.get('shop') or tags.get('amenity') or tags.get('tourism') or tags.get('office') or ''}"
            if key in keys:
                continue
            keys.add(key)
            if name and name not in names:
                names.append(name)
    return len(keys), names[:6]


def count_simple_pois(pois, key, lat, lon):
    return sum(1 for p in pois.get(key, []) if len(p) >= 2 and within(lat, lon, (p[0], p[1])))


def strongest_drivers(row):
    drivers = []
    if row["large_commercial"] >= 2:
        drivers.append("大規模商業")
    if row["supermarket"] >= 3:
        drivers.append("スーパー・日常買物")
    if row["restaurant"] + row["fast_food"] >= 60:
        drivers.append("飲食集積")
    if row["bar_pub"] >= 18:
        drivers.append("夜間飲食")
    if row["cafe_tagged"] >= 10 or row["cafe_poi"] >= 10:
        drivers.append("カフェ")
    if row["office"] >= 25:
        drivers.append("業務・オフィス")
    if row["pedestrian_area_m2"] >= 70000:
        drivers.append("歩行者空間")
    if row["arcade_area_m2"] >= 3000:
        drivers.append("商店街・アーケード")
    if row["green_area_m2"] >= 80000:
        drivers.append("緑地・観光散策")
    if row["parking"] >= 180:
        drivers.append("駐車場アクセス")
    return drivers[:5] or ["複合要因"]


def read_context():
    flows = load_json(SUMMARY_PATH, [])
    green = load_json(GREEN_PATH, {"features": []}).get("features", [])
    parking = load_json(PARKING_PATH, {"features": []}).get("features", [])
    pois = load_json(POIS_PATH, {})
    tagged = load_tagged_points()

    rows = []
    for flow in flows:
        lat, lon = flow["lat"], flow["lon"]
        ped_area, ped_count, ped_names = sum_area_near(
            green, lat, lon, {"pedestrian", "arcade", "footway", "path"}
        )
        arcade_area, arcade_count, arcade_names = sum_area_near(green, lat, lon, {"arcade", "pedestrian"})
        green_area, green_count, green_names = sum_area_near(green, lat, lon, {"park", "garden", "square"})
        restaurant, restaurant_names = count_tagged(tagged, lat, lon, lambda t: t.get("amenity") == "restaurant")
        fast_food, _ = count_tagged(tagged, lat, lon, lambda t: t.get("amenity") == "fast_food")
        cafe_tagged, cafe_names = count_tagged(tagged, lat, lon, lambda t: t.get("amenity") == "cafe")
        bar_pub, bar_names = count_tagged(tagged, lat, lon, lambda t: t.get("amenity") in {"bar", "pub"})
        supermarket, supermarket_names = count_tagged(tagged, lat, lon, lambda t: t.get("shop") == "supermarket")
        large_commercial, large_names = count_tagged(
            tagged,
            lat,
            lon,
            lambda t: t.get("shop") in {"mall", "department_store"}
            or (t.get("building") == "retail" and bool(unique_name(t))),
        )
        office, _ = count_tagged(tagged, lat, lon, lambda t: "office" in t)
        tourism_culture, tourism_names = count_tagged(
            tagged, lat, lon, lambda t: t.get("tourism") in {"museum", "gallery", "attraction", "zoo", "viewpoint"}
        )
        row = {
            **flow,
            "food_poi": count_simple_pois(pois, "food", lat, lon),
            "cafe_poi": count_simple_pois(pois, "cafe", lat, lon),
            "bar_poi": count_simple_pois(pois, "bar", lat, lon),
            "shop_poi": count_simple_pois(pois, "shop", lat, lon),
            "convenience_poi": count_simple_pois(pois, "convenience", lat, lon),
            "office_poi": count_simple_pois(pois, "office", lat, lon),
            "restaurant": restaurant,
            "fast_food": fast_food,
            "cafe_tagged": cafe_tagged,
            "bar_pub": bar_pub,
            "supermarket": supermarket,
            "large_commercial": large_commercial,
            "office": office,
            "tourism_culture": tourism_culture,
            "parking": count_features_near(parking, lat, lon),
            "pedestrian_area_m2": ped_area,
            "pedestrian_feature_count": ped_count,
            "arcade_area_m2": arcade_area,
            "arcade_count": arcade_count,
            "green_area_m2": green_area,
            "green_count": green_count,
            "sample_large_commercial": large_names,
            "sample_supermarket": supermarket_names,
            "sample_bar_pub": bar_names,
            "sample_cafe": cafe_names,
            "sample_tourism": tourism_names,
            "sample_pedestrian": ped_names + arcade_names,
            "sample_green": green_names,
        }
        row["drivers"] = strongest_drivers(row)
        row["driver_label"] = "・".join(row["drivers"])
        row["analysis_note"] = make_note(row)
        rows.append(row)
    return rows


def make_note(row):
    parts = []
    if row["large_commercial"] >= 2:
        parts.append("百貨店・モール等の大規模商業が集客核")
    if row["supermarket"] >= 3:
        parts.append("スーパーが多く日常買物も効く")
    if row["restaurant"] + row["fast_food"] >= 60:
        parts.append("飲食店が厚い")
    if row["bar_pub"] >= 18:
        parts.append("バー/パブが多く夜間滞留の受け皿")
    if row["cafe_tagged"] >= 10 or row["cafe_poi"] >= 10:
        parts.append("カフェが多く昼間滞留に向く")
    if row["pedestrian_area_m2"] >= 70000:
        parts.append("歩行者空間が広く回遊を受け止める")
    if row["green_area_m2"] >= 80000:
        parts.append("緑地・公園が大きく散策/観光を支える")
    if row["parking"] >= 180:
        parts.append("駐車場が多く車アクセスを支える")
    return "。".join(parts[:3]) + "。" if parts else "複数条件の組み合わせを地図で確認。"


def write_geojson(rows):
    features = []
    for row in rows:
        if row["rank_13"] > 10 and row["rank_20"] > 10:
            continue
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [row["lon"], row["lat"]]},
                "properties": {
                    "name": row["name"],
                    "flow_13": row["flow_13"],
                    "flow_20": row["flow_20"],
                    "rank_13": row["rank_13"],
                    "rank_20": row["rank_20"],
                    "drivers": row["drivers"],
                    "driver_label": row["driver_label"],
                    "note": row["analysis_note"],
                },
            }
        )
    OUT_NOTES.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def table_row(row, flow_key, rank_key):
    return (
        f"|{row[rank_key]}|{row['name']}|{row[flow_key]}|{row['driver_label']}|"
        f"{row['restaurant'] + row['fast_food']}|{row['cafe_tagged']}|{row['bar_pub']}|"
        f"{row['supermarket']}|{row['large_commercial']}|{row['parking']}|"
        f"{row['pedestrian_area_m2']:,}|{row['green_area_m2']:,}|{row['analysis_note']}|\n"
    )


def write_markdown(rows):
    by_day = sorted(rows, key=lambda r: r["rank_13"])
    by_night = sorted(rows, key=lambda r: r["rank_20"])
    lines = []
    lines.append("# 人流要因分析: 13時・20時を別々に読む\n\n")
    lines.append("単に商業地が多いかではなく、飲食、カフェ、バー、スーパー、大規模商業、歩行者空間、緑地、駐車場の重なりから、人流が多い理由を読む。集計範囲は各人流代表点から約500m。\n\n")
    lines.append("## 13時: 昼の人流が多い場所\n\n")
    lines.append("|順位|エリア|13時|主な要因|飲食|カフェ|バー/パブ|スーパー|大規模商業|駐車場|歩行者空間㎡|緑地㎡|読み取り|\n")
    lines.append("|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|\n")
    for row in by_day[:8]:
        lines.append(table_row(row, "flow_13", "rank_13"))

    lines.append("\n### 13時の要点\n\n")
    lines.append("- 下石井、岡山駅、本町は、大規模商業、飲食、歩行者空間、駐車場が重なり、昼の中心核になっている。\n")
    lines.append("- 表町は商店街・歩行者空間と商業のまとまりが効く。モール型というより、回遊型商業地として読む。\n")
    lines.append("- 桑田町は駐車場とスーパー・日常買物系の要素が強く、車アクセス型の日中目的地として確認したい。\n")
    lines.append("- 緑地が大きい場所は、買物というより散策・観光・公共空間利用の人流として分けて読む。\n\n")

    lines.append("## 20時: 夜の人流が多い場所\n\n")
    lines.append("|順位|エリア|20時|主な要因|飲食|カフェ|バー/パブ|スーパー|大規模商業|駐車場|歩行者空間㎡|緑地㎡|読み取り|\n")
    lines.append("|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|\n")
    for row in by_night[:8]:
        lines.append(table_row(row, "flow_20", "rank_20"))

    lines.append("\n### 20時の要点\n\n")
    lines.append("- 本町、磨屋町、田町、中央町は、バー/パブや飲食の厚みが夜の人流を支える可能性がある。\n")
    lines.append("- 桑田町は20時でも強く、夜間飲食だけでなく、車アクセス・日常買物・周辺施設の複合目的地として見る必要がある。\n")
    lines.append("- 岡山駅周辺は夜も残るが、昼ほど強くない。駅利用・商業施設・飲食が混ざるが、夜型歓楽地とは性格が違う。\n")
    lines.append("- 夜の人流は、公共交通だけではなく駐車場や車アクセスに支えられている可能性が高い。\n\n")

    lines.append("## 地図に載せる候補\n\n")
    lines.append("- 注釈レイヤー: 上位エリアに「大規模商業」「飲食集積」「夜間飲食」「歩行者空間」「駐車場アクセス」などのラベルを付ける。\n")
    lines.append("- ポップアップ: 飲食、カフェ、バー/パブ、スーパー、大規模商業、駐車場、歩行者空間面積を表示する。\n")
    lines.append("- 色分け: 昼は商業・歩行者空間、夜はバー/パブ・飲食を強調すると読みやすい。\n\n")

    lines.append("## 簡潔な結論\n\n")
    lines.append("13時の人流は、大規模商業、商店街、カフェを含む飲食、歩行者空間、駐車場アクセスが重なる場所で強い。20時の人流は、飲食とバー/パブが厚い場所で相対的に残りやすいが、岡山では車アクセスや駐車場も夜の人流を支える。したがって、人流の要因は商業地の量だけではなく、店舗の種類、滞留できる歩行者空間、車から歩行へ切り替わる入口の配置まで含めて読む必要がある。\n")
    OUT_MD.write_text("".join(lines), encoding="utf-8")


def main():
    rows = read_context()
    OUT_JSON.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    write_geojson(rows)
    write_markdown(rows)
    print(f"created: {OUT_JSON}")
    print(f"created: {OUT_NOTES}")
    print(f"created: {OUT_MD}")


if __name__ == "__main__":
    main()
