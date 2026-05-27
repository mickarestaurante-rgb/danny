#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vista Plan Único de Cuentas - CONTACOL PRO"""
import tkinter as tk
from tkinter import ttk
from .styles import C_PRIMARY, C_WHITE, C_BG, FONT_HEADER, FONT_TITLE
from .widgets import DataTable, ToolBar, show_info, show_error, ask_confirm
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import DB, get_plan_cuentas


TIPOS = ["ACTIVO", "PASIVO", "PATRIMONIO", "INGRESO", "GASTO", "COSTO", "ORDEN"]
NATURALEZAS = ["DEBITO", "CREDITO"]


class PUCView(ttk.Frame):
    def __init__(self, parent, db: DB):
        super().__init__(parent)
        self.db = db
        self._build()
        self._load()

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=C_PRIMARY, height=40)
        hdr.pack(fill="x")
        tk.Label(hdr, text="  Plan Único de Cuentas (PUC)", bg=C_PRIMARY,
                 fg="white", font=FONT_TITLE).place(x=0, y=5)

        # Toolbar
        tb = ToolBar(self)
        tb.pack(fill="x", padx=8, pady=4)
        tb.add_button("new", "➕ Nueva Cuenta", self._new)
        tb.add_button("edit", "✏️ Editar", self._edit)
        tb.add_separator()
        tb.add_button("toggle", "⏸ Activar/Desactivar", self._toggle)
        tb.add_separator()

        # Búsqueda
        sf = ttk.Frame(self)
        sf.pack(fill="x", padx=8, pady=2)
        ttk.Label(sf, text="Buscar:").pack(side="left", padx=4)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *a: self._filter())
        ttk.Entry(sf, textvariable=self.search_var, width=30).pack(side="left", padx=4)
        ttk.Label(sf, text="Tipo:").pack(side="left", padx=4)
        self.tipo_var = tk.StringVar(value="TODOS")
        ttk.Combobox(sf, textvariable=self.tipo_var,
                     values=["TODOS"] + TIPOS,
                     state="readonly", width=14).pack(side="left")
        self.tipo_var.trace("w", lambda *a: self._filter())

        # Tabla
        cols = [
            ("codigo", "Código", 90, "w"),
            ("nombre", "Nombre", 380, "w"),
            ("nivel", "Niv", 40, "center"),
            ("tipo", "Tipo", 100, "w"),
            ("naturaleza", "Naturaleza", 90, "center"),
            ("permite_movimiento", "Mov.", 45, "center"),
            ("exige_tercero", "3ro", 40, "center"),
            ("activa", "Activa", 50, "center"),
        ]
        self.tabla = DataTable(self, cols)
        self.tabla.pack(fill="both", expand=True, padx=8, pady=6)
        self.tabla.tree.bind("<Double-1>", lambda e: self._edit())
        self._all_rows = []

    def _load(self):
        self._all_rows = [dict(r) for r in get_plan_cuentas(self.db)]
        self._filter()

    def _filter(self):
        q = self.search_var.get().strip().lower()
        tipo = self.tipo_var.get()
        self.tabla.clear()
        for r in self._all_rows:
            if tipo != "TODOS" and r.get("tipo") != tipo:
                continue
            if q and q not in r["codigo"].lower() and q not in r["nombre"].lower():
                continue
            self.tabla.insert([
                r["codigo"], r["nombre"], r["nivel"],
                r["tipo"], r["naturaleza"],
                "✓" if r["permite_movimiento"] else "",
                "✓" if r["exige_tercero"] else "",
                "✓" if r["activa"] else "✗",
            ])

    def _new(self):
        CuentaDialog(self, self.db, None, self._load)

    def _edit(self):
        sel = self.tabla.get_selected()
        if not sel:
            show_error("Seleccione una cuenta.")
            return
        codigo = sel[0]
        r = self.db.fetchone("SELECT * FROM plan_cuentas WHERE codigo=?", (codigo,))
        if r:
            CuentaDialog(self, self.db, dict(r), self._load)

    def _toggle(self):
        sel = self.tabla.get_selected()
        if not sel:
            show_error("Seleccione una cuenta.")
            return
        codigo = sel[0]
        r = self.db.fetchone("SELECT activa FROM plan_cuentas WHERE codigo=?", (codigo,))
        if r:
            nueva = 0 if r["activa"] else 1
            self.db.execute("UPDATE plan_cuentas SET activa=? WHERE codigo=?", (nueva, codigo))
            self.db.commit()
            self._load()


class CuentaDialog(tk.Toplevel):
    def __init__(self, parent, db, data, on_save):
        super().__init__(parent)
        self.db = db
        self.data = data or {}
        self.on_save = on_save
        self.title("Nueva Cuenta" if not data else f"Editar Cuenta {data['codigo']}")
        self.resizable(False, False)
        self.grab_set()
        self._build()
        if data:
            self._load()

    def _build(self):
        f = ttk.Frame(self, padding=16, style="White.TFrame")
        f.pack(fill="both", expand=True)

        self.vs = {}
        fields = [
            ("codigo", "Código:", True),
            ("nombre", "Nombre:", True),
            ("nivel", "Nivel (1-5):", True),
            ("codigo_padre", "Código Padre:", False),
        ]
        for i, (k, lbl, req) in enumerate(fields):
            v = tk.StringVar()
            self.vs[k] = v
            ttk.Label(f, text=lbl + (" *" if req else ""),
                      style="White.TLabel", width=22, anchor="e").grid(
                          row=i, column=0, padx=4, pady=4, sticky="e")
            ttk.Entry(f, textvariable=v, width=28).grid(
                row=i, column=1, padx=4, pady=4, sticky="w")

        combos = [
            ("tipo", "Tipo:", TIPOS),
            ("naturaleza", "Naturaleza:", NATURALEZAS),
        ]
        for j, (k, lbl, opts) in enumerate(combos):
            v = tk.StringVar(value=opts[0])
            self.vs[k] = v
            ttk.Label(f, text=lbl, style="White.TLabel",
                      width=22, anchor="e").grid(
                          row=len(fields)+j, column=0, padx=4, pady=4, sticky="e")
            ttk.Combobox(f, textvariable=v, values=opts,
                         state="readonly", width=26).grid(
                             row=len(fields)+j, column=1, padx=4, pady=4, sticky="w")

        checks = [
            ("permite_movimiento", "Permite Movimiento"),
            ("exige_tercero", "Exige Tercero"),
            ("exige_centro_costo", "Exige Centro de Costo"),
            ("exige_base", "Exige Base de Retención"),
        ]
        for m, (k, lbl) in enumerate(checks):
            v = tk.BooleanVar()
            self.vs[k] = v
            ttk.Checkbutton(f, text=lbl, variable=v).grid(
                row=len(fields)+len(combos)+m, column=1,
                padx=4, pady=2, sticky="w")

        # Botones
        bf = ttk.Frame(f, style="White.TFrame")
        bf.grid(row=20, column=0, columnspan=2, pady=10)
        ttk.Button(bf, text="Guardar", command=self._save,
                   style="Success.TButton").pack(side="left", padx=4)
        ttk.Button(bf, text="Cancelar", command=self.destroy,
                   style="Danger.TButton").pack(side="left", padx=4)

    def _load(self):
        for k, v in self.vs.items():
            val = self.data.get(k)
            if isinstance(v, tk.BooleanVar):
                v.set(bool(val))
            else:
                v.set(str(val) if val is not None else "")

    def _save(self):
        codigo = self.vs["codigo"].get().strip()
        nombre = self.vs["nombre"].get().strip()
        nivel_s = self.vs["nivel"].get().strip()
        if not codigo or not nombre or not nivel_s:
            show_error("Código, Nombre y Nivel son obligatorios.")
            return
        try:
            nivel = int(nivel_s)
        except ValueError:
            show_error("Nivel debe ser un número entre 1 y 5.")
            return
        clase = int(codigo[0]) if codigo else 0
        row = self.data.get("id")
        data_dict = {
            "codigo": codigo, "nombre": nombre, "nivel": nivel, "clase": clase,
            "tipo": self.vs["tipo"].get(),
            "naturaleza": self.vs["naturaleza"].get(),
            "codigo_padre": self.vs["codigo_padre"].get().strip() or None,
            "permite_movimiento": 1 if self.vs["permite_movimiento"].get() else 0,
            "exige_tercero": 1 if self.vs["exige_tercero"].get() else 0,
            "exige_centro_costo": 1 if self.vs["exige_centro_costo"].get() else 0,
            "exige_base": 1 if self.vs["exige_base"].get() else 0,
        }
        if row:
            cols = ", ".join(f"{k}=?" for k in data_dict)
            self.db.execute(f"UPDATE plan_cuentas SET {cols} WHERE id=?",
                            list(data_dict.values()) + [row])
        else:
            cols = ", ".join(data_dict.keys())
            ph = ", ".join("?" * len(data_dict))
            self.db.execute(f"INSERT OR REPLACE INTO plan_cuentas ({cols}) VALUES ({ph})",
                            list(data_dict.values()))
        self.db.commit()
        show_info("Cuenta guardada.")
        self.on_save()
        self.destroy()
