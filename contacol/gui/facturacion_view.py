#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vista Facturación Electrónica - CONTACOL PRO"""
import tkinter as tk
from tkinter import ttk
import datetime
from .styles import C_PRIMARY, C_WHITE, C_BG, FONT_TITLE, col_fmt
from .widgets import DataTable, ToolBar, show_info, show_error, ask_confirm
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import DB, get_terceros, next_consecutivo
from tax_calc import calcular_iva, calcular_reteiva, calcular_retencion_fuente


CONDICION_PAGO = ["CONTADO", "CREDITO_15", "CREDITO_30", "CREDITO_45",
                   "CREDITO_60", "CREDITO_90"]


class FacturacionView(ttk.Frame):
    def __init__(self, parent, db: DB, tipo="VENTA"):
        super().__init__(parent)
        self.db = db
        self.tipo = tipo
        titulo = "Facturas de Venta" if tipo == "VENTA" else "Facturas de Compra"
        self.titulo = titulo
        self._build()
        self._load()

    def _build(self):
        hdr = tk.Frame(self, bg=C_PRIMARY, height=40)
        hdr.pack(fill="x")
        tk.Label(hdr, text=f"  {self.titulo}",
                 bg=C_PRIMARY, fg="white", font=FONT_TITLE).place(x=0, y=5)

        tb = ToolBar(self)
        tb.pack(fill="x", padx=8, pady=4)
        tb.add_button("new", "➕ Nueva Factura", self._new)
        tb.add_button("view", "🔍 Ver / Imprimir", self._view)
        tb.add_separator()
        tb.add_button("nc", "📋 Nota Crédito", self._nota_credito)
        tb.add_button("nd", "📋 Nota Débito", self._nota_debito)
        tb.add_separator()
        tb.add_button("anular", "🚫 Anular", self._anular, "Danger.TButton")

        ff = ttk.Frame(self)
        ff.pack(fill="x", padx=8, pady=2)
        ttk.Label(ff, text="Desde:").pack(side="left", padx=3)
        self.v_desde = tk.StringVar(value=f"{datetime.date.today().year}-01-01")
        ttk.Entry(ff, textvariable=self.v_desde, width=12).pack(side="left", padx=3)
        ttk.Label(ff, text="Hasta:").pack(side="left", padx=3)
        self.v_hasta = tk.StringVar(value=str(datetime.date.today()))
        ttk.Entry(ff, textvariable=self.v_hasta, width=12).pack(side="left", padx=3)
        ttk.Label(ff, text="Estado:").pack(side="left", padx=3)
        self.v_estado = tk.StringVar(value="TODOS")
        ttk.Combobox(ff, textvariable=self.v_estado,
                     values=["TODOS", "ACTIVO", "PAGADA", "ANULADO"],
                     state="readonly", width=10).pack(side="left", padx=3)
        ttk.Button(ff, text="🔎 Buscar", command=self._load).pack(side="left", padx=6)

        cols = [
            ("tipo", "Tipo", 55, "center"),
            ("consecutivo", "N°", 65, "center"),
            ("fecha", "Fecha", 90, "center"),
            ("tercero", "Cliente / Proveedor", 260, "w"),
            ("subtotal", "Subtotal", 110, "e"),
            ("iva", "IVA", 90, "e"),
            ("total", "Total", 110, "e"),
            ("saldo", "Saldo", 110, "e"),
            ("estado", "Estado", 70, "center"),
        ]
        self.tabla = DataTable(self, cols)
        self.tabla.pack(fill="both", expand=True, padx=8, pady=6)
        self.tabla.tree.bind("<Double-1>", lambda e: self._view())

        # Totalizador
        sf = tk.Frame(self, bg=C_BG)
        sf.pack(fill="x", padx=8, pady=2)
        self.lbl_total = tk.Label(sf, text="", bg=C_BG,
                                   font=("Segoe UI", 10, "bold"),
                                   foreground=C_PRIMARY)
        self.lbl_total.pack(side="right", padx=8)

    def _load(self):
        desde = self.v_desde.get().strip()
        hasta = self.v_hasta.get().strip()
        estado = self.v_estado.get()
        tabla_db = "facturas_venta" if self.tipo == "VENTA" else "facturas_compra"
        col_tercero = "cliente_id" if self.tipo == "VENTA" else "proveedor_id"

        sql = f"""SELECT f.tipo, f.consecutivo, f.fecha, t.razon_social,
                         f.subtotal, f.iva19+f.iva5 as iva, f.total, f.saldo, f.estado
                  FROM {tabla_db} f
                  LEFT JOIN terceros t ON t.id=f.{col_tercero}
                  WHERE f.fecha>=? AND f.fecha<=?"""
        params = [desde, hasta]
        if estado != "TODOS":
            sql += " AND f.estado=?"
            params.append(estado)
        sql += " ORDER BY f.fecha DESC, f.consecutivo DESC"

        rows = self.db.fetchall(sql, params)
        self.tabla.clear()
        total_sum = 0
        for r in rows:
            total_sum += r[6] or 0
            self.tabla.insert([
                r[0], r[1], r[2], r[3] or "(Sin tercero)",
                col_fmt(r[4]), col_fmt(r[5]),
                col_fmt(r[6]), col_fmt(r[7]), r[8],
            ], tags=("danger",) if r[8] == "ANULADO" else None)
        self.lbl_total.config(
            text=f"Total período: {col_fmt(total_sum)}  ({len(rows)} registros)")

    def _new(self):
        FacturaDialog(self, self.db, None, self.tipo, self._load)

    def _view(self):
        sel = self.tabla.get_selected()
        if not sel:
            show_error("Seleccione una factura.")
            return
        tabla_db = "facturas_venta" if self.tipo == "VENTA" else "facturas_compra"
        r = self.db.fetchone(
            f"SELECT * FROM {tabla_db} WHERE tipo=? AND consecutivo=?",
            (sel[0], sel[1]))
        if r:
            FacturaDialog(self, self.db, dict(r), self.tipo, self._load, readonly=True)

    def _nota_credito(self):
        show_info("Módulo de Notas Crédito disponible próximamente.")

    def _nota_debito(self):
        show_info("Módulo de Notas Débito disponible próximamente.")

    def _anular(self):
        sel = self.tabla.get_selected()
        if not sel:
            show_error("Seleccione una factura.")
            return
        if sel[8] == "ANULADO":
            show_error("Esta factura ya está anulada.")
            return
        if not ask_confirm("Anular Factura",
                           "¿Está seguro de anular esta factura? Esta acción no se puede deshacer."):
            return
        tabla_db = "facturas_venta" if self.tipo == "VENTA" else "facturas_compra"
        self.db.execute(
            f"UPDATE {tabla_db} SET estado='ANULADO' WHERE tipo=? AND consecutivo=?",
            (sel[0], sel[1]))
        self.db.commit()
        show_info("Factura anulada.")
        self._load()


class FacturaDialog(tk.Toplevel):
    def __init__(self, parent, db: DB, data, tipo, on_save, readonly=False):
        super().__init__(parent)
        self.db = db
        self.data = data or {}
        self.tipo = tipo
        self.on_save = on_save
        self.readonly = readonly
        self.lineas = []
        title = "Factura de Venta" if tipo == "VENTA" else "Factura de Compra"
        self.title(title)
        self.geometry("960x650")
        self.grab_set()
        self._build()
        if data:
            self._load_data()

    def _build(self):
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=4, pady=4)

        # Tab 1: Datos factura
        f1 = ttk.Frame(nb, padding=8)
        nb.add(f1, text="  Datos Generales  ")
        self._build_encabezado(f1)

        # Tab 2: Detalle
        f2 = ttk.Frame(nb, padding=8)
        nb.add(f2, text="  Productos / Servicios  ")
        self._build_detalle(f2)

        # Tab 3: Impuestos y totales
        f3 = ttk.Frame(nb, padding=8)
        nb.add(f3, text="  Impuestos y Totales  ")
        self._build_totales(f3)

        # Botones
        bf = ttk.Frame(self)
        bf.pack(fill="x", padx=8, pady=6)
        if not self.readonly:
            ttk.Button(bf, text="💾 Guardar Factura",
                       command=self._save, style="Success.TButton").pack(side="left", padx=4)
        ttk.Button(bf, text="🖨 Imprimir PDF",
                   command=lambda: show_info("Generando PDF...")).pack(side="left", padx=4)
        ttk.Button(bf, text="✖ Cerrar",
                   command=self.destroy, style="Danger.TButton").pack(side="left", padx=4)

    def _build_encabezado(self, f):
        self.vs = {}
        label_col = "Cliente:" if self.tipo == "VENTA" else "Proveedor:"
        is_venta = self.tipo == "VENTA"
        tercero_tipo = "CLIENTE" if is_venta else "PROVEEDOR"
        terceros = self.db.fetchall(
            f"SELECT id, numero_id, razon_social FROM terceros "
            f"WHERE {'es_cliente' if is_venta else 'es_proveedor'}=1 AND activo=1 "
            "ORDER BY razon_social")
        tercero_opts = [f"{t['numero_id']} - {t['razon_social']}" for t in terceros]
        self._tercero_ids = {f"{t['numero_id']} - {t['razon_social']}": t['id']
                             for t in terceros}

        fields_left = [
            ("fecha", "Fecha:", str(datetime.date.today()), 12),
        ]
        if not is_venta:
            fields_left.append(("numero_externo", "N° Factura Proveedor:", "", 20))
        fields_left.append(("fecha_vencimiento", "Fecha Vencimiento:", "", 12))

        lf = ttk.LabelFrame(f, text="Encabezado", padding=8)
        lf.pack(fill="x", pady=4)
        for i, (k, lbl, default, w) in enumerate(fields_left):
            v = tk.StringVar(value=default)
            self.vs[k] = v
            row = ttk.Frame(lf)
            row.grid(row=i // 2, column=(i % 2) * 2, sticky="w", padx=8, pady=3)
            ttk.Label(row, text=lbl, width=20, anchor="e").pack(side="left", padx=3)
            ttk.Entry(row, textvariable=v, width=w,
                      state="disabled" if self.readonly else "normal").pack(side="left")

        # Tercero
        r = ttk.Frame(lf)
        r.grid(row=3, column=0, columnspan=4, sticky="w", padx=8, pady=3)
        ttk.Label(r, text=label_col, width=20, anchor="e").pack(side="left", padx=3)
        v = tk.StringVar()
        self.vs["tercero_sel"] = v
        ttk.Combobox(r, textvariable=v, values=tercero_opts,
                     width=45, state="readonly" if not self.readonly else "disabled").pack(side="left")

        # Condición de pago
        r2 = ttk.Frame(lf)
        r2.grid(row=4, column=0, columnspan=4, sticky="w", padx=8, pady=3)
        ttk.Label(r2, text="Condición de Pago:", width=20, anchor="e").pack(side="left", padx=3)
        v = tk.StringVar(value="CONTADO")
        self.vs["condicion_pago"] = v
        ttk.Combobox(r2, textvariable=v, values=CONDICION_PAGO,
                     width=20, state="readonly" if not self.readonly else "disabled").pack(side="left")
        ttk.Label(r2, text="Observaciones:", width=14, anchor="e").pack(side="left", padx=8)
        v2 = tk.StringVar()
        self.vs["observaciones"] = v2
        ttk.Entry(r2, textvariable=v2, width=35,
                  state="disabled" if self.readonly else "normal").pack(side="left")

        lf.grid_columnconfigure(1, weight=1)
        lf.grid_columnconfigure(3, weight=1)

    def _build_detalle(self, f):
        dtb = ttk.Frame(f)
        dtb.pack(fill="x", pady=2)
        if not self.readonly:
            ttk.Button(dtb, text="➕ Agregar Producto/Servicio",
                       command=self._add_linea).pack(side="left", padx=3)
            ttk.Button(dtb, text="🗑 Eliminar Línea",
                       command=self._del_linea).pack(side="left", padx=3)

        cols = [
            ("codigo", "Código", 80, "w"),
            ("descripcion", "Descripción", 280, "w"),
            ("cantidad", "Cantidad", 70, "center"),
            ("precio", "Precio Unit.", 100, "e"),
            ("descuento", "Desc%", 55, "center"),
            ("subtotal", "Subtotal", 100, "e"),
            ("iva_pct", "IVA%", 50, "center"),
            ("iva_val", "IVA", 90, "e"),
            ("total", "Total", 110, "e"),
        ]
        self.tabla_det = DataTable(f, cols)
        self.tabla_det.pack(fill="both", expand=True)

    def _build_totales(self, f):
        self.v_tots = {}
        totales = [
            ("subtotal", "Subtotal Bruto:", False),
            ("descuento_comercial", "Descuento Comercial:", False),
            ("base_iva19", "Base Gravada 19%:", False),
            ("iva19", "IVA 19%:", False),
            ("base_iva5", "Base Gravada 5%:", False),
            ("iva5", "IVA 5%:", False),
            ("excluido", "Excluido de IVA:", False),
            ("exento", "Exento de IVA:", False),
            ("reteiva", "Retención IVA (15%):", False),
            ("rete_fuente", "Retención en la Fuente:", True),
            ("rete_ica", "Retención ICA:", True),
            ("total", "TOTAL FACTURA:", False),
            ("saldo", "Saldo Pendiente:", False),
        ]
        lf = ttk.LabelFrame(f, text="Resumen de Impuestos y Totales", padding=12)
        lf.pack(fill="both", expand=True, padx=20, pady=10)

        for i, (k, lbl, editable) in enumerate(totales):
            v = tk.StringVar(value="$ 0")
            self.v_tots[k] = v
            row = ttk.Frame(lf)
            row.grid(row=i, column=0, sticky="ew", pady=2)
            weight = ("Segoe UI", 11, "bold") if k == "total" else ("Segoe UI", 10)
            color = C_PRIMARY if k == "total" else "#2c3e50"
            ttk.Label(row, text=lbl, width=28, anchor="e",
                      font=weight, foreground=color).pack(side="left", padx=6)
            if editable and not self.readonly:
                ttk.Entry(row, textvariable=v, width=18).pack(side="left")
            else:
                ttk.Label(row, textvariable=v, width=18, anchor="e",
                          font=weight, foreground=color).pack(side="left")

        # Botón recalcular
        if not self.readonly:
            ttk.Button(lf, text="🔄 Recalcular Impuestos",
                       command=self._recalculate).grid(row=len(totales)+1, column=0,
                                                        pady=8, sticky="w", padx=6)
        lf.columnconfigure(0, weight=1)

    def _add_linea(self):
        LineaFacturaDialog(self, self.db, self._on_linea_added)

    def _on_linea_added(self, linea):
        self.lineas.append(linea)
        self.tabla_det.insert([
            linea["codigo"], linea["descripcion"],
            linea["cantidad"], col_fmt(linea["precio"], 2),
            f"{linea['descuento_pct']:.1f}%",
            col_fmt(linea["subtotal"]), f"{linea['iva_pct']:.0f}%",
            col_fmt(linea["iva"]), col_fmt(linea["total"]),
        ])
        self._recalculate()

    def _del_linea(self):
        sel = self.tabla_det.tree.selection()
        if not sel:
            return
        idx = list(self.tabla_det.tree.get_children()).index(sel[0])
        if idx < len(self.lineas):
            self.lineas.pop(idx)
        self.tabla_det.tree.delete(sel[0])
        self._recalculate()

    def _recalculate(self):
        subtotal = sum(l["subtotal"] for l in self.lineas)
        base_19 = sum(l["subtotal"] for l in self.lineas if l["iva_pct"] == 19)
        base_5 = sum(l["subtotal"] for l in self.lineas if l["iva_pct"] == 5)
        excluido = sum(l["subtotal"] for l in self.lineas if l["iva_pct"] == -1)
        exento = sum(l["subtotal"] for l in self.lineas if l["iva_pct"] == 0)
        iva19 = round(base_19 * 0.19)
        iva5 = round(base_5 * 0.05)
        iva_total = iva19 + iva5
        reteiva = round(iva_total * 0.15)
        total = subtotal + iva_total - reteiva
        try:
            rete_f = float(self.v_tots.get("rete_fuente", tk.StringVar()).get().replace("$", "").replace(".", "").replace(",", ".").strip() or 0)
        except ValueError:
            rete_f = 0
        try:
            rete_ica = float(self.v_tots.get("rete_ica", tk.StringVar()).get().replace("$", "").replace(".", "").replace(",", ".").strip() or 0)
        except ValueError:
            rete_ica = 0
        total_neto = total - rete_f - rete_ica

        mapping = {
            "subtotal": subtotal, "descuento_comercial": 0,
            "base_iva19": base_19, "iva19": iva19,
            "base_iva5": base_5, "iva5": iva5,
            "excluido": excluido, "exento": exento,
            "reteiva": reteiva, "total": total_neto,
            "saldo": total_neto,
        }
        for k, v in mapping.items():
            if k in self.v_tots:
                self.v_tots[k].set(col_fmt(v))

    def _load_data(self):
        self.vs["fecha"].set(self.data.get("fecha", ""))
        self.vs.get("numero_externo", tk.StringVar()).set(
            self.data.get("numero_externo", "") or "")
        self.vs.get("fecha_vencimiento", tk.StringVar()).set(
            self.data.get("fecha_vencimiento", "") or "")
        self.vs["condicion_pago"].set(self.data.get("condicion_pago", "CONTADO"))
        self.vs["observaciones"].set(self.data.get("observaciones", "") or "")

        tabla_det = ("facturas_venta_detalle" if self.tipo == "VENTA"
                     else "facturas_compra_detalle")
        det = self.db.fetchall(
            f"SELECT * FROM {tabla_det} WHERE factura_id=?", (self.data["id"],))
        for d in det:
            linea = {
                "codigo": "", "descripcion": d["descripcion"],
                "cantidad": d["cantidad"],
                "precio": d["precio_unitario"],
                "descuento_pct": d["descuento_pct"] or 0,
                "subtotal": d["subtotal"],
                "iva_pct": d["tarifa_iva"],
                "iva": d["iva"], "total": d["total"],
            }
            self.lineas.append(linea)
            self.tabla_det.insert([
                "", linea["descripcion"], linea["cantidad"],
                col_fmt(linea["precio"], 2),
                f"{linea['descuento_pct']:.1f}%",
                col_fmt(linea["subtotal"]),
                f"{linea['iva_pct']:.0f}%",
                col_fmt(linea["iva"]), col_fmt(linea["total"]),
            ])
        self._recalculate()

    def _save(self):
        if not self.lineas:
            show_error("Debe agregar al menos un producto o servicio.")
            return
        tercero_sel = self.vs["tercero_sel"].get()
        if not tercero_sel:
            show_error("Debe seleccionar un cliente o proveedor.")
            return
        tercero_id = self._tercero_ids.get(tercero_sel)
        self._recalculate()

        subtotal = sum(l["subtotal"] for l in self.lineas)
        base_19 = sum(l["subtotal"] for l in self.lineas if l["iva_pct"] == 19)
        base_5 = sum(l["subtotal"] for l in self.lineas if l["iva_pct"] == 5)
        iva19 = round(base_19 * 0.19)
        iva5 = round(base_5 * 0.05)
        iva_total = iva19 + iva5
        reteiva = round(iva_total * 0.15)
        total = subtotal + iva_total - reteiva

        tipo_comp = "FV" if self.tipo == "VENTA" else "FC"
        prefijo = tipo_comp
        consec = next_consecutivo(self.db, tipo_comp)
        fecha = self.vs["fecha"].get().strip()

        if self.tipo == "VENTA":
            self.db.execute("""INSERT INTO facturas_venta
                (tipo, consecutivo, prefijo, fecha,
                 fecha_vencimiento, cliente_id, condicion_pago,
                 subtotal, base_iva19, iva19, base_iva5, iva5, reteiva,
                 total, saldo, observaciones, estado)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                ("FV", consec, prefijo, fecha,
                 self.vs.get("fecha_vencimiento", tk.StringVar()).get() or None,
                 tercero_id, self.vs["condicion_pago"].get(),
                 subtotal, base_19, iva19, base_5, iva5, reteiva,
                 total, total, self.vs["observaciones"].get() or None, "ACTIVO"))
            fac_id = self.db.conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            for i, l in enumerate(self.lineas, 1):
                self.db.execute("""INSERT INTO facturas_venta_detalle
                    (factura_id, linea, descripcion, cantidad, precio_unitario,
                     descuento_pct, subtotal, tarifa_iva, iva, total)
                    VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (fac_id, i, l["descripcion"], l["cantidad"], l["precio"],
                     l["descuento_pct"], l["subtotal"], l["iva_pct"], l["iva"], l["total"]))
        else:
            self.db.execute("""INSERT INTO facturas_compra
                (tipo, numero_externo, fecha, fecha_vencimiento, proveedor_id,
                 condicion_pago, subtotal, base_iva19, iva19, base_iva5, iva5, reteiva,
                 total, saldo, observaciones, estado)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                ("FC", self.vs.get("numero_externo", tk.StringVar()).get() or None,
                 fecha,
                 self.vs.get("fecha_vencimiento", tk.StringVar()).get() or None,
                 tercero_id, self.vs["condicion_pago"].get(),
                 subtotal, base_19, iva19, base_5, iva5, reteiva,
                 total, total, self.vs["observaciones"].get() or None, "ACTIVO"))
            fac_id = self.db.conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            for i, l in enumerate(self.lineas, 1):
                self.db.execute("""INSERT INTO facturas_compra_detalle
                    (factura_id, linea, descripcion, cantidad, precio_unitario,
                     descuento_pct, subtotal, tarifa_iva, iva, total)
                    VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (fac_id, i, l["descripcion"], l["cantidad"], l["precio"],
                     l["descuento_pct"], l["subtotal"], l["iva_pct"], l["iva"], l["total"]))
        self.db.commit()
        show_info(f"Factura {prefijo}-{consec} guardada correctamente.")
        self.on_save()
        self.destroy()


class LineaFacturaDialog(tk.Toplevel):
    def __init__(self, parent, db: DB, callback):
        super().__init__(parent)
        self.db = db
        self.callback = callback
        self.title("Agregar Producto / Servicio")
        self.resizable(False, False)
        self.grab_set()
        self._build()

    def _build(self):
        f = ttk.Frame(self, padding=16, style="White.TFrame")
        f.pack(fill="both", expand=True)

        productos = self.db.fetchall(
            "SELECT codigo, descripcion, precio_venta, tarifa_iva FROM productos WHERE activo=1 ORDER BY descripcion")
        prod_opts = [f"{p['codigo']} - {p['descripcion']}" for p in productos]
        self._prod_map = {f"{p['codigo']} - {p['descripcion']}": p for p in productos}

        fields = [
            ("producto", "Producto/Servicio:", None, 40),
        ]
        self.vs = {}
        v = tk.StringVar()
        self.vs["producto"] = v
        r = ttk.Frame(f, style="White.TFrame")
        r.pack(fill="x", pady=4)
        ttk.Label(r, text="Producto/Servicio:", style="White.TLabel",
                  width=20, anchor="e").pack(side="left", padx=4)
        cb = ttk.Combobox(r, textvariable=v, values=[""] + prod_opts, width=38)
        cb.pack(side="left")
        cb.bind("<<ComboboxSelected>>", self._on_prod_select)

        for k, lbl, default, w in [
            ("descripcion", "Descripción:", "", 40),
            ("cantidad", "Cantidad:", "1", 10),
            ("precio", "Precio Unitario:", "0", 15),
            ("descuento_pct", "Descuento %:", "0", 8),
        ]:
            v = tk.StringVar(value=default)
            self.vs[k] = v
            r = ttk.Frame(f, style="White.TFrame")
            r.pack(fill="x", pady=4)
            ttk.Label(r, text=lbl, style="White.TLabel",
                      width=20, anchor="e").pack(side="left", padx=4)
            e = ttk.Entry(r, textvariable=v, width=w)
            e.pack(side="left")
            if k in ("cantidad", "precio", "descuento_pct"):
                e.bind("<FocusOut>", self._recalc_preview)

        v = tk.StringVar(value="19")
        self.vs["iva_pct"] = v
        r = ttk.Frame(f, style="White.TFrame")
        r.pack(fill="x", pady=4)
        ttk.Label(r, text="Tarifa IVA:", style="White.TLabel",
                  width=20, anchor="e").pack(side="left", padx=4)
        ttk.Combobox(r, textvariable=v,
                     values=["19", "5", "0", "-1"],
                     state="readonly", width=8).pack(side="left")
        ttk.Label(r, text="-1 = Excluido", style="Light.TLabel").pack(side="left", padx=6)

        self.lbl_total = ttk.Label(f, text="Total: $0", style="White.TLabel",
                                    font=("Segoe UI", 11, "bold"), foreground=C_PRIMARY)
        self.lbl_total.pack(pady=6)

        bf = ttk.Frame(f, style="White.TFrame")
        bf.pack(pady=8)
        ttk.Button(bf, text="Agregar", command=self._add,
                   style="Success.TButton").pack(side="left", padx=4)
        ttk.Button(bf, text="Cancelar", command=self.destroy,
                   style="Danger.TButton").pack(side="left", padx=4)

    def _on_prod_select(self, event=None):
        sel = self.vs["producto"].get()
        if sel in self._prod_map:
            p = self._prod_map[sel]
            self.vs["descripcion"].set(p["descripcion"])
            self.vs["precio"].set(str(p["precio_venta"]))
            self.vs["iva_pct"].set(str(int(p["tarifa_iva"])))
        self._recalc_preview()

    def _recalc_preview(self, event=None):
        try:
            qty = float(self.vs["cantidad"].get() or 0)
            price = float(self.vs["precio"].get().replace(".", "").replace(",", ".") or 0)
            desc = float(self.vs["descuento_pct"].get() or 0)
            sub = qty * price * (1 - desc / 100)
            iva_p = float(self.vs["iva_pct"].get() or 0)
            iva_v = round(sub * iva_p / 100) if iva_p > 0 else 0
            self.lbl_total.config(text=f"Subtotal: {col_fmt(sub)}  |  IVA: {col_fmt(iva_v)}  |  Total: {col_fmt(sub+iva_v)}")
        except Exception:
            pass

    def _add(self):
        desc = self.vs["descripcion"].get().strip()
        if not desc:
            show_error("Ingrese la descripción.")
            return
        try:
            qty = float(self.vs["cantidad"].get() or 0)
            price = float(self.vs["precio"].get().replace(".", "").replace(",", ".") or 0)
            desc_pct = float(self.vs["descuento_pct"].get() or 0)
            iva_pct = float(self.vs["iva_pct"].get() or 0)
        except ValueError:
            show_error("Valores numéricos inválidos.")
            return
        sub = round(qty * price * (1 - desc_pct / 100))
        iva_v = round(sub * iva_pct / 100) if iva_pct > 0 else 0
        linea = {
            "codigo": self.vs["producto"].get().split(" - ")[0] if " - " in self.vs["producto"].get() else "",
            "descripcion": desc, "cantidad": qty,
            "precio": price, "descuento_pct": desc_pct,
            "subtotal": sub, "iva_pct": iva_pct,
            "iva": iva_v, "total": sub + iva_v,
        }
        self.callback(linea)
        self.destroy()
