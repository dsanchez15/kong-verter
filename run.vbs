' Launch Kong-verter without a console window.
' Uses the folder where this .vbs lives as the project root.

Set fso = CreateObject("Scripting.FileSystemObject")
repoRoot = fso.GetParentFolderName(WScript.ScriptFullName)

pythonw = repoRoot & "\.venv\Scripts\pythonw.exe"
gui     = repoRoot & "\src\gui.py"

If Not fso.FileExists(pythonw) Then
    MsgBox "Virtual environment not found." & vbCrLf & _
           "Please run: python -m venv .venv" & vbCrLf & _
           "Then: pip install -r requirements.txt", _
           vbExclamation, "Kong-verter — Missing venv"
    WScript.Quit 1
End If

Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = repoRoot
WshShell.Run Chr(34) & pythonw & Chr(34) & " " & Chr(34) & gui & Chr(34), 0, False
