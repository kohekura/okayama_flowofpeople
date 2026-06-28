import json
import glob
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LUSE_DIR = ROOT.parent / "00_parking" / "plateau_luse" / "udx" / "luse"
OUTPUT_PATH = ROOT / "_plateau_luse_core.geojson"

# 岡山駅-表町-後楽園手前を中心に、まちなか分析で使う範囲だけ残す。
FOCUS_BBOX = (34.652, 133.908, 34.6725, 133.9395)  # south, west, north, east
TARGET_CODES = {
    "212": ("商業用地", "commercial"),
}
MAX_POINTS_PER_RING = 90
COORD_PRECISION = 6


def lname(tag):
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def parse_pos_list(text):
    nums = [float(value) for value in text.split()]
    points = []
    for index in range(0, len(nums) - 2, 3):
        lat = nums[index]
        lon = nums[index + 1]
        points.append((lat, lon))
    return points


def bbox_of(points):
    lats = [point[0] for point in points]
    lons = [point[1] for point in points]
    return min(lats), min(lons), max(lats), max(lons)


def bbox_intersects(a, b):
    south_a, west_a, north_a, east_a = a
    south_b, west_b, north_b, east_b = b
    return not (
        north_a < south_b
        or north_b < south_a
        or east_a < west_b
        or east_b < west_a
    )


def ring_area(points):
    if len(points) < 3:
        return 0
    area = 0
    for (lat1, lon1), (lat2, lon2) in zip(points, points[1:] + points[:1]):
        area += lon1 * lat2 - lon2 * lat1
    return abs(area) / 2


def compact_ring(points):
    if len(points) > 1 and points[0] == points[-1]:
        points = points[:-1]
    if len(points) > MAX_POINTS_PER_RING:
        step = max(1, round(len(points) / MAX_POINTS_PER_RING))
        points = points[::step]
    ring = [
        [round(lon, COORD_PRECISION), round(lat, COORD_PRECISION)]
        for lat, lon in points
    ]
    if len(ring) >= 3 and ring[0] != ring[-1]:
        ring.append(ring[0])
    return ring


def feature_code(element):
    for child in element:
        if lname(child.tag) == "class":
            return (child.text or "").strip()
    return None


def extract_rings(element):
    rings = []
    for ring in element.iter():
        if lname(ring.tag) != "LinearRing":
            continue
        for pos in ring:
            if lname(pos.tag) == "posList" and pos.text:
                points = parse_pos_list(pos.text)
                if len(points) >= 4:
                    rings.append(points)
    return rings


def iter_landuse():
    for gml_path in sorted(glob.glob(str(LUSE_DIR / "*.gml"))):
        context = ET.iterparse(gml_path, events=("end",))
        for _, element in context:
            if lname(element.tag) != "LandUse":
                continue
            yield gml_path, element
            element.clear()


def main():
    features = []
    counts = Counter()
    skipped_tiny = 0

    if not LUSE_DIR.exists():
        raise SystemExit(f"luse folder not found: {LUSE_DIR}")

    for _, element in iter_landuse():
        code = feature_code(element)
        if code not in TARGET_CODES:
            continue
        label, group = TARGET_CODES[code]
        for points in extract_rings(element):
            if not bbox_intersects(bbox_of(points), FOCUS_BBOX):
                continue
            if ring_area(points) < 0.000000015:
                skipped_tiny += 1
                continue
            ring = compact_ring(points)
            if len(ring) < 4:
                continue
            features.append(
                {
                    "type": "Feature",
                    "geometry": {"type": "Polygon", "coordinates": [ring]},
                    "properties": {
                        "luse_class_code": code,
                        "luse_class_label": label,
                        "luse_group": group,
                    },
                }
            )
            counts[label] += 1

    OUTPUT_PATH.write_text(
        json.dumps(
            {"type": "FeatureCollection", "features": features},
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )
    print(f"created: {OUTPUT_PATH}")
    print(f"features: {len(features)} / skipped tiny: {skipped_tiny}")
    for label, count in counts.most_common():
        print(f"{label}: {count}")


if __name__ == "__main__":
    main()
