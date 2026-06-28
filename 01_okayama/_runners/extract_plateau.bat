@echo off
powershell -NoProfile -Command "Expand-Archive -Path '%USERPROFILE%\Downloads\33100_okayama-shi_city_2024_citygml_1_op.zip' -DestinationPath 'C:\Users\rd006\Documents\projectGIS_2026\plateau_citygml' -Force"
echo Done > C:\Users\rd006\Documents\projectGIS_2026\plateau_citygml_done.txt
