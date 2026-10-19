Option Explicit
Dim shell, files, root, python
Set shell = CreateObject("WScript.Shell")
Set files = CreateObject("Scripting.FileSystemObject")
root = files.GetParentFolderName(WScript.ScriptFullName)
python = root & "\runtime\pythonw.exe"
If Not files.FileExists(python) Then python = root & "\.venv\Scripts\pythonw.exe"
If Not files.FileExists(python) Then
    MsgBox "Install the project into .venv. See docs/INSTALLATION.md. Local offline kits have their own setup instructions.", vbExclamation, "eChemTips setup required"
    WScript.Quit 1
End If
shell.CurrentDirectory = root
shell.Run """" & python & """ """ & root & "\scripts\windows_launch.pyw"" --analysis", 0, False
