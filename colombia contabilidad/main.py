#!/usr/bin/env python3.12
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║          CONTACOL PRO - Sistema Contable Colombiano          ║
║                        Versión 1.0.0                         ║
║  Desarrollado según: NIIF, PUC Colombia, Normativa DIAN 2026 ║
║  Para Personas Naturales y Jurídicas                         ║
╚══════════════════════════════════════════════════════════════╝
"""
import tkinter as tk
from tkinter import ttk, messagebox
import hashlib, os, sys, datetime

# ─── Asegurar que el directorio raíz esté en sys.path ────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from database import DB, init_db, get_config, get_empresa, DB_PATH
from puc_data import load_puc
from gui.styles import apply_theme, C_PRIMARY, C_SECONDARY, C_WHITE, C_BG, C_ACCENT
from gui.styles import FONT_TITLE, FONT_HEADER, FONT_NORMAL, FONT_SMALL


# ─── Pantalla de Carga ────────────────────────────────────────────────────────
class SplashScreen(tk.Toplevel):
    def __init__(self, root):
        super().__init__(root)
        self.overrideredirect(True)
        w, h = 520, 300
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.configure(bg=C_PRIMARY)

        tk.Frame(self, bg=C_ACCENT, height=5).pack(fill="x")

        tk.Label(self, text="CONTACOL PRO",
                 bg=C_PRIMARY, fg="white",
                 font=("Segoe UI", 32, "bold")).pack(pady=(30, 4))
        tk.Label(self, text="Sistema Contable Colombiano",
                 bg=C_PRIMARY, fg="#aed6f1",
                 font=("Segoe UI", 14)).pack()
        tk.Label(self, text="Versión 1.0 - 2026",
                 bg=C_PRIMARY, fg="#aed6f1",
                 font=("Segoe UI", 10)).pack(pady=4)
        tk.Label(self, text="NIIF  ·  PUC  ·  DIAN  ·  Nómina  ·  IVA  ·  Retención",
                 bg=C_PRIMARY, fg="#85c1e9",
                 font=("Segoe UI", 9)).pack(pady=8)

        self.prog_frame = tk.Frame(self, bg=C_PRIMARY)
        self.prog_frame.pack(pady=20)
        self.progress = ttk.Progressbar(self.prog_frame, length=360,
                                         mode="determinate", maximum=100)
        self.progress.pack()
        self.lbl_status = tk.Label(self.prog_frame, text="Iniciando...",
                                    bg=C_PRIMARY, fg="#aed6f1", font=FONT_SMALL)
        self.lbl_status.pack(pady=6)

        tk.Label(self, text="Para Personas Naturales y Jurídicas",
                 bg=C_PRIMARY, fg="#5d6d7e", font=("Segoe UI", 8)).pack(side="bottom", pady=8)
        tk.Frame(self, bg=C_ACCENT, height=3).pack(side="bottom", fill="x")

    def update_progress(self, pct, msg):
        self.progress["value"] = pct
        self.lbl_status.config(text=msg)
        self.update()


# ─── Login ────────────────────────────────────────────────────────────────────
class LoginWindow(tk.Toplevel):
    def __init__(self, root, db: DB, on_success):
        super().__init__(root)
        self.db = db
        self.on_success = on_success
        self.title("CONTACOL PRO - Iniciar Sesión")
        self.resizable(False, False)
        w, h = 400, 340
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.configure(bg=C_PRIMARY)
        self.protocol("WM_DELETE_WINDOW", root.destroy)
        self.grab_set()
        self._build()

    def _build(self):
        tk.Frame(self, bg=C_ACCENT, height=4).pack(fill="x")
        tk.Label(self, text="CONTACOL PRO",
                 bg=C_PRIMARY, fg="white",
                 font=("Segoe UI", 22, "bold")).pack(pady=(22, 4))
        tk.Label(self, text="Sistema Contable Colombiano",
                 bg=C_PRIMARY, fg="#aed6f1",
                 font=("Segoe UI", 10)).pack()

        f = tk.Frame(self, bg=C_WHITE, padx=28, pady=22)
        f.pack(fill="both", expand=True, padx=22, pady=16)

        tk.Label(f, text="Usuario:", bg=C_WHITE,
                 font=FONT_NORMAL, anchor="w").pack(fill="x", pady=(0, 2))
        self.e_user = ttk.Entry(f, font=FONT_NORMAL, width=28)
        self.e_user.pack(fill="x", pady=(0, 10))
        self.e_user.insert(0, "admin")

        tk.Label(f, text="Contraseña:", bg=C_WHITE,
                 font=FONT_NORMAL, anchor="w").pack(fill="x", pady=(0, 2))
        self.e_pass = ttk.Entry(f, show="•", font=FONT_NORMAL, width=28)
        self.e_pass.pack(fill="x", pady=(0, 14))
        self.e_pass.bind("<Return>", lambda e: self._login())

        ttk.Button(f, text="  Iniciar Sesión →",
                   command=self._login, style="TButton").pack(fill="x", pady=4)

        self.lbl_err = tk.Label(f, text="", bg=C_WHITE, fg="red",
                                 font=FONT_SMALL)
        self.lbl_err.pack()
        self.e_pass.focus()

    def _login(self):
        user = self.e_user.get().strip()
        pwd = hashlib.sha256(self.e_pass.get().encode()).hexdigest()
        row = self.db.fetchone(
            "SELECT * FROM usuarios WHERE username=? AND password_hash=? AND activo=1",
            (user, pwd))
        if row:
            self.db.execute(
                "UPDATE usuarios SET ultimo_acceso=? WHERE id=?",
                (str(datetime.datetime.now()), row["id"]))
            self.db.commit()
            self.destroy()
            self.on_success(dict(row))
        else:
            self.lbl_err.config(text="Usuario o contraseña incorrectos.")
            self.e_pass.delete(0, "end")
            self.e_pass.focus()


# ─── Aplicación Principal ─────────────────────────────────────────────────────
class ContaColApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        apply_theme(self.root)
        self.db = None
        self.usuario = None
        self._init()

    def _init(self):
        splash = SplashScreen(self.root)
        self.root.update()

        try:
            splash.update_progress(10, "Inicializando base de datos...")
            self.root.update()
            init_db()

            splash.update_progress(35, "Cargando Plan Único de Cuentas (PUC)...")
            self.root.update()
            self.db = DB()
            # Solo cargar PUC si está vacío
            count = self.db.fetchone("SELECT COUNT(*) as n FROM plan_cuentas")
            if not count or count["n"] == 0:
                load_puc(self.db)

            splash.update_progress(65, "Verificando configuración fiscal...")
            self.root.update()

            splash.update_progress(85, "Cargando interfaz...")
            self.root.update()
            splash.after(600, lambda: self._on_splash_done(splash))

        except Exception as e:
            splash.destroy()
            messagebox.showerror("Error de Inicialización",
                                  f"No se pudo iniciar CONTACOL PRO:\n\n{e}")
            self.root.destroy()

    def _on_splash_done(self, splash):
        splash.update_progress(100, "Listo.")
        self.root.update()
        splash.after(400, lambda: self._show_login(splash))

    def _show_login(self, splash):
        splash.destroy()
        self.root.deiconify()
        self.root.withdraw()
        LoginWindow(self.root, self.db, self._on_login_success)

    def _on_login_success(self, usuario):
        self.usuario = usuario
        self.root.deiconify()
        self._build_main()

    def _build_main(self):
        empresa = get_empresa(self.db)
        nombre_emp = empresa["razon_social"] if empresa else "Sin Empresa Configurada"
        nit = f" | NIT: {empresa['nit']}" if empresa else ""

        self.root.title(f"CONTACOL PRO - {nombre_emp}{nit}")
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f"{min(1400, sw-20)}x{min(820, sh-60)}+10+30")
        self.root.minsize(900, 600)
        self.root.configure(bg=C_BG)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # ── Layout principal
        main = tk.Frame(self.root, bg=C_BG)
        main.pack(fill="both", expand=True)

        # Sidebar izquierdo
        self._build_sidebar(main)

        # Área de contenido
        self.content_frame = tk.Frame(main, bg=C_BG)
        self.content_frame.pack(side="left", fill="both", expand=True)

        # Status bar
        self._build_statusbar()

        # Dashboard inicial
        self._show_dashboard()

    def _build_sidebar(self, parent):
        sb = tk.Frame(parent, bg=C_PRIMARY, width=210)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)

        # Logo/nombre empresa
        tk.Label(sb, text="CONTACOL PRO",
                 bg=C_PRIMARY, fg="white",
                 font=("Segoe UI", 13, "bold")).pack(pady=(16, 2))
        tk.Label(sb, text="Sistema Contable",
                 bg=C_PRIMARY, fg="#85c1e9",
                 font=("Segoe UI", 8)).pack()
        tk.Frame(sb, bg=C_ACCENT, height=2).pack(fill="x", pady=10)

        empresa = get_empresa(self.db)
        emp_nombre = (empresa["razon_social"][:22] if empresa else "Sin Empresa")
        tk.Label(sb, text=emp_nombre, bg=C_PRIMARY, fg="#aed6f1",
                 font=("Segoe UI", 8), wraplength=190).pack(pady=(0, 8))
        tk.Frame(sb, bg="#2e4a6e", height=1).pack(fill="x")

        # Menú de navegación
        menu_items = [
            ("🏠  Dashboard",          self._show_dashboard),
            ("🏢  Empresa",             self._show_empresa),
            ("📋  Plan de Cuentas",     self._show_puc),
            ("📝  Comprobantes",         self._show_comprobantes),
            ("👥  Terceros",            self._show_terceros),
            ("🧾  Facturas de Venta",   self._show_fv),
            ("📦  Facturas de Compra",  self._show_fc),
            ("🏦  Tesorería",           self._show_tesoreria),
            ("👨‍💼  Nómina",             self._show_nomina),
            ("📊  Activos Fijos",       self._show_activos),
            ("💰  Impuestos",           self._show_impuestos),
            ("📈  Informes",            self._show_informes),
            ("⚙️  Configuración",       self._show_config),
        ]

        self._active_btn = None
        self._menu_btns = {}
        for lbl, cmd in menu_items:
            btn = tk.Button(sb, text=lbl, bg=C_PRIMARY, fg="white",
                             font=("Segoe UI", 10), anchor="w",
                             padx=16, pady=7, bd=0, cursor="hand2",
                             activebackground=C_SECONDARY, activeforeground="white",
                             command=lambda c=cmd, b=lbl: self._nav(c, b))
            btn.pack(fill="x")
            self._menu_btns[lbl] = btn

        tk.Frame(sb, bg="#2e4a6e", height=1).pack(fill="x", pady=8)
        u = self.usuario or {}
        tk.Label(sb, text=f"👤 {u.get('nombre', 'Usuario')}",
                 bg=C_PRIMARY, fg="#85c1e9",
                 font=("Segoe UI", 9)).pack(pady=2)
        tk.Label(sb, text=f"Rol: {u.get('rol', '')}",
                 bg=C_PRIMARY, fg="#5d6d7e",
                 font=("Segoe UI", 8)).pack()
        tk.Button(sb, text="🚪 Cerrar Sesión",
                  bg=C_PRIMARY, fg="#e74c3c",
                  font=("Segoe UI", 9), bd=0, cursor="hand2",
                  command=self._logout).pack(pady=8)

    def _nav(self, cmd, key):
        if self._active_btn:
            self._active_btn.config(bg=C_PRIMARY)
        btn = self._menu_btns.get(key)
        if btn:
            btn.config(bg=C_SECONDARY)
            self._active_btn = btn
        cmd()

    def _build_statusbar(self):
        sb = tk.Frame(self.root, bg=C_PRIMARY, height=24)
        sb.pack(fill="x", side="bottom")
        self.lbl_status = tk.Label(sb, text="  Listo", bg=C_PRIMARY, fg="white",
                                    font=FONT_SMALL, anchor="w")
        self.lbl_status.pack(side="left", fill="x", expand=True)
        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        tk.Label(sb, text=f"CONTACOL PRO v1.0  |  {now}  ",
                 bg=C_PRIMARY, fg="#aed6f1", font=FONT_SMALL).pack(side="right")

    def _clear_content(self):
        for w in self.content_frame.winfo_children():
            w.destroy()

    # ─── Vistas ───────────────────────────────────────────────────────────────
    def _show_dashboard(self):
        self._clear_content()
        f = tk.Frame(self.content_frame, bg=C_BG)
        f.pack(fill="both", expand=True, padx=16, pady=12)

        empresa = get_empresa(self.db)
        nombre_emp = empresa["razon_social"] if empresa else "Sin Empresa Configurada"
        nit = f"NIT: {empresa['nit']}" if empresa else ""
        tipo = empresa["tipo_persona"] if empresa else ""

        # Encabezado
        hf = tk.Frame(f, bg=C_WHITE, padx=16, pady=12)
        hf.pack(fill="x", pady=(0, 12))
        tk.Label(hf, text=f"  Bienvenido a CONTACOL PRO",
                 bg=C_WHITE, fg=C_PRIMARY,
                 font=("Segoe UI", 16, "bold")).pack(anchor="w")
        tk.Label(hf, text=f"  {nombre_emp}  |  {nit}  |  Persona {tipo.capitalize() if tipo else ''}",
                 bg=C_WHITE, fg="#5d6d7e",
                 font=("Segoe UI", 10)).pack(anchor="w")
        tk.Label(hf, text=f"  {datetime.datetime.now().strftime('%A, %d de %B de %Y')}  |  Año fiscal: 2026",
                 bg=C_WHITE, fg="#5d6d7e",
                 font=("Segoe UI", 9)).pack(anchor="w")

        # Indicadores
        cards_frame = tk.Frame(f, bg=C_BG)
        cards_frame.pack(fill="x", pady=8)

        cards = self._get_dashboard_metrics()
        colors = [C_SECONDARY, "#27ae60", "#e74c3c", "#8e44ad",
                   "#16a085", "#d35400", "#2c3e50", "#c0392b"]
        for i, (titulo, valor, sub) in enumerate(cards):
            c = tk.Frame(cards_frame, bg=colors[i % len(colors)],
                          padx=14, pady=10, relief="flat")
            c.grid(row=i // 4, column=i % 4, padx=6, pady=6, sticky="ew")
            tk.Label(c, text=titulo, bg=colors[i % len(colors)], fg="white",
                     font=("Segoe UI", 9)).pack(anchor="w")
            tk.Label(c, text=valor, bg=colors[i % len(colors)], fg="white",
                     font=("Segoe UI", 15, "bold")).pack(anchor="w")
            tk.Label(c, text=sub, bg=colors[i % len(colors)], fg="#d6eaf8",
                     font=("Segoe UI", 8)).pack(anchor="w")
        for col in range(4):
            cards_frame.columnconfigure(col, weight=1)

        # Accesos rápidos
        qf = tk.LabelFrame(f, text="  Accesos Rápidos", bg=C_WHITE,
                            fg=C_PRIMARY, font=FONT_HEADER, padx=12, pady=10)
        qf.pack(fill="x", pady=8)
        accesos = [
            ("🧾 Nueva Factura de Venta", self._show_fv),
            ("📦 Nueva Factura de Compra", self._show_fc),
            ("📝 Nuevo Comprobante", self._show_comprobantes),
            ("👥 Gestionar Terceros", self._show_terceros),
            ("📊 Balance General", self._show_informes),
            ("👨‍💼 Liquidar Nómina", self._show_nomina),
        ]
        for i, (lbl, cmd) in enumerate(accesos):
            btn = tk.Button(qf, text=lbl, bg=C_SECONDARY, fg="white",
                             font=("Segoe UI", 10), padx=12, pady=8, bd=0,
                             cursor="hand2", command=cmd,
                             activebackground=C_PRIMARY)
            btn.grid(row=i // 3, column=i % 3, padx=6, pady=4, sticky="ew")
        for col in range(3):
            qf.columnconfigure(col, weight=1)

        # Alertas / Novedades
        af = tk.LabelFrame(f, text="  ℹ Información Fiscal 2026",
                            bg=C_WHITE, fg=C_PRIMARY,
                            font=FONT_HEADER, padx=12, pady=10)
        af.pack(fill="x", pady=8)
        alertas = [
            "✅ SMLV 2026: $1.600.000 (estimado) | Auxilio transporte: $202.000",
            "✅ IVA General: 19% | IVA Reducida: 5% | GMF: 4x1000 (0.4%)",
            "✅ Impuesto de Renta Empresas: 35% | UVT 2026: $49.799",
            "✅ Facturación Electrónica: Obligatoria para responsables de IVA",
            "✅ Retención en la Fuente: Aplica desde base mínima en UVT",
            "✅ Nómina Electrónica DIAN: Obligatoria para empleadores con nómina",
        ]
        for a in alertas:
            tk.Label(af, text=a, bg=C_WHITE, fg="#2c3e50",
                     font=("Segoe UI", 9), anchor="w").pack(fill="x", pady=1)

    def _get_dashboard_metrics(self):
        today = str(datetime.date.today())
        year = datetime.date.today().year

        # Facturas de venta del mes
        fv = self.db.fetchone(
            "SELECT COUNT(*) as n, SUM(total) as t FROM facturas_venta "
            "WHERE strftime('%Y', fecha)=? AND estado='ACTIVO'",
            (str(year),)) or {}
        # Facturas de compra
        fc = self.db.fetchone(
            "SELECT COUNT(*) as n, SUM(total) as t FROM facturas_compra "
            "WHERE strftime('%Y', fecha)=? AND estado='ACTIVO'",
            (str(year),)) or {}
        # Empleados activos
        emp = self.db.fetchone("SELECT COUNT(*) as n FROM empleados WHERE activo=1") or {}
        # Terceros
        ter = self.db.fetchone("SELECT COUNT(*) as n FROM terceros WHERE activo=1") or {}
        # Cartera pendiente
        cxc = self.db.fetchone(
            "SELECT SUM(saldo) as t FROM facturas_venta WHERE estado='ACTIVO' AND saldo>0") or {}
        cxp = self.db.fetchone(
            "SELECT SUM(saldo) as t FROM facturas_compra WHERE estado='ACTIVO' AND saldo>0") or {}
        # Cuentas del PUC
        puc = self.db.fetchone("SELECT COUNT(*) as n FROM plan_cuentas WHERE activa=1") or {}

        def fmt(v):
            if v is None:
                return "$ 0"
            v = float(v)
            if v >= 1_000_000_000:
                return f"$ {v/1e9:.1f}B"
            if v >= 1_000_000:
                return f"$ {v/1e6:.1f}M"
            return f"$ {v:,.0f}".replace(",", ".")

        return [
            ("Ventas del Año", fmt(fv.get("t") or 0), f"{fv.get('n') or 0} facturas"),
            ("Compras del Año", fmt(fc.get("t") or 0), f"{fc.get('n') or 0} facturas"),
            ("CxC Pendiente", fmt(cxc.get("t") or 0), "Por cobrar"),
            ("CxP Pendiente", fmt(cxp.get("t") or 0), "Por pagar"),
            ("Empleados Activos", str(emp.get("n") or 0), "En nómina"),
            ("Terceros Registrados", str(ter.get("n") or 0), "Clientes/Prov/Emp"),
            ("Cuentas PUC", str(puc.get("n") or 0), "Plan de Cuentas"),
            ("Año Fiscal", "2026", "Activo"),
        ]

    def _show_empresa(self):
        self._clear_content()
        from gui.empresa_view import EmpresaView
        EmpresaView(self.content_frame, self.db,
                    on_saved=self._show_dashboard).pack(fill="both", expand=True)

    def _show_puc(self):
        self._clear_content()
        from gui.puc_view import PUCView
        PUCView(self.content_frame, self.db).pack(fill="both", expand=True)

    def _show_comprobantes(self):
        self._clear_content()
        from gui.contabilidad_view import ContabilidadView
        ContabilidadView(self.content_frame, self.db).pack(fill="both", expand=True)

    def _show_terceros(self):
        self._clear_content()
        from gui.terceros_view import TercerosView
        TercerosView(self.content_frame, self.db, "TODOS").pack(fill="both", expand=True)

    def _show_fv(self):
        self._clear_content()
        from gui.facturacion_view import FacturacionView
        FacturacionView(self.content_frame, self.db, "VENTA").pack(fill="both", expand=True)

    def _show_fc(self):
        self._clear_content()
        from gui.facturacion_view import FacturacionView
        FacturacionView(self.content_frame, self.db, "COMPRA").pack(fill="both", expand=True)

    def _show_tesoreria(self):
        self._clear_content()
        self._placeholder("Tesorería (Caja y Bancos)", [
            "• Registro de entradas y salidas de caja",
            "• Consignaciones y retiros bancarios",
            "• Conciliación bancaria mensual",
            "• GMF 4x1000 automático",
            "• Extractos bancarios",
            "• Saldo actual por cuenta",
        ])

    def _show_nomina(self):
        self._clear_content()
        from gui.nomina_view import NominaView
        NominaView(self.content_frame, self.db).pack(fill="both", expand=True)

    def _show_activos(self):
        self._clear_content()
        self._placeholder("Activos Fijos", [
            "• Registro de activos fijos (edificios, maquinaria, equipos, vehículos)",
            "• Depreciación automática: Línea recta, Saldo decreciente",
            "• Vidas útiles según NIIF y norma fiscal",
            "• Libro de activos fijos",
            "• Comprobante automático de depreciación mensual",
            "• Retiro o baja de activos",
        ])

    def _show_impuestos(self):
        self._clear_content()
        self._placeholder("Gestión de Impuestos DIAN", [
            "• Declaración de IVA (Formulario 300 y 310)",
            "• Retención en la Fuente (Formulario 350)",
            "• ReteIVA (15% del IVA)",
            "• Retención ICA según municipio",
            "• Declaración de Renta (Formulario 110 y 210)",
            "• Información Exógena (1001, 1002, 1004, 1007, 1008)",
            "• Nómina Electrónica DIAN",
            "• GMF - Gravamen Movimientos Financieros 4x1000",
            "• Anticipo de renta",
        ])

    def _show_informes(self):
        self._clear_content()
        from gui.informes_view import InformesView
        InformesView(self.content_frame, self.db).pack(fill="both", expand=True)

    def _show_config(self):
        self._clear_content()
        self._config_view()

    def _config_view(self):
        f = tk.Frame(self.content_frame, bg=C_BG)
        f.pack(fill="both", expand=True, padx=16, pady=12)

        tk.Frame(f, bg=C_PRIMARY, height=40).pack(fill="x")
        tk.Label(f, text="  Configuración del Sistema",
                 bg=C_PRIMARY, fg="white", font=FONT_TITLE).place(x=0, y=0)

        nb = ttk.Notebook(f)
        nb.pack(fill="both", expand=True, pady=(48, 0))

        # Tab usuarios
        fu = ttk.Frame(nb, style="White.TFrame", padding=14)
        nb.add(fu, text="  Usuarios  ")
        tk.Label(fu, text="Gestión de Usuarios", bg=C_WHITE,
                 font=FONT_HEADER, fg=C_PRIMARY).pack(anchor="w")
        ttk.Button(fu, text="➕ Nuevo Usuario",
                   command=self._new_user).pack(anchor="w", pady=8)

        cols_u = [("username", "Usuario", 120, "w"),
                  ("nombre", "Nombre", 200, "w"),
                  ("rol", "Rol", 100, "w"),
                  ("activo", "Activo", 60, "center")]
        from gui.widgets import DataTable
        tabla_u = DataTable(fu, cols_u)
        tabla_u.pack(fill="both", expand=True, pady=8)
        for row in self.db.fetchall("SELECT * FROM usuarios ORDER BY nombre"):
            tabla_u.insert([row["username"], row["nombre"], row["rol"],
                            "✓" if row["activo"] else "✗"])

        # Tab parámetros fiscales
        fp = ttk.Frame(nb, style="White.TFrame", padding=14)
        nb.add(fp, text="  Parámetros Fiscales  ")
        from gui.nomina_view import get_parametros_display
        params = get_parametros_display()
        for lbl, val in params:
            r = ttk.Frame(fp, style="White.TFrame")
            r.pack(fill="x", pady=2)
            ttk.Label(r, text=lbl, style="White.TLabel",
                      width=36, anchor="e").pack(side="left", padx=4)
            ttk.Label(r, text=val, style="White.TLabel",
                      foreground=C_PRIMARY,
                      font=("Segoe UI", 10, "bold")).pack(side="left")

        # Tab acerca de
        fa = ttk.Frame(nb, style="White.TFrame", padding=24)
        nb.add(fa, text="  Acerca de  ")
        info = [
            ("CONTACOL PRO", "Sistema Contable Colombiano"),
            ("Versión:", "1.0.0 - 2026"),
            ("Normativa:", "NIIF (Decreto 2420/2015)"),
            ("PUC:", "Decreto 2650/1993 y actualizaciones"),
            ("DIAN:", "Facturación electrónica, retenciones, IVA"),
            ("Nómina:", "CST, Ley 1607/2012, Ley 2277/2022"),
            ("Impuesto Renta:", "35% personas jurídicas"),
            ("IVA:", "19% general, 5% reducida"),
            ("SMLV 2026:", "$1.600.000 (estimado)"),
            ("UVT 2026:", "$49.799"),
            ("Soporte:", "Para personas Naturales y Jurídicas"),
        ]
        for lbl, val in info:
            r = ttk.Frame(fa, style="White.TFrame")
            r.pack(fill="x", pady=3)
            ttk.Label(r, text=lbl, style="White.TLabel",
                      width=24, anchor="e",
                      font=("Segoe UI", 10, "bold"),
                      foreground=C_PRIMARY).pack(side="left", padx=6)
            ttk.Label(r, text=val, style="White.TLabel").pack(side="left")

    def _new_user(self):
        d = tk.Toplevel(self.root)
        d.title("Nuevo Usuario")
        d.resizable(False, False)
        d.grab_set()
        f = ttk.Frame(d, padding=16, style="White.TFrame")
        f.pack()
        vs = {}
        for k, lbl, show in [("username", "Usuario:", False),
                               ("nombre", "Nombre:", False),
                               ("password", "Contraseña:", True)]:
            v = tk.StringVar()
            vs[k] = v
            r = ttk.Frame(f, style="White.TFrame")
            r.pack(fill="x", pady=4)
            ttk.Label(r, text=lbl, style="White.TLabel", width=16, anchor="e").pack(side="left", padx=4)
            ttk.Entry(r, textvariable=v, width=22,
                      show="•" if show else "").pack(side="left")
        v_rol = tk.StringVar(value="CONTADOR")
        vs["rol"] = v_rol
        r = ttk.Frame(f, style="White.TFrame")
        r.pack(fill="x", pady=4)
        ttk.Label(r, text="Rol:", style="White.TLabel", width=16, anchor="e").pack(side="left", padx=4)
        ttk.Combobox(r, textvariable=v_rol,
                     values=["ADMIN", "CONTADOR", "AUXILIAR", "CONSULTA"],
                     state="readonly", width=20).pack(side="left")

        def save():
            u = vs["username"].get().strip()
            n = vs["nombre"].get().strip()
            p = vs["password"].get()
            if not u or not n or not p:
                from gui.widgets import show_error
                show_error("Todos los campos son obligatorios.")
                return
            ph = hashlib.sha256(p.encode()).hexdigest()
            self.db.execute(
                "INSERT OR IGNORE INTO usuarios (username, password_hash, nombre, rol) VALUES (?,?,?,?)",
                (u, ph, n, vs["rol"].get()))
            self.db.commit()
            from gui.widgets import show_info
            show_info("Usuario creado.")
            d.destroy()

        ttk.Button(f, text="Guardar", command=save,
                   style="Success.TButton").pack(pady=8)

    def _placeholder(self, titulo, features):
        f = tk.Frame(self.content_frame, bg=C_BG)
        f.pack(fill="both", expand=True, padx=16, pady=12)
        hf = tk.Frame(f, bg=C_PRIMARY, height=40)
        hf.pack(fill="x")
        tk.Label(hf, text=f"  {titulo}",
                 bg=C_PRIMARY, fg="white", font=FONT_TITLE).place(x=0, y=5)
        cf = tk.Frame(f, bg=C_WHITE, padx=24, pady=20)
        cf.pack(fill="both", expand=True, padx=0, pady=0)
        tk.Label(cf, text=f"📋 {titulo}",
                 bg=C_WHITE, fg=C_PRIMARY,
                 font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 12))
        tk.Label(cf, text="Este módulo estará disponible en la próxima versión.\n"
                          "Funcionalidades incluidas:",
                 bg=C_WHITE, fg="#5d6d7e",
                 font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 8))
        for feat in features:
            tk.Label(cf, text=feat, bg=C_WHITE, fg="#2c3e50",
                     font=("Segoe UI", 10), anchor="w").pack(fill="x", pady=2)

    def _logout(self):
        if messagebox.askyesno("Cerrar Sesión", "¿Desea cerrar la sesión actual?"):
            self.usuario = None
            self.root.withdraw()
            for w in self.root.winfo_children():
                w.destroy()
            self._build_statusbar_placeholder()
            LoginWindow(self.root, self.db, self._on_login_success)

    def _build_statusbar_placeholder(self):
        pass

    def _on_close(self):
        if messagebox.askyesno("Salir", "¿Desea salir de CONTACOL PRO?"):
            if self.db:
                try:
                    self.db.close()
                except Exception:
                    pass
            self.root.destroy()

    def run(self):
        self.root.mainloop()


# ─── Punto de entrada ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = ContaColApp()
    app.run()
