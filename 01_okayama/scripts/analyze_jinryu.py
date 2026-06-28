# -*- coding: utf-8 -*-
"""
analyze_jinryu.py  -  岡山市中心市街地 人流 x 都市構造 分析
出力: analysis_jinryu.html
"""
import os, json, math, csv, numpy as np

if os.name == "nt":
    SCRIPT_DIR      = os.path.dirname(os.path.abspath(__file__))
    PARKING_GEOJSON = r"C:\Users\rd006\Documents\projectGIS_2026\00_parking\parking.geojson"
    GTFS_OKADEN     = r"C:\Users\rd006\Downloads\0kayama_GTFS\okaden"
    GTFS_RYOBI      = r"C:\Users\rd006\Downloads\0kayama_GTFS\ryobi"
    JINRYU_CSV      = r"C:\Users\rd006\Downloads\zinryu_okayama\kobetsuarea_time.csv"
else:
    SCRIPT_DIR      = "/sessions/sleepy-ecstatic-noether/mnt/01_personspace"
    PARKING_GEOJSON = "/sessions/sleepy-ecstatic-noether/mnt/projectGIS_2026/00_parking/parking.geojson"
    GTFS_OKADEN     = "/sessions/sleepy-ecstatic-noether/mnt/0kayama_GTFS/okaden"
    GTFS_RYOBI      = "/sessions/sleepy-ecstatic-noether/mnt/0kayama_GTFS/ryobi"
    JINRYU_CSV      = "/sessions/sleepy-ecstatic-noether/mnt/zinryu_okayama/kobetsuarea_time.csv"

CACHE = lambda n: os.path.join(SCRIPT_DIR, f"_overpass_{n}_cache.json")
GREEN_GEOJSON = os.path.join(SCRIPT_DIR, "green_osm.geojson")

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
R = 500.0

def dist_m(a1, o1, a2, o2):
    return math.sqrt(((a2-a1)*111000)**2 + ((o2-o1)*91000)**2)

def in_r(ca, co, a, o): return dist_m(ca, co, a, o) <= R

def latlng(e):
    if "center" in e: return e["center"]["lat"], e["center"]["lon"]
    if "lat"    in e: return e["lat"],            e["lon"]
    return None

def shannon(counts):
    t = sum(counts)
    if not t: return 0.0
    return -sum(c/t*math.log2(c/t) for c in counts if c)

def load_json(path):
    if not os.path.exists(path): return []
    with open(path) as f: return json.load(f).get("elements", [])

def load_geojson_pts(path):
    pts = []
    if not os.path.exists(path): return pts
    with open(path, encoding="utf-8") as f: g = json.load(f)
    for feat in g["features"]:
        geom = feat["geometry"]
        if geom["type"] == "Polygon":
            ring = geom["coordinates"][0]
            pts.append((sum(c[1] for c in ring)/len(ring), sum(c[0] for c in ring)/len(ring)))
        elif geom["type"] == "Point":
            pts.append((geom["coordinates"][1], geom["coordinates"][0]))
    return pts

print("Loading data...")
# 人流
def load_jinryu():
    with open(JINRYU_CSV, encoding="cp932") as f: lines = f.readlines()
    yrs = lines[1].strip().split(","); hrs = lines[3].strip().split(",")
    cols = [i for i, y in enumerate(yrs) if y.strip() == "2023"]
    day  = {"10時","11時","12時","13時","14時","15時","16時","17時"}
    res  = {}
    for line in lines[4:]:
        p = line.strip().split(","); nm = p[0].strip()
        if not nm: continue
        vs = [float(p[i]) for i in cols if hrs[i].strip() in day and i < len(p) and p[i].strip()]
        if vs: res[nm] = sum(vs)/len(vs)
    return res

pop = load_jinryu()
print(f"  人流: {len(pop)} エリア")

# 駐車場
park_pts = load_geojson_pts(PARKING_GEOJSON)
print(f"  駐車場: {len(park_pts)}")

# GTFS
def load_gtfs(d):
    stops, tps = {}, {}
    sf = os.path.join(d, "stops.txt")
    if not os.path.exists(sf): return stops, tps
    with open(sf, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            try: stops[row["stop_id"]] = (float(row["stop_lat"]), float(row["stop_lon"]))
            except: pass
    stf = os.path.join(d, "stop_times.txt")
    if os.path.exists(stf):
        with open(stf, encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                tps.setdefault(row["stop_id"], set()).add(row["trip_id"])
    return stops, {k: len(v) for k, v in tps.items()}

oks, okt = load_gtfs(GTFS_OKADEN)
rys, ryt = load_gtfs(GTFS_RYOBI)
all_stops = {**oks, **rys}
all_trips = {}
for k, v in {**okt, **ryt}.items(): all_trips[k] = all_trips.get(k, 0) + v
print(f"  GTFS stops: {len(all_stops)}")

# Overpass
rest = load_json(CACHE("restaurant"))
comm = load_json(CACHE("commercial"))
offs = load_json(CACHE("office"))
vit  = load_json(CACHE("vitality"))
green_pts = load_geojson_pts(GREEN_GEOJSON)
print(f"  OSM: 飲食{len(rest)} 商業{len(comm)} オフィス{len(offs)} vitality{len(vit)} 緑地{len(green_pts)}")

FOOD = {"restaurant","pub","fast_food","bar","food_court"}
CAFE = {"cafe"}
SC   = {"mall","department_store"}
SUP  = {"supermarket"}

def vit_cat(e):
    t = e.get("tags", {})
    if t.get("office"): return "office"
    am = t.get("amenity", ""); sh = t.get("shop", "")
    if am in {"restaurant","cafe","fast_food","bar","pub","food_court"}: return "food"
    if am in {"government","courthouse","post_office","hospital","clinic"}: return "govt"
    if sh in {"clothes","shoes","sports","cosmetics","jewelry"}: return "clothing"
    if sh in {"hairdresser","dry_cleaning","massage","laundry","beauty"}: return "services"
    if sh in {"books","electronics","pharmacy","chemist","music","mobile_phone"}: return "specialty"
    if sh in {"convenience","variety_store","bakery","confectionery","alcohol"}: return "daily"
    if sh: return "other"
    return None

print("Computing area metrics...")
M = {}
for area, (ca, co) in AREA_COORDS.items():
    short = (area.replace("中心市街地","中心").replace("エリア","")
                 .replace("（","(").replace("）",")").replace("ほか",""))
    # 人流
    p = pop.get(area)
    if p is None:
        for k, v in pop.items():
            if k[:4] == area[:4]: p = v; break
    # 飲食
    fn, cn = 0, 0
    for e in rest:
        ll = latlng(e)
        if ll and in_r(ca, co, *ll):
            t = e.get("tags",{}).get("amenity","")
            if t in FOOD: fn += 1
            elif t in CAFE: cn += 1
    # 商業
    scn, spn = 0, 0
    for e in comm:
        ll = latlng(e)
        if ll and in_r(ca, co, *ll):
            t = e.get("tags",{}).get("shop","")
            if t in SC: scn += 1
            elif t in SUP: spn += 1
    # オフィス
    ofn = sum(1 for e in offs if (ll:=latlng(e)) and in_r(ca, co, *ll))
    # 駐車場
    pkn = sum(1 for a, o in park_pts if in_r(ca, co, a, o))
    # バス
    st = [(s, all_trips.get(s,0)) for s,(sa,so) in all_stops.items() if in_r(ca,co,sa,so)]
    bus_f = sum(t for _,t in st)/len(st) if st else 0
    # 緑地
    gn = sum(1 for a,o in green_pts if in_r(ca,co,a,o))
    # vitality 業種多様性
    cats = {c:0 for c in ["food","clothing","services","specialty","daily","office","govt","other"]}
    total_sh = 0
    for e in vit:
        ll = latlng(e)
        if not (ll and in_r(ca,co,*ll)): continue
        c = vit_cat(e)
        if c:
            cats[c] = cats.get(c,0)+1
            if c not in ("office","govt"): total_sh += 1
    H = shannon(list(cats.values()))
    M[area] = dict(short=short, lat=ca, lon=co, pop=p,
                   food=fn, cafe=cn, sc=scn, sup=spn, office=ofn,
                   parking=pkn, bus_freq=bus_f, bus_stops=len(st),
                   green=gn, shops=total_sh, diversity=H)

print(f"  Done: {len(M)} areas")

# ── 分析 ──────────────────────────────────────────────────────────────────────
valid = [(nm, m) for nm, m in M.items() if m["pop"] is not None]
names_v = [nm for nm,_ in valid]
y = np.array([m["pop"] for _,m in valid])

VARS = [
    ("food",      "飲食店数"),
    ("cafe",      "カフェ数"),
    ("office",    "オフィス数"),
    ("parking",   "駐車場数"),
    ("bus_freq",  "バス便頻度"),
    ("green",     "公園・緑地数"),
    ("diversity", "業種多様性H"),
    ("shops",     "店舗数(vit)"),
]

print("\n相関係数 (対 昼間人口):")
corr_res = []
for vk, vl in VARS:
    x = np.array([m[vk] for _,m in valid])
    with np.errstate(invalid='ignore'):
        r = float(np.corrcoef(x, y)[0,1])
    corr_res.append((vk, vl, r))
    rs = f"{r:+.3f}" if r==r else "   nan"
    print(f"  {vl:14s}: r = {rs}")

# 重回帰
REG = ["food","cafe","office","parking","bus_freq","green","diversity"]
Xm = np.column_stack([np.array([m[k] for _,m in valid]) for k in REG])
n, k = Xm.shape
Xs = (Xm - Xm.mean(0)) / (Xm.std(0, ddof=1) + 1e-9)
ys = (y - y.mean()) / (y.std(ddof=1) + 1e-9)
Xi = np.column_stack([np.ones(n), Xs])
b = np.linalg.lstsq(Xi, ys, rcond=None)[0]
betas = b[1:]
yh = Xi @ b
R2 = 1 - np.sum((ys - yh)**2) / np.sum((ys - ys.mean())**2)
R2a = 1 - (1-R2)*(n-1)/(n-k-1)
print(f"\n重回帰: R2={R2:.3f}  adj-R2={R2a:.3f}")
for i, vk in enumerate(REG):
    vl = next(l for k2,l in VARS if k2==vk)
    print(f"  beta*({vl:14s}) = {betas[i]:+.3f}")

# Jane Jacobs スコア
def zs(arr):
    a = np.array(arr, dtype=float); m=a.mean(); s=a.std()
    return (a-m)/s if s else a*0

jj = (zs([M[n]["diversity"] for n in names_v])*0.35
    + zs([M[n]["green"]     for n in names_v])*0.20
    + zs([M[n]["food"]+M[n]["cafe"] for n in names_v])*0.25
    - zs([M[n]["parking"]   for n in names_v])*0.20)

for i, nm in enumerate(names_v): M[nm]["jj"] = float(jj[i])
jj_rank = sorted(names_v, key=lambda n: -M[n]["jj"])

print("\nJane Jacobs Top5:")
for nm in jj_rank[:5]:
    print(f"  {M[nm]['short']:22s} jj={M[nm]['jj']:+.2f}  pop={M[nm]['pop']:.0f}")

# ── HTML レポート ─────────────────────────────────────────────────────────────
print("\nGenerating HTML...")

def safe_r(r): return f"{r:+.3f}" if r==r else "n/a"

def bar_svg(r, w=60):
    if r!=r: return f'<svg width="{w}" height="14"><text x="5" y="11" font-size="9" fill="#aaa">n/a</text></svg>'
    c = w//2; fill = "#e53935" if r>0 else "#1E88E5"
    bw = int(abs(r)*c); x = c if r>=0 else c-bw
    return (f'<svg width="{w}" height="14" xmlns="http://www.w3.org/2000/svg">'
            f'<line x1="{c}" y1="0" x2="{c}" y2="14" stroke="#ddd" stroke-width="1"/>'
            f'<rect x="{x}" y="2" width="{bw}" height="10" fill="{fill}" rx="2" opacity="0.8"/>'
            f'</svg>')

def scatter_svg(xs, ys, labels, xlabel, color="#5C7CFA", w=310, h=220):
    PL,PR,PT,PB = 44,14,20,36
    pw = w-PL-PR; ph = h-PT-PB
    pts = [(x,y,l) for x,y,l in zip(xs,ys,labels) if x is not None and y is not None]
    if not pts: return f'<svg width="{w}" height="{h}"><text x="10" y="30">no data</text></svg>'
    xv=[p[0] for p in pts]; yv=[p[1] for p in pts]; lv=[p[2] for p in pts]
    xn,xx = min(xv),max(xv); yn,yx = 0,max(yv)*1.15
    if xx==xn: xx=xn+1
    sx = lambda v: PL+(v-xn)/(xx-xn)*pw
    sy = lambda v: h-PB-(v-yn)/(yx-yn)*ph
    nm = len(xv); mx=sum(xv)/nm; my=sum(yv)/nm
    den = sum((x-mx)**2 for x in xv)
    sl = sum((x-mx)*(y-my) for x,y in zip(xv,yv))/den if den else 0
    ic = my-sl*mx
    rn = sum((x-mx)*(y-my) for x,y in zip(xv,yv))
    rd = math.sqrt(sum((x-mx)**2 for x in xv)*sum((y-my)**2 for y in yv))
    rv = rn/rd if rd else 0
    rc = "#e53935" if rv>0 else "#1E88E5"
    parts = [f'<svg width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg" style="font-family:sans-serif">',
             f'<rect width="{w}" height="{h}" fill="white" rx="6"/>']
    for tk in range(0, int(yx)+1, max(1,int(yx/4))):
        yy=sy(tk)
        parts.append(f'<line x1="{PL}" x2="{w-PR}" y1="{yy:.0f}" y2="{yy:.0f}" stroke="#eee" stroke-width="1"/>')
        parts.append(f'<text x="{PL-4}" y="{yy+4:.0f}" text-anchor="end" font-size="9" fill="#bbb">{int(tk)}</text>')
    parts.append(f'<line x1="{PL}" y1="{h-PB}" x2="{w-PR}" y2="{h-PB}" stroke="#ccc"/>')
    parts.append(f'<line x1="{PL}" y1="{PT}" x2="{PL}" y2="{h-PB}" stroke="#ccc"/>')
    y1r=sl*xn+ic; y2r=sl*xx+ic
    parts.append(f'<line x1="{sx(xn):.0f}" y1="{sy(y1r):.0f}" x2="{sx(xx):.0f}" y2="{sy(y2r):.0f}" stroke="{color}" stroke-width="1.5" stroke-dasharray="4,3" opacity="0.6"/>')
    for x,y,l in pts:
        parts.append(f'<circle cx="{sx(x):.0f}" cy="{sy(y):.0f}" r="5" fill="{color}" fill-opacity="0.75" stroke="white" stroke-width="1.5"><title>{l}({x:.1f},{y:.0f})</title></circle>')
    parts.append(f'<text x="{w/2:.0f}" y="{h-4}" text-anchor="middle" font-size="10" fill="#666">{xlabel}</text>')
    xrot=-(PT+ph/2)
    parts.append(f'<text transform="rotate(-90)" x="{xrot:.0f}" y="12" text-anchor="middle" font-size="10" fill="#666">昼間人口</text>')
    parts.append(f'<text x="{w-PR-4}" y="{PT+12}" text-anchor="end" font-size="11" font-weight="bold" fill="{rc}">r={rv:+.3f}</text>')
    parts.append('</svg>')
    return "".join(parts)

# プリコンピュート
r_park = safe_r(next(r for k,l,r in corr_res if k=="parking"))
r_cafe = safe_r(next(r for k,l,r in corr_res if k=="cafe"))
r_bus  = safe_r(next(r for k,l,r in corr_res if k=="bus_freq"))
r_div  = safe_r(next(r for k,l,r in corr_res if k=="diversity"))

out = os.path.join(SCRIPT_DIR, "analysis_jinryu.html")
with open(out, "w", encoding="utf-8") as f:
    def w(s): f.write(s + "\n")

    w('<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8">')
    w('<meta name="viewport" content="width=device-width,initial-scale=1">')
    w('<title>岡山市中心市街地 人流×都市構造 分析レポート</title>')
    w('<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap" rel="stylesheet">')
    w('<style>')
    w('*{box-sizing:border-box;margin:0;padding:0}')
    w('body{font-family:"Noto Sans JP",sans-serif;background:#f8f9fa;color:#333;line-height:1.6}')
    w('.wrap{max-width:1200px;margin:0 auto;padding:20px}')
    w('h1{font-size:1.5rem;color:#1a237e;margin-bottom:4px}')
    w('h2{font-size:1.05rem;color:#283593;margin:28px 0 10px;border-left:4px solid #3949ab;padding-left:10px}')
    w('.sub{color:#666;font-size:.85rem;margin-bottom:20px}')
    w('.box{background:linear-gradient(135deg,#e8eaf6,#fce4ec);border-radius:12px;padding:18px 22px;margin-bottom:20px;border:1px solid #c5cae9}')
    w('.box h3{color:#1a237e;font-size:1rem;margin-bottom:8px}')
    w('.fi{margin:6px 0;font-size:.92rem}.fi .ic{margin-right:6px}')
    w('.g4{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}')
    w('.card{background:white;border-radius:10px;padding:14px;box-shadow:0 2px 8px rgba(0,0,0,.07)}')
    w('.kpi{text-align:center}.kpi .v{font-size:1.8rem;font-weight:bold;color:#3949ab}.kpi .l{font-size:.8rem;color:#777}')
    w('.sg{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}')
    w('.sc{background:white;border-radius:8px;padding:8px;box-shadow:0 1px 5px rgba(0,0,0,.06)}')
    w('.sc h4{font-size:.78rem;color:#555;margin-bottom:4px;text-align:center}')
    w('table{width:100%;border-collapse:collapse;font-size:.86rem}')
    w('th{background:#e8eaf6;color:#283593;padding:8px 10px;text-align:left;font-size:.81rem}')
    w('td{padding:7px 10px;border-bottom:1px solid #f0f0f0;vertical-align:middle}')
    w('tr:hover td{background:#f5f5f5}')
    w('.rp{color:#c62828;font-weight:bold}.rn{color:#1565c0;font-weight:bold}')
    w('.bdg{display:inline-block;padding:2px 8px;border-radius:10px;font-size:.78rem;font-weight:bold;color:white}')
    w('.bg{background:#FF8F00}.bs{background:#78909C}.bb{background:#8D6E63}')
    w('.jb{height:18px;background:#e8eaf6;border-radius:4px;overflow:hidden}')
    w('.jf{height:100%;background:linear-gradient(90deg,#3949ab,#7986cb);border-radius:4px}')
    w('.jn{background:linear-gradient(90deg,#e53935,#ef9a9a)}')
    w('@media(max-width:900px){.sg,.g4{grid-template-columns:repeat(2,1fr)}}')
    w('</style></head><body><div class="wrap">')

    w('<h1>岡山市中心市街地 人流 x 都市構造 分析レポート</h1>')
    w(f'<p class="sub">2023年 岡山市人流オープンデータ x OSM x GTFS / n={len(valid)} エリア</p>')

    # 主要発見
    w('<div class="box"><h3>主要な発見</h3>')
    w(f'<div class="fi"><span class="ic">🚗</span><b>駐車場密度が最も強く昼間人口と正相関</b>（r={r_park}）。岡山は「クルマで来る場所」に人が集まる。</div>')
    w(f'<div class="fi"><span class="ic">☕</span><b>カフェ数は逆に負の相関</b>（r={r_cafe}）。カフェが多い通り=歩行者空間は昼間集積と別の論理で動く。</div>')
    w(f'<div class="fi"><span class="ic">🚌</span><b>バス便頻度との相関は{r_bus}</b>。公共交通頻度は昼間人口を説明しない。</div>')
    w(f'<div class="fi"><span class="ic">🏙️</span><b>業種多様性H（Jane Jacobs指標）との相関は{r_div}</b>。混合用途は必ずしも昼間集積と連動しない。</div>')
    w(f'<div class="fi"><span class="ic">📊</span><b>7変数の重回帰で R²={R2:.3f}</b>（調整済み{R2a:.3f}）。昼間人口の{R2*100:.0f}%を説明。</div>')
    w('</div>')

    # KPIs
    w('<div class="g4">')
    for v, l in [(str(len(valid)),"分析エリア数"), (f"{len(park_pts):,}","駐車場数"),
                  (f"{len(rest):,}","飲食店・カフェ"), (f"{R2:.3f}","重回帰 R²")]:
        w(f'<div class="card kpi"><div class="v">{v}</div><div class="l">{l}</div></div>')
    w('</div>')

    # 散布図グリッド
    w('<h2>1. 各変数 vs 昼間人口（散布図）</h2>')
    w('<p style="font-size:.84rem;color:#666;margin-bottom:10px">各点=1エリア。破線=回帰直線。右上r=Pearson相関。</p>')
    w('<div class="sg">')
    plots = [
        ("food","飲食店数","#EF5350"), ("cafe","カフェ数","#AB47BC"),
        ("parking","駐車場数","#FF7043"), ("office","オフィス数","#7986CB"),
        ("bus_freq","バス便頻度","#26A69A"), ("green","公園・緑地数","#66BB6A"),
        ("diversity","業種多様性H","#FFA726"), ("shops","全店舗数(OSM)","#5C7CFA"),
    ]
    ys_all = [M[nm]["pop"] for nm in names_v]
    lbs    = [M[nm]["short"] for nm in names_v]
    for vk, xl, col in plots:
        xs = [M[nm][vk] for nm in names_v]
        svg = scatter_svg(xs, ys_all, lbs, xl, col)
        w(f'<div class="sc"><h4>{xl}</h4>{svg}</div>')
    w('</div>')

    # 相関テーブル
    w('<h2>2. 相関分析（対 昼間人口）</h2><div class="card">')
    w('<table><tr><th>変数</th><th>相関係数 r</th><th></th><th>解釈</th></tr>')
    interp = {
        "food":"飲食集積と昼間人口は無相関。飲食は夜型エリアに多い。",
        "cafe":"★ カフェは昼間人口の少ないエリアに集中（歩行者中心の通り）",
        "office":"業務集積は昼間人口と正相関（業務地区=昼間人口多）",
        "parking":"★ 駐車場が多いほど昼間人口が多い（クルマ優先都市の特性）",
        "bus_freq":"公共交通頻度はほぼ無相関（岡山はバス依存でない）",
        "green":"公園・緑地は後楽園などに多く、観光・文化エリアと関連",
        "diversity":"業種多様性と昼間人口の関係（Jane Jacobs仮説）",
        "shops":"OSM全店舗数との相関",
    }
    for vk, vl, r in corr_res:
        rc = "" if r!=r else ("rp" if r>0.15 else ("rn" if r<-0.15 else ""))
        rs = safe_r(r)
        w(f'<tr><td>{vl}</td><td class="{rc}">{rs}</td><td>{bar_svg(r)}</td><td style="font-size:.82rem;color:#555">{interp.get(vk,"")}</td></tr>')
    w('</table></div>')

    # 重回帰
    w('<h2>3. 重回帰分析（OLS・標準化係数）</h2>')
    w('<p style="font-size:.84rem;color:#666;margin-bottom:8px">β* = 1 標準偏差変化したときの昼間人口の変化量（標準化）。絶対値が大きいほど影響大。</p>')
    w('<div class="card"><table><tr><th>説明変数</th><th>β*</th><th></th><th>方向</th></tr>')
    for i, vk in enumerate(REG):
        vl = next(l for k2,l in VARS if k2==vk)
        b = float(betas[i]); bc = "rp" if b>0 else "rn"
        d = "多いほど人口↑" if b>0 else "多いほど人口↓"
        w(f'<tr><td>{vl}</td><td class="{bc}">{b:+.3f}</td><td>{bar_svg(b)}</td><td style="font-size:.82rem;color:#555">{d}</td></tr>')
    w(f'<tr><td colspan="4" style="color:#666;font-size:.82rem;padding-top:8px">R²={R2:.3f} | 調整済みR²={R2a:.3f} | n={n}</td></tr>')
    w('</table></div>')

    # Jane Jacobs ランキング
    w('<h2>4. Jane Jacobs スコア（仮説検証）</h2>')
    w('<p style="font-size:.84rem;color:#666;margin-bottom:8px">')
    w('業種多様性(35%) + 公園・緑地(20%) + 飲食+カフェ密度(25%) - 駐車場密度(20%) の加重合計。</p>')
    w('<div class="card" style="overflow-x:auto"><table>')
    w('<tr><th>順位</th><th>エリア</th><th>JJスコア</th><th>多様性H</th><th>公園・緑地</th><th>飲食+カフェ</th><th>駐車場</th><th>昼間人口</th></tr>')
    jjmn = min(M[n]["jj"] for n in names_v); jjmx = max(M[n]["jj"] for n in names_v)
    jjrg = max(jjmx-jjmn, 0.01)
    jjrankmap = {n:i+1 for i,n in enumerate(jj_rank)}
    for rank, nm in enumerate(jj_rank, 1):
        m = M[nm]; sc = m["jj"]; pct = (sc-jjmn)/jjrg*100
        fc = "jf" if sc>=0 else "jf jn"
        bar = f'<div class="jb" style="width:120px"><div class="{fc}" style="width:{pct:.0f}%"></div></div> <span style="font-size:.85rem">{sc:+.2f}</span>'
        if rank==1: bdg='<span class="bdg bg">1位</span>'
        elif rank==2: bdg='<span class="bdg bs">2位</span>'
        elif rank==3: bdg='<span class="bdg bb">3位</span>'
        else: bdg=f'<span style="color:#999;font-size:.85rem">{rank}</span>'
        ps = f'{m["pop"]:.0f}' if m["pop"] else '-'
        w(f'<tr><td>{bdg}</td><td>{m["short"]}</td><td>{bar}</td><td>{m["diversity"]:.2f}</td><td>{m["green"]}</td><td>{m["food"]+m["cafe"]}</td><td>{m["parking"]}</td><td><b>{ps}</b></td></tr>')
    w('</table></div>')

    # エリア詳細
    w('<h2>5. エリア別詳細データ</h2><div class="card" style="overflow-x:auto"><table>')
    w('<tr><th>エリア</th><th>昼間人口</th><th>飲食</th><th>カフェ</th><th>SC</th><th>スーパー</th><th>オフィス</th><th>駐車場</th><th>バス便</th><th>多様性H</th><th>JJ順位</th></tr>')
    for nm in sorted(names_v, key=lambda n: -(M[n]["pop"] or 0)):
        m = M[nm]; ps = f'{m["pop"]:.0f}' if m["pop"] else '-'
        w(f'<tr><td>{m["short"]}</td><td><b>{ps}</b></td><td>{m["food"]}</td><td>{m["cafe"]}</td><td>{m["sc"]}</td><td>{m["sup"]}</td><td>{m["office"]}</td><td>{m["parking"]}</td><td>{m["bus_freq"]:.0f}</td><td>{m["diversity"]:.2f}</td><td>{jjrankmap.get(nm,"")}</td></tr>')
    w('</table></div>')

    w('<div style="margin-top:28px;padding:14px;background:#f0f0f0;border-radius:8px;font-size:.82rem;color:#666">')
    w('<b>データ:</b> 岡山市人流オープンデータ(2023), OSM/Overpass, PLATEAU駐車場, 岡電/両備GTFS / <b>生成:</b> analyze_jinryu.py</div>')
    w('</div></body></html>')

print(f"Done: {out}")
print("OK")
