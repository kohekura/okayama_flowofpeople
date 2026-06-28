import ast
import csv
import json
import math
import re
from pathlib import Path

import geopandas as gpd
import pandas as pd


ROOT = Path(__file__).resolve().parent
FLOW_ROOT = Path(r"C:\Users\rd006\Downloads\zinryu_okayama")
BUILD_SCRIPT = ROOT / "build_osm_overview.py"
JINRYU_PATH = FLOW_ROOT / "kobetsuarea_time.csv"
TOSHIN_2023_PATH = FLOW_ROOT / "toshin2023.csv"
FINE_SHP_GLOB = "r2ka*.shp"

OUT_SUMMARY = ROOT / "_flow_day_night_summary.json"
OUT_NOTES = ROOT / "_flow_day_night_notes.geojson"
OUT_FINE = ROOT / "_toshin_fine_flow_base.geojson"
OUT_MD = ROOT / "人流昼夜比較_要点.md"

YEAR = "2023"
DAY_HOUR = "13時"
NIGHT_HOUR = "20時"
FOCUS_BBOX = (34.62, 133.89, 34.69, 133.95)  # south, west, north, east


def load_jinryu_coords():
    text = BUILD_SCRIPT.read_text(encoding="utf-8")
    match = re.search(r"JINRYU_COORDS\s*=\s*(\{.*?\n\})", text, re.S)
    if not match:
        raise RuntimeError("JINRYU_COORDS not found")
    return ast.literal_eval(match.group(1))


def load_hourly_flows():
    coords = load_jinryu_coords()
    with JINRYU_PATH.open("r", encoding="cp932") as f:
        lines = f.readlines()
    years = lines[1].strip().split(",")
    hours = lines[3].strip().split(",")
    year_columns = [i for i, value in enumerate(years) if value.strip() == YEAR]
    rows = []
    for line in lines[4:]:
        parts = line.strip().split(",")
        name = parts[0].strip()
        if name not in coords:
            continue
        hourly = {}
        for hour in [f"{h}時" for h in range(5, 29)]:
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
        if DAY_HOUR not in hourly or NIGHT_HOUR not in hourly:
            continue
        day = hourly[DAY_HOUR]
        night = hourly[NIGHT_HOUR]
        peak_hour, peak = max(hourly.items(), key=lambda item: item[1])
        rows.append(
            {
                "name": name,
                "lat": coords[name][0],
                "lon": coords[name][1],
                "flow_13": round(day, 1),
                "flow_20": round(night, 1),
                "delta_20_minus_13": round(night - day, 1),
                "night_day_ratio": round(night / day, 3) if day else None,
                "peak_hour": peak_hour,
                "peak": round(peak, 1),
            }
        )
    rows.sort(key=lambda item: max(item["flow_13"], item["flow_20"]), reverse=True)
    return rows


def classify(row):
    ratio = row["night_day_ratio"] or 0
    day = row["flow_13"]
    night = row["flow_20"]
    if day >= 180 and night >= 140:
        return "昼夜両方強い中心核"
    if ratio >= 0.95 and night >= 70:
        return "夜に相対的に強い"
    if day >= night * 1.8:
        return "昼型"
    if night >= day * 1.2:
        return "夜型"
    return "昼夜バランス型"


def short_note(row, rank13, rank20):
    kind = row["day_night_type"]
    if kind == "昼夜両方強い中心核":
        return "昼も夜も人流が残る中心核。商業・交通・滞留の重なりを確認。"
    if kind == "夜に相対的に強い" or kind == "夜型":
        return "20時に相対的に強い。飲食・夜間滞留・帰宅前行動の可能性。"
    if kind == "昼型":
        return "13時に強い。買物・業務・観光・駅利用の昼間活動が中心。"
    if rank13 <= 8 and rank20 > rank13 + 5:
        return "昼の順位が高いが夜は落ちる。日中目的地型の可能性。"
    if rank20 <= 8 and rank13 > rank20 + 5:
        return "夜の順位が上がる。昼の商業核とは異なる夜の目的地。"
    return "昼夜の差は中程度。周辺条件との重なりを確認。"


def build_summary():
    rows = load_hourly_flows()
    by_13 = sorted(rows, key=lambda item: item["flow_13"], reverse=True)
    by_20 = sorted(rows, key=lambda item: item["flow_20"], reverse=True)
    rank13 = {row["name"]: i + 1 for i, row in enumerate(by_13)}
    rank20 = {row["name"]: i + 1 for i, row in enumerate(by_20)}
    for row in rows:
        row["rank_13"] = rank13[row["name"]]
        row["rank_20"] = rank20[row["name"]]
        row["rank_change_20_minus_13"] = row["rank_20"] - row["rank_13"]
        row["day_night_type"] = classify(row)
        row["map_note"] = short_note(row, row["rank_13"], row["rank_20"])
        row["map_label"] = f"{row['name']} 13時{row['flow_13']} / 20時{row['flow_20']}"
    return rows, by_13, by_20


def write_note_geojson(rows):
    features = []
    for row in rows:
        if row["rank_13"] > 12 and row["rank_20"] > 12:
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
                    "type": row["day_night_type"],
                    "label": row["map_label"],
                    "note": row["map_note"],
                },
            }
        )
    OUT_NOTES.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def write_fine_base_geojson():
    if not TOSHIN_2023_PATH.exists():
        return
    flow = pd.read_csv(
        TOSHIN_2023_PATH,
        encoding="cp932",
        skiprows=2,
        names=["KEY_CODE", "area_name", "flow_2023"],
        dtype={"KEY_CODE": str},
    )
    flow = flow.dropna(subset=["KEY_CODE", "flow_2023"])
    flow["KEY_CODE"] = flow["KEY_CODE"].astype(str)
    flow["flow_2023"] = pd.to_numeric(flow["flow_2023"], errors="coerce")

    frames = []
    for shp in FLOW_ROOT.glob(FINE_SHP_GLOB):
        gdf = gpd.read_file(shp, encoding="cp932")
        gdf["KEY_CODE"] = gdf["KEY_CODE"].astype(str)
        frames.append(gdf)
    if not frames:
        return
    areas = pd.concat(frames, ignore_index=True)
    merged = areas.merge(flow, on="KEY_CODE", how="inner")
    south, west, north, east = FOCUS_BBOX
    merged = merged[
        (merged["Y_CODE"] >= south)
        & (merged["Y_CODE"] <= north)
        & (merged["X_CODE"] >= west)
        & (merged["X_CODE"] <= east)
    ].copy()
    merged = merged[merged["flow_2023"].notna()]
    if merged.empty:
        return
    merged["geometry"] = merged.geometry.simplify(0.00003, preserve_topology=True)
    out = merged[["KEY_CODE", "S_NAME", "area_name", "flow_2023", "X_CODE", "Y_CODE", "geometry"]].copy()
    out = gpd.GeoDataFrame(out, geometry="geometry", crs=merged.crs)
    out.to_file(OUT_FINE, driver="GeoJSON", encoding="utf-8")


def write_markdown(rows, by_13, by_20):
    night_risers = sorted(rows, key=lambda item: item["night_day_ratio"] or 0, reverse=True)[:6]
    rank_risers = sorted(rows, key=lambda item: item["rank_change_20_minus_13"])[:6]

    lines = []
    lines.append("# 13時・20時で見る岡山中心部の人流\n\n")
    lines.append("地図掲載を前提に、昼は13時、夜は20時に絞って整理する。13時は昼の商業・業務・観光・駅利用、20時は飲食・夜間滞留・帰宅前行動を見る時間帯として扱う。\n\n")

    lines.append("## 13時に人流が多い場所\n\n")
    lines.append("|順位|エリア|13時|20時|タイプ|読み取り|\n")
    lines.append("|---:|---|---:|---:|---|---|\n")
    for row in by_13[:8]:
        lines.append(f"|{row['rank_13']}|{row['name']}|{row['flow_13']}|{row['flow_20']}|{row['day_night_type']}|{row['map_note']}|\n")

    lines.append("\n## 20時に人流が多い場所\n\n")
    lines.append("|順位|エリア|20時|13時|タイプ|読み取り|\n")
    lines.append("|---:|---|---:|---:|---|---|\n")
    for row in by_20[:8]:
        lines.append(f"|{row['rank_20']}|{row['name']}|{row['flow_20']}|{row['flow_13']}|{row['day_night_type']}|{row['map_note']}|\n")

    lines.append("\n## 昼夜差の見どころ\n\n")
    lines.append("- 昼夜とも強い場所は、岡山の中心核として読む。商業、交通、歩行者空間、駐車場の複合条件が効いている可能性が高い。\n")
    lines.append("- 13時に強く20時に落ちる場所は、買物・業務・観光などの日中目的地性が強い。\n")
    lines.append("- 20時に相対的に強い場所は、飲食、夜間滞留、帰宅前行動の受け皿になっている可能性がある。\n")
    lines.append("- 地方都市では、夜の人流も公共交通だけでなく車アクセスや駐車場に支えられている可能性がある。\n\n")

    lines.append("## 20時に相対的に残りやすいエリア\n\n")
    lines.append("|エリア|13時|20時|20時/13時|メモ|\n")
    lines.append("|---|---:|---:|---:|---|\n")
    for row in night_risers:
        lines.append(f"|{row['name']}|{row['flow_13']}|{row['flow_20']}|{row['night_day_ratio']}|{row['map_note']}|\n")

    lines.append("\n## 地図に載せるときの整理\n\n")
    lines.append("- 13時レイヤー: 昼の商業・業務・観光の中心を見る。\n")
    lines.append("- 20時レイヤー: 夜の飲食・滞留・帰宅前行動を見る。\n")
    lines.append("- 注釈レイヤー: 上位エリアだけに短いコメントを付ける。\n")
    lines.append("- 細かい小地域ポリゴン: 2023年平均の人流の地形として背景的に使う。時間帯別の細密分布ではない点は明記する。\n\n")

    lines.append("## 要点\n\n")
    lines.append("岡山中心部は、昼は商業・業務・駅利用が重なる場所に人流が集まり、夜は飲食や滞留の性格を持つ場所が相対的に残る。昼夜の差を見ることで、単なる人流の多寡ではなく、まちの使われ方の違いを説明できる。特に地方都市では、車アクセスと駐車場が昼夜双方の人流を支える一方、歩行者回遊を分断する可能性もあるため、車で来た人をどう歩かせるかがまちづくりの論点になる。\n")
    OUT_MD.write_text("".join(lines), encoding="utf-8")


def main():
    rows, by_13, by_20 = build_summary()
    OUT_SUMMARY.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    write_note_geojson(rows)
    write_fine_base_geojson()
    write_markdown(rows, by_13, by_20)
    print(f"created: {OUT_SUMMARY}")
    print(f"created: {OUT_NOTES}")
    print(f"created: {OUT_FINE}")
    print(f"created: {OUT_MD}")


if __name__ == "__main__":
    main()
