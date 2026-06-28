Set oShell = CreateObject("WScript.Shell")
sPy  = "C:\Python311\python.exe"
sDir = "C:\Users\rd006\Documents\projectGIS_2026\01_personspace"
sLog = sDir & "\vitality_log.txt"
sCmd = "cmd /c " & sPy & " " & sDir & "\build_vitality_map.py > " & sLog & " 2>&1"
oShell.Run sCmd, 0, True
MsgBox "Done! See vitality_log.txt", 64, "vitality_map"
