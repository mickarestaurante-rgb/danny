#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Estilos y constantes visuales de CONTACOL PRO"""
import tkinter as tk
from tkinter import ttk

# Paleta de colores
C_PRIMARY   = "#1a3a5c"   # Azul corporativo oscuro
C_SECONDARY = "#2e86c1"   # Azul medio
C_ACCENT    = "#f39c12"   # Naranja acento
C_BG        = "#f0f4f8"   # Fondo general
C_WHITE     = "#ffffff"
C_SIDEBAR   = "#1a3a5c"
C_SIDEBAR_H = "#2e86c1"
C_TEXT      = "#2c3e50"
C_TEXT_LIGHT= "#7f8c8d"
C_SUCCESS   = "#27ae60"
C_DANGER    = "#e74c3c"
C_WARNING   = "#f39c12"
C_BORDER    = "#bdc3c7"
C_ROW_ODD   = "#eaf0f6"
C_ROW_EVEN  = "#ffffff"

FONT_TITLE  = ("Segoe UI", 14, "bold")
FONT_HEADER = ("Segoe UI", 11, "bold")
FONT_NORMAL = ("Segoe UI", 10)
FONT_SMALL  = ("Segoe UI", 9)
FONT_MONO   = ("Courier New", 10)


def apply_theme(root):
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(".",
        background=C_BG, foreground=C_TEXT,
        font=FONT_NORMAL)

    style.configure("TFrame", background=C_BG)
    style.configure("White.TFrame", background=C_WHITE)

    style.configure("TLabel",
        background=C_BG, foreground=C_TEXT, font=FONT_NORMAL)
    style.configure("Title.TLabel",
        font=FONT_TITLE, foreground=C_PRIMARY, background=C_BG)
    style.configure("Header.TLabel",
        font=FONT_HEADER, foreground=C_PRIMARY, background=C_WHITE)
    style.configure("White.TLabel",
        background=C_WHITE, foreground=C_TEXT)
    style.configure("Light.TLabel",
        foreground=C_TEXT_LIGHT, font=FONT_SMALL)

    style.configure("TButton",
        background=C_SECONDARY, foreground=C_WHITE,
        font=FONT_NORMAL, padding=(8, 5), relief="flat")
    style.map("TButton",
        background=[("active", C_PRIMARY), ("pressed", C_PRIMARY)])

    style.configure("Accent.TButton",
        background=C_ACCENT, foreground=C_WHITE, padding=(8, 5))
    style.map("Accent.TButton",
        background=[("active", "#d68910"), ("pressed", "#d68910")])

    style.configure("Success.TButton",
        background=C_SUCCESS, foreground=C_WHITE, padding=(8, 5))
    style.map("Success.TButton",
        background=[("active", "#1e8449")])

    style.configure("Danger.TButton",
        background=C_DANGER, foreground=C_WHITE, padding=(8, 5))
    style.map("Danger.TButton",
        background=[("active", "#c0392b")])

    style.configure("TEntry",
        fieldbackground=C_WHITE, borderwidth=1,
        relief="solid", padding=4)
    style.map("TEntry", bordercolor=[("focus", C_SECONDARY)])

    style.configure("TCombobox",
        fieldbackground=C_WHITE, padding=4)

    style.configure("TNotebook", background=C_BG, tabmargins=[2, 5, 2, 0])
    style.configure("TNotebook.Tab",
        background=C_BORDER, foreground=C_TEXT,
        padding=[12, 5], font=FONT_NORMAL)
    style.map("TNotebook.Tab",
        background=[("selected", C_WHITE)],
        foreground=[("selected", C_PRIMARY)])

    style.configure("Treeview",
        background=C_WHITE, foreground=C_TEXT,
        fieldbackground=C_WHITE, rowheight=24,
        font=FONT_NORMAL)
    style.configure("Treeview.Heading",
        background=C_PRIMARY, foreground=C_WHITE,
        font=FONT_HEADER, relief="flat")
    style.map("Treeview",
        background=[("selected", C_SECONDARY)],
        foreground=[("selected", C_WHITE)])

    style.configure("TScrollbar",
        background=C_BORDER, troughcolor=C_BG,
        width=12, relief="flat")

    style.configure("TSeparator", background=C_BORDER)

    style.configure("TLabelframe",
        background=C_WHITE, bordercolor=C_BORDER,
        relief="solid", padding=8)
    style.configure("TLabelframe.Label",
        background=C_WHITE, foreground=C_PRIMARY,
        font=FONT_HEADER)

    style.configure("TCheckbutton", background=C_WHITE)
    style.configure("TRadiobutton", background=C_WHITE)
    style.configure("TSpinbox", fieldbackground=C_WHITE, padding=4)

    return style


def col_fmt(value, decimals=0):
    """Formatea un número como moneda colombiana"""
    if value is None:
        return "$ 0"
    try:
        v = float(value)
        if decimals == 0:
            return f"$ {v:,.0f}".replace(",", ".")
        return f"$ {v:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "$ 0"


def num_fmt(value, decimals=2):
    """Formatea un número"""
    try:
        return f"{float(value):,.{decimals}f}"
    except (ValueError, TypeError):
        return "0"


def pct_fmt(value):
    """Formatea porcentaje"""
    try:
        return f"{float(value):.2f}%"
    except (ValueError, TypeError):
        return "0.00%"
