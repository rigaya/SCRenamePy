@echo off
setlocal

rem SCRename.py ���C���X�g�[�������p�X��ݒ�
set SCRPATH=C:\SCRename

for /F "usebackq delims=" %%I in (`py "%SCRPATH%\SCRename.py" "$FilePath$" "$SCtitle$ $SCpart$��$SCnumber$�b �u$SCsubtitle$�v ($SCservice$)" %2 %3`) do set SCRTARGET=%%~I

rem �ݒ��
rem call encode.bat "%SCRTARGET%"
endlocal
