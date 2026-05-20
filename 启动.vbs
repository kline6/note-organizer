' 笔记智能整理工具 - 静默启动（不显示命令行窗口）
' 双击此文件即可静默启动

Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

' Get the directory where this script is located
ScriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)

' Try to find Python
PythonCmd = ""

' Try common Python paths
PythonPaths = Array("pythonw", "python", "python3", _
    "C:\Python312\pythonw.exe", _
    "C:\Python311\pythonw.exe", _
    "C:\Python310\pythonw.exe", _
    "C:\Python313\pythonw.exe", _
    WshShell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Programs\Python\Python312\pythonw.exe", _
    WshShell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Programs\Python\Python311\pythonw.exe", _
    WshShell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Programs\Python\Python313\pythonw.exe", _
    WshShell.ExpandEnvironmentStrings("%APPDATA%") & "\Python\Python312\pythonw.exe" _
)

For Each path In PythonPaths
    If FSO.FileExists(path) Then
        PythonCmd = path
        Exit For
    End If
Next

' Also try "where python" command
If PythonCmd = "" Then
    On Error Resume Next
    PythonCmd = "python"
    ' Use pythonw.exe to avoid console window
    PythonwCmd = Replace(PythonCmd, "python.exe", "pythonw.exe")
    If FSO.FileExists(PythonwCmd) Then
        PythonCmd = PythonwCmd
    End If
    On Error GoTo 0
End If

If PythonCmd = "" Then
    MsgBox "未找到 Python，请先安装 Python 3.10+。" & vbCrLf & vbCrLf & _
           "下载地址: https://www.python.org/downloads/", 48, "错误"
    WScript.Quit 1
End If

' Run the launcher script
WshShell.Run """" & PythonCmd & """ """ & ScriptDir & "\start.py""", 0, False
