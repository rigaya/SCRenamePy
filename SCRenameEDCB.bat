@echo off
setlocal

rem SCRename.py をインストールしたパスを設定
set SCRPATH=C:\SCRename

for /F "usebackq delims=" %%I in (`py "%SCRPATH%\SCRename.py" "$FilePath$" "$SCtitle$ $SCpart$第$SCnumber$話 「$SCsubtitle$」 ($SCservice$)" %2 %3`) do set SCRTARGET=%%~I

rem 設定例
rem call encode.bat "%SCRTARGET%"
endlocal
