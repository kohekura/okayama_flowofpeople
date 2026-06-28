# -*- coding: utf-8 -*-
"""
run_chain.py
GeoJSON再生成 → オーバーレイマップ生成 を連続実行する。
MsgBox なし・ダイアログなし・完全サイレント。
完了後に done_chain.txt にタイムスタンプを書き出す。
"""
import sys, io, subprocess, os, datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

PY = sys.executable
LOG = os.path.join(SCRIPT_DIR, "chain_log.txt")

def run(script_name):
    path = os.path.join(SCRIPT_DIR, script_name)
    print(f"\n=== {script_name} ===")
    result = subprocess.run(
        [PY, path],
        capture_output=True, encoding="utf-8", errors="replace"
    )
    if result.stdout:
        print(result.stdout)
    if result.returncode != 0:
        print(f"[ERROR] {result.stderr or ''}")
        return False
    return True

ok1 = run("green_extract_osm.py")
if not ok1:
    print("green_extract_osm.py 失敗。中断。")
    sys.exit(1)

ok2 = run("build_overlay_map.py")
if not ok2:
    print("build_overlay_map.py 失敗。")
    sys.exit(1)

ok3 = run("analyze_jinryu.py")
if not ok3:
    print("analyze_jinryu.py 失敗（スキップして続行）")

# 完了マーカー
done_path = os.path.join(SCRIPT_DIR, "done_chain.txt")
with open(done_path, "w", encoding="utf-8") as f:
    f.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")

print("\n=== 完了 ===")
