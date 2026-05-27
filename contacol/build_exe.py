#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de compilación para CONTACOL PRO
Genera el archivo .exe para Windows usando PyInstaller
Uso: python build_exe.py
"""
import subprocess
import sys
import os
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))


def check_requirements():
    print("Verificando dependencias...")
    try:
        import PyInstaller
        print(f"  ✓ PyInstaller {PyInstaller.__version__}")
    except ImportError:
        print("  ✗ PyInstaller no encontrado. Instalando...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    for pkg in ["reportlab", "openpyxl", "PIL"]:
        try:
            __import__(pkg)
            print(f"  ✓ {pkg}")
        except ImportError:
            print(f"  ✗ {pkg} no encontrado. Instalando...")
            install_name = "Pillow" if pkg == "PIL" else pkg
            subprocess.check_call([sys.executable, "-m", "pip", "install", install_name])


def clean_build():
    print("\nLimpiando compilaciones anteriores...")
    for folder in ["dist", "build"]:
        path = os.path.join(ROOT, folder)
        if os.path.exists(path):
            shutil.rmtree(path)
            print(f"  Eliminado: {folder}/")
    spec = os.path.join(ROOT, "CONTACOL_PRO.spec")
    if os.path.exists(spec):
        os.remove(spec)


def build():
    print("\nCompilando CONTACOL PRO...")
    main_py = os.path.join(ROOT, "main.py")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "CONTACOL_PRO",
        "--add-data", f"gui{os.pathsep}gui",
        "--hidden-import", "tkinter",
        "--hidden-import", "tkinter.ttk",
        "--hidden-import", "sqlite3",
        "--hidden-import", "database",
        "--hidden-import", "puc_data",
        "--hidden-import", "tax_calc",
        "--hidden-import", "nomina_calc",
        "--hidden-import", "gui.styles",
        "--hidden-import", "gui.widgets",
        "--hidden-import", "gui.empresa_view",
        "--hidden-import", "gui.puc_view",
        "--hidden-import", "gui.contabilidad_view",
        "--hidden-import", "gui.terceros_view",
        "--hidden-import", "gui.facturacion_view",
        "--hidden-import", "gui.nomina_view",
        "--hidden-import", "gui.informes_view",
        "--clean",
        "--noconfirm",
        main_py
    ]

    # Intentar agregar icono si existe
    ico = os.path.join(ROOT, "contacol.ico")
    if os.path.exists(ico):
        cmd.extend(["--icon", ico])

    result = subprocess.run(cmd, cwd=ROOT)
    return result.returncode == 0


def verify():
    exe = os.path.join(ROOT, "dist", "CONTACOL_PRO.exe")
    if os.path.exists(exe):
        size_mb = os.path.getsize(exe) / (1024 * 1024)
        print(f"\n{'='*60}")
        print(f"  ✓ ÉXITO! Ejecutable creado:")
        print(f"  📁 {exe}")
        print(f"  📦 Tamaño: {size_mb:.1f} MB")
        print(f"{'='*60}")
        print("\n  Puede distribuir CONTACOL_PRO.exe a cualquier PC")
        print("  con Windows 7/8/10/11 sin necesidad de instalar Python.")
        return True
    else:
        print("\n✗ ERROR: No se creó el ejecutable.")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("  CONTACOL PRO - Generador de Ejecutable Windows")
    print("=" * 60)
    check_requirements()
    clean_build()
    success = build()
    if success:
        verify()
    else:
        print("\nLa compilación falló. Revise los mensajes de error.")
        sys.exit(1)
