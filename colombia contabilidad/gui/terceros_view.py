#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vista de Terceros (Clientes, Proveedores, Empleados) - CONTACOL PRO"""
import tkinter as tk
from tkinter import ttk
from .styles import C_PRIMARY, C_WHITE, C_BG, FONT_TITLE
from .widgets import DataTable, ToolBar, show_info, show_error, ask_confirm
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import DB


TIPOS_ID = ["NIT", "CC", "CE", "TI", "PAS", "NIT_EX", "NUIP"]
TIPOS_PERSONA = ["JURIDICA", "NATURAL"]
REGIMENES = ["RESPONSABLE_IVA", "NO_RESPONSABLE_IVA", "REGIMEN_SIMPLE",
             "NO_APLICA"]
DEPARTAMENTOS_CO = [
    "Amazonas", "Antioquia", "Arauca", "Atlántico", "Bogotá D.C.",
    "Bolívar", "Boyacá", "Caldas", "Caquetá", "Casanare", "Cauca",
    "Cesar", "Chocó", "Córdoba", "Cundinamarca", "Guainía", "Guaviare",
    "Huila", "La Guajira", "Magdalena", "Meta", "Nariño",
    "Norte de Santander", "Putumayo", "Quindío", "Risaralda",
    "San Andrés y Providencia", "Santander", "Sucre", "Tolima",
    "Valle del Cauca", "Vaupés", "Vichada",
]


class TercerosView(ttk.Frame):
    def __init__(self, parent, db: DB, tipo_filtro="TODOS"):
        super().__init__(parent)
        self.db = db
        self.tipo_filtro = tipo_filtro
        titulo = {
            "CLIENTE": "Clientes",
            "PROVEEDOR": "Proveedores",
            "EMPLEADO": "Empleados",
            "TODOS": "Terceros",
        }.get(tipo_filtro, "Terceros")
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
        tb.add_button("new", f"➕ Nuevo {self.titulo[:-1]}", self._new)
        tb.add_button("edit", "✏️ Editar", self._edit)
        tb.add_separator()
        tb.add_button("del", "🗑 Eliminar", self._delete, "Danger.TButton")
        tb.add_separator()

        sf = ttk.Frame(self)
        sf.pack(fill="x", padx=8, pady=2)
        ttk.Label(sf, text="Buscar:").pack(side="left", padx=4)
        self.v_q = tk.StringVar()
        self.v_q.trace("w", lambda *a: self._load())
        ttk.Entry(sf, textvariable=self.v_q, width=35).pack(side="left", padx=4)

        cols = [
            ("tipo_id", "Tipo ID", 70, "center"),
            ("numero_id", "NIT / Cédula", 110, "w"),
            ("dv", "DV", 35, "center"),
            ("razon_social", "Razón Social / Nombre", 280, "w"),
            ("tipo_persona", "Tipo", 80, "center"),
            ("regimen", "Régimen", 120, "w"),
            ("municipio", "Ciudad", 100, "w"),
            ("telefono", "Teléfono", 100, "w"),
        ]
        self.tabla = DataTable(self, cols)
        self.tabla.pack(fill="both", expand=True, padx=8, pady=6)
        self.tabla.tree.bind("<Double-1>", lambda e: self._edit())

    def _load(self):
        q = self.v_q.get().strip().lower()
        where = "WHERE activo=1"
        params = []
        if self.tipo_filtro == "CLIENTE":
            where += " AND es_cliente=1"
        elif self.tipo_filtro == "PROVEEDOR":
            where += " AND es_proveedor=1"
        elif self.tipo_filtro == "EMPLEADO":
            where += " AND es_empleado=1"
        if q:
            where += " AND (LOWER(razon_social) LIKE ? OR numero_id LIKE ?)"
            params += [f"%{q}%", f"%{q}%"]
        rows = self.db.fetchall(
            f"SELECT * FROM terceros {where} ORDER BY razon_social", params)
        self.tabla.clear()
        for r in rows:
            self.tabla.insert([
                r["tipo_id"], r["numero_id"],
                r["digito_verificacion"] or "",
                r["razon_social"],
                r["tipo_persona"],
                r["regimen_fiscal"] or "",
                r["municipio"] or "",
                r["telefono"] or "",
            ])

    def _new(self):
        TerceroDialog(self, self.db, None, self.tipo_filtro, self._load)

    def _edit(self):
        sel = self.tabla.get_selected()
        if not sel:
            show_error("Seleccione un registro.")
            return
        tipo_id, num_id = sel[0], sel[1]
        r = self.db.fetchone(
            "SELECT * FROM terceros WHERE tipo_id=? AND numero_id=?",
            (tipo_id, num_id))
        if r:
            TerceroDialog(self, self.db, dict(r), self.tipo_filtro, self._load)

    def _delete(self):
        sel = self.tabla.get_selected()
        if not sel:
            show_error("Seleccione un registro.")
            return
        if not ask_confirm("Eliminar Tercero", "¿Eliminar este tercero?"):
            return
        tipo_id, num_id = sel[0], sel[1]
        self.db.execute(
            "UPDATE terceros SET activo=0 WHERE tipo_id=? AND numero_id=?",
            (tipo_id, num_id))
        self.db.commit()
        self._load()


class TerceroDialog(tk.Toplevel):
    def __init__(self, parent, db: DB, data, tipo_filtro, on_save):
        super().__init__(parent)
        self.db = db
        self.data = data or {}
        self.tipo_filtro = tipo_filtro
        self.on_save = on_save
        self.title("Nuevo Tercero" if not data else "Editar Tercero")
        self.geometry("700x580")
        self.grab_set()
        self._build()
        if data:
            self._load()

    def _build(self):
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=6, pady=6)
        self._tab_general(nb)
        self._tab_fiscal(nb)
        self._tab_contacto(nb)
        self._tab_contable(nb)

        bf = ttk.Frame(self)
        bf.pack(fill="x", padx=10, pady=6)
        ttk.Button(bf, text="💾 Guardar", command=self._save,
                   style="Success.TButton").pack(side="left", padx=4)
        ttk.Button(bf, text="✖ Cancelar", command=self.destroy,
                   style="Danger.TButton").pack(side="left", padx=4)

    def _tab_general(self, nb):
        f = ttk.Frame(nb, style="White.TFrame", padding=14)
        nb.add(f, text="  General  ")
        self.vs = {}

        row = ttk.Frame(f, style="White.TFrame")
        row.pack(fill="x", pady=3)
        ttk.Label(row, text="Tipo ID: *", style="White.TLabel",
                  width=22, anchor="e").pack(side="left", padx=(0, 4))
        v = tk.StringVar(value="NIT")
        self.vs["tipo_id"] = v
        ttk.Combobox(row, textvariable=v, values=TIPOS_ID,
                     state="readonly", width=10).pack(side="left")

        for k, lbl, req, w in [
            ("numero_id", "NIT / Número ID: *", True, 20),
            ("digito_verificacion", "Dígito Verificación:", False, 5),
            ("razon_social", "Razón Social / Nombre: *", True, 40),
        ]:
            r = ttk.Frame(f, style="White.TFrame")
            r.pack(fill="x", pady=3)
            ttk.Label(r, text=lbl, style="White.TLabel",
                      width=22, anchor="e").pack(side="left", padx=(0, 4))
            v = tk.StringVar()
            self.vs[k] = v
            ttk.Entry(r, textvariable=v, width=w).pack(side="left")

        # Persona natural: nombres separados
        for k, lbl in [("nombre1", "Primer Nombre:"), ("nombre2", "Segundo Nombre:"),
                        ("apellido1", "Primer Apellido:"), ("apellido2", "Segundo Apellido:")]:
            r = ttk.Frame(f, style="White.TFrame")
            r.pack(fill="x", pady=2)
            ttk.Label(r, text=lbl, style="White.TLabel",
                      width=22, anchor="e").pack(side="left", padx=(0, 4))
            v = tk.StringVar()
            self.vs[k] = v
            ttk.Entry(r, textvariable=v, width=22).pack(side="left")

        # Tipo persona
        r = ttk.Frame(f, style="White.TFrame")
        r.pack(fill="x", pady=3)
        ttk.Label(r, text="Tipo Persona:", style="White.TLabel",
                  width=22, anchor="e").pack(side="left", padx=(0, 4))
        v = tk.StringVar(value="JURIDICA")
        self.vs["tipo_persona"] = v
        for val, lbl in [("JURIDICA", "Jurídica"), ("NATURAL", "Natural")]:
            ttk.Radiobutton(r, text=lbl, variable=v, value=val).pack(side="left", padx=6)

        # Roles
        r = ttk.Frame(f, style="White.TFrame")
        r.pack(fill="x", pady=3)
        ttk.Label(r, text="Roles:", style="White.TLabel",
                  width=22, anchor="e").pack(side="left", padx=(0, 4))
        for k, lbl in [("es_cliente", "Cliente"), ("es_proveedor", "Proveedor"),
                        ("es_empleado", "Empleado"), ("es_accionista", "Accionista/Socio")]:
            v = tk.BooleanVar()
            self.vs[k] = v
            if self.tipo_filtro == "CLIENTE" and k == "es_cliente":
                v.set(True)
            elif self.tipo_filtro == "PROVEEDOR" and k == "es_proveedor":
                v.set(True)
            elif self.tipo_filtro == "EMPLEADO" and k == "es_empleado":
                v.set(True)
            ttk.Checkbutton(r, text=lbl, variable=v).pack(side="left", padx=4)

    def _tab_fiscal(self, nb):
        f = ttk.Frame(nb, style="White.TFrame", padding=14)
        nb.add(f, text="  Fiscal  ")
        for k, lbl, opts in [
            ("regimen_fiscal", "Régimen Fiscal:", REGIMENES),
        ]:
            r = ttk.Frame(f, style="White.TFrame")
            r.pack(fill="x", pady=4)
            ttk.Label(r, text=lbl, style="White.TLabel",
                      width=26, anchor="e").pack(side="left", padx=(0, 4))
            v = tk.StringVar(value=opts[0])
            self.vs[k] = v
            ttk.Combobox(r, textvariable=v, values=opts,
                         state="readonly", width=26).pack(side="left")

        for k, lbl in [
            ("responsable_iva", "Responsable de IVA"),
            ("autoretenedor", "Autoretenedor"),
            ("gran_contribuyente", "Gran Contribuyente"),
            ("no_aplica_retencion", "No aplica Retención en la Fuente"),
        ]:
            r = ttk.Frame(f, style="White.TFrame")
            r.pack(fill="x", pady=3)
            ttk.Label(r, text="", style="White.TLabel", width=26).pack(side="left")
            v = tk.BooleanVar()
            self.vs[k] = v
            ttk.Checkbutton(r, text=lbl, variable=v).pack(side="left")

        r = ttk.Frame(f, style="White.TFrame")
        r.pack(fill="x", pady=4)
        ttk.Label(r, text="CIIU:", style="White.TLabel",
                  width=26, anchor="e").pack(side="left", padx=(0, 4))
        v = tk.StringVar()
        self.vs["codigo_ciiu"] = v
        ttk.Entry(r, textvariable=v, width=10).pack(side="left")

    def _tab_contacto(self, nb):
        f = ttk.Frame(nb, style="White.TFrame", padding=14)
        nb.add(f, text="  Contacto  ")
        for k, lbl, w in [
            ("direccion", "Dirección:", 40),
            ("municipio", "Municipio / Ciudad:", 25),
            ("codigo_municipio", "Código Municipio (DANE):", 10),
            ("telefono", "Teléfono:", 18),
            ("email", "Correo Electrónico:", 35),
        ]:
            r = ttk.Frame(f, style="White.TFrame")
            r.pack(fill="x", pady=4)
            ttk.Label(r, text=lbl, style="White.TLabel",
                      width=26, anchor="e").pack(side="left", padx=(0, 4))
            v = tk.StringVar()
            self.vs[k] = v
            ttk.Entry(r, textvariable=v, width=w).pack(side="left")

        r = ttk.Frame(f, style="White.TFrame")
        r.pack(fill="x", pady=4)
        ttk.Label(r, text="Departamento:", style="White.TLabel",
                  width=26, anchor="e").pack(side="left", padx=(0, 4))
        v = tk.StringVar()
        self.vs["departamento"] = v
        ttk.Combobox(r, textvariable=v, values=DEPARTAMENTOS_CO,
                     width=24).pack(side="left")

    def _tab_contable(self, nb):
        f = ttk.Frame(nb, style="White.TFrame", padding=14)
        nb.add(f, text="  Contable  ")
        r = ttk.Frame(f, style="White.TFrame")
        r.pack(fill="x", pady=4)
        ttk.Label(r, text="Cuenta Contable:", style="White.TLabel",
                  width=22, anchor="e").pack(side="left", padx=(0, 4))
        v = tk.StringVar()
        self.vs["cuenta_contable"] = v
        ttk.Entry(r, textvariable=v, width=14).pack(side="left")
        ttk.Label(r, text="(ej: 130505)", style="Light.TLabel").pack(side="left", padx=4)

    def _load(self):
        for k, v in self.vs.items():
            val = self.data.get(k)
            if isinstance(v, tk.BooleanVar):
                v.set(bool(val))
            else:
                v.set(str(val) if val is not None else "")

    def _save(self):
        num_id = self.vs["numero_id"].get().strip()
        rs = self.vs["razon_social"].get().strip()
        tipo_id = self.vs["tipo_id"].get()
        if not num_id or not rs:
            show_error("Número de Identificación y Razón Social son obligatorios.")
            return
        data = {}
        for k, v in self.vs.items():
            if isinstance(v, tk.BooleanVar):
                data[k] = 1 if v.get() else 0
            else:
                val = v.get().strip()
                data[k] = val if val else None

        existing = self.db.fetchone(
            "SELECT id FROM terceros WHERE tipo_id=? AND numero_id=?",
            (tipo_id, num_id))
        if existing and not self.data.get("id"):
            show_error(f"Ya existe un tercero con {tipo_id}: {num_id}")
            return

        if self.data.get("id"):
            cols = ", ".join(f"{k}=?" for k in data)
            self.db.execute(
                f"UPDATE terceros SET {cols} WHERE id=?",
                list(data.values()) + [self.data["id"]])
        else:
            cols = ", ".join(data.keys())
            ph = ", ".join("?" * len(data))
            self.db.execute(
                f"INSERT INTO terceros ({cols}) VALUES ({ph})",
                list(data.values()))
        self.db.commit()
        show_info("Tercero guardado correctamente.")
        self.on_save()
        self.destroy()
