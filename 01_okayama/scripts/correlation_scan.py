# -*- coding: utf-8 -*-
"""
correlation_scan.py  -  岡山市中心部 人流×都市構造 相関スキャン
全変数×全距離(100/200/300/500m)でスキャンし、HTMLレポートを出力する
PLATEAUキャッシュ(_plateau_bldg_cache.json)があれば建物変数を追加
"""
import os, json, math, csv, numpy as np

if os.name == "nt":
    SCRIPT_DIR      = os.path.dirname(os.path.abspath(__file__))
    PARKING_GEOJSON = r"C:\Users\rd006\Documents\projectGIS_2026\00_parking\parking.geojson"
    PARKING_PLATEAU = r"C:\Users\rd006\Documents\projectGIS_2026\00_parking\parking_plateau.geojson"
    GTFS_OKADEN     = r"C:\Users\rd006\Downloads\0kayama_GTFS\okaden"
    GTFS_RYOBI      = r"C:\Users\rd006\Downloads\0kayama_GTFS\ryobi"
    JINRYU_CSV      = r"C:\Users\rd006\Downloads\zinryu_okayama\kobetsuarea_time.csv"
else:
    SCRIPT_DIR      = "/sessions/sleepy-ecstatic-noether/mnt/01_personspace"
    PARKING_GEOJSON = "/sessions/sleepy-ecstatic-noether/mnt/projectGIS_2026/00_parking/parking.geojson"
    PARKING_PLATEAU = "/sessions/sleepy-ecstatic-noether/mnt/projectGIS_2026/00_parking/parking_plateau.geojson"
    GTFS_OKADEN     = "/sessions/sleepy-ecstatic-noether/mnt/0kayama_GTFS/okaden"
    GTFS_RYOBI      = "/sessions/sleepy-ecstatic-noether/mnt/0kayama_GTFS/ryobi"
    JINRYU_CSV      = "/sessions/sleepy-ecstatic-noether/mnt/zinryu_okayama/kobetsuarea_time.csv"

BLDG_CACHE  = os.path.join(SCRIPT_DIR, "_plateau_bldg_cache.json")
CACHE       = lambda n: os.path.join(SCRIPT_DIR, f"_overpass_{n}_cache.json")
GREEN_GEOJSON = os.path.join(SCRIPT_DIR, "green_osm.geojson")
OUT_HTML    = os.path.join(SCRIPT_DIR, "correlation_scan.html")
OUT_CSV     = os.path.join(SCRIPT_DIR, "correlation_scan.csv")

RADII = [100, 200, 300, 500]
LAT_M = 111000.0
LON_M = 91000.0

AREA_COORDS = {
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

USAGE_CAT = {
    "401":"業務","402":"商業","403":"宿泊","404":"商業複合",
    "411":"住宅","412":"共同住宅","413":"店舗併用住宅","414":"店舗併用共同住宅",
    "415":"作業所住宅","421":"工業","422":"農林水産",
    "431":"文化宗教","451":"行政公共","461":"交通施設","462":"公共空地","463":"その他公共",
}
USAGE_5 = {
    "401":"業務","402":"商業","403":"商業","404":"商業",
    "411":"住宅","412":"住宅","413":"住宅","414":"住宅","415":"住宅",
    "421":"工業","422":"工業",
    "431":"文化行政","451":"文化行政","461":"文化行政","462":"その他","463":"その他",
}

def dist_m(a1,o1,a2,o2):
    return math.sqrt(((a2-a1)*LAT_M)**2+((o2-o1)*LON_M)**2)

def in_r(ca,co,a,o,r): return dist_m(ca,co,a,o)<=r

def shannon(counts):
    t=sum(counts)
    if not t: return 0.0
    return -sum(c/t*math.log2(c/t) for c in counts if c)

def poly_area_m2(ring):
    if len(ring)<3: return 0.0
    n=len(ring); A=0.0
    for i in range(n-1):
        x1=ring[i][0]*LON_M; y1=ring[i][1]*LAT_M
        x2=ring[i+1][0]*LON_M; y2=ring[i+1][1]*LAT_M
        A+=(x1*y2-x2*y1)
    return abs(A)/2.0

def latlng_osm(e):
    if "center" in e: return e["center"]["lat"],e["center"]["lon"]
    if "lat"    in e: return e["lat"],e["lon"]
    return None

def load_json_osm(path):
    if not os.path.exists(path): return []
    with open(path) as f: return json.load(f).get("elements",[])

def vit_cat(e):
    t=e.get("tags",{})
    if t.get("office"): return "office"
    am=t.get("amenity",""); sh=t.get("shop","")
    if am in {"restaurant","cafe","fast_food","bar","pub","food_court"}: return "food"
    if am in {"government","courthouse","post_office","hospital","clinic"}: return "govt"
    if sh in {"clothes","shoes","sports","cosmetics","jewelry"}: return "clothing"
    if sh in {"hairdresser","dry_cleaning","massage","laundry","beauty"}: return "services"
    if sh in {"books","electronics","pharmacy","chemist","music","mobile_phone"}: return "specialty"
    if sh in {"convenience","variety_store","bakery","confectionery","alcohol"}: return "daily"
    if sh: return "other"
    return None

# ─── データ読み込み ───────────────────────────────────────────────────────────
print("=== データ読み込み ===")

# 人流
def load_jinryu():
    pop_d, pop_n = {}, {}
    with open(JINRYU_CSV,encoding="cp932") as f: lines=f.readlines()
    yrs=lines[1].strip().split(","); hrs=lines[3].strip().split(",")
    cols=[i for i,y in enumerate(yrs) if y.strip()=="2023"]
    dh={"10時","11時","12時","13時","14時","15時","16時","17時"}
    nh={"22時","23時","24時","25時","26時","27時","28時"}
    for line in lines[4:]:
        p=line.strip().split(","); nm=p[0].strip()
        if not nm: continue
        vd=[float(p[i]) for i in cols if hrs[i].strip() in dh and i<len(p) and p[i].strip()]
        vn=[float(p[i]) for i in cols if hrs[i].strip() in nh and i<len(p) and p[i].strip()]
        if vd: pop_d[nm]=sum(vd)/len(vd)
        if vn: pop_n[nm]=sum(vn)/len(vn)
    return pop_d, pop_n

pop_day, pop_night = load_jinryu()
print(f"  人流 昼:{len(pop_day)} 夜:{len(pop_night)}")

# 駐車場
park_osm = []
with open(PARKING_GEOJSON,encoding="utf-8") as f: gj=json.load(f)
for feat in gj["features"]:
    geom=feat["geometry"]
    if geom["type"]=="Point": park_osm.append((geom["coordinates"][1],geom["coordinates"][0]))

park_plateau = []
if os.path.exists(PARKING_PLATEAU):
    with open(PARKING_PLATEAU,encoding="utf-8") as f: gj=json.load(f)
    for feat in gj["features"]:
        geom=feat["geometry"]
        if geom["type"]=="Polygon":
            ring=geom["coordinates"][0]
            clat=sum(c[1] for c in ring)/len(ring); clon=sum(c[0] for c in ring)/len(ring)
            area=poly_area_m2(ring)
            park_plateau.append((clat,clon,area))
print(f"  駐車場 OSM:{len(park_osm)} PLATEAU面:{len(park_plateau)}")

# GTFS
def load_gtfs(d):
    stops,tps={},{}
    sf=os.path.join(d,"stops.txt")
    if not os.path.exists(sf): return stops,tps
    with open(sf,encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            try: stops[row["stop_id"]]=(float(row["stop_lat"]),float(row["stop_lon"]))
            except: pass
    stf=os.path.join(d,"stop_times.txt")
    if os.path.exists(stf):
        with open(stf,encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                tps.setdefault(row["stop_id"],set()).add(row["trip_id"])
    return stops,{k:len(v) for k,v in tps.items()}

oks,okt=load_gtfs(GTFS_OKADEN); rys,ryt=load_gtfs(GTFS_RYOBI)
all_stops={**oks,**rys}; all_trips={}
for k,v in {**okt,**ryt}.items(): all_trips[k]=all_trips.get(k,0)+v
print(f"  GTFS stops:{len(all_stops)}")

# OSM
rest=load_json_osm(CACHE("restaurant")); comm=load_json_osm(CACHE("commercial"))
offs=load_json_osm(CACHE("office"));    vit=load_json_osm(CACHE("vitality"))
print(f"  OSM 飲食:{len(rest)} 商業:{len(comm)} オフィス:{len(offs)} vitality:{len(vit)}")

# 緑地
green_pts=[]; green_areas=[]
with open(GREEN_GEOJSON,encoding="utf-8") as f: gj=json.load(f)
for feat in gj["features"]:
    geom=feat["geometry"]
    if geom["type"]=="Polygon":
        ring=geom["coordinates"][0]
        clat=sum(c[1] for c in ring)/len(ring); clon=sum(c[0] for c in ring)/len(ring)
        area=poly_area_m2(ring)
        green_pts.append((clat,clon)); green_areas.append((clat,clon,area))
print(f"  緑地:{len(green_pts)}")

# PLATEAUキャッシュ
USE_PLATEAU = os.path.exists(BLDG_CACHE)
bldg = []
if USE_PLATEAU:
    with open(BLDG_CACHE,encoding="utf-8") as f: bldg=json.load(f)
    print(f"  PLATEAU建物:{len(bldg)}棟")
else:
    print("  PLATEAU キャッシュなし → build_plateau_cache.py を実行してください")

FOOD_AM={"restaurant","pub","fast_food","food_court"}; CAFE_AM={"cafe"}; BAR_AM={"bar"}

# ─── エリア×距離で変数計算 ────────────────────────────────────────────────────
print("\n=== 変数計算 ===")
AREAS = list(AREA_COORDS.keys())
RESULTS = {}

for area,(ca,co) in AREA_COORDS.items():
    # 人流マッチング
    pop_d = pop_day.get(area)
    if pop_d is None:
        for k,v in pop_day.items():
            if k[:4]==area[:4]: pop_d=v; break
    pop_n = pop_night.get(area)
    if pop_n is None:
        for k,v in pop_night.items():
            if k[:4]==area[:4]: pop_n=v; break

    RESULTS[area]={}
    for R in RADII:
        v={}
        ca_m2=math.pi*R*R

        v["pop_day"]=pop_d; v["pop_night"]=pop_n

        # 飲食（種別）
        fn=cn=bn=0
        for e in rest:
            ll=latlng_osm(e)
            if not(ll and in_r(ca,co,*ll,R)): continue
            am=e.get("tags",{}).get("amenity","")
            if am in FOOD_AM: fn+=1
            elif am in CAFE_AM: cn+=1
            elif am in BAR_AM: bn+=1
        v["food_n"]=fn; v["cafe_n"]=cn; v["bar_n"]=bn; v["fnb_n"]=fn+cn+bn
        v["food_den"]=fn/ca_m2*1e6; v["fnb_den"]=v["fnb_n"]/ca_m2*1e6

        # 商業
        scn=spn=0
        for e in comm:
            ll=latlng_osm(e)
            if not(ll and in_r(ca,co,*ll,R)): continue
            sh=e.get("tags",{}).get("shop","")
            if sh in {"mall","department_store"}: scn+=1
            elif sh=="supermarket": spn+=1
        v["sc_n"]=scn; v["sup_n"]=spn

        # オフィス
        ofn=sum(1 for e in offs if(ll:=latlng_osm(e)) and in_r(ca,co,*ll,R))
        v["office_n"]=ofn; v["office_den"]=ofn/ca_m2*1e6

        # 駐車場
        pkn=sum(1 for a,o in park_osm if in_r(ca,co,a,o,R))
        v["park_n"]=pkn; v["park_den"]=pkn/ca_m2*1e6
        pk_area=sum(ar for la,lo,ar in park_plateau if in_r(ca,co,la,lo,R))
        v["park_area"]=pk_area; v["park_area_ratio"]=pk_area/ca_m2

        # バス
        st=[(s,all_trips.get(s,0)) for s,(sa,so) in all_stops.items() if in_r(ca,co,sa,so,R)]
        v["bus_stop_n"]=len(st); v["bus_trip_n"]=sum(t for _,t in st)
        v["bus_avg"]=sum(t for _,t in st)/len(st) if st else 0
        v["bus_den"]=v["bus_trip_n"]/ca_m2*1e6

        # 緑地
        gn=sum(1 for ga,go in green_pts if in_r(ca,co,ga,go,R))
        ga_sum=sum(ar for ga,go,ar in green_areas if in_r(ca,co,ga,go,R))
        v["green_n"]=gn; v["green_area"]=ga_sum; v["green_ratio"]=ga_sum/ca_m2

        # 業種多様性
        cats8={c:0 for c in ["food","clothing","services","specialty","daily","office","govt","other"]}
        total_sh=0
        for e in vit:
            ll=latlng_osm(e)
            if not(ll and in_r(ca,co,*ll,R)): continue
            c=vit_cat(e)
            if c: cats8[c]=cats8.get(c,0)+1; total_sh+=1
        v["H8"]=shannon(list(cats8.values()))
        v["shop_n"]=total_sh; v["shop_den"]=total_sh/ca_m2*1e6

        # ─── PLATEAU ──────────────────────────────────────────────────────
        if USE_PLATEAU:
            fp_total=0.0; usages=[]; years=[]; heights=[]
            for b in bldg:
                if not in_r(ca,co,b["lat"],b["lon"],R): continue
                fp_total+=b["fp"]
                if b["usage"]: usages.append(b["usage"])
                if b["year"]:  years.append(b["year"])
                if b["ht"]:    heights.append(b["ht"])
            bn_all=len([b for b in bldg if in_r(ca,co,b["lat"],b["lon"],R)])
            v["bldg_n"]=bn_all; v["bldg_cov"]=fp_total/ca_m2

            c14={}; c5={}
            for u in usages:
                lbl14=USAGE_CAT.get(u,"その他"); lbl5=USAGE_5.get(u,"その他")
                c14[lbl14]=c14.get(lbl14,0)+1; c5[lbl5]=c5.get(lbl5,0)+1
            v["bldg_H14"]=shannon(list(c14.values()))
            v["bldg_H5"]=shannon(list(c5.values()))

            tb=len(usages) or 1
            comm_c=sum(c14.get(x,0) for x in ["商業","宿泊","商業複合","店舗併用住宅","店舗併用共同住宅"])
            v["bldg_comm_ratio"]=comm_c/tb
            v["bldg_biz_ratio"]=c14.get("業務",0)/tb
            v["bldg_house_ratio"]=sum(c14.get(x,0) for x in ["住宅","共同住宅","作業所住宅"])/tb

            v["year_std"] =float(np.std(years))  if len(years)>=3 else None
            v["year_mean"]=float(np.mean(years)) if years else None
            v["ht_mean"]  =float(np.mean(heights)) if heights else None
            v["ht_std"]   =float(np.std(heights))  if len(heights)>=3 else None

        RESULTS[area][R]=v

# ─── 相関計算 ────────────────────────────────────────────────────────────────
print("=== 相関スキャン ===")

def corr(xs,ys):
    pairs=[(x,y) for x,y in zip(xs,ys) if x is not None and y is not None]
    if len(pairs)<5: return None,len(pairs)
    xs2,ys2=zip(*pairs)
    xs2=np.array(xs2,float); ys2=np.array(ys2,float)
    if xs2.std()==0 or ys2.std()==0: return None,len(pairs)
    return float(np.corrcoef(xs2,ys2)[0,1]),len(pairs)

VARS=[
    ("food_n","飲食店数"),("cafe_n","カフェ数"),("bar_n","バー・居酒屋"),
    ("fnb_n","飲食合計"),("fnb_den","飲食密度(/km²)"),
    ("office_n","オフィス数"),("office_den","オフィス密度"),
    ("sc_n","大規模SC"),("sup_n","スーパー"),
    ("park_n","駐車場件数(OSM)"),("park_den","駐車場密度"),
    ("park_area","駐車場面積(m²)"),("park_area_ratio","駐車場面積比率"),
    ("bus_stop_n","バス停数"),("bus_trip_n","バス総便数"),
    ("bus_avg","バス平均便数"),("bus_den","バス便数密度"),
    ("green_n","緑地件数"),("green_area","緑地面積"),("green_ratio","緑地面積比率"),
    ("H8","業種多様性H(8分類)"),
    ("shop_n","全店舗数"),("shop_den","全店舗密度"),
]
if USE_PLATEAU:
    VARS+=[
        ("bldg_n","建物数(PLATEAU)"),("bldg_cov","建蔽率"),
        ("bldg_H14","建物用途混在H(14分類)"),("bldg_H5","建物用途混在H(5分類)"),
        ("bldg_comm_ratio","建物商業系比率"),("bldg_biz_ratio","建物業務比率"),
        ("bldg_house_ratio","建物住宅比率"),
        ("year_std","建物年代多様性"),("year_mean","平均建築年"),
        ("ht_mean","平均建物高さ"),("ht_std","建物高さばらつき"),
    ]

TARGET="pop_day"
rows=[]
for vkey,vlabel in VARS:
    for R in RADII:
        xs=[RESULTS[a][R].get(vkey) for a in AREAS]
        ys=[RESULTS[a][R].get(TARGET) for a in AREAS]
        r,n=corr(xs,ys)
        rows.append({"var":vkey,"label":vlabel,"radius":R,"r":r,"n":n})

rows.sort(key=lambda x: x["r"] if x["r"] is not None else -99,reverse=True)

# CSV
with open(OUT_CSV,"w",newline="",encoding="utf-8-sig") as f:
    w=csv.DictWriter(f,fieldnames=["var","label","radius","r","n"])
    w.writeheader()
    for row in rows:
        w.writerow({"var":row["var"],"label":row["label"],"radius":row["radius"],
                    "r":f"{row['r']:.4f}" if row["r"] is not None else "NA","n":row["n"]})
print(f"  → {OUT_CSV}")

# ─── HTML ───────────────────────────────────────────────────────────────────
print("  HTMLレポート生成中...")

def bar_svg(r,w=110):
    if r is None: return '<span style="color:#aaa">N/A</span>'
    col="#1976D2" if r>=0 else "#E53935"
    px=int(abs(r)*w)
    sign="+" if r>=0 else ""
    return (f'<div style="display:flex;align-items:center;gap:5px">'
            f'<div style="width:{w}px;height:12px;background:#eee;border-radius:2px">'
            f'<div style="width:{px}px;height:12px;background:{col};border-radius:2px"></div></div>'
            f'<span style="font-size:11px;color:{col};font-weight:bold">{sign}{r:.3f}</span></div>')

def rc(r):
    if r is None: return '<td style="color:#aaa;text-align:right">—</td>'
    if   r>= 0.4: bg,co="#1A237E","#fff"
    elif r>= 0.3: bg,co="#3949AB","#fff"
    elif r>= 0.1: bg,co="#E3F2FD","#1565C0"
    elif r>=-0.1: bg,co="","#999"
    elif r>=-0.3: bg,co="#FFF3E0","#E65100"
    else:         bg,co="#FFEBEE","#B71C1C"
    fw="bold" if abs(r)>=0.3 else "normal"
    return f'<td style="text-align:right;background:{bg};color:{co};font-weight:{fw};padding:4px 8px">{r:+.3f}</td>'

var_r={}
for row in rows:
    var_r.setdefault(row["var"],{})[row["radius"]]=row["r"]
vkey_lbl={k:l for k,l in VARS}
var_order=sorted(var_r.keys(),key=lambda v:abs(var_r[v].get(500) or 0),reverse=True)

plateau_note="" if USE_PLATEAU else " ⚠️ PLATEAUキャッシュなし（build_plateau_cache.pyを実行して再度実行してください）"

with open(OUT_HTML,"w",encoding="utf-8") as f:
    def w(s): f.write(s+"\n")
    w("<!DOCTYPE html><html lang='ja'><head><meta charset='utf-8'>")
    w("<title>相関スキャン | 岡山市GIS分析</title>")
    w("<style>")
    w("body{font-family:'Meiryo',sans-serif;margin:24px;color:#222;font-size:13px;max-width:1100px}")
    w("h1{color:#1A237E;border-bottom:3px solid #3949AB;padding-bottom:8px;margin-bottom:4px}")
    w("h2{color:#283593;margin-top:32px;border-left:5px solid #5C6BC0;padding-left:10px}")
    w("table{border-collapse:collapse;width:100%;margin-top:8px}")
    w("th{background:#3949AB;color:#fff;padding:6px 10px;text-align:left;position:sticky;top:0;font-size:12px}")
    w("td{padding:4px 8px;border-bottom:1px solid #e8e8e8}")
    w("tr:hover td{background:#f0f4ff} .note{color:#666;font-size:12px;margin:4px 0 12px}")
    w("</style></head><body>")
    w("<h1>岡山市中心市街地 — 人流×都市構造 相関スキャン</h1>")
    w(f"<p class='note'>従属変数: 昼間滞在人口（2023年 10〜17時）| エリア N={len(AREAS)} | 変数 {len(VARS)}種 | 距離 100/200/300/500m{plateau_note}</p>")

    # ヒートマップ
    w("<h2>1. 変数 × 距離 相関係数ヒートマップ</h2>")
    w("<p class='note'>濃青=強正相関(r≥0.4) | 薄青=弱正相関 | 橙=弱負 | 赤=強負(r≤−0.3)</p>")
    w("<div style='overflow-x:auto'><table>")
    w("<tr><th>変数</th><th>100m</th><th>200m</th><th>300m</th><th>500m</th></tr>")
    for vk in var_order:
        rm=var_r[vk]
        r500=rm.get(500)
        row_bg="background:#E8EAF6" if r500 and r500>=0.3 else ("background:#FFF3E0" if r500 and r500<=-0.3 else "")
        w(f"<tr style='{row_bg}'><td><b>{vkey_lbl.get(vk,vk)}</b> <small style='color:#999'>{vk}</small></td>")
        for R in RADII: w(rc(rm.get(R)))
        w("</tr>")
    w("</table></div>")

    # TOP10正
    w("<h2>2. 正の相関 TOP 10</h2>")
    w("<table><tr><th>#</th><th>変数</th><th>距離</th><th>r</th><th>N</th></tr>")
    top_pos=[r for r in rows if r["r"] is not None and r["r"]>0][:10]
    for i,row in enumerate(top_pos):
        w(f"<tr style='background:#E8EAF6'><td>{i+1}</td><td>{row['label']} <small>{row['var']}</small></td>"
          f"<td>{row['radius']}m</td><td>{bar_svg(row['r'])}</td><td>{row['n']}</td></tr>")
    w("</table>")

    # TOP10負
    w("<h2>3. 負の相関 TOP 10（人流を下げる変数）</h2>")
    w("<table><tr><th>#</th><th>変数</th><th>距離</th><th>r</th><th>N</th></tr>")
    top_neg=[r for r in reversed(rows) if r["r"] is not None and r["r"]<0][:10]
    for i,row in enumerate(top_neg):
        w(f"<tr style='background:#FFF3E0'><td>{i+1}</td><td>{row['label']} <small>{row['var']}</small></td>"
          f"<td>{row['radius']}m</td><td>{bar_svg(row['r'])}</td><td>{row['n']}</td></tr>")
    w("</table>")

    # エリア別スコア表
    w("<h2>4. エリア別スコア（500m圏）</h2>")
    kv=["pop_day","H8","park_area_ratio","green_ratio","fnb_den","bus_trip_n","office_n"]
    kl=["昼間人口(千人)","業種多様性H","駐車場面積比","緑地比","飲食密度","バス便数","オフィス数"]
    if USE_PLATEAU:
        kv+=["bldg_H5","bldg_cov","year_std"]
        kl+=["建物用途混在H","建蔽率","年代多様性"]
    w("<div style='overflow-x:auto'><table>")
    w("<tr><th>エリア</th>"+"".join(f"<th>{l}</th>" for l in kl)+"</tr>")
    sorted_areas=sorted(AREAS,key=lambda a:RESULTS[a][500].get("pop_day") or 0,reverse=True)
    for area in sorted_areas:
        v5=RESULTS[area][500]
        short=area.replace("中心市街地","中心").replace("エリア","")
        w(f"<tr><td>{short}</td>")
        for vvk in kv:
            val=v5.get(vvk)
            if val is None: w("<td style='color:#aaa'>—</td>")
            elif vvk=="pop_day": w(f"<td style='font-weight:bold'>{val:.1f}</td>")
            elif "ratio" in vvk or "cov" in vvk: w(f"<td>{val*100:.1f}%</td>")
            elif vvk=="year_std": w(f"<td>{val:.1f}年</td>")
            else: w(f"<td>{val:.1f}</td>")
        w("</tr>")
    w("</table></div>")

    if USE_PLATEAU:
        w("<h2>5. Jane Jacobs 4条件 × 岡山データ</h2>")
        jj=[("①用途混在","bldg_H5","建物用途混在H(5分類)"),
            ("①用途混在","H8","業種多様性H(8分類)"),
            ("③古建物混在","year_std","建物年代多様性(std)"),
            ("④高密度","bldg_cov","建蔽率"),
            ("④高密度","bldg_n","建物数")]
        w("<table><tr><th>条件</th><th>変数</th><th>r(500m)</th><th>判定</th></tr>")
        for cond,vk,label in jj:
            rv=var_r.get(vk,{}).get(500)
            if rv is not None:
                judge="✅ 正相関" if rv>=0.2 else ("❌ 負相関" if rv<=-0.2 else "➖ 不明瞭")
                w(f"<tr><td>{cond}</td><td>{label}</td>{rc(rv)}<td>{judge}</td></tr>")
        w("</table>")

    w("<p style='margin-top:40px;color:#aaa;font-size:11px'>Generated by correlation_scan.py</p>")
    w("</body></html>")

print(f"  → {OUT_HTML}")

import datetime
with open(os.path.join(SCRIPT_DIR,"done_scan.txt"),"w",encoding="utf-8") as f:
    f.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"\n")
print("\n=== 完了 ===")
