Set oShell = CreateObject("WScript.Shell")
sDir = "C:\Users\rd006\Documents\projectGIS_2026\01_personspace"
sLog = sDir & "\chain_log.txt"
sPy  = "C:\Python311\python.exe"
sCmd = "powershell.exe -NonInteractive -WindowStyle Hidden -Command " & _
       Chr(34) & "& '" & sPy & "' '" & sDir & "\run_chain.py' " & _
       "*>&1 | Out-File -Encoding utf8 '" & sLog & "'" & Chr(34)
oShell.Run sCmd, 0, True
