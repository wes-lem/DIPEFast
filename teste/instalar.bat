@echo off
echo ========================================
echo Instalando dependencias de testes
echo ========================================
echo.

REM Ativar venv e instalar dependências
call ..\venv\Scripts\activate.bat
pip install -r ..\requirements.txt

echo.
echo ========================================
echo Instalacao concluida!
echo ========================================
echo.
echo Para executar os testes, use:
echo   pytest teste/
echo.
pause

