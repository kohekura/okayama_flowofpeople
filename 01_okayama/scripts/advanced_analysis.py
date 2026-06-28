# -*- coding: utf-8 -*-
"""
advanced_analysis.py  -  岡山市中心部 人流×都市構造 発展分析
  1. 全変数マトリクスの構築（200m 基準）
  2. PCA（主成分分析）+ バイプロット
  3. OLS 重回帰（多重共線性チェック付き）
  4. Moran's I（空間的自己相関）
  5. KMeans クラスタ分析（k=3/4）
  6. HTML レポート出力（matplotlib グラフ埋め込み）

PLATEAUキャッシュ（_plateau_bldg_cache.json）があれば建物変数を追加
"""
import os, json, math, csv, io, base64, warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
warnings.filterwarnings("ignore")

# ─── パス設定 ──────────────────────────────────────────────────────────────────
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

BLDG_CACHE    = os.path.join(SCRIPT_DIR, "_plateau_bldg_cache.json")
CACHE         = lambda n: os.path.join(SCRIPT_DIR, f"_overpass_{n}_cache.json")
GREEN_GEOJSON = os.path.join(SCRIPT_DIR, "green_osm.geojson")
OUT_HTML      = os.path.join(SCRIPT_DIR, "advanced_analysis.html")

LAT_M = 111000.0; LON_M = 91000.0

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
AREAS = list(AREA_COORDS.keys())

# ─── ユーティリティ ────────────────────────────────────────────────────────────
def dist_m(a1,o1,a2,o2):
    return math.sqrt(((a2-a1)*LAT_M)**2+((o2-o1)*LON_M)**2)

def in_r(ca,co,a,o,r): return dist_m(ca,co,a,o)<=r

def shannon(counts):
    t=sum(counts)
    if not t: return 0.0
    return -sum(c/t*math.log2(c/t) for c in counts if c)

def poly_area_m2(ring):
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

def fig_to_b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=120)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()

# ─── データ読み込み ────────────────────────────────────────────────────────────
print("=== データ読み込み ===")

def load_jinryu():
    pop_d, pop_n = {}, {}
    with open(JINRYU_CSV, encoding="cp932") as f: lines = f.readlines()
    yrs = lines[1].strip().split(","); hrs = lines[3].strip().split(",")
    cols = [i for i,y in enumerate(yrs) if y.strip()=="2023"]
    dh = {"10時","11時","12時","13時","14時","15時","16時","17時"}
    nh = {"22時","23時","24時","25時","26時","27時","28時"}
    for line in lines[4:]:
        p = line.strip().split(","); nm = p[0].strip()
        if not nm: continue
        vd = [float(p[i]) for i in cols if hrs[i].strip() in dh and i<len(p) and p[i].strip()]
        vn = [float(p[i]) for i in cols if hrs[i].strip() in nh and i<len(p) and p[i].strip()]
        if vd: pop_d[nm] = sum(vd)/len(vd)
        if vn: pop_n[nm] = sum(vn)/len(vn)
    return pop_d, pop_n

pop_day, pop_night = load_jinryu()
print(f"  人流 昼:{len(pop_day)} 夜:{len(pop_night)}")

# 駐車場
park_osm = []
with open(PARKING_GEOJSON, encoding="utf-8") as f: gj = json.load(f)
for feat in gj["features"]:
    geom = feat["geometry"]
    if geom["type"] == "Point":
        park_osm.append((geom["coordinates"][1], geom["coordinates"][0]))

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
    return stops, {k: len(v) for k,v in tps.items()}

oks,okt = load_gtfs(GTFS_OKADEN); rys,ryt = load_gtfs(GTFS_RYOBI)
all_stops = {**oks, **rys}; all_trips = {}
for k,v in {**okt,**ryt}.items(): all_trips[k] = all_trips.get(k,0)+v
print(f"  GTFS stops:{len(all_stops)}")

# OSM
rest = load_json_osm(CACHE("restaurant"))
comm = load_json_osm(CACHE("commercial"))
offs = load_json_osm(CACHE("office"))
FOOD_AM = {"restaurant","pub","fast_food","food_court"}
CAFE_AM = {"cafe"}; BAR_AM = {"bar"}
print(f"  OSM 飲食:{len(rest)} 商業:{len(comm)} オフィス:{len(offs)}")

# 緑地
green_pts=[]; green_areas=[]
with open(GREEN_GEOJSON, encoding="utf-8") as f: gj = json.load(f)
for feat in gj["features"]:
    geom = feat["geometry"]
    if geom["type"] == "Polygon":
        ring = geom["coordinates"][0]
        clat = sum(c[1] for c in ring)/len(ring)
        clon = sum(c[0] for c in ring)/len(ring)
        area = poly_area_m2(ring)
        green_pts.append((clat,clon)); green_areas.append((clat,clon,area))
print(f"  緑地:{len(green_pts)}")

# PLATEAU
USE_PLATEAU = os.path.exists(BLDG_CACHE)
bldg = []
if USE_PLATEAU:
    with open(BLDG_CACHE, encoding="utf-8") as f: bldg = json.load(f)
    print(f"  PLATEAU建物:{len(bldg)}棟")
else:
    print("  PLATEAU キャッシュなし → 建物変数スキップ")

USAGE_5 = {
    "401":"業務","402":"商業","403":"商業","404":"商業",
    "411":"住宅","412":"住宅","413":"住宅","414":"住宅","415":"住宅",
    "421":"工業","422":"工業",
    "431":"文化行政","451":"文化行政","461":"文化行政","462":"その他","463":"その他",
}

# ─── 全変数マトリクス構築（全距離） ───────────────────────────────────────────
print("\n=== 変数計算 ===")
RADII = [100, 200, 300, 500]
rows = []

for area, (ca,co) in AREA_COORDS.items():
    # 人流マッチング
    pd_v = pop_day.get(area)
    if pd_v is None:
        for k,v in pop_day.items():
            if k[:4] == area[:4]: pd_v = v; break
    pn_v = pop_night.get(area)
    if pn_v is None:
        for k,v in pop_night.items():
            if k[:4] == area[:4]: pn_v = v; break

    row = {"area": area, "lat": ca, "lon": co, "pop_day": pd_v, "pop_night": pn_v}

    for R in RADII:
        ca_m2 = math.pi * R * R

        # 飲食
        fn=cn=bn=0
        for e in rest:
            ll = latlng_osm(e)
            if not (ll and in_r(ca,co,*ll,R)): continue
            am = e.get("tags",{}).get("amenity","")
            if am in FOOD_AM: fn+=1
            elif am in CAFE_AM: cn+=1
            elif am in BAR_AM: bn+=1
        row[f"food_n_{R}"]    = fn
        row[f"cafe_n_{R}"]    = cn
        row[f"bar_n_{R}"]     = bn
        row[f"fnb_n_{R}"]     = fn+cn+bn
        row[f"fnb_den_{R}"]   = (fn+cn+bn)/ca_m2*1e6

        # 商業
        scn=spn=0
        for e in comm:
            ll = latlng_osm(e)
            if not (ll and in_r(ca,co,*ll,R)): continue
            sh = e.get("tags",{}).get("shop","")
            if sh in {"mall","department_store"}: scn+=1
            elif sh == "supermarket": spn+=1
        row[f"sc_n_{R}"] = scn; row[f"sup_n_{R}"] = spn

        # オフィス
        on=0
        for e in offs:
            ll = latlng_osm(e)
            if ll and in_r(ca,co,*ll,R): on+=1
        row[f"office_n_{R}"]  = on
        row[f"office_den_{R}"]= on/ca_m2*1e6

        # 駐車場
        pkn=0
        for (pa,po) in park_osm:
            if in_r(ca,co,pa,po,R): pkn+=1
        row[f"park_n_{R}"] = pkn

        # バス
        sn=0; total_trips=0
        for sid,(sa,so) in all_stops.items():
            if in_r(ca,co,sa,so,R):
                sn+=1; total_trips+=all_trips.get(sid,0)
        row[f"bus_stop_n_{R}"]  = sn
        row[f"bus_trip_n_{R}"]  = total_trips
        row[f"bus_avg_{R}"]     = (total_trips/sn) if sn else 0
        row[f"bus_den_{R}"]     = total_trips/ca_m2*1e6

        # 緑地
        gn=0; ga=0.0
        for (gla,glo) in green_pts:
            if in_r(ca,co,gla,glo,R): gn+=1
        for (gla,glo,garea) in green_areas:
            if in_r(ca,co,gla,glo,R): ga+=garea
        row[f"green_n_{R}"]     = gn
        row[f"green_area_{R}"]  = ga
        row[f"green_ratio_{R}"] = ga/ca_m2

        # 業種多様性（8分類シャノンH）
        cat_counts = {}
        for e in rest:
            ll = latlng_osm(e)
            if not (ll and in_r(ca,co,*ll,R)): continue
            am = e.get("tags",{}).get("amenity","")
            if am in FOOD_AM: cat_counts["food"] = cat_counts.get("food",0)+1
            elif am in CAFE_AM: cat_counts["cafe"] = cat_counts.get("cafe",0)+1
            elif am in BAR_AM: cat_counts["bar"] = cat_counts.get("bar",0)+1
        for e in offs:
            ll = latlng_osm(e)
            if ll and in_r(ca,co,*ll,R):
                cat_counts["office"] = cat_counts.get("office",0)+1
        for e in comm:
            ll = latlng_osm(e)
            if not (ll and in_r(ca,co,*ll,R)): continue
            sh = e.get("tags",{}).get("shop","")
            if sh in {"mall","department_store"}: cat_counts["SC"] = cat_counts.get("SC",0)+1
            elif sh == "supermarket": cat_counts["sup"] = cat_counts.get("sup",0)+1
        row[f"H8_{R}"] = shannon(list(cat_counts.values()))

        # PLATEAU建物変数
        if USE_PLATEAU:
            bb=[b for b in bldg if in_r(ca,co,b["lat"],b["lon"],R)]
            bn2=len(bb)
            tot_fp=sum(b.get("fp_area",0) for b in bb)
            bldg_cov=tot_fp/ca_m2 if ca_m2 else 0
            u5_cnt={}
            for b in bb:
                u=USAGE_5.get(str(b.get("usage","")),"その他")
                u5_cnt[u]=u5_cnt.get(u,0)+1
            bldg_H=shannon(list(u5_cnt.values()))
            comm_cnt=u5_cnt.get("商業",0); biz_cnt=u5_cnt.get("業務",0)
            house_cnt=u5_cnt.get("住宅",0)
            yr_vals=[b["year"] for b in bb if b.get("year")]
            ht_vals=[b["height"] for b in bb if b.get("height")]
            row[f"bldg_n_{R}"]          = bn2
            row[f"bldg_cov_{R}"]        = bldg_cov
            row[f"bldg_H5_{R}"]         = bldg_H
            row[f"bldg_comm_ratio_{R}"] = comm_cnt/bn2 if bn2 else 0
            row[f"bldg_biz_ratio_{R}"]  = biz_cnt/bn2 if bn2 else 0
            row[f"bldg_house_ratio_{R}"]= house_cnt/bn2 if bn2 else 0
            row[f"year_mean_{R}"]       = float(np.mean(yr_vals)) if yr_vals else np.nan
            row[f"year_std_{R}"]        = float(np.std(yr_vals))  if len(yr_vals)>1 else np.nan
            row[f"ht_mean_{R}"]         = float(np.mean(ht_vals)) if ht_vals else np.nan
            row[f"ht_std_{R}"]          = float(np.std(ht_vals))  if len(ht_vals)>1 else np.nan

    rows.append(row)
    print(f"  {area[:8]}: 昼人流={pd_v:.0f}" if pd_v else f"  {area[:8]}: 人流データなし")

DF = pd.DataFrame(rows).set_index("area")
print(f"\n  → DataFrame: {DF.shape[0]}エリア × {DF.shape[1]}変数")

# ─── 分析用変数セット（200m基準 + 補完） ──────────────────────────────────────
# 相関スキャンで有意だった変数 + PLATEAU変数（あれば）
BASE_VARS = [
    ("green_n_200",    "緑地件数200m"),
    ("bus_avg_200",    "バス平均便数200m"),
    ("H8_500",         "業種多様性H500m"),
    ("bar_n_100",      "バー居酒屋100m"),
    ("office_n_200",   "オフィス数200m"),
    ("cafe_n_100",     "カフェ数100m"),
    ("green_area_500", "緑地面積500m"),
    ("park_n_200",     "駐車場数200m"),
    ("food_n_100",     "飲食店数100m"),
    ("bus_stop_n_200", "バス停数200m"),
]
if USE_PLATEAU:
    BASE_VARS += [
        ("bldg_cov_200",        "建蔽率200m"),
        ("bldg_H5_200",         "建物用途多様性200m"),
        ("year_std_200",        "建物年代多様性200m"),
        ("bldg_comm_ratio_200", "商業建物比200m"),
        ("ht_mean_200",         "平均建物高さ200m"),
    ]

var_cols  = [v for v,_ in BASE_VARS if v in DF.columns]
var_names = [n for v,n in BASE_VARS if v in DF.columns]

# 人流が取れているエリアのみ
AN = DF.dropna(subset=["pop_day"]).copy()
y  = AN["pop_day"].values.astype(float)
X_raw = AN[var_cols].fillna(AN[var_cols].median()).values.astype(float)

# ─── 標準化 ───────────────────────────────────────────────────────────────────
def standardize(X):
    mu = X.mean(axis=0); sd = X.std(axis=0, ddof=1)
    sd[sd==0] = 1.0
    return (X - mu)/sd, mu, sd

Xs, x_mu, x_sd = standardize(X_raw)
y_z = (y - y.mean()) / y.std(ddof=1)
n, p = Xs.shape

# ══════════════════════════════════════════════════════════════════════════════
# 1. PCA（主成分分析）
# ══════════════════════════════════════════════════════════════════════════════
print("\n=== 1. PCA ===")
C = np.cov(Xs.T)                        # p×p 相関行列（標準化済みなのでほぼ相関行列）
evals, evecs = np.linalg.eigh(C)
idx = np.argsort(evals)[::-1]
evals = evals[idx]; evecs = evecs[:,idx]

exp_var = evals / evals.sum() * 100
cum_var = np.cumsum(exp_var)

# スコア
scores = Xs @ evecs

# バイプロット（PC1 vs PC2）
fig, axes = plt.subplots(1, 2, figsize=(14,6))
fig.patch.set_facecolor("#1a1a2e")
for ax in axes: ax.set_facecolor("#16213e")

# 左：スクリープロット
ax = axes[0]
ax.bar(range(1, min(p+1,9)), exp_var[:8], color="#e94560", alpha=0.8)
ax.plot(range(1, min(p+1,9)), cum_var[:8], "o-", color="#f5a623", lw=2)
ax.axhline(80, color="white", lw=0.7, linestyle="--", alpha=0.5)
ax.set_xlabel("主成分", color="white"); ax.set_ylabel("寄与率 (%)", color="white")
ax.set_title("スクリープロット", color="white", fontsize=13)
ax.tick_params(colors="white"); [s.set_color("white") for s in ax.spines.values()]

# 右：バイプロット（PC1 × PC2）
ax = axes[1]
sc = ax.scatter(scores[:,0], scores[:,1], c=y, cmap="plasma", s=80, zorder=5)
for i, name in enumerate(AN.index):
    ax.annotate(name[:4], (scores[i,0], scores[i,1]),
                color="white", fontsize=7, ha="center", va="bottom")

# 矢印（ローディング）
scale = 2.5
for j, vname in enumerate(var_names):
    lx, ly = evecs[j,0]*scale, evecs[j,1]*scale
    ax.annotate("", xy=(lx,ly), xytext=(0,0),
                arrowprops=dict(arrowstyle="->", color="#a8dadc", lw=1.2))
    ax.text(lx*1.1, ly*1.1, vname, color="#a8dadc", fontsize=7,
            ha="center" if abs(lx)<0.5 else ("left" if lx>0 else "right"))

cb = fig.colorbar(sc, ax=axes[1])
cb.set_label("昼間人流", color="white"); cb.ax.yaxis.set_tick_params(color="white")
plt.setp(cb.ax.yaxis.get_ticklabels(), color="white")
ax.axhline(0, color="white", lw=0.4); ax.axvline(0, color="white", lw=0.4)
ax.set_xlabel(f"PC1 ({exp_var[0]:.1f}%)", color="white")
ax.set_ylabel(f"PC2 ({exp_var[1]:.1f}%)", color="white")
ax.set_title("バイプロット（PC1 × PC2）", color="white", fontsize=13)
ax.tick_params(colors="white"); [s.set_color("white") for s in ax.spines.values()]

plt.tight_layout()
PCA_IMG = fig_to_b64(fig)

# PC1 ローディング（何を表すか）
PC1_load = [(var_names[j], evecs[j,0]) for j in range(len(var_names))]
PC1_load.sort(key=lambda x: abs(x[1]), reverse=True)
print("  PC1 ローディング（上位）:")
for vn, ld in PC1_load[:5]: print(f"    {vn}: {ld:+.3f}")
print(f"  PC1 寄与率: {exp_var[0]:.1f}%  PC2: {exp_var[1]:.1f}%")

# ══════════════════════════════════════════════════════════════════════════════
# 2. OLS 重回帰（VIF付き）
# ══════════════════════════════════════════════════════════════════════════════
print("\n=== 2. OLS 重回帰 ===")

def ols(X, y):
    """Returns (beta, y_hat, resid, R2, adj_R2, F, df1, df2, se_beta)"""
    n, p = X.shape
    Xb = np.hstack([np.ones((n,1)), X])
    beta = np.linalg.lstsq(Xb, y, rcond=None)[0]
    y_hat = Xb @ beta
    resid = y - y_hat
    SS_res = resid @ resid
    SS_tot = ((y - y.mean())**2).sum()
    R2 = 1 - SS_res/SS_tot
    df1 = p; df2 = n - p - 1
    adj_R2 = 1 - (SS_res/df2) / (SS_tot/(n-1))
    F = (R2/df1) / ((1-R2)/df2) if df2 > 0 else np.nan
    s2 = SS_res / df2
    XbT_Xb_inv = np.linalg.pinv(Xb.T @ Xb)
    se_beta = np.sqrt(np.diag(s2 * XbT_Xb_inv))
    return beta, y_hat, resid, R2, adj_R2, F, df1, df2, se_beta

def vif(X):
    """Variance Inflation Factor for each column"""
    n, p = X.shape
    vifs = []
    for j in range(p):
        y_j = X[:,j]; X_rest = np.delete(X, j, axis=1)
        Xb = np.hstack([np.ones((n,1)), X_rest])
        b = np.linalg.lstsq(Xb, y_j, rcond=None)[0]
        y_hat = Xb @ b
        ss_res = ((y_j - y_hat)**2).sum()
        ss_tot = ((y_j - y_j.mean())**2).sum()
        r2 = 1 - ss_res/ss_tot if ss_tot else 0
        vifs.append(1/(1-r2) if r2 < 1 else np.inf)
    return vifs

# 全変数での回帰
beta_all, y_hat_all, resid_all, R2_all, adjR2_all, F_all, df1, df2, se_all = ols(Xs, y)
print(f"  全変数モデル: R²={R2_all:.3f}, adj-R²={adjR2_all:.3f}, F({df1},{df2})={F_all:.2f}")

# VIF計算
vif_vals = vif(Xs)
print("  VIF:")
for vn, vi in zip(var_names, vif_vals): print(f"    {vn}: {vi:.1f}")

# VIF < 5 の変数のみで再回帰（多重共線性排除）
ok_idx = [j for j,vi in enumerate(vif_vals) if vi < 5]
ok_names = [var_names[j] for j in ok_idx]
Xs_ok = Xs[:, ok_idx]
beta_ok, y_hat_ok, resid_ok, R2_ok, adjR2_ok, F_ok, df1_ok, df2_ok, se_ok = ols(Xs_ok, y)
print(f"\n  VIF<5 変数モデル ({len(ok_idx)}変数): R²={R2_ok:.3f}, adj-R²={adjR2_ok:.3f}, F({df1_ok},{df2_ok})={F_ok:.2f}")
for j, (vn, b, se) in enumerate(zip(ok_names, beta_ok[1:], se_ok[1:])):
    t = b/se if se else np.nan
    print(f"    {vn}: β={b:+.3f}, t={t:+.2f}")

# t値 & 近似p値（正規近似）
def t_pval(t, df):
    """Two-tailed p-value using normal approximation when df large"""
    import math
    # Beta function approximation for t-distribution
    x = df/(df+t**2)
    # Use simple normal approximation
    return 2*(1 - 0.5*(1+math.erf(abs(t)/math.sqrt(2))))

# OLS 可視化
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.patch.set_facecolor("#1a1a2e")
for ax in axes: ax.set_facecolor("#16213e")

# 係数プロット
ax = axes[0]
betas = beta_ok[1:]; ses = se_ok[1:]
colors = ["#e94560" if b < 0 else "#4cc9f0" for b in betas]
y_pos = range(len(ok_names))
ax.barh(y_pos, betas, xerr=ses*1.96, color=colors, alpha=0.85,
        error_kw=dict(ecolor="white", capsize=4))
ax.set_yticks(list(y_pos)); ax.set_yticklabels(ok_names, color="white", fontsize=9)
ax.axvline(0, color="white", lw=0.8)
ax.set_title("OLS 標準化係数（95%CI）", color="white", fontsize=13)
ax.set_xlabel("β（標準化）", color="white")
ax.tick_params(colors="white"); [s.set_color("white") for s in ax.spines.values()]

# 実測 vs 予測
ax = axes[1]
ax.scatter(y, y_hat_ok, c="#f5a623", s=60, zorder=5)
mn, mx = min(y.min(), y_hat_ok.min()), max(y.max(), y_hat_ok.max())
ax.plot([mn,mx],[mn,mx], "w--", lw=0.8)
for i, name in enumerate(AN.index):
    ax.annotate(name[:4], (y[i], y_hat_ok[i]), color="white", fontsize=7)
ax.set_xlabel("実測 昼間人流", color="white")
ax.set_ylabel("予測値", color="white")
ax.set_title(f"実測 vs 予測  (adj-R²={adjR2_ok:.2f})", color="white", fontsize=13)
ax.tick_params(colors="white"); [s.set_color("white") for s in ax.spines.values()]

plt.tight_layout()
OLS_IMG = fig_to_b64(fig)

# ══════════════════════════════════════════════════════════════════════════════
# 3. Moran's I（空間的自己相関）
# ══════════════════════════════════════════════════════════════════════════════
print("\n=== 3. Moran's I ===")

coords = np.array([(AN.at[a,"lat"], AN.at[a,"lon"]) for a in AN.index])
nn = len(AN)

def make_W(coords, mode="inv_dist", k=5):
    """空間重み行列（逆距離 or k近傍）"""
    W = np.zeros((nn, nn))
    for i in range(nn):
        dists = [dist_m(coords[i,0], coords[i,1], coords[j,0], coords[j,1])
                 if i!=j else np.inf for j in range(nn)]
        if mode == "knn":
            top_k = np.argsort(dists)[:k]
            for j in top_k: W[i,j] = 1.0
        else:  # inv_dist
            for j in range(nn):
                if i!=j and dists[j]>0: W[i,j] = 1.0/dists[j]
    # 行標準化
    row_sums = W.sum(axis=1, keepdims=True)
    row_sums[row_sums==0] = 1
    return W / row_sums

def morans_i(z, W):
    """z: 標準化済みベクトル, W: 行標準化重み行列"""
    n = len(z)
    z_mean = z - z.mean()
    S0 = W.sum()
    I = (n / S0) * (z_mean @ (W @ z_mean)) / (z_mean @ z_mean)
    # 期待値・分散（正規近似）
    E_I = -1/(n-1)
    S1 = 0.5*((W+W.T)**2).sum()
    S2 = ((W.sum(axis=1)+W.sum(axis=0))**2).sum()
    n2 = n**2
    E_I2 = (n*((n2-3*n+3)*S1 - n*S2 + 3*S0**2)) / \
           ((n-1)*(n-2)*(n-3)*S0**2) - E_I**2
    z_score = (I - E_I) / math.sqrt(max(E_I2, 1e-12))
    p_val = 2*(1 - 0.5*(1+math.erf(abs(z_score)/math.sqrt(2))))
    return I, E_I, z_score, p_val

W_inv  = make_W(coords, mode="inv_dist")
W_knn  = make_W(coords, mode="knn", k=4)

y_std = (y - y.mean()) / (y.std()+1e-12)
I_inv, E_inv, z_inv, p_inv = morans_i(y_std, W_inv)
I_knn, E_knn, z_knn, p_knn = morans_i(y_std, W_knn)
print(f"  人流 Moran's I (逆距離): I={I_inv:.3f}, z={z_inv:.2f}, p={p_inv:.4f}")
print(f"  人流 Moran's I (k=4近傍): I={I_knn:.3f}, z={z_knn:.2f}, p={p_knn:.4f}")

# OLS残差のMoran's I（空間的自己相関が残っているか）
resid_std = (resid_ok - resid_ok.mean()) / (resid_ok.std()+1e-12)
Ir_inv, Er, zr_inv, pr_inv = morans_i(resid_std, W_inv)
print(f"  OLS残差 Moran's I (逆距離): I={Ir_inv:.3f}, z={zr_inv:.2f}, p={pr_inv:.4f}")

# モランプロット
lag_y = W_inv @ y_std
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.patch.set_facecolor("#1a1a2e")
for ax in axes: ax.set_facecolor("#16213e")

ax = axes[0]
ax.scatter(y_std, lag_y, c="#f5a623", s=70, zorder=5)
for i, name in enumerate(AN.index):
    ax.annotate(name[:4], (y_std[i], lag_y[i]), color="white", fontsize=7)
# 回帰線
xf = np.linspace(y_std.min(), y_std.max(), 100)
slope = np.polyfit(y_std, lag_y, 1)
ax.plot(xf, np.polyval(slope, xf), "r--", lw=1.5)
ax.axhline(0, color="white", lw=0.4); ax.axvline(0, color="white", lw=0.4)
ax.set_xlabel("昼間人流（標準化）", color="white")
ax.set_ylabel("空間ラグ（逆距離加重平均）", color="white")
ax.set_title(f"モランプロット  I={I_inv:.3f}  p={p_inv:.3f}", color="white", fontsize=13)
ax.tick_params(colors="white"); [s.set_color("white") for s in ax.spines.values()]

# 残差モランプロット
lag_r = W_inv @ resid_std
ax = axes[1]
ax.scatter(resid_std, lag_r, c="#a8dadc", s=70, zorder=5)
for i, name in enumerate(AN.index):
    ax.annotate(name[:4], (resid_std[i], lag_r[i]), color="white", fontsize=7)
slope_r = np.polyfit(resid_std, lag_r, 1)
xf2 = np.linspace(resid_std.min(), resid_std.max(), 100)
ax.plot(xf2, np.polyval(slope_r, xf2), "r--", lw=1.5)
ax.axhline(0, color="white", lw=0.4); ax.axvline(0, color="white", lw=0.4)
ax.set_xlabel("OLS残差（標準化）", color="white")
ax.set_ylabel("空間ラグ残差", color="white")
ax.set_title(f"残差モランプロット  I={Ir_inv:.3f}  p={pr_inv:.3f}", color="white", fontsize=13)
ax.tick_params(colors="white"); [s.set_color("white") for s in ax.spines.values()]

plt.tight_layout()
MORAN_IMG = fig_to_b64(fig)

# ══════════════════════════════════════════════════════════════════════════════
# 4. KMeans クラスタ分析
# ══════════════════════════════════════════════════════════════════════════════
print("\n=== 4. KMeans クラスタ分析 ===")

def kmeans(X, k, n_init=30, max_iter=300, seed=42):
    rng = np.random.default_rng(seed)
    best_inertia = np.inf; best_labels = None; best_centers = None
    for _ in range(n_init):
        idx = rng.choice(len(X), k, replace=False)
        centers = X[idx].copy()
        for _ in range(max_iter):
            dists = np.array([[np.sum((x-c)**2) for c in centers] for x in X])
            labels = dists.argmin(axis=1)
            new_centers = np.array([X[labels==ki].mean(axis=0) if (labels==ki).any()
                                    else centers[ki] for ki in range(k)])
            if np.allclose(centers, new_centers): break
            centers = new_centers
        inertia = sum(np.sum((X[labels==ki]-centers[ki])**2) for ki in range(k))
        if inertia < best_inertia:
            best_inertia = inertia; best_labels = labels.copy(); best_centers = centers.copy()
    return best_labels, best_centers, best_inertia

# エルボー法
inertias = {}
for k in range(2, 7):
    _, _, inertia = kmeans(Xs, k)
    inertias[k] = inertia
    print(f"  k={k}: inertia={inertia:.1f}")

# k=4で分析
K = 4
labels4, centers4, _ = kmeans(Xs, K)
AN_clust = AN.copy()
AN_clust["cluster"] = labels4

# クラスタ別人流
print("\n  クラスタ別 平均人流:")
CNAMES = []
for ki in range(K):
    mask = labels4 == ki
    avg_pop = y[mask].mean()
    members = [AN.index[i] for i in range(nn) if mask[i]]
    cname = f"C{ki+1}(n={mask.sum()})"
    CNAMES.append(cname)
    print(f"    {cname}: 昼間人流={avg_pop:.0f}  {[m[:4] for m in members]}")

CLUST_COLORS = ["#e94560","#f5a623","#4cc9f0","#80ed99"]

# 可視化
fig, axes = plt.subplots(1, 3, figsize=(18, 6))
fig.patch.set_facecolor("#1a1a2e")
for ax in axes: ax.set_facecolor("#16213e")

# エルボープロット
ax = axes[0]
ax.plot(list(inertias.keys()), list(inertias.values()), "o-", color="#f5a623", lw=2)
ax.set_xlabel("クラスタ数 k", color="white"); ax.set_ylabel("慣性（Inertia）", color="white")
ax.set_title("エルボー法", color="white", fontsize=13)
ax.tick_params(colors="white"); [s.set_color("white") for s in ax.spines.values()]

# PC空間でのクラスタ
ax = axes[1]
for ki in range(K):
    mask = labels4 == ki
    ax.scatter(scores[mask,0], scores[mask,1],
               c=CLUST_COLORS[ki], s=80, label=CNAMES[ki], zorder=5)
    for i in range(nn):
        if mask[i]:
            ax.annotate(AN.index[i][:4], (scores[i,0], scores[i,1]),
                        color="white", fontsize=7, ha="center", va="bottom")
ax.axhline(0, color="white", lw=0.4); ax.axvline(0, color="white", lw=0.4)
ax.set_xlabel(f"PC1 ({exp_var[0]:.1f}%)", color="white")
ax.set_ylabel(f"PC2 ({exp_var[1]:.1f}%)", color="white")
ax.set_title(f"クラスタ（k={K}）× PC空間", color="white", fontsize=13)
ax.tick_params(colors="white"); [s.set_color("white") for s in ax.spines.values()]
ax.legend(facecolor="#16213e", labelcolor="white", fontsize=8)

# 地図上プロット（緯度経度）
ax = axes[2]
for ki in range(K):
    mask = labels4 == ki
    lats = [AN.at[area,"lat"] for area in AN.index if labels4[list(AN.index).index(area)]==ki]
    lons = [AN.at[area,"lon"] for area in AN.index if labels4[list(AN.index).index(area)]==ki]
    ax.scatter(lons, lats, c=CLUST_COLORS[ki], s=y[mask]*0.2+20, label=CNAMES[ki], zorder=5, alpha=0.85)
    for i, area in enumerate(AN.index):
        if labels4[i]==ki:
            ax.annotate(area[:4], (AN.at[area,"lon"], AN.at[area,"lat"]),
                        color="white", fontsize=7, ha="center", va="bottom")
ax.set_xlabel("経度", color="white"); ax.set_ylabel("緯度", color="white")
ax.set_title("地図上のクラスタ（円サイズ=人流）", color="white", fontsize=13)
ax.tick_params(colors="white"); [s.set_color("white") for s in ax.spines.values()]
ax.legend(facecolor="#16213e", labelcolor="white", fontsize=8)

plt.tight_layout()
CLUST_IMG = fig_to_b64(fig)

# クラスタ別プロファイル
fig, ax = plt.subplots(figsize=(12, 5))
fig.patch.set_facecolor("#1a1a2e"); ax.set_facecolor("#16213e")
theta = np.arange(len(var_names))
width = 0.15
for ki in range(K):
    mask = labels4 == ki
    profile = Xs[mask].mean(axis=0)
    ax.bar(theta + ki*width, profile, width, label=CNAMES[ki],
           color=CLUST_COLORS[ki], alpha=0.85)
ax.set_xticks(theta + width*1.5)
ax.set_xticklabels(var_names, rotation=35, ha="right", color="white", fontsize=8)
ax.axhline(0, color="white", lw=0.5)
ax.set_ylabel("平均スコア（標準化）", color="white")
ax.set_title("クラスタ別 変数プロファイル", color="white", fontsize=13)
ax.tick_params(colors="white"); [s.set_color("white") for s in ax.spines.values()]
ax.legend(facecolor="#16213e", labelcolor="white", fontsize=9)
plt.tight_layout()
PROFILE_IMG = fig_to_b64(fig)

# ══════════════════════════════════════════════════════════════════════════════
# HTML レポート出力
# ══════════════════════════════════════════════════════════════════════════════
print("\n=== HTML レポート生成 ===")

# クラスタ別エリア表
clust_rows_html = ""
for ki in range(K):
    mask = labels4 == ki
    members = [AN.index[i] for i in range(nn) if mask[i]]
    avg_pop = y[mask].mean()
    # クラスタの特徴（上位変数）
    prof = Xs[mask].mean(axis=0)
    top_pos = [(var_names[j], prof[j]) for j in np.argsort(prof)[::-1][:3]]
    top_neg = [(var_names[j], prof[j]) for j in np.argsort(prof)[:3]]
    pos_str = " / ".join(f"{v}({s:+.2f})" for v,s in top_pos)
    neg_str = " / ".join(f"{v}({s:+.2f})" for v,s in top_neg)
    clust_rows_html += f"""
    <tr style="border-left:4px solid {CLUST_COLORS[ki]}">
      <td style="color:{CLUST_COLORS[ki]};font-weight:bold">{CNAMES[ki]}</td>
      <td>{avg_pop:.0f}</td>
      <td style="color:#4cc9f0">{pos_str}</td>
      <td style="color:#e94560">{neg_str}</td>
      <td>{"　".join(m[:5] for m in members)}</td>
    </tr>"""

# OLS係数表
ols_rows_html = ""
for j, (vn, b, se) in enumerate(zip(ok_names, beta_ok[1:], se_ok[1:])):
    t = b/se if se else np.nan
    p_v = t_pval(t, df2_ok)
    sig = "***" if p_v<0.001 else "**" if p_v<0.01 else "*" if p_v<0.05 else ""
    col = "#4cc9f0" if b > 0 else "#e94560"
    ols_rows_html += f"""
    <tr>
      <td>{vn}</td>
      <td style="color:{col}">{b:+.3f}</td>
      <td>{se:.3f}</td>
      <td>{t:+.2f}</td>
      <td>{p_v:.4f}</td>
      <td style="color:#f5a623;font-weight:bold">{sig}</td>
    </tr>"""

# VIF表
vif_rows_html = ""
for vn, vi in zip(var_names, vif_vals):
    col = "#e94560" if vi >= 5 else "#80ed99"
    warn = "⚠ 高" if vi >= 10 else "注意" if vi >= 5 else "OK"
    vif_rows_html += f"<tr><td>{vn}</td><td style='color:{col}'>{vi:.1f}</td><td style='color:{col}'>{warn}</td></tr>"

# PCA寄与率
pca_rows = "".join(
    f"<tr><td>PC{i+1}</td><td>{exp_var[i]:.1f}%</td><td>{cum_var[i]:.1f}%</td>"
    f"<td>{'、'.join(f'{vn}({evecs[j,i]:+.2f})' for j,vn in enumerate(var_names) if abs(evecs[j,i])>0.25)}</td></tr>"
    for i in range(min(5, p))
)

plateau_note = ("✅ PLATEAU建物データ使用（建蔽率・用途多様性・年代多様性を含む）" if USE_PLATEAU
                else "⚠ PLATEAUキャッシュなし。build_plateau_cache.py を実行後に再実行で建物変数追加")

HTML = f"""<!DOCTYPE html>
<html lang="ja"><head>
<meta charset="UTF-8">
<title>岡山市GIS 発展分析レポート</title>
<style>
  body{{background:#0f0e17;color:#e0e0e0;font-family:'Noto Sans JP',sans-serif;margin:0;padding:20px}}
  h1{{color:#f5a623;text-align:center;font-size:1.8rem;margin-bottom:4px}}
  h2{{color:#a8dadc;border-left:4px solid #a8dadc;padding-left:12px;margin-top:40px}}
  h3{{color:#e0e0e0;margin-top:20px}}
  .sub{{color:#888;text-align:center;margin-bottom:30px;font-size:0.9rem}}
  .note{{background:#1a1a2e;border:1px solid #333;padding:12px 18px;border-radius:8px;margin:16px 0;font-size:0.92rem}}
  .warn{{background:#2d1b00;border-left:4px solid #f5a623;padding:10px 14px;border-radius:4px;margin:10px 0}}
  img{{max-width:100%;border-radius:8px;margin:12px 0}}
  table{{border-collapse:collapse;width:100%;margin:12px 0;font-size:0.9rem}}
  th{{background:#1a1a2e;color:#a8dadc;padding:8px 12px;text-align:left}}
  td{{padding:7px 12px;border-bottom:1px solid #222}}
  tr:hover{{background:#1a1a2e}}
  .stat{{display:inline-block;background:#1a1a2e;border-radius:8px;padding:10px 20px;margin:6px;text-align:center}}
  .stat .val{{font-size:1.6rem;color:#f5a623;font-weight:bold}}
  .stat .lbl{{font-size:0.8rem;color:#888}}
  .grid2{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin:16px 0}}
</style>
</head><body>
<h1>🏙 岡山市中心市街地 GIS 発展分析レポート</h1>
<p class="sub">n=22エリア | {plateau_note}</p>

<div class="note">
このレポートは相関スキャン（第1段階）の次ステップとして、
<strong>① PCA（主成分分析）</strong>・
<strong>② OLS重回帰（多重共線性制御）</strong>・
<strong>③ Moran's I（空間的自己相関）</strong>・
<strong>④ KMeansクラスタ分析（k=4）</strong>
の4つの手法で人流の構造を分析した。
</div>

<!-- ═══ PCA ═══ -->
<h2>① 主成分分析（PCA）</h2>

<div>
{"".join(f'<div class="stat"><div class="val">{exp_var[i]:.1f}%</div><div class="lbl">PC{i+1}寄与率</div></div>' for i in range(min(4,p)))}
</div>

<img src="data:image/png;base64,{PCA_IMG}" alt="PCA">

<table>
<tr><th>主成分</th><th>寄与率</th><th>累積</th><th>主な変数（ローディング絶対値 &gt; 0.25）</th></tr>
{pca_rows}
</table>

<div class="note">
<strong>解釈のポイント</strong>：PC1が全変数の共通因子を捉えており、
ローディングの符号と大きさから「{PC1_load[0][0]}」と「{PC1_load[1][0]}」が最も支配的な軸の要素。
バイプロットで人流（色）と矢印方向の一致を確認。
</div>

<!-- ═══ OLS ═══ -->
<h2>② OLS 重回帰（多重共線性チェック付き）</h2>

<div>
<div class="stat"><div class="val">R² = {R2_ok:.3f}</div><div class="lbl">決定係数</div></div>
<div class="stat"><div class="val">adj-R² = {adjR2_ok:.3f}</div><div class="lbl">自由度調整済</div></div>
<div class="stat"><div class="val">F({df1_ok},{df2_ok}) = {F_ok:.2f}</div><div class="lbl">F統計量</div></div>
<div class="stat"><div class="val">n={nn}</div><div class="lbl">サンプル数</div></div>
</div>

<img src="data:image/png;base64,{OLS_IMG}" alt="OLS">

<div class="grid2">
<div>
<h3>VIF（分散膨張因子）</h3>
<table>
<tr><th>変数</th><th>VIF</th><th>判定</th></tr>
{vif_rows_html}
</table>
</div>
<div>
<h3>回帰係数（VIF&lt;5 変数のみ）</h3>
<table>
<tr><th>変数</th><th>β</th><th>SE</th><th>t値</th><th>p値</th><th>有意</th></tr>
{ols_rows_html}
</table>
<p style="font-size:0.8rem;color:#888">*** p&lt;0.001, ** p&lt;0.01, * p&lt;0.05（正規近似）</p>
</div>
</div>

<div class="note">
<strong>解釈のポイント</strong>：adj-R²={adjR2_ok:.2f}は「選ばれた変数で昼間人流の{adjR2_ok*100:.0f}%を説明できる」ことを示す。
n=22のため係数の標準誤差が大きく、t値・p値は目安として参照すること。
VIF≥5の変数は多重共線性が疑われモデルから除外した。
</div>

<!-- ═══ MORAN ═══ -->
<h2>③ 空間的自己相関（Moran's I）</h2>

<div>
<div class="stat"><div class="val">I = {I_inv:.3f}</div><div class="lbl">昼間人流（逆距離重み）</div></div>
<div class="stat"><div class="val">z = {z_inv:.2f}</div><div class="lbl">z値</div></div>
<div class="stat"><div class="val">p = {p_inv:.4f}</div><div class="lbl">p値（正規近似）</div></div>
<div class="stat"><div class="val">I = {Ir_inv:.3f}</div><div class="lbl">OLS残差（逆距離重み）</div></div>
</div>

<img src="data:image/png;base64,{MORAN_IMG}" alt="Moran">

<div class="note">
<strong>Moran's I の解釈</strong>：
I &gt; 0 → 空間的な正のクラスタリング（類似した値のエリアが隣接）。
I ≈ 0 → ランダム配置。I &lt; 0 → 空間的な分散（高低が交互）。<br>
期待値 E[I] = {E_inv:.4f}。
{"<strong>昼間人流に有意な空間的自己相関あり</strong>（隣接エリアが似た人流を持つ傾向）。" if p_inv<0.05 else "昼間人流の空間的自己相関は有意でない（p={p_inv:.3f}）。"}
OLS残差のMoran's I={Ir_inv:.3f}（{"残差に空間構造が残存→空間ラグモデルへの発展を検討" if abs(Ir_inv)>0.2 else "残差の空間パターンは小さく、OLSモデルは概ね適切"}）。
</div>

<!-- ═══ CLUSTER ═══ -->
<h2>④ KMeansクラスタ分析（k=4）</h2>

<img src="data:image/png;base64,{CLUST_IMG}" alt="Cluster">
<img src="data:image/png;base64,{PROFILE_IMG}" alt="Profile">

<table>
<tr><th>クラスタ</th><th>平均人流</th><th>高スコア変数</th><th>低スコア変数</th><th>所属エリア</th></tr>
{clust_rows_html}
</table>

<div class="note">
<strong>クラスタ命名の手がかり</strong>：変数プロファイルを見て、各クラスタに「駅前商業型」「緑地型」「住宅混在型」などのラベルをつけると分析の解像度が上がる。
地図プロット（右図）で地理的なまとまりがあるかも確認すること。
</div>

<!-- ═══ NEXT ═══ -->
<h2>⑤ 次のステップ</h2>
<div class="note">
<ul>
  <li><strong>空間ラグモデル（SLM）</strong>：残差にMoran's Iが残る場合、W×pop_dayを説明変数に追加したSLMが有効。</li>
  <li><strong>PLATEAU建物データ投入</strong>：build_plateau_cache.py実行後に再実行すれば建物変数（建蔽率・用途多様性・年代多様性）が加わる。</li>
  <li><strong>交差検証（LOOCV）</strong>：n=22のためLeave-One-Out CVでモデルの汎化性能を確認すること。</li>
  <li><strong>カテゴリ別回帰</strong>：クラスタ別に回帰を走らせると「エリア類型によって効くドライバーが違う」という知見が得られる可能性。</li>
</ul>
</div>

<p style="text-align:right;color:#444;font-size:0.8rem">generated by advanced_analysis.py</p>
</body></html>"""

with open(OUT_HTML, "w", encoding="utf-8") as f:
    f.write(HTML)
print(f"\n✅ レポート出力: {OUT_HTML}")
