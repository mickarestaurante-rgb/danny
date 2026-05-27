#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vista de configuración de empresa - CONTACOL PRO"""
import tkinter as tk
from tkinter import ttk, filedialog
from .styles import C_WHITE, C_PRIMARY, C_BG, FONT_HEADER, FONT_TITLE
from .widgets import LabeledEntry, LabeledCombo, show_info, show_error
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import DB, save_empresa, get_empresa


class EmpresaView(ttk.Frame):
    def __init__(self, parent, db: DB, on_saved=None):
        super().__init__(parent)
        self.db = db
        self.on_saved = on_saved
        self._build()
        self._load()

    def _build(self):
        self.config(style="TFrame")
        # Título
        hdr = tk.Frame(self, bg=C_PRIMARY, height=40)
        hdr.pack(fill="x")
        tk.Label(hdr, text="  Configuración de Empresa", bg=C_PRIMARY,
                 fg="white", font=FONT_TITLE).place(x=0, y=5)

        # Notebook con pestañas
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=10)

        self._tab_basicos(nb)
        self._tab_fiscal(nb)
        self._tab_contacto(nb)
        self._tab_representantes(nb)

        # Botones
        bf = tk.Frame(self, bg=C_BG)
        bf.pack(fill="x", padx=10, pady=6)
        ttk.Button(bf, text="💾  Guardar Empresa",
                   command=self._save, style="Success.TButton").pack(side="left", padx=4)
        ttk.Button(bf, text="✖  Cancelar",
                   command=self._load, style="Danger.TButton").pack(side="left", padx=4)

    def _tab_basicos(self, nb):
        f = ttk.Frame(nb, style="White.TFrame", padding=16)
        nb.add(f, text="  Datos Básicos  ")
        entries = [
            ("razon_social", "Razón Social / Nombre:", True, 40),
            ("nit", "NIT / CC / CE:", True, 20),
            ("digito_verificacion", "Dígito Verificación:", False, 5),
            ("matricula_mercantil", "Matrícula Mercantil:", False, 20),
            ("codigo_ciiu", "Código CIIU:", False, 10),
            ("actividad_principal", "Actividad Principal:", False, 40),
        ]
        self.vars = {}
        for i, (k, lbl, req, w) in enumerate(entries):
            v = tk.StringVar()
            self.vars[k] = v
            row = ttk.Frame(f, style="White.TFrame")
            row.grid(row=i, column=0, sticky="ew", pady=3)
            ttk.Label(row, text=lbl + (" *" if req else ""),
                      style="White.TLabel", width=26, anchor="e").pack(side="left", padx=(0, 6))
            ttk.Entry(row, textvariable=v, width=w).pack(side="left")

        # Tipo persona
        v = tk.StringVar(value="JURIDICA")
        self.vars["tipo_persona"] = v
        row = ttk.Frame(f, style="White.TFrame")
        row.grid(row=len(entries), column=0, sticky="ew", pady=3)
        ttk.Label(row, text="Tipo de Persona:", style="White.TLabel",
                  width=26, anchor="e").pack(side="left", padx=(0, 6))
        for val, lbl in [("JURIDICA", "Jurídica"), ("NATURAL", "Natural")]:
            ttk.Radiobutton(row, text=lbl, variable=v, value=val).pack(side="left", padx=6)

        f.columnconfigure(0, weight=1)

    def _tab_fiscal(self, nb):
        f = ttk.Frame(nb, style="White.TFrame", padding=16)
        nb.add(f, text="  Datos Fiscales  ")

        for i, (k, lbl, opts) in enumerate([
            ("regimen_fiscal", "Régimen Fiscal:", [
                "RESPONSABLE_IVA", "NO_RESPONSABLE_IVA", "REGIMEN_SIMPLE"]),
            ("tipo_contribuyente", "Tipo Contribuyente:", [
                "GRAN_CONTRIBUYENTE", "AUTORETENEDOR",
                "AGENTE_RETENCION_IVA", "OTRO"]),
            ("grupo_niif", "Grupo NIIF:", ["GRUPO1", "GRUPO2", "GRUPO3"]),
        ]):
            v = tk.StringVar(value=opts[0])
            self.vars[k] = v
            row = ttk.Frame(f, style="White.TFrame")
            row.grid(row=i, column=0, sticky="ew", pady=4)
            ttk.Label(row, text=lbl, style="White.TLabel",
                      width=26, anchor="e").pack(side="left", padx=(0, 6))
            ttk.Combobox(row, textvariable=v, values=opts,
                         state="readonly", width=28).pack(side="left")

        # Checkboxes
        for j, (k, lbl) in enumerate([
            ("responsable_iva", "Responsable de IVA"),
            ("retenedor", "Agente Retenedor"),
        ]):
            v = tk.BooleanVar(value=True)
            self.vars[k] = v
            row = ttk.Frame(f, style="White.TFrame")
            row.grid(row=3 + j, column=0, sticky="ew", pady=3)
            ttk.Label(row, text="", style="White.TLabel",
                      width=26).pack(side="left")
            ttk.Checkbutton(row, text=lbl, variable=v).pack(side="left")

        # Capital social (para jurídicas)
        for j, (k, lbl) in enumerate([
            ("capital_autorizado", "Capital Autorizado ($):"),
            ("capital_suscrito", "Capital Suscrito ($):"),
            ("capital_pagado", "Capital Pagado ($):"),
        ]):
            v = tk.StringVar(value="0")
            self.vars[k] = v
            row = ttk.Frame(f, style="White.TFrame")
            row.grid(row=5 + j, column=0, sticky="ew", pady=3)
            ttk.Label(row, text=lbl, style="White.TLabel",
                      width=26, anchor="e").pack(side="left", padx=(0, 6))
            ttk.Entry(row, textvariable=v, width=20).pack(side="left")

        f.columnconfigure(0, weight=1)

    def _tab_contacto(self, nb):
        f = ttk.Frame(nb, style="White.TFrame", padding=16)
        nb.add(f, text="  Contacto y Ubicación  ")
        entries = [
            ("direccion", "Dirección:", 40),
            ("municipio", "Municipio/Ciudad:", 25),
            ("codigo_municipio", "Código Municipio (DANE):", 10),
            ("departamento", "Departamento:", 20),
            ("telefono", "Teléfono:", 20),
            ("email", "Correo Electrónico:", 35),
            ("sitio_web", "Sitio Web:", 35),
        ]
        for i, (k, lbl, w) in enumerate(entries):
            v = tk.StringVar()
            self.vars[k] = v
            row = ttk.Frame(f, style="White.TFrame")
            row.grid(row=i, column=0, sticky="ew", pady=3)
            ttk.Label(row, text=lbl, style="White.TLabel",
                      width=26, anchor="e").pack(side="left", padx=(0, 6))
            ttk.Entry(row, textvariable=v, width=w).pack(side="left")
        f.columnconfigure(0, weight=1)

    def _tab_representantes(self, nb):
        f = ttk.Frame(nb, style="White.TFrame", padding=16)
        nb.add(f, text="  Representantes  ")
        entries = [
            ("representante_legal", "Representante Legal:", 35),
            ("cc_representante", "Cédula Representante:", 20),
            ("contador", "Contador:", 35),
            ("tarjeta_contador", "Tarjeta Profesional Contador:", 20),
            ("revisor_fiscal", "Revisor Fiscal:", 35),
            ("tarjeta_revisor", "Tarjeta Revisor Fiscal:", 20),
            ("fecha_constitucion", "Fecha Constitución (YYYY-MM-DD):", 15),
        ]
        for i, (k, lbl, w) in enumerate(entries):
            v = tk.StringVar()
            self.vars[k] = v
            row = ttk.Frame(f, style="White.TFrame")
            row.grid(row=i, column=0, sticky="ew", pady=4)
            ttk.Label(row, text=lbl, style="White.TLabel",
                      width=32, anchor="e").pack(side="left", padx=(0, 6))
            ttk.Entry(row, textvariable=v, width=w).pack(side="left")
        f.columnconfigure(0, weight=1)

    def _load(self):
        e = get_empresa(self.db)
        if not e:
            return
        for k, v in dict(e).items():
            if k in self.vars:
                if isinstance(self.vars[k], tk.BooleanVar):
                    self.vars[k].set(bool(v))
                else:
                    self.vars[k].set(str(v) if v is not None else "")

    def _save(self):
        rs = self.vars.get("razon_social", tk.StringVar()).get().strip()
        nit = self.vars.get("nit", tk.StringVar()).get().strip()
        if not rs or not nit:
            show_error("Razón Social y NIT son obligatorios.")
            return
        data = {}
        for k, v in self.vars.items():
            if isinstance(v, tk.BooleanVar):
                data[k] = 1 if v.get() else 0
            else:
                val = v.get().strip()
                if val:
                    data[k] = val
        save_empresa(self.db, data)
        show_info("Empresa guardada correctamente.")
        if self.on_saved:
            self.on_saved()
