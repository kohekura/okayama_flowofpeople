# -*- coding: utf-8 -*-
"""
launcher.py - folium インストール確認 + green_extract_osm.py 実行
"""
import sys
import io
import subprocess
import os

# stdout を UTF-8 で固定（Windows CP932環境での UnicodeEncodeError 対策）
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

# folium チェック
try:
    import folium
    print("folium: already installed")
except ImportError:
    print("folium not found. Installing...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "folium"],
        capture_output=True, text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print("pip install FAILED:", result.stderr)
        sys.exit(1)
    print("folium installed OK")

# メインスクリプト実行
print("=" * 50)
print("Running green_extract_osm.py ...")
print("=" * 50)
result = subprocess.run(
    [sys.executable, os.path.join(SCRIPT_DIR, "green_extract_osm.py")],
    capture_output=True, encoding="utf-8", errors="replace"
)
if result.stdout:
    print(result.stdout)
if result.returncode != 0:
    print("ERROR:", result.stderr or "")
    sys.exit(1)
print("Done.")
