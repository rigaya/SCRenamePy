@echo off
setlocal

rem SCRename.vbs をインストールしたパスを設定
set SCRPATH=C:\SCRename

for /F "usebackq delims=" %%I in (`cscript //nologo "%SCRPATH%\SCRename.vbs" "$FilePath$" "$SCtitle$ $SCpart$第$SCnumber$話 「$SCsubtitle$」 ($SCservice$)" %2 %3`) do set SCRTARGET=%%~I

rem 設定例
rem call encode.bat "%SCRTARGET%"
endlocal
