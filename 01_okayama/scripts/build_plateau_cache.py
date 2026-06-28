# -*- coding: utf-8 -*-
"""
build_plateau_cache.py
PLATEAUの建物データ(bldg/*.gml)を解析してJSONキャッシュを生成する。
Windowsで直接実行してください: python build_plateau_cache.py
完了後 _plateau_bldg_cache.json が生成されます。
"""
import os, json, glob, time, xml.etree.ElementTree as ET

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BLDG_DIR   = r"C:\Users\rd006\Documents\projectGIS_2026\plateau_citygml\udx\bldg"
OUT_CACHE  = os.path.join(SCRIPT_DIR, "_plateau_bldg_cache.json")

BLDG_NS = 'http://www.opengis.net/citygml/building/2.0'
GML_NS  = 'http://www.opengis.net/gml'

# 岡山市中心部（少し広めに取る）
LAT_MIN, LAT_MAX = 34.60, 34.72
LON_MIN, LON_MAX = 133.87, 133.97

USAGE_CAT = {
    "401":"業務", "402":"商業", "403":"宿泊", "404":"商業複合",
    "411":"住宅", "412":"共同住宅", "413":"店舗併用住宅", "414":"店舗併用共同住宅",
    "415":"作業所住宅",
    "421":"工業", "422":"農林水産",
    "431":"文化宗教", "451":"行政公共", "461":"交通施設",
    "462":"公共空地", "463":"その他公共",
}

LON_M = 91000.0
LAT_M = 111000.0

def poly_area_m2(ring_coords):
    if len(ring_coords) < 3: return 0.0
    n = len(ring_coords)
    A = 0.0
    for i in range(n-1):
        x1 = ring_coords[i][0]   * LON_M
        y1 = ring_coords[i][1]   * LAT_M
        x2 = ring_coords[i+1][0] * LON_M
        y2 = ring_coords[i+1][1] * LAT_M
        A += (x1*y2 - x2*y1)
    return abs(A) / 2.0

print("=== PLATEAU 建物キャッシュ生成 ===")
files = sorted(glob.glob(os.path.join(BLDG_DIR, "**", "*.gml"), recursive=True))
print(f"GMLファイル数: {len(files)}")

result = []
t_start = time.time()
skip_count = 0

for i, fpath in enumerate(files):
    if i % 50 == 0:
        elapsed = time.time() - t_start
        eta = elapsed / (i+1) * (len(files) - i) if i > 0 else 0
        print(f"  [{i}/{len(files)}] 取得済:{len(result)}棟  経過:{elapsed:.0f}s  残り推定:{eta:.0f}s")
    try:
        # 最初の座標だけ見てBBOX外は早期スキップ
        with open(fpath, 'r', encoding='utf-8') as fp:
            head = fp.read(2000)
        if 'posList' not in head and 'pos>' not in head:
            skip_count += 1
            continue
        
        root = ET.parse(fpath).getroot()
        for b in root.findall(f'.//{{{BLDG_NS}}}Building'):
            roof_pos = b.find(f'.//{{{BLDG_NS}}}lod0RoofEdge//{{{GML_NS}}}posList')
            if roof_pos is None:
                roof_pos = b.find(f'.//{{{BLDG_NS}}}lod1Solid//{{{GML_NS}}}posList')
            if roof_pos is None: continue
            
            coords_raw = roof_pos.text.strip().split()
            pts3 = [(float(coords_raw[j]), float(coords_raw[j+1]))
                    for j in range(0, len(coords_raw)-2, 3)]
            if not pts3: continue
            
            lat = sum(p[0] for p in pts3) / len(pts3)
            lon = sum(p[1] for p in pts3) / len(pts3)
            
            if not (LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX):
                continue
            
            ring_geo = [[p[1], p[0]] for p in pts3]
            fp_area = poly_area_m2(ring_geo)
            
            usage_el = b.find(f'{{{BLDG_NS}}}usage')
            year_el  = b.find(f'{{{BLDG_NS}}}yearOfConstruction')
            ht_el    = b.find(f'{{{BLDG_NS}}}measuredHeight')
            stor_el  = b.find(f'{{{BLDG_NS}}}storeysAboveGround')
            
            usage = usage_el.text.strip() if usage_el is not None else None
            year_s = year_el.text.strip() if year_el is not None else "0001"
            year = int(year_s) if year_s not in ("0001","9999","") else None
            ht_s = ht_el.text.strip() if ht_el is not None else "-9999"
            ht = float(ht_s) if ht_s not in ("-9999","9999","") else None
            stor_s = stor_el.text.strip() if stor_el is not None else "9999"
            stor = int(stor_s) if stor_s not in ("0","9999","") else None
            
            result.append({
                "lat": round(lat, 7), "lon": round(lon, 7),
                "fp": round(fp_area, 2),
                "usage": usage,
                "year": year, "ht": ht, "stor": stor
            })
    except Exception as ex:
        pass  # ファイル読み取りエラーはスキップ

elapsed = time.time() - t_start
print(f"\n完了: {len(result)}棟 / {elapsed:.1f}秒")
print(f"保存先: {OUT_CACHE}")

with open(OUT_CACHE, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, separators=(',',':'))

size = os.path.getsize(OUT_CACHE) / 1024
print(f"ファイルサイズ: {size:.0f} KB")
print("=== キャッシュ生成完了 ===")
input("Enterで終了")
