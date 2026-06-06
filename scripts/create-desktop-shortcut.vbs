' Creates a desktop shortcut (.lnk) to run.vbs
' Zero hardcoded paths — uses the folder where this .vbs lives.

Set fso = CreateObject("Scripting.FileSystemObject")
repoRoot = fso.GetParentFolderName(fso.GetParentFolderName(WScript.ScriptFullName))
runVbs   = repoRoot & "\run.vbs"

If Not fso.FileExists(runVbs) Then
    MsgBox "run.vbs not found at:" & vbCrLf & runVbs, vbExclamation, "Kong-verter"
    WScript.Quit 1
End If

Set WshShell = CreateObject("WScript.Shell")
desktop = WshShell.SpecialFolders("Desktop")

iconPath = repoRoot & "\assets\icon.ico"
If Not fso.FileExists(iconPath) Then
    iconPath = "%SystemRoot%\System32\SHELL32.dll,14"
End If

Set lnk = WshShell.CreateShortcut(desktop & "\Kong-verter.lnk")
lnk.TargetPath         = runVbs
lnk.WorkingDirectory   = repoRoot
lnk.Description        = "Launch Kong-verter"
lnk.IconLocation       = iconPath
lnk.Save()

MsgBox "Shortcut created on your Desktop!" & vbCrLf & _
       desktop & "\Kong-verter.lnk", vbInformation, "Kong-verter"
