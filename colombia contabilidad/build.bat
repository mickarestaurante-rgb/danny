@echo off
echo ============================================================
echo  CONTACOL PRO - Compilacion del Ejecutable Windows (.exe)
echo ============================================================
echo.

:: Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no esta instalado o no esta en el PATH.
    echo Descargue Python desde https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Instalar dependencias
echo [1/4] Instalando dependencias...
pip install pyinstaller reportlab openpyxl Pillow --quiet

:: Limpiar compilaciones anteriores
echo [2/4] Limpiando compilaciones anteriores...
if exist "dist" rd /s /q "dist"
if exist "build" rd /s /q "build"
if exist "CONTACOL_PRO.spec" del /f /q "CONTACOL_PRO.spec"

:: Compilar con PyInstaller
echo [3/4] Compilando CONTACOL PRO...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "CONTACOL_PRO" ^
    --icon "contacol.ico" ^
    --add-data "gui;gui" ^
    --hidden-import "tkinter" ^
    --hidden-import "tkinter.ttk" ^
    --hidden-import "sqlite3" ^
    --hidden-import "reportlab" ^
    --hidden-import "openpyxl" ^
    --clean ^
    main.py

echo [4/4] Verificando compilacion...
if exist "dist\CONTACOL_PRO.exe" (
    echo.
    echo ============================================================
    echo  EXITO! El ejecutable fue creado en:
    echo  dist\CONTACOL_PRO.exe
    echo ============================================================
    echo.
    echo Puede copiar el archivo CONTACOL_PRO.exe a cualquier PC
    echo con Windows y ejecutarlo sin instalar Python.
    echo.
) else (
    echo ERROR: No se pudo crear el ejecutable.
    echo Revise los mensajes de error anteriores.
)

pause
