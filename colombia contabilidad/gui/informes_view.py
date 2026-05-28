#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vista Informes y Estados Financieros - CONTACOL PRO"""
import tkinter as tk
from tkinter import ttk, filedialog
import datetime
from .styles import C_PRIMARY, C_WHITE, C_BG, FONT_TITLE, FONT_HEADER, col_fmt
from .widgets import DataTable, show_info, show_error
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import DB, get_balance_comprobacion, get_movimientos_cuenta


class InformesView(ttk.Frame):
    def __init__(self, parent, db: DB):
        super().__init__(parent)
        self.db = db
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=C_PRIMARY, height=40)
        hdr.pack(fill="x")
        tk.Label(hdr, text="  Informes y Estados Financieros",
                 bg=C_PRIMARY, fg="white", font=FONT_TITLE).place(x=0, y=5)

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=6, pady=6)

        self._tab_balance(nb)
        self._tab_pyg(nb)
        self._tab_libro_mayor(nb)
        self._tab_balance_comp(nb)
        self._tab_cartera(nb)
        self._tab_impuestos(nb)

    # ── Balance General ──────────────────────────────────────────────────────
    def _tab_balance(self, nb):
        f = ttk.Frame(nb)
        nb.add(f, text="  Balance General  ")

        ff = ttk.Frame(f)
        ff.pack(fill="x", padx=8, pady=6)
        ttk.Label(ff, text="Al:").pack(side="left", padx=4)
        self.v_fecha_bg = tk.StringVar(value=str(datetime.date.today()))
        ttk.Entry(ff, textvariable=self.v_fecha_bg, width=12).pack(side="left", padx=4)
        ttk.Button(ff, text="📊 Generar Balance",
                   command=self._generar_balance).pack(side="left", padx=6)
        ttk.Button(ff, text="📄 Exportar PDF",
                   command=lambda: self._exportar_pdf("balance")).pack(side="left", padx=4)
        ttk.Button(ff, text="📊 Exportar Excel",
                   command=lambda: self._exportar_excel("balance")).pack(side="left", padx=4)

        self.txt_balance = tk.Text(f, font=("Courier New", 10),
                                    bg=C_WHITE, fg="#2c3e50",
                                    wrap="none", state="disabled")
        sb_v = ttk.Scrollbar(f, orient="vertical", command=self.txt_balance.yview)
        sb_h = ttk.Scrollbar(f, orient="horizontal", command=self.txt_balance.xview)
        self.txt_balance.configure(yscrollcommand=sb_v.set, xscrollcommand=sb_h.set)
        sb_v.pack(side="right", fill="y")
        sb_h.pack(side="bottom", fill="x")
        self.txt_balance.pack(fill="both", expand=True, padx=8, pady=4)

    def _generar_balance(self):
        fecha_str = self.v_fecha_bg.get().strip()
        try:
            fecha = datetime.datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            show_error("Formato de fecha inválido (YYYY-MM-DD).")
            return

        anio = fecha.year
        mes = fecha.month

        # Obtener balance de comprobación
        bc = get_balance_comprobacion(self.db, anio, mes)

        activos = {}
        pasivos = {}
        patrimonio = {}

        for row in bc:
            codigo = row[0]
            nombre = row[1]
            naturaleza = row[2]
            debito = row[3] or 0
            credito = row[4] or 0
            clase = int(codigo[0]) if codigo else 0
            saldo = debito - credito if naturaleza == "DEBITO" else credito - debito

            if clase == 1:
                activos[codigo] = (nombre, saldo)
            elif clase == 2:
                pasivos[codigo] = (nombre, saldo)
            elif clase == 3:
                patrimonio[codigo] = (nombre, saldo)

        empresa = self.db.fetchone("SELECT razon_social, nit FROM empresa LIMIT 1")
        nombre_empresa = empresa["razon_social"] if empresa else "SIN EMPRESA"
        nit = empresa["nit"] if empresa else ""

        lineas = []
        ancho = 72

        def line(txt=""):
            lineas.append(txt)

        def sep(c="═"):
            lineas.append(c * ancho)

        def head(txt):
            lineas.append(f"{'':^4}{txt.upper()}")

        def fila(codigo, nombre, valor, indent=4):
            nombre_trunc = nombre[:38] if len(nombre) > 38 else nombre
            lineas.append(f"{'':>{indent}}{codigo:<10}{nombre_trunc:<38}  {col_fmt(valor):>16}")

        def subtotal(lbl, valor, indent=2):
            lineas.append(f"{'':>{indent}}{'':10}{lbl:<38}  {col_fmt(valor):>16}")
            lineas.append("─" * ancho)

        sep()
        lineas.append(f"{'BALANCE GENERAL':^{ancho}}")
        lineas.append(f"{nombre_empresa:^{ancho}}")
        lineas.append(f"{'NIT: ' + nit:^{ancho}}")
        lineas.append(f"{'Al ' + fecha.strftime('%d de %B de %Y'):^{ancho}}")
        lineas.append(f"{'(Expresado en Pesos Colombianos)':^{ancho}}")
        sep()

        # ACTIVOS
        total_activo = sum(v[1] for v in activos.values())
        head("ACTIVOS")
        for codigo in sorted(activos.keys()):
            nombre, saldo = activos[codigo]
            if len(codigo) >= 4:
                fila(codigo, nombre, saldo, 6)
        subtotal("TOTAL ACTIVOS", total_activo)
        line()

        # PASIVOS
        total_pasivo = sum(v[1] for v in pasivos.values())
        head("PASIVOS")
        for codigo in sorted(pasivos.keys()):
            nombre, saldo = pasivos[codigo]
            if len(codigo) >= 4:
                fila(codigo, nombre, saldo, 6)
        subtotal("TOTAL PASIVOS", total_pasivo)
        line()

        # PATRIMONIO
        total_pat = sum(v[1] for v in patrimonio.values())
        head("PATRIMONIO")
        for codigo in sorted(patrimonio.keys()):
            nombre, saldo = patrimonio[codigo]
            if len(codigo) >= 4:
                fila(codigo, nombre, saldo, 6)
        subtotal("TOTAL PATRIMONIO", total_pat)
        line()

        sep("═")
        total_p_pat = total_pasivo + total_pat
        lineas.append(f"{'TOTAL PASIVO + PATRIMONIO':<50}  {col_fmt(total_p_pat):>16}")
        lineas.append(f"{'TOTAL ACTIVOS':<50}  {col_fmt(total_activo):>16}")
        diff = total_activo - total_p_pat
        lineas.append(f"{'DIFERENCIA (debe ser 0)':<50}  {col_fmt(diff):>16}")
        sep()
        lineas.append("")
        lineas.append(f"  Generado: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}    CONTACOL PRO v1.0")

        self._show_text(self.txt_balance, "\n".join(lineas))

    # ── Estado de Resultados ─────────────────────────────────────────────────
    def _tab_pyg(self, nb):
        f = ttk.Frame(nb)
        nb.add(f, text="  Estado de Resultados (P&G)  ")

        ff = ttk.Frame(f)
        ff.pack(fill="x", padx=8, pady=6)
        ttk.Label(ff, text="Año:").pack(side="left", padx=4)
        self.v_anio_pyg = tk.StringVar(value="2026")
        ttk.Entry(ff, textvariable=self.v_anio_pyg, width=6).pack(side="left", padx=4)
        ttk.Label(ff, text="Mes hasta:").pack(side="left", padx=4)
        self.v_mes_pyg = tk.StringVar(value=str(datetime.date.today().month))
        ttk.Combobox(ff, textvariable=self.v_mes_pyg,
                     values=[str(i) for i in range(1, 13)],
                     state="readonly", width=4).pack(side="left", padx=4)
        ttk.Button(ff, text="📊 Generar P&G",
                   command=self._generar_pyg).pack(side="left", padx=6)
        ttk.Button(ff, text="📄 Exportar PDF",
                   command=lambda: self._exportar_pdf("pyg")).pack(side="left", padx=4)

        self.txt_pyg = tk.Text(f, font=("Courier New", 10),
                                bg=C_WHITE, fg="#2c3e50",
                                wrap="none", state="disabled")
        sb_v = ttk.Scrollbar(f, orient="vertical", command=self.txt_pyg.yview)
        sb_h = ttk.Scrollbar(f, orient="horizontal", command=self.txt_pyg.xview)
        self.txt_pyg.configure(yscrollcommand=sb_v.set, xscrollcommand=sb_h.set)
        sb_v.pack(side="right", fill="y")
        sb_h.pack(side="bottom", fill="x")
        self.txt_pyg.pack(fill="both", expand=True, padx=8, pady=4)

    def _generar_pyg(self):
        try:
            anio = int(self.v_anio_pyg.get())
            mes = int(self.v_mes_pyg.get())
        except ValueError:
            show_error("Año o mes inválido.")
            return

        bc = get_balance_comprobacion(self.db, anio, mes)
        ingresos = {}
        gastos = {}
        costos = {}

        for row in bc:
            codigo = row[0]
            nombre = row[1]
            naturaleza = row[2]
            debito = row[3] or 0
            credito = row[4] or 0
            clase = int(codigo[0]) if codigo else 0
            if naturaleza == "CREDITO":
                saldo = credito - debito
            else:
                saldo = debito - credito

            if clase == 4:
                ingresos[codigo] = (nombre, saldo)
            elif clase == 5:
                gastos[codigo] = (nombre, saldo)
            elif clase == 6:
                costos[codigo] = (nombre, saldo)

        empresa = self.db.fetchone("SELECT razon_social, nit FROM empresa LIMIT 1")
        nombre_empresa = empresa["razon_social"] if empresa else "SIN EMPRESA"
        nit = empresa["nit"] if empresa else ""

        lineas = []
        ancho = 68

        meses_n = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                   "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

        def sep(c="═"):
            lineas.append(c * ancho)

        sep()
        lineas.append(f"{'ESTADO DE RESULTADOS (P&G)':^{ancho}}")
        lineas.append(f"{nombre_empresa:^{ancho}}")
        lineas.append(f"{'NIT: ' + nit:^{ancho}}")
        lineas.append(f"{'Enero - ' + meses_n[mes] + ' ' + str(anio):^{ancho}}")
        lineas.append(f"{'(Expresado en Pesos Colombianos)':^{ancho}}")
        sep()

        total_ingresos = sum(v[1] for v in ingresos.values())
        lineas.append(f"\n  {'INGRESOS OPERACIONALES'}")
        lineas.append("─" * ancho)
        for c in sorted(ingresos.keys()):
            if len(c) >= 4:
                n, s = ingresos[c]
                lineas.append(f"  {c:<10}{n[:36]:<36}  {col_fmt(s):>16}")
        lineas.append("─" * ancho)
        lineas.append(f"  {'TOTAL INGRESOS':<46}  {col_fmt(total_ingresos):>16}")

        total_costos = sum(v[1] for v in costos.values())
        lineas.append(f"\n  {'COSTOS DE VENTAS Y SERVICIOS'}")
        lineas.append("─" * ancho)
        for c in sorted(costos.keys()):
            if len(c) >= 4:
                n, s = costos[c]
                lineas.append(f"  {c:<10}{n[:36]:<36}  {col_fmt(s):>16}")
        lineas.append("─" * ancho)
        lineas.append(f"  {'TOTAL COSTO DE VENTAS':<46}  {col_fmt(total_costos):>16}")

        utilidad_bruta = total_ingresos - total_costos
        lineas.append("═" * ancho)
        lineas.append(f"  {'UTILIDAD BRUTA':<46}  {col_fmt(utilidad_bruta):>16}")

        total_gastos_adm = sum(v[1] for c, v in gastos.items() if c.startswith("51"))
        total_gastos_vta = sum(v[1] for c, v in gastos.items() if c.startswith("52"))
        total_gastos_fin = sum(v[1] for c, v in gastos.items() if c.startswith("53"))
        total_impuesto = sum(v[1] for c, v in gastos.items() if c.startswith("54"))

        lineas.append(f"\n  {'GASTOS OPERACIONALES'}")
        lineas.append(f"  {'  Administración':<44}  {col_fmt(total_gastos_adm):>16}")
        lineas.append(f"  {'  Ventas':<44}  {col_fmt(total_gastos_vta):>16}")
        lineas.append("─" * ancho)
        total_gastos_op = total_gastos_adm + total_gastos_vta
        lineas.append(f"  {'TOTAL GASTOS OPERACIONALES':<44}  {col_fmt(total_gastos_op):>16}")

        utilidad_op = utilidad_bruta - total_gastos_op
        lineas.append("═" * ancho)
        lineas.append(f"  {'UTILIDAD OPERACIONAL':<44}  {col_fmt(utilidad_op):>16}")

        lineas.append(f"\n  {'INGRESOS/GASTOS NO OPERACIONALES'}")
        lineas.append(f"  {'  Gastos Financieros':<44}  ({col_fmt(total_gastos_fin):>14})")
        utilidad_antes = utilidad_op - total_gastos_fin
        lineas.append("─" * ancho)
        lineas.append(f"  {'UTILIDAD ANTES DE IMPUESTOS':<44}  {col_fmt(utilidad_antes):>16}")

        impuesto_renta = round(max(0, utilidad_antes) * 0.35)
        lineas.append(f"  {'  Impuesto de Renta (35%)':<44}  ({col_fmt(impuesto_renta):>14})")
        utilidad_neta = utilidad_antes - impuesto_renta
        lineas.append("═" * ancho)
        lineas.append(f"  {'UTILIDAD NETA DEL EJERCICIO':<44}  {col_fmt(utilidad_neta):>16}")
        sep()
        lineas.append("")
        lineas.append(f"  Generado: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}    CONTACOL PRO v1.0")

        self._show_text(self.txt_pyg, "\n".join(lineas))

    # ── Libro Mayor ──────────────────────────────────────────────────────────
    def _tab_libro_mayor(self, nb):
        f = ttk.Frame(nb)
        nb.add(f, text="  Libro Mayor  ")

        ff = ttk.Frame(f)
        ff.pack(fill="x", padx=8, pady=6)
        ttk.Label(ff, text="Cuenta:").pack(side="left", padx=4)
        self.v_cuenta_mayor = tk.StringVar()
        ttk.Entry(ff, textvariable=self.v_cuenta_mayor, width=14).pack(side="left", padx=4)
        ttk.Label(ff, text="Desde:").pack(side="left", padx=4)
        self.v_desde_mayor = tk.StringVar(value=f"{datetime.date.today().year}-01-01")
        ttk.Entry(ff, textvariable=self.v_desde_mayor, width=12).pack(side="left", padx=4)
        ttk.Label(ff, text="Hasta:").pack(side="left", padx=4)
        self.v_hasta_mayor = tk.StringVar(value=str(datetime.date.today()))
        ttk.Entry(ff, textvariable=self.v_hasta_mayor, width=12).pack(side="left", padx=4)
        ttk.Button(ff, text="📋 Ver Movimientos",
                   command=self._ver_mayor).pack(side="left", padx=6)

        cols = [
            ("fecha", "Fecha", 90, "center"),
            ("tipo", "Tipo", 55, "center"),
            ("consec", "N°", 60, "center"),
            ("tercero", "Tercero", 180, "w"),
            ("descripcion", "Descripción", 220, "w"),
            ("debito", "Débito", 110, "e"),
            ("credito", "Crédito", 110, "e"),
            ("saldo", "Saldo", 110, "e"),
        ]
        self.tabla_mayor = DataTable(f, cols)
        self.tabla_mayor.pack(fill="both", expand=True, padx=8, pady=4)
        self.lbl_saldo_mayor = tk.Label(f, text="", bg=C_BG,
                                         font=("Segoe UI", 10, "bold"),
                                         foreground=C_PRIMARY)
        self.lbl_saldo_mayor.pack(padx=8, pady=3, anchor="e")

    def _ver_mayor(self):
        cuenta = self.v_cuenta_mayor.get().strip()
        if not cuenta:
            show_error("Ingrese el código de cuenta.")
            return
        desde = self.v_desde_mayor.get().strip()
        hasta = self.v_hasta_mayor.get().strip()
        movs = get_movimientos_cuenta(self.db, cuenta, desde, hasta)
        self.tabla_mayor.clear()
        saldo = 0
        total_db = total_cr = 0
        r = self.db.fetchone("SELECT nombre, naturaleza FROM plan_cuentas WHERE codigo=?", (cuenta,))
        nat = r["naturaleza"] if r else "DEBITO"

        for m in movs:
            db_v = m["debito"] or 0
            cr_v = m["credito"] or 0
            if nat == "DEBITO":
                saldo += db_v - cr_v
            else:
                saldo += cr_v - db_v
            total_db += db_v
            total_cr += cr_v
            self.tabla_mayor.insert([
                m["fecha"], m["tipo_codigo"], m["consecutivo"],
                m["tercero_nom"] or "",
                m["descripcion"] or m["comp_desc"] or "",
                col_fmt(db_v) if db_v else "",
                col_fmt(cr_v) if cr_v else "",
                col_fmt(saldo),
            ])
        self.tabla_mayor.insert(
            ["", "", "", "", "TOTALES",
             col_fmt(total_db), col_fmt(total_cr), col_fmt(saldo)],
            tags=("total",))
        cuenta_nombre = r["nombre"] if r else cuenta
        self.lbl_saldo_mayor.config(
            text=f"Cuenta: {cuenta} - {cuenta_nombre}  |  "
                 f"Débitos: {col_fmt(total_db)}  |  "
                 f"Créditos: {col_fmt(total_cr)}  |  "
                 f"Saldo: {col_fmt(saldo)}")

    # ── Balance de Comprobación ───────────────────────────────────────────────
    def _tab_balance_comp(self, nb):
        f = ttk.Frame(nb)
        nb.add(f, text="  Balance de Comprobación  ")

        ff = ttk.Frame(f)
        ff.pack(fill="x", padx=8, pady=6)
        ttk.Label(ff, text="Año:").pack(side="left", padx=4)
        self.v_anio_bc = tk.StringVar(value="2026")
        ttk.Entry(ff, textvariable=self.v_anio_bc, width=6).pack(side="left", padx=4)
        ttk.Label(ff, text="Mes:").pack(side="left", padx=4)
        self.v_mes_bc = tk.StringVar(value=str(datetime.date.today().month))
        ttk.Combobox(ff, textvariable=self.v_mes_bc,
                     values=[str(i) for i in range(1, 13)],
                     state="readonly", width=4).pack(side="left", padx=4)
        ttk.Button(ff, text="📊 Generar",
                   command=self._generar_bc).pack(side="left", padx=6)

        cols = [
            ("codigo", "Código", 80, "w"),
            ("nombre", "Nombre Cuenta", 300, "w"),
            ("debito_acum", "Débito Acum.", 120, "e"),
            ("credito_acum", "Crédito Acum.", 120, "e"),
            ("saldo_db", "Saldo Débito", 120, "e"),
            ("saldo_cr", "Saldo Crédito", 120, "e"),
        ]
        self.tabla_bc = DataTable(f, cols)
        self.tabla_bc.pack(fill="both", expand=True, padx=8, pady=4)

    def _generar_bc(self):
        try:
            anio = int(self.v_anio_bc.get())
            mes = int(self.v_mes_bc.get())
        except ValueError:
            show_error("Año o mes inválido.")
            return
        bc = get_balance_comprobacion(self.db, anio, mes)
        self.tabla_bc.clear()
        total_db = total_cr = total_sd = total_sc = 0
        for row in bc:
            codigo, nombre, naturaleza = row[0], row[1], row[2]
            debito, credito = row[3] or 0, row[4] or 0
            if naturaleza == "DEBITO":
                sd = max(0, debito - credito)
                sc = max(0, credito - debito)
            else:
                sc = max(0, credito - debito)
                sd = max(0, debito - credito)
            total_db += debito
            total_cr += credito
            total_sd += sd
            total_sc += sc
            self.tabla_bc.insert([
                codigo, nombre,
                col_fmt(debito), col_fmt(credito),
                col_fmt(sd) if sd else "",
                col_fmt(sc) if sc else "",
            ])
        self.tabla_bc.insert(
            ["", "TOTALES", col_fmt(total_db), col_fmt(total_cr),
             col_fmt(total_sd), col_fmt(total_sc)],
            tags=("total",))

    # ── Cartera ───────────────────────────────────────────────────────────────
    def _tab_cartera(self, nb):
        f = ttk.Frame(nb)
        nb.add(f, text="  Cartera C×C / C×P  ")

        ff = ttk.Frame(f)
        ff.pack(fill="x", padx=8, pady=6)
        self.v_tipo_cartera = tk.StringVar(value="VENTA")
        ttk.Radiobutton(ff, text="Cuentas por Cobrar (Clientes)",
                         variable=self.v_tipo_cartera, value="VENTA").pack(side="left", padx=6)
        ttk.Radiobutton(ff, text="Cuentas por Pagar (Proveedores)",
                         variable=self.v_tipo_cartera, value="COMPRA").pack(side="left", padx=6)
        ttk.Label(ff, text="Al:").pack(side="left", padx=4)
        self.v_fecha_cartera = tk.StringVar(value=str(datetime.date.today()))
        ttk.Entry(ff, textvariable=self.v_fecha_cartera, width=12).pack(side="left", padx=4)
        ttk.Button(ff, text="📊 Generar Cartera",
                   command=self._generar_cartera).pack(side="left", padx=6)

        cols = [
            ("tercero", "Cliente / Proveedor", 260, "w"),
            ("nit", "NIT", 110, "w"),
            ("facturas", "# Facturas", 75, "center"),
            ("total", "Total Facturado", 130, "e"),
            ("pagado", "Pagado", 110, "e"),
            ("saldo", "Saldo Pendiente", 130, "e"),
            ("vencido", "Vencido", 110, "e"),
        ]
        self.tabla_cartera = DataTable(f, cols)
        self.tabla_cartera.pack(fill="both", expand=True, padx=8, pady=4)
        self.lbl_cartera_total = tk.Label(f, text="", bg=C_BG,
                                           font=("Segoe UI", 10, "bold"),
                                           foreground=C_PRIMARY)
        self.lbl_cartera_total.pack(padx=8, pady=3, anchor="e")

    def _generar_cartera(self):
        tipo = self.v_tipo_cartera.get()
        fecha = self.v_fecha_cartera.get().strip()
        tabla_db = "facturas_venta" if tipo == "VENTA" else "facturas_compra"
        col_tercero = "cliente_id" if tipo == "VENTA" else "proveedor_id"

        sql = f"""SELECT t.razon_social, t.numero_id,
                         COUNT(f.id) as num_fac,
                         SUM(f.total) as total_fac,
                         SUM(f.total - f.saldo) as pagado,
                         SUM(f.saldo) as saldo,
                         SUM(CASE WHEN f.fecha_vencimiento < ? AND f.saldo > 0
                                  THEN f.saldo ELSE 0 END) as vencido
                  FROM {tabla_db} f
                  JOIN terceros t ON t.id=f.{col_tercero}
                  WHERE f.estado='ACTIVO' AND f.saldo > 0
                  GROUP BY f.{col_tercero}
                  ORDER BY t.razon_social"""
        rows = self.db.fetchall(sql, (fecha,))
        self.tabla_cartera.clear()
        total_saldo = total_vencido = 0
        for r in rows:
            total_saldo += r[5] or 0
            total_vencido += r[6] or 0
            self.tabla_cartera.insert([
                r[0] or "", r[1] or "", r[2],
                col_fmt(r[3]), col_fmt(r[4]),
                col_fmt(r[5]), col_fmt(r[6]),
            ], tags=("danger",) if (r[6] or 0) > 0 else None)
        self.tabla_cartera.insert(
            ["TOTALES", "", "", "", "", col_fmt(total_saldo), col_fmt(total_vencido)],
            tags=("total",))
        self.lbl_cartera_total.config(
            text=f"Total por cobrar: {col_fmt(total_saldo)}  |  Vencido: {col_fmt(total_vencido)}")

    # ── Impuestos ─────────────────────────────────────────────────────────────
    def _tab_impuestos(self, nb):
        f = ttk.Frame(nb)
        nb.add(f, text="  Resumen Impuestos  ")

        ff = ttk.Frame(f)
        ff.pack(fill="x", padx=8, pady=6)
        ttk.Label(ff, text="Año:").pack(side="left", padx=4)
        self.v_anio_imp = tk.StringVar(value="2026")
        ttk.Entry(ff, textvariable=self.v_anio_imp, width=6).pack(side="left", padx=4)
        ttk.Label(ff, text="Período IVA:").pack(side="left", padx=4)
        self.v_bim = tk.StringVar(value="1")
        ttk.Combobox(ff, textvariable=self.v_bim,
                     values=["1", "2", "3", "4", "5", "6"],
                     state="readonly", width=4).pack(side="left", padx=4)
        ttk.Button(ff, text="📊 Calcular IVA Bimestral",
                   command=self._calcular_iva).pack(side="left", padx=6)

        self.txt_imp = tk.Text(f, font=("Courier New", 10), bg=C_WHITE,
                                fg="#2c3e50", wrap="none", state="disabled")
        sb = ttk.Scrollbar(f, orient="vertical", command=self.txt_imp.yview)
        self.txt_imp.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.txt_imp.pack(fill="both", expand=True, padx=8, pady=4)

    def _calcular_iva(self):
        try:
            anio = int(self.v_anio_imp.get())
            bim = int(self.v_bim.get())
        except ValueError:
            show_error("Valores inválidos.")
            return

        mes_ini = (bim - 1) * 2 + 1
        mes_fin = mes_ini + 1
        meses_n = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                   "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

        # Ventas gravadas
        fecha_ini = f"{anio}-{mes_ini:02d}-01"
        fecha_fin = f"{anio}-{mes_fin:02d}-31"
        vtas = self.db.fetchone(
            """SELECT SUM(base_iva19) as b19, SUM(iva19) as v19,
                      SUM(base_iva5) as b5, SUM(iva5) as v5,
                      SUM(excluido) as excl, SUM(exento) as exen
               FROM facturas_venta WHERE fecha>=? AND fecha<=? AND estado='ACTIVO'""",
            (fecha_ini, fecha_fin)) or {}

        # Compras (iva descontable)
        cmpras = self.db.fetchone(
            """SELECT SUM(base_iva19) as b19, SUM(iva19) as v19,
                      SUM(base_iva5) as b5, SUM(iva5) as v5
               FROM facturas_compra WHERE fecha>=? AND fecha<=? AND estado='ACTIVO'""",
            (fecha_ini, fecha_fin)) or {}

        b19v = (vtas["b19"] if vtas and vtas["b19"] else 0)
        iva19g = (vtas["v19"] if vtas and vtas["v19"] else 0)
        b5v = (vtas["b5"] if vtas and vtas["b5"] else 0)
        iva5g = (vtas["v5"] if vtas and vtas["v5"] else 0)

        iva19d = (cmpras["v19"] if cmpras and cmpras["v19"] else 0)
        iva5d = (cmpras["v5"] if cmpras and cmpras["v5"] else 0)

        iva_gen = iva19g + iva5g
        iva_desc = iva19d + iva5d
        saldo = iva_gen - iva_desc

        ancho = 60
        lineas = [
            "═" * ancho,
            f"{'DECLARACIÓN DE IVA - FORMULARIO 300':^{ancho}}",
            f"{'Período: ' + meses_n[mes_ini] + '-' + meses_n[mes_fin] + ' ' + str(anio):^{ancho}}",
            "═" * ancho,
            "",
            "  INGRESOS / VENTAS:",
            f"  {'Base gravada 19%':<36}  {col_fmt(b19v):>16}",
            f"  {'IVA generado 19%':<36}  {col_fmt(iva19g):>16}",
            f"  {'Base gravada 5%':<36}  {col_fmt(b5v):>16}",
            f"  {'IVA generado 5%':<36}  {col_fmt(iva5g):>16}",
            "─" * ancho,
            f"  {'TOTAL IVA GENERADO':<36}  {col_fmt(iva_gen):>16}",
            "",
            "  COMPRAS / COSTOS (IVA DESCONTABLE):",
            f"  {'IVA descontable 19%':<36}  {col_fmt(iva19d):>16}",
            f"  {'IVA descontable 5%':<36}  {col_fmt(iva5d):>16}",
            "─" * ancho,
            f"  {'TOTAL IVA DESCONTABLE':<36}  {col_fmt(iva_desc):>16}",
            "",
            "═" * ancho,
        ]
        if saldo >= 0:
            lineas.append(f"  {'IMPUESTO A CARGO':<36}  {col_fmt(saldo):>16}")
        else:
            lineas.append(f"  {'SALDO A FAVOR':<36}  {col_fmt(abs(saldo)):>16}")
        lineas += [
            "═" * ancho,
            "",
            f"  Generado: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}",
        ]
        self._show_text(self.txt_imp, "\n".join(lineas))

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _show_text(self, widget, content):
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", content)
        widget.config(state="disabled")

    def _exportar_pdf(self, tipo):
        show_info("Para exportar a PDF, instale reportlab:\n  pip install reportlab\n\nLuego use Archivo → Exportar PDF.")

    def _exportar_excel(self, tipo):
        show_info("Para exportar a Excel, instale openpyxl:\n  pip install openpyxl\n\nLuego use Archivo → Exportar Excel.")
