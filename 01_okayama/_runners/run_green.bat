@echo off
cd /d "%~dp0"
echo Pythonのバージョン確認...
python --version 2>&1
echo.
echo ライブラリ確認...
python -c "import requests, folium; print('requests/folium OK')" 2>&1
echo.
echo スクリプト実行中...
python green_extract_osm.py > run_green_log.txt 2>&1
echo.
echo 終了コード: %ERRORLEVEL%
if %ERRORLEVEL% == 0 (
  echo 正常完了しました。run_green_log.txt を確認してください。
) else (
  echo エラーが発生しました。run_green_log.txt を確認してください。
)
pause
