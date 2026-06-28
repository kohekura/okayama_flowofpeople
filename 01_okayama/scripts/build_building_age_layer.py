import json
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BLDG_DIR = ROOT.parent / "plateau_citygml" / "udx" / "bldg"
OUTPUT = ROOT / "_plateau_building_age.geojson"

# 初期表示とその周辺。駅西～表町～岡山城を含む。
SOUTH, WEST, NORTH, EAST = 34.650, 133.905, 34.674, 133.941

BLDG_NS = "http://www.opengis.net/citygml/building/2.0"
GML_NS = "http://www.opengis.net/gml"
BLDG = f"{{{BLDG_NS}}}Building"


def parse_ring(text):
    values = text.strip().split()
    if len(values) < 9:
        return None
    points = []
    for index in range(0, len(values) - 2, 3):
        try:
            lat = float(values[index])
            lon = float(values[index + 1])
        except ValueError:
            return None
        points.append([lon, lat])
    if len(points) < 4:
        return None
    if points[0] != points[-1]:
        points.append(points[0])
    return points


def building_feature(building):
    year_element = building.find(f"{{{BLDG_NS}}}yearOfConstruction")
    year = None
    if year_element is not None and year_element.text:
        value = year_element.text.strip()
        if value not in {"", "0001", "9999"}:
            try:
                year = int(value)
            except ValueError:
                pass

    usage_element = building.find(f"{{{BLDG_NS}}}usage")
    usage = usage_element.text.strip() if usage_element is not None and usage_element.text else None

    height_element = building.find(f"{{{BLDG_NS}}}measuredHeight")
    height = None
    if height_element is not None and height_element.text:
        try:
            candidate = float(height_element.text)
            if candidate not in {-9999, 9999}:
                height = candidate
        except ValueError:
            pass

    polygon = None
    for path in (
        f".//{{{BLDG_NS}}}lod0FootPrint//{{{GML_NS}}}posList",
        f".//{{{BLDG_NS}}}lod0RoofEdge//{{{GML_NS}}}posList",
        f".//{{{BLDG_NS}}}lod1Solid//{{{GML_NS}}}posList",
    ):
        position_list = building.find(path)
        if position_list is not None and position_list.text:
            polygon = parse_ring(position_list.text)
            if polygon:
                break
    if not polygon:
        return None

    center_lon = sum(point[0] for point in polygon[:-1]) / (len(polygon) - 1)
    center_lat = sum(point[1] for point in polygon[:-1]) / (len(polygon) - 1)
    if not (SOUTH <= center_lat <= NORTH and WEST <= center_lon <= EAST):
        return None

    return {
        "type": "Feature",
        "properties": {
            "year": year,
            "usage": usage,
            "height": height,
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [polygon],
        },
    }


features = []
files = sorted(BLDG_DIR.glob("*.gml"))
for file_index, path in enumerate(files, 1):
    try:
        for _, element in ET.iterparse(path, events=("end",)):
            if element.tag == BLDG:
                feature = building_feature(element)
                if feature:
                    features.append(feature)
                element.clear()
    except (ET.ParseError, OSError):
        continue
    if file_index % 100 == 0:
        print(f"{file_index}/{len(files)} files, {len(features)} buildings")

collection = {"type": "FeatureCollection", "features": features}
OUTPUT.write_text(
    json.dumps(collection, ensure_ascii=False, separators=(",", ":")),
    encoding="utf-8",
)

known = sum(1 for feature in features if feature["properties"]["year"])
print(f"created: {OUTPUT}")
print(f"buildings: {len(features)}, year known: {known}")
