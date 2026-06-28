Set oShell = CreateObject("WScript.Shell")
sPy  = "C:\Python311\python.exe"
sDir = "C:\Users\rd006\Documents\projectGIS_2026\01_personspace"
sLog = sDir & "\overlay_log.txt"
sCmd = "cmd /c " & sPy & " " & sDir & "\build_overlay_map.py > " & sLog & " 2>&1"
oShell.Run sCmd, 0, True
MsgBox "Done! See overlay_log.txt", 64, "overlay_map"
