@echo off
setlocal

rem SCRename.py ���C���X�g�[�������p�X��ݒ�
set SCRPATH=%~dp0

:LOOP
for /F "usebackq delims=" %%I in (`py "%SCRPATH%\SCRename.py" "%~1" "$SCtitle$ $SCpart$��$SCnumber$�b �u$SCsubtitle$�v ($SCservice$)"`) do set SCRTARGET=%%~I

rem �ݒ��
rem call encode.bat "%SCRTARGET%"

shift
if "%~1" NEQ "" goto LOOP
endlocal
