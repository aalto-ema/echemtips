Option Explicit
Dim shell, files, root, python
Set shell = CreateObject("WScript.Shell")
Set files = CreateObject("Scripting.FileSystemObject")
root = files.GetParentFolderName(WScript.ScriptFullName)
python = root & "\runtime\pythonw.exe"
If Not files.FileExists(python) Then python = root & "\.venv\Scripts\pythonw.exe"
If Not files.FileExists(python) Then
    MsgBox "Run Setup-Offline.cmd first (offline kit), or install the project into .venv. See docs/WINDOWS_INSTALL.md.", vbExclamation, "eChemTips setup required"
    WScript.Quit 1
End If
shell.CurrentDirectory = root
shell.Run """" & python & """ """ & root & "\scripts\windows_launch.pyw"" --analysis", 0, False
