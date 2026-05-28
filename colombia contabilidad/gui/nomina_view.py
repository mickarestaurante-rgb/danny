#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vista Nómina - CONTACOL PRO"""
import tkinter as tk
from tkinter import ttk
import datetime
from .styles import C_PRIMARY, C_WHITE, C_BG, FONT_TITLE, col_fmt
from .widgets import DataTable, ToolBar, show_info, show_error, ask_confirm
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import DB, get_parametros
from nomina_calc import calcular_nomina_empleado, get_params, SMLV_2026


TIPOS_CONTRATO = ["INDEFINIDO", "FIJO", "OBRA_LABOR", "APRENDIZAJE", "PRESTACION_SERVICIOS"]
NIVELES_RIESGO = [1, 2, 3, 4, 5]
TIPOS_COTIZANTE = [
    ("01", "Empleado"), ("12", "Trabajador Independiente"),
    ("19", "Cotizante sin categoría especial"), ("23", "Empleado - Extranjero sin residencia"),
]
FONDOS_PENSION = ["Porvenir", "Protección", "Colfondos", "Old Mutual (Skandia)",
                   "Colpensiones", "Horizonte"]
FONDOS_EPS = ["Sanitas", "Compensar", "Sura", "Nueva EPS", "Colsanitas",
               "Famisanar", "Coomeva", "Coosalud", "Medimás"]
CAJAS_COMP = ["Compensar", "Colsubsidio", "Comfama", "Comfenalco",
               "Cafam", "Comfandi", "Comfaboy"]
ARL_LIST = ["Positiva", "Sura", "AXA Colpatria", "Colmena", "Liberty",
             "Seguros Bolívar", "Mapfre"]
MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
          "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]


class NominaView(ttk.Frame):
    def __init__(self, parent, db: DB):
        super().__init__(parent)
        self.db = db
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=C_PRIMARY, height=40)
        hdr.pack(fill="x")
        tk.Label(hdr, text="  Nómina y Prestaciones Sociales",
                 bg=C_PRIMARY, fg="white", font=FONT_TITLE).place(x=0, y=5)

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=6, pady=6)

        self._tab_empleados(nb)
        self._tab_liquidacion(nb)
        self._tab_parametros(nb)

    # ── Pestaña Empleados ────────────────────────────────────────────────────
    def _tab_empleados(self, nb):
        f = ttk.Frame(nb)
        nb.add(f, text="  Empleados  ")

        tb = ToolBar(f)
        tb.pack(fill="x", padx=6, pady=4)
        tb.add_button("new", "➕ Nuevo Empleado", lambda: self._new_empleado(f))
        tb.add_button("edit", "✏️ Editar", lambda: self._edit_empleado(f))
        tb.add_separator()
        tb.add_button("retire", "🚪 Retirar", lambda: self._retirar_empleado(f))

        cols = [
            ("id", "ID", 45, "center"),
            ("nombre", "Nombre Completo", 220, "w"),
            ("cargo", "Cargo", 130, "w"),
            ("tipo_contrato", "Contrato", 100, "w"),
            ("fecha_ingreso", "F. Ingreso", 90, "center"),
            ("salario", "Salario", 110, "e"),
            ("eps", "EPS", 100, "w"),
            ("arl", "ARL", 80, "w"),
            ("activo", "Estado", 60, "center"),
        ]
        self.tabla_emp = DataTable(f, cols)
        self.tabla_emp.pack(fill="both", expand=True, padx=6, pady=4)
        self.tabla_emp.tree.bind("<Double-1>", lambda e: self._edit_empleado(f))
        self._load_empleados()

    def _load_empleados(self):
        rows = self.db.fetchall("""
            SELECT e.id, t.razon_social, e.cargo, e.tipo_contrato,
                   e.fecha_ingreso, e.salario_basico, e.eps, e.arl, e.activo
            FROM empleados e
            LEFT JOIN terceros t ON t.id=e.tercero_id
            ORDER BY t.razon_social""")
        self.tabla_emp.clear()
        for r in rows:
            self.tabla_emp.insert([
                r[0], r[1] or "Sin nombre", r[2] or "", r[3] or "",
                r[4] or "", col_fmt(r[5]), r[6] or "", r[7] or "",
                "Activo" if r[8] else "Retirado",
            ])

    def _new_empleado(self, parent):
        EmpleadoDialog(self, self.db, None, self._load_empleados)

    def _edit_empleado(self, parent):
        sel = self.tabla_emp.get_selected()
        if not sel:
            show_error("Seleccione un empleado.")
            return
        emp_id = sel[0]
        r = self.db.fetchone("SELECT * FROM empleados WHERE id=?", (emp_id,))
        if r:
            EmpleadoDialog(self, self.db, dict(r), self._load_empleados)

    def _retirar_empleado(self, parent):
        sel = self.tabla_emp.get_selected()
        if not sel:
            show_error("Seleccione un empleado.")
            return
        if not ask_confirm("Retirar Empleado",
                           "¿Confirma el retiro de este empleado?"):
            return
        today = str(datetime.date.today())
        self.db.execute(
            "UPDATE empleados SET activo=0, fecha_retiro=? WHERE id=?",
            (today, sel[0]))
        self.db.commit()
        self._load_empleados()

    # ── Pestaña Liquidación ──────────────────────────────────────────────────
    def _tab_liquidacion(self, nb):
        f = ttk.Frame(nb)
        nb.add(f, text="  Liquidar Nómina  ")

        # Período
        pf = ttk.LabelFrame(f, text="Período de Nómina", padding=8)
        pf.pack(fill="x", padx=8, pady=6)
        r = ttk.Frame(pf)
        r.pack(fill="x")
        ttk.Label(r, text="Año:").pack(side="left", padx=4)
        self.v_anio_nom = tk.StringVar(value="2026")
        ttk.Entry(r, textvariable=self.v_anio_nom, width=6).pack(side="left", padx=4)
        ttk.Label(r, text="Mes:").pack(side="left", padx=4)
        self.v_mes_nom = tk.StringVar(value="1")
        ttk.Combobox(r, textvariable=self.v_mes_nom,
                     values=[str(i) for i in range(1, 13)],
                     state="readonly", width=4).pack(side="left", padx=4)
        ttk.Button(r, text="📊 Liquidar Período",
                   command=self._liquidar_periodo).pack(side="left", padx=8)
        ttk.Button(r, text="✅ Confirmar Nómina",
                   command=self._confirmar_nomina,
                   style="Success.TButton").pack(side="left", padx=4)

        # Tabla resultados
        cols = [
            ("nombre", "Empleado", 200, "w"),
            ("dias", "Días", 45, "center"),
            ("devengado", "Devengado", 110, "e"),
            ("deducciones", "Deducciones", 100, "e"),
            ("neto", "Neto a Pagar", 110, "e"),
            ("aportes_emp", "Aportes Empresa", 120, "e"),
            ("costo_total", "Costo Total", 120, "e"),
        ]
        self.tabla_nom = DataTable(f, cols)
        self.tabla_nom.pack(fill="both", expand=True, padx=8, pady=4)
        self.tabla_nom.tree.bind("<Double-1>", lambda e: self._ver_detalle_empleado())

        # Totales
        self.lbl_nom_total = tk.Label(f, text="", bg=C_BG,
                                       font=("Segoe UI", 11, "bold"),
                                       foreground=C_PRIMARY)
        self.lbl_nom_total.pack(padx=8, pady=4, anchor="e")

    def _liquidar_periodo(self):
        try:
            anio = int(self.v_anio_nom.get())
            mes = int(self.v_mes_nom.get())
        except ValueError:
            show_error("Año y mes inválidos.")
            return

        empleados = self.db.fetchall(
            "SELECT e.*, t.razon_social FROM empleados e "
            "LEFT JOIN terceros t ON t.id=e.tercero_id "
            "WHERE e.activo=1 ORDER BY t.razon_social")

        if not empleados:
            show_error("No hay empleados activos.")
            return

        self.tabla_nom.clear()
        self._liq_data = []
        total_dev = total_ded = total_neto = total_aportes = 0

        for emp in empleados:
            salario = emp["salario_basico"]
            tiene_aux = salario <= (2 * SMLV_2026)
            result = calcular_nomina_empleado(
                salario_basico=salario,
                dias_trabajados=30,
                auxilio_transporte=tiene_aux,
                nivel_riesgo=emp["nivel_riesgo"] or 1,
                anio=anio,
            )
            self._liq_data.append({
                "emp_id": emp["id"],
                "nombre": emp["razon_social"] or "Sin nombre",
                **result
            })
            total_dev += result["total_devengado"]
            total_ded += result["total_deducciones"]
            total_neto += result["neto_pagar"]
            total_aportes += result["total_aportes_empresa"]

            self.tabla_nom.insert([
                emp["razon_social"] or "Sin nombre",
                30,
                col_fmt(result["total_devengado"]),
                col_fmt(result["total_deducciones"]),
                col_fmt(result["neto_pagar"]),
                col_fmt(result["total_aportes_empresa"]),
                col_fmt(result["costo_total_empresa"]),
            ])

        self.tabla_nom.insert(
            ["TOTALES", "", col_fmt(total_dev), col_fmt(total_ded),
             col_fmt(total_neto), col_fmt(total_aportes),
             col_fmt(total_dev + total_aportes)],
            tags=("total",))
        self.lbl_nom_total.config(
            text=f"Total nómina {MESES[mes-1]} {anio}: "
                 f"Devengado {col_fmt(total_dev)} | "
                 f"Neto {col_fmt(total_neto)} | "
                 f"Costo empresa {col_fmt(total_dev + total_aportes)}")

    def _confirmar_nomina(self):
        if not hasattr(self, "_liq_data") or not self._liq_data:
            show_error("Primero liquide la nómina del período.")
            return
        try:
            anio = int(self.v_anio_nom.get())
            mes = int(self.v_mes_nom.get())
        except ValueError:
            return
        if not ask_confirm("Confirmar Nómina",
                           f"¿Confirmar y guardar la nómina de {MESES[mes-1]} {anio}?"):
            return

        # Crear período
        self.db.execute("""INSERT OR REPLACE INTO nomina_periodos
                           (anio, mes, tipo, estado, fecha_pago,
                            total_devengado, total_deducciones,
                            total_neto, total_aportes_empresa)
                           VALUES (?,?,?,?,?,?,?,?,?)""",
                        (anio, mes, "MENSUAL", "CONFIRMADO",
                         str(datetime.date.today()),
                         sum(l["total_devengado"] for l in self._liq_data),
                         sum(l["total_deducciones"] for l in self._liq_data),
                         sum(l["neto_pagar"] for l in self._liq_data),
                         sum(l["total_aportes_empresa"] for l in self._liq_data)))
        periodo_id = self.db.conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        for l in self._liq_data:
            self.db.execute("""INSERT OR REPLACE INTO nomina_liquidacion
                (periodo_id, empleado_id, dias_trabajados,
                 salario_basico, auxilio_transporte,
                 total_devengado, salud_empleado, pension_empleado,
                 fondo_solidaridad, total_deducciones, neto_pagar,
                 salud_empresa, pension_empresa, arl_empresa,
                 caja_compensacion, sena, icbf, total_aportes_empresa,
                 prima_proporcional, cesantias_proporcional,
                 intereses_cesantias_prop, vacaciones_proporcional)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (periodo_id, l["emp_id"], l["dias_trabajados"],
                 l["salario_basico"], l["auxilio_transporte"],
                 l["total_devengado"], l["salud_empleado"], l["pension_empleado"],
                 l["fondo_solidaridad"], l["total_deducciones"], l["neto_pagar"],
                 l["salud_empresa"], l["pension_empresa"], l["arl_empresa"],
                 l["caja_compensacion"], l["sena"], l["icbf"], l["total_aportes_empresa"],
                 l["prima_proporcional"], l["cesantias_proporcional"],
                 l["intereses_cesantias_prop"], l["vacaciones_proporcional"]))
        self.db.commit()
        show_info(f"Nómina de {MESES[mes-1]} {anio} confirmada y guardada.")

    def _ver_detalle_empleado(self):
        sel = self.tabla_nom.get_selected()
        if not sel or not hasattr(self, "_liq_data"):
            return
        nombre = sel[0]
        liq = next((l for l in self._liq_data if l["nombre"] == nombre), None)
        if not liq:
            return
        DetalleNominaDialog(self, liq)

    # ── Pestaña Parámetros ───────────────────────────────────────────────────
    def _tab_parametros(self, nb):
        f = ttk.Frame(nb, style="White.TFrame", padding=14)
        nb.add(f, text="  Parámetros 2026  ")
        params = get_parametros_display()
        for i, (lbl, val) in enumerate(params):
            r = ttk.Frame(f, style="White.TFrame")
            r.pack(fill="x", pady=3)
            ttk.Label(r, text=lbl, style="White.TLabel",
                      width=36, anchor="e").pack(side="left", padx=6)
            ttk.Label(r, text=val, style="White.TLabel",
                      foreground=C_PRIMARY, font=("Segoe UI", 10, "bold")).pack(side="left")


def get_parametros_display():
    return [
        ("SMLV 2026:", f"$ {SMLV_2026:,}".replace(",", ".")),
        ("Auxilio de Transporte 2026:", "$ 202.000 (estimado)"),
        ("UVT 2026:", "$ 49.799"),
        ("Salud empleado:", "4%"),
        ("Pensión empleado:", "4%"),
        ("Salud empresa:", "8.5%"),
        ("Pensión empresa:", "12%"),
        ("ARL Nivel I:", "0.522%"),
        ("ARL Nivel II:", "1.044%"),
        ("ARL Nivel III:", "2.436%"),
        ("ARL Nivel IV:", "4.350%"),
        ("ARL Nivel V:", "6.960%"),
        ("Caja Compensación:", "4%"),
        ("SENA (si aplica):", "2%"),
        ("ICBF (si aplica):", "3%"),
        ("Prima de servicios:", "1 mes/año (8.33% mensual)"),
        ("Cesantías:", "1 mes/año (8.33% mensual)"),
        ("Intereses s/cesantías:", "12% anual"),
        ("Vacaciones:", "15 días hábiles/año"),
        ("Impuesto de Renta empresas:", "35%"),
        ("IVA general:", "19%"),
        ("IVA reducida:", "5%"),
        ("GMF:", "4x1000 (0.4%)"),
        ("ReteIVA:", "15% del IVA"),
    ]


class EmpleadoDialog(tk.Toplevel):
    def __init__(self, parent, db, data, on_save):
        super().__init__(parent)
        self.db = db
        self.data = data or {}
        self.on_save = on_save
        self.title("Nuevo Empleado" if not data else "Editar Empleado")
        self.geometry("680x580")
        self.grab_set()
        self._build()
        if data:
            self._load()

    def _build(self):
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=6, pady=6)
        self._tab_basico(nb)
        self._tab_contrato(nb)
        self._tab_aportes(nb)
        self._tab_banco(nb)
        bf = ttk.Frame(self)
        bf.pack(fill="x", padx=8, pady=6)
        ttk.Button(bf, text="💾 Guardar",
                   command=self._save, style="Success.TButton").pack(side="left", padx=4)
        ttk.Button(bf, text="✖ Cancelar",
                   command=self.destroy, style="Danger.TButton").pack(side="left", padx=4)

    def _tab_basico(self, nb):
        f = ttk.Frame(nb, style="White.TFrame", padding=14)
        nb.add(f, text="  Datos Básicos  ")
        self.vs = {}
        # Vincular a tercero
        terceros_pn = self.db.fetchall(
            "SELECT id, numero_id, razon_social FROM terceros "
            "WHERE tipo_persona='NATURAL' AND activo=1 ORDER BY razon_social")
        opts = [f"{t['numero_id']} - {t['razon_social']}" for t in terceros_pn]
        self._tercero_ids = {f"{t['numero_id']} - {t['razon_social']}": t['id']
                             for t in terceros_pn}
        v = tk.StringVar()
        self.vs["tercero_sel"] = v
        r = ttk.Frame(f, style="White.TFrame")
        r.pack(fill="x", pady=4)
        ttk.Label(r, text="Persona: *", style="White.TLabel",
                  width=24, anchor="e").pack(side="left", padx=4)
        ttk.Combobox(r, textvariable=v, values=opts, width=38).pack(side="left")
        for k, lbl, default, w in [
            ("cargo", "Cargo:", "", 28),
            ("departamento_empresa", "Departamento/Área:", "", 28),
            ("fecha_ingreso", "Fecha Ingreso (YYYY-MM-DD): *", "", 14),
            ("fecha_retiro", "Fecha Retiro:", "", 14),
            ("salario_basico", "Salario Básico: *", "", 16),
        ]:
            v2 = tk.StringVar(value=default)
            self.vs[k] = v2
            r = ttk.Frame(f, style="White.TFrame")
            r.pack(fill="x", pady=4)
            ttk.Label(r, text=lbl, style="White.TLabel",
                      width=24, anchor="e").pack(side="left", padx=4)
            ttk.Entry(r, textvariable=v2, width=w).pack(side="left")

        # Auxilio transporte
        v3 = tk.BooleanVar(value=True)
        self.vs["auxilio_transporte"] = v3
        r = ttk.Frame(f, style="White.TFrame")
        r.pack(fill="x", pady=3)
        ttk.Label(r, text="", style="White.TLabel", width=24).pack(side="left")
        ttk.Checkbutton(r, text="Aplica Auxilio de Transporte", variable=v3).pack(side="left")

    def _tab_contrato(self, nb):
        f = ttk.Frame(nb, style="White.TFrame", padding=14)
        nb.add(f, text="  Contrato  ")
        for k, lbl, opts in [
            ("tipo_contrato", "Tipo de Contrato:", TIPOS_CONTRATO),
            ("tipo_cotizante", "Tipo Cotizante PILA:", [c[0] for c in TIPOS_COTIZANTE]),
        ]:
            v = tk.StringVar(value=opts[0])
            self.vs[k] = v
            r = ttk.Frame(f, style="White.TFrame")
            r.pack(fill="x", pady=4)
            ttk.Label(r, text=lbl, style="White.TLabel",
                      width=26, anchor="e").pack(side="left", padx=4)
            ttk.Combobox(r, textvariable=v, values=opts,
                         state="readonly", width=24).pack(side="left")
        for k, lbl, w in [
            ("nivel_riesgo", "Nivel Riesgo ARL (1-5):", 5),
            ("porcentaje_arl", "% ARL:", 8),
        ]:
            v = tk.StringVar(value="1" if k == "nivel_riesgo" else "0.522")
            self.vs[k] = v
            r = ttk.Frame(f, style="White.TFrame")
            r.pack(fill="x", pady=4)
            ttk.Label(r, text=lbl, style="White.TLabel",
                      width=26, anchor="e").pack(side="left", padx=4)
            ttk.Entry(r, textvariable=v, width=w).pack(side="left")

    def _tab_aportes(self, nb):
        f = ttk.Frame(nb, style="White.TFrame", padding=14)
        nb.add(f, text="  Aportes  ")
        for k, lbl, opts in [
            ("eps", "EPS:", FONDOS_EPS),
            ("fondo_pension", "Fondo de Pensión:", FONDOS_PENSION),
            ("fondo_cesantias", "Fondo de Cesantías:", FONDOS_PENSION + ["Fondo Nacional del Ahorro"]),
            ("arl", "ARL:", ARL_LIST),
            ("caja_compensacion", "Caja de Compensación:", CAJAS_COMP),
        ]:
            v = tk.StringVar()
            self.vs[k] = v
            r = ttk.Frame(f, style="White.TFrame")
            r.pack(fill="x", pady=4)
            ttk.Label(r, text=lbl, style="White.TLabel",
                      width=26, anchor="e").pack(side="left", padx=4)
            ttk.Combobox(r, textvariable=v, values=opts, width=24).pack(side="left")

    def _tab_banco(self, nb):
        f = ttk.Frame(nb, style="White.TFrame", padding=14)
        nb.add(f, text="  Datos Bancarios  ")
        for k, lbl, opts in [
            ("banco_nombre", "Banco:", ["Bancolombia", "Davivienda", "Banco de Bogotá",
                                         "BBVA", "Colpatria", "Popular", "Agrario", "Caja Social"]),
            ("tipo_cuenta_banco", "Tipo Cuenta:", ["AHORROS", "CORRIENTE"]),
        ]:
            v = tk.StringVar()
            self.vs[k] = v
            r = ttk.Frame(f, style="White.TFrame")
            r.pack(fill="x", pady=4)
            ttk.Label(r, text=lbl, style="White.TLabel",
                      width=22, anchor="e").pack(side="left", padx=4)
            ttk.Combobox(r, textvariable=v, values=opts, width=22).pack(side="left")
        v = tk.StringVar()
        self.vs["cuenta_banco"] = v
        r = ttk.Frame(f, style="White.TFrame")
        r.pack(fill="x", pady=4)
        ttk.Label(r, text="Número de Cuenta:", style="White.TLabel",
                  width=22, anchor="e").pack(side="left", padx=4)
        ttk.Entry(r, textvariable=v, width=22).pack(side="left")

    def _load(self):
        for k, v in self.vs.items():
            if k == "tercero_sel":
                t = self.db.fetchone("SELECT numero_id, razon_social FROM terceros WHERE id=?",
                                     (self.data.get("tercero_id"),))
                if t:
                    v.set(f"{t['numero_id']} - {t['razon_social']}")
            elif isinstance(v, tk.BooleanVar):
                v.set(bool(self.data.get(k, False)))
            else:
                val = self.data.get(k)
                v.set(str(val) if val is not None else "")

    def _save(self):
        t_sel = self.vs["tercero_sel"].get()
        if not t_sel:
            show_error("Seleccione la persona.")
            return
        tercero_id = self._tercero_ids.get(t_sel)
        fecha_ing = self.vs["fecha_ingreso"].get().strip()
        sal_str = self.vs["salario_basico"].get().strip()
        if not fecha_ing or not sal_str:
            show_error("Fecha de ingreso y salario son obligatorios.")
            return
        try:
            sal = float(sal_str.replace(".", "").replace(",", "."))
        except ValueError:
            show_error("Salario inválido.")
            return
        data = {"tercero_id": tercero_id}
        for k, v in self.vs.items():
            if k == "tercero_sel":
                continue
            if isinstance(v, tk.BooleanVar):
                data[k] = 1 if v.get() else 0
            else:
                val = v.get().strip()
                data[k] = val if val else None
        data["salario_basico"] = sal
        try:
            data["nivel_riesgo"] = int(data.get("nivel_riesgo") or 1)
            data["porcentaje_arl"] = float(data.get("porcentaje_arl") or 0.522)
        except ValueError:
            pass

        if self.data.get("id"):
            cols = ", ".join(f"{k}=?" for k in data)
            self.db.execute(f"UPDATE empleados SET {cols} WHERE id=?",
                            list(data.values()) + [self.data["id"]])
        else:
            cols = ", ".join(data.keys())
            ph = ", ".join("?" * len(data))
            self.db.execute(f"INSERT INTO empleados ({cols}) VALUES ({ph})",
                            list(data.values()))
        self.db.commit()
        show_info("Empleado guardado correctamente.")
        self.on_save()
        self.destroy()


class DetalleNominaDialog(tk.Toplevel):
    def __init__(self, parent, liq):
        super().__init__(parent)
        self.title(f"Detalle Nómina - {liq['nombre']}")
        self.resizable(False, False)
        self.grab_set()
        f = ttk.Frame(self, padding=16, style="White.TFrame")
        f.pack(fill="both", expand=True)
        rows = [
            ("DEVENGADO", ""),
            ("Salario Básico", liq["salario_proporcional"]),
            ("Auxilio de Transporte", liq["auxilio_transporte"]),
            ("Horas Extras Diurnas", liq["horas_extras_diurnas_val"]),
            ("Horas Extras Nocturnas", liq["horas_extras_nocturnas_val"]),
            ("Horas Extras Dominicales", liq["horas_extras_dominicales_val"]),
            ("Comisiones", liq["comisiones"]),
            ("Bonificaciones", liq["bonificaciones"]),
            ("TOTAL DEVENGADO", liq["total_devengado"]),
            ("", ""),
            ("DEDUCCIONES", ""),
            ("Salud (4%)", liq["salud_empleado"]),
            ("Pensión (4%)", liq["pension_empleado"]),
            ("Fondo de Solidaridad", liq["fondo_solidaridad"]),
            ("TOTAL DEDUCCIONES", liq["total_deducciones"]),
            ("", ""),
            ("NETO A PAGAR", liq["neto_pagar"]),
            ("", ""),
            ("APORTES EMPRESA", ""),
            ("Salud (8.5%)", liq["salud_empresa"]),
            ("Pensión (12%)", liq["pension_empresa"]),
            ("ARL", liq["arl_empresa"]),
            ("Caja Compensación (4%)", liq["caja_compensacion"]),
            ("SENA (2%)", liq["sena"]),
            ("ICBF (3%)", liq["icbf"]),
            ("TOTAL APORTES EMPRESA", liq["total_aportes_empresa"]),
            ("", ""),
            ("PROVISIONES PRESTACIONES", ""),
            ("Prima de Servicios", liq["prima_proporcional"]),
            ("Cesantías", liq["cesantias_proporcional"]),
            ("Intereses Cesantías", liq["intereses_cesantias_prop"]),
            ("Vacaciones", liq["vacaciones_proporcional"]),
            ("COSTO TOTAL EMPRESA", liq["costo_total_empresa"]),
        ]
        bold_keys = {"DEVENGADO", "TOTAL DEVENGADO", "DEDUCCIONES", "TOTAL DEDUCCIONES",
                     "NETO A PAGAR", "APORTES EMPRESA", "TOTAL APORTES EMPRESA",
                     "PROVISIONES PRESTACIONES", "COSTO TOTAL EMPRESA"}
        for i, (lbl, val) in enumerate(rows):
            is_header = lbl in bold_keys or (lbl and not val and lbl != "")
            fg = C_PRIMARY if lbl in bold_keys else "#2c3e50"
            font = ("Segoe UI", 10, "bold") if lbl in bold_keys else ("Segoe UI", 10)
            ttk.Label(f, text=lbl, style="White.TLabel", width=28, anchor="w",
                      font=font, foreground=fg).grid(
                          row=i, column=0, sticky="w", padx=6, pady=1)
            if val != "":
                ttk.Label(f, text=col_fmt(val) if isinstance(val, (int, float)) else val,
                          style="White.TLabel", width=16, anchor="e",
                          font=font, foreground=fg).grid(
                              row=i, column=1, sticky="e", padx=6, pady=1)
        ttk.Button(f, text="Cerrar", command=self.destroy).grid(
            row=len(rows)+1, column=0, columnspan=2, pady=10)
