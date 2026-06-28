Set oShell = CreateObject("WScript.Shell")
sPy  = "C:\Python311\python.exe"
sDir = "C:\Users\rd006\Documents\projectGIS_2026\01_personspace"
sLog = sDir & "\run_green_log.txt"
sCmd = "cmd /c " & sPy & " " & sDir & "\launcher.py > " & sLog & " 2>&1"
oShell.Run sCmd, 0, True
MsgBox "Done! See run_green_log.txt", 64, "green_extract_osm"
