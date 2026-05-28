#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vista Comprobantes Contables - CONTACOL PRO"""
import tkinter as tk
from tkinter import ttk
import datetime
from .styles import C_PRIMARY, C_WHITE, C_BG, FONT_TITLE, FONT_HEADER, col_fmt
from .widgets import DataTable, ToolBar, show_info, show_error, ask_confirm
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import DB, get_plan_cuentas, get_terceros, next_consecutivo


TIPOS_COMP = [
    ("AJ", "Ajuste Contable"),
    ("AP", "Apertura"),
    ("CI", "Cierre"),
    ("NM", "Nómina"),
    ("CC", "Conciliación"),
]


class ContabilidadView(ttk.Frame):
    def __init__(self, parent, db: DB):
        super().__init__(parent)
        self.db = db
        self._build()
        self._load()

    def _build(self):
        hdr = tk.Frame(self, bg=C_PRIMARY, height=40)
        hdr.pack(fill="x")
        tk.Label(hdr, text="  Comprobantes Contables",
                 bg=C_PRIMARY, fg="white", font=FONT_TITLE).place(x=0, y=5)

        tb = ToolBar(self)
        tb.pack(fill="x", padx=8, pady=4)
        tb.add_button("new", "➕ Nuevo Comprobante", self._new)
        tb.add_button("view", "🔍 Ver / Editar", self._view)
        tb.add_separator()
        tb.add_button("anular", "🚫 Anular", self._anular, "Danger.TButton")
        tb.add_separator()

        # Filtros
        ff = ttk.Frame(self)
        ff.pack(fill="x", padx=8, pady=2)
        ttk.Label(ff, text="Desde:").pack(side="left", padx=3)
        self.v_desde = tk.StringVar(value=f"{datetime.date.today().year}-01-01")
        ttk.Entry(ff, textvariable=self.v_desde, width=12).pack(side="left", padx=3)
        ttk.Label(ff, text="Hasta:").pack(side="left", padx=3)
        self.v_hasta = tk.StringVar(value=str(datetime.date.today()))
        ttk.Entry(ff, textvariable=self.v_hasta, width=12).pack(side="left", padx=3)
        ttk.Label(ff, text="Tipo:").pack(side="left", padx=3)
        self.v_tipo = tk.StringVar(value="TODOS")
        tipos_list = ["TODOS", "AJ", "AP", "CI", "NM", "CC", "FV", "FC", "RC", "CP"]
        ttk.Combobox(ff, textvariable=self.v_tipo, values=tipos_list,
                     state="readonly", width=8).pack(side="left", padx=3)
        ttk.Button(ff, text="🔎 Buscar", command=self._load).pack(side="left", padx=6)

        cols = [
            ("tipo", "Tipo", 55, "center"),
            ("consecutivo", "N°", 65, "center"),
            ("fecha", "Fecha", 90, "center"),
            ("descripcion", "Descripción", 320, "w"),
            ("total_debito", "Débito", 120, "e"),
            ("total_credito", "Crédito", 120, "e"),
            ("estado", "Estado", 70, "center"),
        ]
        self.tabla = DataTable(self, cols)
        self.tabla.pack(fill="both", expand=True, padx=8, pady=6)
        self.tabla.tree.bind("<Double-1>", lambda e: self._view())

    def _load(self):
        desde = self.v_desde.get().strip()
        hasta = self.v_hasta.get().strip()
        tipo = self.v_tipo.get()
        sql = """SELECT tipo_codigo, consecutivo, fecha, descripcion,
                        total_debito, total_credito, estado
                 FROM comprobantes WHERE fecha>=? AND fecha<=?"""
        params = [desde, hasta]
        if tipo != "TODOS":
            sql += " AND tipo_codigo=?"
            params.append(tipo)
        sql += " ORDER BY fecha DESC, id DESC"
        rows = self.db.fetchall(sql, params)
        self.tabla.clear()
        for r in rows:
            self.tabla.insert([
                r[0], r[1], r[2], r[3] or "",
                col_fmt(r[4]), col_fmt(r[5]),
                r[6],
            ], tags=("danger",) if r[6] == "ANULADO" else None)

    def _new(self):
        ComprobanteDialog(self, self.db, None, self._load)

    def _view(self):
        sel = self.tabla.get_selected()
        if not sel:
            show_error("Seleccione un comprobante.")
            return
        tipo, consec = sel[0], sel[1]
        r = self.db.fetchone(
            "SELECT * FROM comprobantes WHERE tipo_codigo=? AND consecutivo=?",
            (tipo, consec))
        if r:
            ComprobanteDialog(self, self.db, dict(r), self._load)

    def _anular(self):
        sel = self.tabla.get_selected()
        if not sel:
            show_error("Seleccione un comprobante.")
            return
        if not ask_confirm("Anular Comprobante",
                           "¿Está seguro de anular este comprobante?"):
            return
        tipo, consec = sel[0], sel[1]
        self.db.execute(
            "UPDATE comprobantes SET estado='ANULADO' WHERE tipo_codigo=? AND consecutivo=?",
            (tipo, consec))
        self.db.commit()
        show_info("Comprobante anulado.")
        self._load()


class ComprobanteDialog(tk.Toplevel):
    def __init__(self, parent, db: DB, data, on_save):
        super().__init__(parent)
        self.db = db
        self.data = data or {}
        self.on_save = on_save
        self.lineas = []
        self.title("Comprobante Contable")
        self.geometry("900x600")
        self.grab_set()
        self._build()
        if data:
            self._load_data()

    def _build(self):
        # Encabezado
        hf = ttk.LabelFrame(self, text="Encabezado del Comprobante", padding=8)
        hf.pack(fill="x", padx=10, pady=6)

        # Fila 1
        r1 = ttk.Frame(hf)
        r1.pack(fill="x", pady=2)
        ttk.Label(r1, text="Tipo:").pack(side="left", padx=4)
        self.v_tipo = tk.StringVar(value="AJ")
        ttk.Combobox(r1, textvariable=self.v_tipo,
                     values=[t[0] for t in TIPOS_COMP],
                     state="readonly", width=8).pack(side="left", padx=4)
        ttk.Label(r1, text="Fecha:").pack(side="left", padx=4)
        self.v_fecha = tk.StringVar(value=str(datetime.date.today()))
        ttk.Entry(r1, textvariable=self.v_fecha, width=12).pack(side="left", padx=4)
        ttk.Label(r1, text="Descripción:").pack(side="left", padx=4)
        self.v_desc = tk.StringVar()
        ttk.Entry(r1, textvariable=self.v_desc, width=40).pack(side="left", padx=4)

        # Detalle movimientos
        df = ttk.LabelFrame(self, text="Movimientos Contables", padding=8)
        df.pack(fill="both", expand=True, padx=10, pady=4)

        # Toolbar detalle
        dtb = ttk.Frame(df)
        dtb.pack(fill="x", pady=2)
        ttk.Button(dtb, text="➕ Agregar Línea",
                   command=self._add_linea).pack(side="left", padx=3)
        ttk.Button(dtb, text="🗑 Eliminar Línea",
                   command=self._del_linea).pack(side="left", padx=3)

        cols = [
            ("cuenta", "Cuenta", 90, "w"),
            ("nombre_cuenta", "Nombre Cuenta", 260, "w"),
            ("tercero", "Tercero", 120, "w"),
            ("descripcion", "Descripción", 180, "w"),
            ("debito", "Débito", 110, "e"),
            ("credito", "Crédito", 110, "e"),
        ]
        self.tabla_det = DataTable(df, cols)
        self.tabla_det.pack(fill="both", expand=True)

        # Totales
        tf = ttk.Frame(self)
        tf.pack(fill="x", padx=10, pady=4)
        self.lbl_total_db = ttk.Label(tf, text="Total Débito: $0",
                                       font=("Segoe UI", 11, "bold"),
                                       foreground=C_PRIMARY)
        self.lbl_total_db.pack(side="right", padx=12)
        self.lbl_total_cr = ttk.Label(tf, text="Total Crédito: $0",
                                       font=("Segoe UI", 11, "bold"),
                                       foreground=C_PRIMARY)
        self.lbl_total_cr.pack(side="right", padx=12)
        self.lbl_diff = ttk.Label(tf, text="Diferencia: $0",
                                   font=("Segoe UI", 11, "bold"),
                                   foreground="red")
        self.lbl_diff.pack(side="right", padx=12)

        # Botones
        bf = ttk.Frame(self)
        bf.pack(fill="x", padx=10, pady=6)
        ttk.Button(bf, text="💾 Guardar Comprobante",
                   command=self._save, style="Success.TButton").pack(side="left", padx=4)
        ttk.Button(bf, text="✖ Cancelar",
                   command=self.destroy, style="Danger.TButton").pack(side="left", padx=4)
        ttk.Button(bf, text="🖨 Imprimir",
                   command=lambda: show_info("Función de impresión próximamente")).pack(side="left", padx=4)

    def _load_data(self):
        self.v_tipo.set(self.data.get("tipo_codigo", "AJ"))
        self.v_fecha.set(self.data.get("fecha", ""))
        self.v_desc.set(self.data.get("descripcion", ""))
        # Cargar movimientos
        movs = self.db.fetchall(
            """SELECT m.cuenta_codigo, pc.nombre, t.razon_social,
                      m.descripcion, m.debito, m.credito
               FROM movimientos m
               LEFT JOIN plan_cuentas pc ON pc.codigo=m.cuenta_codigo
               LEFT JOIN terceros t ON t.id=m.tercero_id
               WHERE m.comprobante_id=?""",
            (self.data["id"],))
        for m in movs:
            self._add_linea_data(m[0], m[1] or "", m[2] or "",
                                  m[3] or "", m[4], m[5])
        self._update_totals()

    def _add_linea(self):
        LineaDialog(self, self.db, self._add_linea_data)

    def _add_linea_data(self, cuenta, nombre, tercero, desc, debito, credito):
        self.lineas.append({
            "cuenta": cuenta, "nombre": nombre,
            "tercero": tercero, "desc": desc,
            "debito": float(debito or 0),
            "credito": float(credito or 0),
        })
        self.tabla_det.insert([
            cuenta, nombre, tercero, desc,
            col_fmt(debito), col_fmt(credito),
        ])
        self._update_totals()

    def _del_linea(self):
        sel = self.tabla_det.get_selected()
        if not sel:
            return
        idx = list(self.tabla_det.tree.get_children()).index(
            self.tabla_det.tree.selection()[0])
        if idx < len(self.lineas):
            self.lineas.pop(idx)
        self.tabla_det.tree.delete(self.tabla_det.tree.selection()[0])
        self._update_totals()

    def _update_totals(self):
        td = sum(l["debito"] for l in self.lineas)
        tc = sum(l["credito"] for l in self.lineas)
        diff = td - tc
        self.lbl_total_db.config(text=f"Total Débito: {col_fmt(td)}")
        self.lbl_total_cr.config(text=f"Total Crédito: {col_fmt(tc)}")
        color = "green" if abs(diff) < 1 else "red"
        self.lbl_diff.config(text=f"Diferencia: {col_fmt(diff)}", foreground=color)

    def _save(self):
        if not self.lineas:
            show_error("Debe agregar al menos una línea.")
            return
        td = sum(l["debito"] for l in self.lineas)
        tc = sum(l["credito"] for l in self.lineas)
        if abs(td - tc) >= 1:
            show_error(f"El comprobante no está cuadrado.\n"
                       f"Débito: {col_fmt(td)} | Crédito: {col_fmt(tc)}")
            return

        tipo = self.v_tipo.get()
        fecha = self.v_fecha.get().strip()
        desc = self.v_desc.get().strip()

        if self.data.get("id"):
            comp_id = self.data["id"]
            self.db.execute("UPDATE comprobantes SET fecha=?, descripcion=?, "
                            "total_debito=?, total_credito=? WHERE id=?",
                            (fecha, desc, td, tc, comp_id))
            self.db.execute("DELETE FROM movimientos WHERE comprobante_id=?", (comp_id,))
        else:
            consec = next_consecutivo(self.db, tipo)
            self.db.execute("""INSERT INTO comprobantes
                               (tipo_codigo, consecutivo, prefijo, fecha, descripcion,
                                total_debito, total_credito, estado)
                               VALUES (?,?,?,?,?,?,?,?)""",
                            (tipo, consec, tipo, fecha, desc, td, tc, "ACTIVO"))
            comp_id = self.db.conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        for l in self.lineas:
            self.db.execute("""INSERT INTO movimientos
                               (comprobante_id, cuenta_codigo, descripcion, debito, credito)
                               VALUES (?,?,?,?,?)""",
                            (comp_id, l["cuenta"], l["desc"],
                             l["debito"], l["credito"]))

        self.db.commit()
        show_info("Comprobante guardado correctamente.")
        self.on_save()
        self.destroy()


class LineaDialog(tk.Toplevel):
    def __init__(self, parent, db: DB, callback):
        super().__init__(parent)
        self.db = db
        self.callback = callback
        self.title("Agregar Línea Contable")
        self.resizable(False, False)
        self.grab_set()
        self._build()

    def _build(self):
        f = ttk.Frame(self, padding=16, style="White.TFrame")
        f.pack(fill="both", expand=True)

        # Cuenta
        ttk.Label(f, text="Cuenta:", style="White.TLabel",
                  width=16, anchor="e").grid(row=0, column=0, padx=4, pady=4, sticky="e")
        self.v_cuenta = tk.StringVar()
        e_cuenta = ttk.Entry(f, textvariable=self.v_cuenta, width=14)
        e_cuenta.grid(row=0, column=1, padx=4, pady=4, sticky="w")
        e_cuenta.bind("<FocusOut>", self._lookup_cuenta)
        e_cuenta.bind("<Return>", self._lookup_cuenta)
        self.lbl_nombre = ttk.Label(f, text="", style="White.TLabel",
                                     foreground="#2980b9", width=35, wraplength=260)
        self.lbl_nombre.grid(row=0, column=2, columnspan=2, sticky="w", padx=4)

        # Tercero
        ttk.Label(f, text="Tercero:", style="White.TLabel",
                  width=16, anchor="e").grid(row=1, column=0, padx=4, pady=4, sticky="e")
        terceros = [f"{t['numero_id']} - {t['razon_social']}"
                    for t in get_terceros(self.db)]
        self.v_tercero = tk.StringVar()
        ttk.Combobox(f, textvariable=self.v_tercero, values=[""] + terceros,
                     width=32).grid(row=1, column=1, columnspan=2, padx=4, pady=4, sticky="w")

        # Descripción
        ttk.Label(f, text="Descripción:", style="White.TLabel",
                  width=16, anchor="e").grid(row=2, column=0, padx=4, pady=4, sticky="e")
        self.v_desc = tk.StringVar()
        ttk.Entry(f, textvariable=self.v_desc, width=40).grid(
            row=2, column=1, columnspan=2, padx=4, pady=4, sticky="w")

        # Débito / Crédito
        ttk.Label(f, text="Débito:", style="White.TLabel",
                  width=16, anchor="e").grid(row=3, column=0, padx=4, pady=4, sticky="e")
        self.v_debito = tk.StringVar(value="0")
        ttk.Entry(f, textvariable=self.v_debito, width=16).grid(
            row=3, column=1, padx=4, pady=4, sticky="w")
        ttk.Label(f, text="Crédito:", style="White.TLabel",
                  width=10, anchor="e").grid(row=3, column=2, padx=4, pady=4, sticky="e")
        self.v_credito = tk.StringVar(value="0")
        ttk.Entry(f, textvariable=self.v_credito, width=16).grid(
            row=3, column=3, padx=4, pady=4, sticky="w")

        # Botones
        bf = ttk.Frame(f, style="White.TFrame")
        bf.grid(row=4, column=0, columnspan=4, pady=10)
        ttk.Button(bf, text="Agregar", command=self._add,
                   style="Success.TButton").pack(side="left", padx=4)
        ttk.Button(bf, text="Cancelar", command=self.destroy,
                   style="Danger.TButton").pack(side="left", padx=4)

    def _lookup_cuenta(self, event=None):
        codigo = self.v_cuenta.get().strip()
        if not codigo:
            return
        r = self.db.fetchone(
            "SELECT nombre, permite_movimiento FROM plan_cuentas WHERE codigo=?",
            (codigo,))
        if r:
            self.lbl_nombre.config(text=r["nombre"])
        else:
            self.lbl_nombre.config(text="⚠ Cuenta no encontrada")

    def _add(self):
        cuenta = self.v_cuenta.get().strip()
        if not cuenta:
            show_error("Ingrese un código de cuenta.")
            return
        r = self.db.fetchone(
            "SELECT nombre, permite_movimiento FROM plan_cuentas WHERE codigo=?",
            (cuenta,))
        if not r:
            show_error(f"La cuenta {cuenta} no existe en el PUC.")
            return
        if not r["permite_movimiento"]:
            show_error(f"La cuenta {cuenta} no permite movimiento directo.")
            return
        try:
            db_val = float(self.v_debito.get().replace(".", "").replace(",", ".") or 0)
            cr_val = float(self.v_credito.get().replace(".", "").replace(",", ".") or 0)
        except ValueError:
            show_error("Valores de débito/crédito inválidos.")
            return
        tercero = self.v_tercero.get()
        self.callback(cuenta, r["nombre"], tercero, self.v_desc.get(), db_val, cr_val)
        self.destroy()
