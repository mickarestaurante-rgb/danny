#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CONTACOL PRO - Módulo de Base de Datos
Sistema Contable Colombiano - NIIF, PUC, DIAN 2026
"""
import sqlite3
import os
import hashlib
import datetime

DB_PATH = os.path.join(os.path.expanduser("~"), "contacol_data", "contacol.db")


def get_db_path():
    return DB_PATH


def set_db_path(path):
    global DB_PATH
    DB_PATH = path


class DB:
    def __init__(self, path=None):
        self.path = path or DB_PATH
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA journal_mode = WAL")

    def execute(self, sql, params=()):
        cur = self.conn.execute(sql, params)
        return cur

    def fetchall(self, sql, params=()):
        return self.conn.execute(sql, params).fetchall()

    def fetchone(self, sql, params=()):
        return self.conn.execute(sql, params).fetchone()

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()


def init_db(path=None):
    db = DB(path)
    _create_tables(db)
    _insert_defaults(db)
    db.commit()
    db.close()
    return True


def _create_tables(db):
    stmts = [
        """CREATE TABLE IF NOT EXISTS configuracion (
            clave TEXT PRIMARY KEY,
            valor TEXT,
            descripcion TEXT
        )""",

        """CREATE TABLE IF NOT EXISTS empresa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            razon_social TEXT NOT NULL,
            nit TEXT NOT NULL,
            digito_verificacion INTEGER,
            tipo_persona TEXT DEFAULT 'JURIDICA',
            tipo_contribuyente TEXT DEFAULT 'GRAN_CONTRIBUYENTE',
            regimen_fiscal TEXT DEFAULT 'RESPONSABLE_IVA',
            actividad_principal TEXT,
            codigo_ciiu TEXT,
            direccion TEXT,
            municipio TEXT,
            codigo_municipio TEXT,
            departamento TEXT,
            telefono TEXT,
            email TEXT,
            sitio_web TEXT,
            representante_legal TEXT,
            cc_representante TEXT,
            contador TEXT,
            tarjeta_contador TEXT,
            revisor_fiscal TEXT,
            tarjeta_revisor TEXT,
            fecha_constitucion TEXT,
            matricula_mercantil TEXT,
            capital_autorizado REAL DEFAULT 0,
            capital_suscrito REAL DEFAULT 0,
            capital_pagado REAL DEFAULT 0,
            logo_path TEXT,
            grupo_niif TEXT DEFAULT 'GRUPO2',
            responsable_iva INTEGER DEFAULT 1,
            retenedor INTEGER DEFAULT 1,
            activo INTEGER DEFAULT 1,
            creado_en TEXT DEFAULT CURRENT_TIMESTAMP
        )""",

        """CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            nombre TEXT NOT NULL,
            rol TEXT DEFAULT 'CONTADOR',
            empresa_id INTEGER,
            activo INTEGER DEFAULT 1,
            ultimo_acceso TEXT,
            creado_en TEXT DEFAULT CURRENT_TIMESTAMP
        )""",

        """CREATE TABLE IF NOT EXISTS plan_cuentas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL UNIQUE,
            nombre TEXT NOT NULL,
            nivel INTEGER NOT NULL,
            clase INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            naturaleza TEXT NOT NULL,
            codigo_padre TEXT,
            permite_movimiento INTEGER DEFAULT 0,
            exige_tercero INTEGER DEFAULT 0,
            exige_centro_costo INTEGER DEFAULT 0,
            exige_base INTEGER DEFAULT 0,
            ajuste_inflacion INTEGER DEFAULT 0,
            activa INTEGER DEFAULT 1
        )""",

        """CREATE TABLE IF NOT EXISTS centros_costo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL UNIQUE,
            nombre TEXT NOT NULL,
            activo INTEGER DEFAULT 1
        )""",

        """CREATE TABLE IF NOT EXISTS terceros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_id TEXT NOT NULL DEFAULT 'NIT',
            numero_id TEXT NOT NULL,
            digito_verificacion INTEGER,
            razon_social TEXT NOT NULL,
            nombre1 TEXT,
            nombre2 TEXT,
            apellido1 TEXT,
            apellido2 TEXT,
            tipo_persona TEXT DEFAULT 'JURIDICA',
            es_cliente INTEGER DEFAULT 0,
            es_proveedor INTEGER DEFAULT 0,
            es_empleado INTEGER DEFAULT 0,
            es_accionista INTEGER DEFAULT 0,
            regimen_fiscal TEXT DEFAULT 'RESPONSABLE_IVA',
            responsable_iva INTEGER DEFAULT 1,
            autoretenedor INTEGER DEFAULT 0,
            gran_contribuyente INTEGER DEFAULT 0,
            no_aplica_retencion INTEGER DEFAULT 0,
            codigo_ciiu TEXT,
            direccion TEXT,
            municipio TEXT,
            codigo_municipio TEXT,
            departamento TEXT,
            pais TEXT DEFAULT 'COLOMBIA',
            telefono TEXT,
            email TEXT,
            cuenta_contable TEXT,
            activo INTEGER DEFAULT 1,
            creado_en TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(tipo_id, numero_id)
        )""",

        """CREATE TABLE IF NOT EXISTS periodos_fiscales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            anio INTEGER NOT NULL,
            mes INTEGER NOT NULL,
            nombre TEXT NOT NULL,
            estado TEXT DEFAULT 'ABIERTO',
            fecha_cierre TEXT,
            UNIQUE(anio, mes)
        )""",

        """CREATE TABLE IF NOT EXISTS tipos_comprobante (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL UNIQUE,
            nombre TEXT NOT NULL,
            prefijo TEXT DEFAULT '',
            consecutivo_actual INTEGER DEFAULT 0,
            activo INTEGER DEFAULT 1
        )""",

        """CREATE TABLE IF NOT EXISTS comprobantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_codigo TEXT NOT NULL,
            consecutivo INTEGER NOT NULL,
            prefijo TEXT DEFAULT '',
            fecha TEXT NOT NULL,
            periodo_id INTEGER,
            tercero_id INTEGER,
            descripcion TEXT,
            total_debito REAL DEFAULT 0,
            total_credito REAL DEFAULT 0,
            estado TEXT DEFAULT 'ACTIVO',
            anulado_motivo TEXT,
            usuario_id INTEGER,
            creado_en TEXT DEFAULT CURRENT_TIMESTAMP
        )""",

        """CREATE TABLE IF NOT EXISTS movimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comprobante_id INTEGER NOT NULL,
            cuenta_codigo TEXT NOT NULL,
            tercero_id INTEGER,
            centro_costo_id INTEGER,
            debito REAL DEFAULT 0,
            credito REAL DEFAULT 0,
            descripcion TEXT,
            referencia TEXT,
            base_retencion REAL DEFAULT 0,
            FOREIGN KEY(comprobante_id) REFERENCES comprobantes(id)
        )""",

        """CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL UNIQUE,
            descripcion TEXT NOT NULL,
            tipo TEXT DEFAULT 'PRODUCTO',
            unidad_medida TEXT DEFAULT 'UND',
            precio_venta REAL DEFAULT 0,
            costo_promedio REAL DEFAULT 0,
            tarifa_iva REAL DEFAULT 19,
            excluido_iva INTEGER DEFAULT 0,
            exento_iva INTEGER DEFAULT 0,
            cuenta_venta TEXT DEFAULT '4135',
            cuenta_costo TEXT DEFAULT '6135',
            cuenta_inventario TEXT DEFAULT '1430',
            cuenta_devolucion TEXT DEFAULT '4175',
            stock_actual REAL DEFAULT 0,
            stock_minimo REAL DEFAULT 0,
            activo INTEGER DEFAULT 1
        )""",

        """CREATE TABLE IF NOT EXISTS facturas_venta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT DEFAULT 'FV',
            consecutivo INTEGER NOT NULL,
            prefijo TEXT DEFAULT 'FV',
            cufe TEXT,
            fecha TEXT NOT NULL,
            fecha_vencimiento TEXT,
            cliente_id INTEGER,
            condicion_pago TEXT DEFAULT 'CONTADO',
            dias_credito INTEGER DEFAULT 0,
            subtotal REAL DEFAULT 0,
            descuento_comercial REAL DEFAULT 0,
            base_iva19 REAL DEFAULT 0,
            iva19 REAL DEFAULT 0,
            base_iva5 REAL DEFAULT 0,
            iva5 REAL DEFAULT 0,
            excluido REAL DEFAULT 0,
            exento REAL DEFAULT 0,
            reteiva REAL DEFAULT 0,
            rete_fuente REAL DEFAULT 0,
            rete_ica REAL DEFAULT 0,
            total REAL DEFAULT 0,
            saldo REAL DEFAULT 0,
            observaciones TEXT,
            estado TEXT DEFAULT 'ACTIVO',
            electronica INTEGER DEFAULT 0,
            comprobante_id INTEGER,
            creado_en TEXT DEFAULT CURRENT_TIMESTAMP
        )""",

        """CREATE TABLE IF NOT EXISTS facturas_venta_detalle (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            factura_id INTEGER NOT NULL,
            linea INTEGER NOT NULL,
            producto_id INTEGER,
            descripcion TEXT NOT NULL,
            cantidad REAL NOT NULL,
            precio_unitario REAL NOT NULL,
            descuento_pct REAL DEFAULT 0,
            descuento_valor REAL DEFAULT 0,
            subtotal REAL NOT NULL,
            tarifa_iva REAL DEFAULT 19,
            iva REAL DEFAULT 0,
            total REAL NOT NULL,
            FOREIGN KEY(factura_id) REFERENCES facturas_venta(id)
        )""",

        """CREATE TABLE IF NOT EXISTS facturas_compra (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT DEFAULT 'FC',
            numero_externo TEXT,
            fecha TEXT NOT NULL,
            fecha_vencimiento TEXT,
            proveedor_id INTEGER,
            condicion_pago TEXT DEFAULT 'CONTADO',
            subtotal REAL DEFAULT 0,
            base_iva19 REAL DEFAULT 0,
            iva19 REAL DEFAULT 0,
            base_iva5 REAL DEFAULT 0,
            iva5 REAL DEFAULT 0,
            reteiva REAL DEFAULT 0,
            rete_fuente REAL DEFAULT 0,
            rete_ica REAL DEFAULT 0,
            total REAL DEFAULT 0,
            saldo REAL DEFAULT 0,
            observaciones TEXT,
            estado TEXT DEFAULT 'ACTIVO',
            comprobante_id INTEGER,
            creado_en TEXT DEFAULT CURRENT_TIMESTAMP
        )""",

        """CREATE TABLE IF NOT EXISTS facturas_compra_detalle (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            factura_id INTEGER NOT NULL,
            linea INTEGER NOT NULL,
            producto_id INTEGER,
            descripcion TEXT NOT NULL,
            cantidad REAL NOT NULL,
            precio_unitario REAL NOT NULL,
            descuento_pct REAL DEFAULT 0,
            descuento_valor REAL DEFAULT 0,
            subtotal REAL NOT NULL,
            tarifa_iva REAL DEFAULT 19,
            iva REAL DEFAULT 0,
            total REAL NOT NULL,
            FOREIGN KEY(factura_id) REFERENCES facturas_compra(id)
        )""",

        """CREATE TABLE IF NOT EXISTS bancos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            banco TEXT NOT NULL,
            numero_cuenta TEXT NOT NULL UNIQUE,
            tipo_cuenta TEXT DEFAULT 'CORRIENTE',
            moneda TEXT DEFAULT 'COP',
            cuenta_contable TEXT DEFAULT '1110',
            saldo_actual REAL DEFAULT 0,
            activo INTEGER DEFAULT 1
        )""",

        """CREATE TABLE IF NOT EXISTS movimientos_banco (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            banco_id INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            tipo TEXT NOT NULL,
            descripcion TEXT,
            referencia TEXT,
            valor REAL NOT NULL,
            saldo REAL,
            conciliado INTEGER DEFAULT 0,
            comprobante_id INTEGER,
            FOREIGN KEY(banco_id) REFERENCES bancos(id)
        )""",

        """CREATE TABLE IF NOT EXISTS empleados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tercero_id INTEGER,
            cargo TEXT,
            departamento_empresa TEXT,
            tipo_contrato TEXT DEFAULT 'INDEFINIDO',
            fecha_ingreso TEXT NOT NULL,
            fecha_retiro TEXT,
            salario_basico REAL NOT NULL,
            auxilio_transporte INTEGER DEFAULT 1,
            tipo_cotizante TEXT DEFAULT '01',
            subtipo_cotizante TEXT DEFAULT '00',
            eps TEXT,
            fondo_pension TEXT,
            fondo_cesantias TEXT,
            arl TEXT,
            caja_compensacion TEXT,
            nivel_riesgo INTEGER DEFAULT 1,
            porcentaje_arl REAL DEFAULT 0.522,
            cuenta_banco TEXT,
            tipo_cuenta_banco TEXT DEFAULT 'AHORROS',
            banco_nombre TEXT,
            activo INTEGER DEFAULT 1
        )""",

        """CREATE TABLE IF NOT EXISTS nomina_periodos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            anio INTEGER NOT NULL,
            mes INTEGER NOT NULL,
            tipo TEXT DEFAULT 'MENSUAL',
            estado TEXT DEFAULT 'BORRADOR',
            fecha_pago TEXT,
            total_devengado REAL DEFAULT 0,
            total_deducciones REAL DEFAULT 0,
            total_neto REAL DEFAULT 0,
            total_aportes_empresa REAL DEFAULT 0,
            comprobante_id INTEGER,
            UNIQUE(anio, mes, tipo)
        )""",

        """CREATE TABLE IF NOT EXISTS nomina_liquidacion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            periodo_id INTEGER NOT NULL,
            empleado_id INTEGER NOT NULL,
            dias_trabajados INTEGER DEFAULT 30,
            salario_basico REAL DEFAULT 0,
            auxilio_transporte REAL DEFAULT 0,
            horas_extras_diurnas_cant REAL DEFAULT 0,
            horas_extras_diurnas_val REAL DEFAULT 0,
            horas_extras_nocturnas_cant REAL DEFAULT 0,
            horas_extras_nocturnas_val REAL DEFAULT 0,
            horas_extras_dominicales_cant REAL DEFAULT 0,
            horas_extras_dominicales_val REAL DEFAULT 0,
            recargo_nocturno_val REAL DEFAULT 0,
            comisiones REAL DEFAULT 0,
            bonificaciones REAL DEFAULT 0,
            otros_devengados REAL DEFAULT 0,
            incapacidad_dias INTEGER DEFAULT 0,
            incapacidad_valor REAL DEFAULT 0,
            licencia_remunerada REAL DEFAULT 0,
            total_devengado REAL DEFAULT 0,
            salud_empleado REAL DEFAULT 0,
            pension_empleado REAL DEFAULT 0,
            fondo_solidaridad REAL DEFAULT 0,
            prestamo REAL DEFAULT 0,
            libranza REAL DEFAULT 0,
            otras_deducciones REAL DEFAULT 0,
            retencion_fuente_nomina REAL DEFAULT 0,
            total_deducciones REAL DEFAULT 0,
            neto_pagar REAL DEFAULT 0,
            salud_empresa REAL DEFAULT 0,
            pension_empresa REAL DEFAULT 0,
            arl_empresa REAL DEFAULT 0,
            caja_compensacion REAL DEFAULT 0,
            sena REAL DEFAULT 0,
            icbf REAL DEFAULT 0,
            total_aportes_empresa REAL DEFAULT 0,
            prima_proporcional REAL DEFAULT 0,
            cesantias_proporcional REAL DEFAULT 0,
            intereses_cesantias_prop REAL DEFAULT 0,
            vacaciones_proporcional REAL DEFAULT 0,
            FOREIGN KEY(periodo_id) REFERENCES nomina_periodos(id),
            FOREIGN KEY(empleado_id) REFERENCES empleados(id)
        )""",

        """CREATE TABLE IF NOT EXISTS activos_fijos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL UNIQUE,
            descripcion TEXT NOT NULL,
            grupo TEXT DEFAULT 'MAQUINARIA',
            fecha_adquisicion TEXT NOT NULL,
            valor_adquisicion REAL NOT NULL,
            vida_util_meses INTEGER DEFAULT 60,
            metodo_depreciacion TEXT DEFAULT 'LINEA_RECTA',
            valor_residual REAL DEFAULT 0,
            depreciacion_acumulada REAL DEFAULT 0,
            valor_libro REAL DEFAULT 0,
            ultima_depreciacion TEXT,
            cuenta_activo TEXT DEFAULT '1520',
            cuenta_dep_acumulada TEXT DEFAULT '1592',
            cuenta_gasto_dep TEXT DEFAULT '5160',
            ubicacion TEXT,
            responsable TEXT,
            serial TEXT,
            activo INTEGER DEFAULT 1
        )""",

        """CREATE TABLE IF NOT EXISTS parametros_impuestos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            anio INTEGER NOT NULL UNIQUE,
            smlv REAL NOT NULL,
            auxilio_transporte REAL NOT NULL,
            uvt REAL NOT NULL,
            tasa_renta_empresa REAL DEFAULT 35,
            tasa_iva_general REAL DEFAULT 19,
            tasa_iva_reducida REAL DEFAULT 5,
            tasa_gmf REAL DEFAULT 0.004,
            tasa_reteica_industria REAL DEFAULT 0.00414,
            tasa_reteica_comercio REAL DEFAULT 0.00414,
            tasa_reteica_servicios REAL DEFAULT 0.00966,
            creado_en TEXT DEFAULT CURRENT_TIMESTAMP
        )""",

        """CREATE TABLE IF NOT EXISTS retenciones_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            concepto TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            codigo_concepto TEXT,
            tarifa_pj REAL NOT NULL,
            tarifa_pn REAL NOT NULL,
            base_uvt REAL DEFAULT 0,
            tipo_base TEXT DEFAULT 'BRUTO',
            cuenta_retencion TEXT,
            activo INTEGER DEFAULT 1
        )""",

        """CREATE TABLE IF NOT EXISTS declaraciones_iva (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            anio INTEGER NOT NULL,
            periodo INTEGER NOT NULL,
            tipo_periodo TEXT DEFAULT 'BIMESTRAL',
            ingresos_brutos REAL DEFAULT 0,
            base_gravada_19 REAL DEFAULT 0,
            iva_generado_19 REAL DEFAULT 0,
            base_gravada_5 REAL DEFAULT 0,
            iva_generado_5 REAL DEFAULT 0,
            iva_descontable REAL DEFAULT 0,
            retenciones_iva REAL DEFAULT 0,
            saldo_favor_anterior REAL DEFAULT 0,
            impuesto_cargo REAL DEFAULT 0,
            saldo_favor REAL DEFAULT 0,
            estado TEXT DEFAULT 'BORRADOR',
            fecha_presentacion TEXT,
            UNIQUE(anio, periodo, tipo_periodo)
        )""",

        """CREATE TABLE IF NOT EXISTS pagos_recibidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            cliente_id INTEGER,
            concepto TEXT,
            valor REAL NOT NULL,
            forma_pago TEXT DEFAULT 'EFECTIVO',
            banco_id INTEGER,
            referencia TEXT,
            comprobante_id INTEGER,
            creado_en TEXT DEFAULT CURRENT_TIMESTAMP
        )""",

        """CREATE TABLE IF NOT EXISTS pagos_realizados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            proveedor_id INTEGER,
            concepto TEXT,
            valor REAL NOT NULL,
            forma_pago TEXT DEFAULT 'EFECTIVO',
            banco_id INTEGER,
            referencia TEXT,
            comprobante_id INTEGER,
            creado_en TEXT DEFAULT CURRENT_TIMESTAMP
        )"""
    ]
    for stmt in stmts:
        db.execute(stmt)


def _insert_defaults(db):
    # Admin user
    pw = hashlib.sha256("admin123".encode()).hexdigest()
    db.execute("""INSERT OR IGNORE INTO usuarios (username, password_hash, nombre, rol)
                  VALUES (?, ?, ?, ?)""", ("admin", pw, "Administrador", "ADMIN"))

    # System config
    configs = [
        ("version", "1.0.0", "Versión del sistema"),
        ("anio_fiscal", "2026", "Año fiscal activo"),
        ("moneda", "COP", "Moneda principal"),
        ("decimales", "0", "Decimales en moneda"),
        ("formato_fecha", "%d/%m/%Y", "Formato de fecha"),
        ("empresa_configurada", "0", "Si la empresa ya fue configurada"),
        ("prefijo_fv", "FV", "Prefijo facturas de venta"),
        ("prefijo_fc", "FC", "Prefijo facturas de compra"),
        ("prefijo_nd", "ND", "Prefijo notas débito"),
        ("prefijo_nc", "NC", "Prefijo notas crédito"),
        ("prefijo_rc", "RC", "Prefijo recibos de caja"),
        ("prefijo_cp", "CP", "Prefijo comprobantes de pago"),
        ("prefijo_ce", "CE", "Prefijo comprobantes de egreso"),
        ("prefijo_aj", "AJ", "Prefijo ajustes"),
    ]
    for c in configs:
        db.execute("INSERT OR IGNORE INTO configuracion (clave, valor, descripcion) VALUES (?,?,?)", c)

    # Tipos de comprobante
    tipos = [
        ("FV", "Factura de Venta", "FV"),
        ("FC", "Factura de Compra", "FC"),
        ("NC", "Nota Crédito", "NC"),
        ("ND", "Nota Débito", "ND"),
        ("RC", "Recibo de Caja", "RC"),
        ("CP", "Comprobante de Pago", "CP"),
        ("CE", "Comprobante de Egreso", "CE"),
        ("NM", "Nómina", "NM"),
        ("AJ", "Ajuste Contable", "AJ"),
        ("CC", "Conciliación Bancaria", "CC"),
        ("AP", "Apertura", "AP"),
        ("CI", "Cierre", "CI"),
    ]
    for t in tipos:
        db.execute("INSERT OR IGNORE INTO tipos_comprobante (codigo, nombre, prefijo) VALUES (?,?,?)", t)

    # Parámetros impuestos 2026
    db.execute("""INSERT OR IGNORE INTO parametros_impuestos
                  (anio, smlv, auxilio_transporte, uvt, tasa_renta_empresa)
                  VALUES (?, ?, ?, ?, ?)""",
               (2026, 1600000, 202000, 49799, 35))

    db.execute("""INSERT OR IGNORE INTO parametros_impuestos
                  (anio, smlv, auxilio_transporte, uvt, tasa_renta_empresa)
                  VALUES (?, ?, ?, ?, ?)""",
               (2025, 1423500, 179013, 49799, 35))

    # Retenciones en la fuente
    retenciones = [
        ("HONORARIOS_PJ", "Honorarios - Persona Jurídica", "1001", 11.0, 10.0, 0, "BRUTO", "2365"),
        ("HONORARIOS_PN_DECL", "Honorarios - Persona Natural Declarante", "1001", 11.0, 10.0, 0, "BRUTO", "2365"),
        ("HONORARIOS_PN_NO_DECL", "Honorarios - Persona Natural No Declarante", "1001", 11.0, 11.0, 0, "BRUTO", "2365"),
        ("SERVICIOS_PJ", "Servicios - Persona Jurídica", "1005", 4.0, 4.0, 4, "BRUTO", "2365"),
        ("SERVICIOS_PN", "Servicios - Persona Natural", "1005", 6.0, 6.0, 4, "BRUTO", "2365"),
        ("COMPRAS", "Compras Generales", "1006", 3.5, 3.5, 27, "BRUTO", "2365"),
        ("ARRENDAMIENTO_INMUEBLE", "Arrendamiento de Inmuebles", "1008", 3.5, 3.5, 0, "BRUTO", "2365"),
        ("ARRENDAMIENTO_MUEBLE", "Arrendamiento de Bienes Muebles", "1008", 4.0, 4.0, 0, "BRUTO", "2365"),
        ("TRANSPORTE_CARGA", "Transporte de Carga Nacional", "1009", 1.0, 1.0, 4, "BRUTO", "2365"),
        ("TRANSPORTE_NAL", "Transporte Nacional de Pasajeros", "1009", 3.5, 3.5, 4, "BRUTO", "2365"),
        ("RENDIMIENTOS", "Rendimientos Financieros", "1010", 7.0, 7.0, 0, "BRUTO", "2365"),
        ("COMISIONES", "Comisiones", "1003", 11.0, 10.0, 0, "BRUTO", "2365"),
        ("DIVIDENDOS_EXENTOS", "Dividendos/Participaciones Exentos", "1001", 10.0, 10.0, 0, "BRUTO", "2365"),
        ("INGRESOS_EXTERIOR", "Pagos al Exterior", "1004", 20.0, 20.0, 0, "BRUTO", "2365"),
        ("LOTERIAS_RIFAS", "Loterías y Rifas", "1001", 20.0, 20.0, 0, "BRUTO", "2365"),
        ("ENAJENACION_ACTIVOS", "Enajenación de Activos Fijos", "1001", 1.0, 1.0, 0, "BRUTO", "2365"),
        ("SEGUROS_VIDA", "Seguros de Vida", "1001", 3.5, 3.5, 0, "BRUTO", "2365"),
        ("SALARIOS_EMPLEADOS", "Salarios y Pagos Laborales", "1002", 0.0, 0.0, 0, "TABLA_MENSUAL", "2370"),
    ]
    for r in retenciones:
        db.execute("""INSERT OR IGNORE INTO retenciones_config
                      (concepto, descripcion, codigo_concepto, tarifa_pj, tarifa_pn,
                       base_uvt, tipo_base, cuenta_retencion)
                      VALUES (?,?,?,?,?,?,?,?)""", r)

    # Periodos fiscales 2026
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    for i, m in enumerate(meses, 1):
        db.execute("INSERT OR IGNORE INTO periodos_fiscales (anio, mes, nombre) VALUES (?,?,?)",
                   (2026, i, f"{m} 2026"))


# ─── CRUD helpers ─────────────────────────────────────────────────────────────

def get_config(db, clave):
    r = db.fetchone("SELECT valor FROM configuracion WHERE clave=?", (clave,))
    return r["valor"] if r else None


def set_config(db, clave, valor):
    db.execute("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES (?,?)", (clave, valor))
    db.commit()


def get_empresa(db):
    return db.fetchone("SELECT * FROM empresa LIMIT 1")


def save_empresa(db, data):
    e = get_empresa(db)
    if e:
        cols = ", ".join(f"{k}=?" for k in data)
        db.execute(f"UPDATE empresa SET {cols} WHERE id=?", list(data.values()) + [e["id"]])
    else:
        cols = ", ".join(data.keys())
        placeholders = ", ".join("?" * len(data))
        db.execute(f"INSERT INTO empresa ({cols}) VALUES ({placeholders})", list(data.values()))
    db.commit()


def get_plan_cuentas(db, solo_movimiento=False):
    if solo_movimiento:
        return db.fetchall("SELECT * FROM plan_cuentas WHERE permite_movimiento=1 AND activa=1 ORDER BY codigo")
    return db.fetchall("SELECT * FROM plan_cuentas WHERE activa=1 ORDER BY codigo")


def get_cuenta(db, codigo):
    return db.fetchone("SELECT * FROM plan_cuentas WHERE codigo=?", (codigo,))


def get_terceros(db, tipo=None):
    if tipo == "CLIENTE":
        return db.fetchall("SELECT * FROM terceros WHERE es_cliente=1 AND activo=1 ORDER BY razon_social")
    elif tipo == "PROVEEDOR":
        return db.fetchall("SELECT * FROM terceros WHERE es_proveedor=1 AND activo=1 ORDER BY razon_social")
    elif tipo == "EMPLEADO":
        return db.fetchall("SELECT * FROM terceros WHERE es_empleado=1 AND activo=1 ORDER BY razon_social")
    return db.fetchall("SELECT * FROM terceros WHERE activo=1 ORDER BY razon_social")


def get_tercero(db, id_):
    return db.fetchone("SELECT * FROM terceros WHERE id=?", (id_,))


def next_consecutivo(db, tipo_codigo):
    r = db.fetchone("SELECT consecutivo_actual FROM tipos_comprobante WHERE codigo=?", (tipo_codigo,))
    n = (r["consecutivo_actual"] if r else 0) + 1
    db.execute("UPDATE tipos_comprobante SET consecutivo_actual=? WHERE codigo=?", (n, tipo_codigo))
    return n


def get_saldo_cuenta(db, codigo, anio=None, mes_hasta=None):
    """Retorna (debito_total, credito_total, saldo)"""
    sql = """SELECT SUM(m.debito) as d, SUM(m.credito) as c
             FROM movimientos m
             JOIN comprobantes c ON c.id=m.comprobante_id
             WHERE m.cuenta_codigo LIKE ? AND c.estado='ACTIVO'"""
    params = [codigo + "%"]
    if anio:
        sql += " AND strftime('%Y', c.fecha)=?"
        params.append(str(anio))
    if mes_hasta:
        sql += " AND strftime('%m', c.fecha)<=?"
        params.append(f"{mes_hasta:02d}")
    r = db.fetchone(sql, params)
    d = r["d"] or 0
    c = r["c"] or 0
    return d, c, d - c


def get_balance_comprobacion(db, anio, mes_hasta=12):
    """Retorna balance de comprobación para cuentas con movimiento"""
    sql = """SELECT m.cuenta_codigo, pc.nombre, pc.naturaleza,
                    SUM(m.debito) as debito, SUM(m.credito) as credito
             FROM movimientos m
             JOIN comprobantes c ON c.id=m.comprobante_id
             JOIN plan_cuentas pc ON pc.codigo=m.cuenta_codigo
             WHERE c.estado='ACTIVO'
               AND strftime('%Y', c.fecha)=?
               AND strftime('%m', c.fecha)<=?
             GROUP BY m.cuenta_codigo
             ORDER BY m.cuenta_codigo"""
    return db.fetchall(sql, (str(anio), f"{mes_hasta:02d}"))


def get_movimientos_cuenta(db, codigo, fecha_ini=None, fecha_fin=None):
    sql = """SELECT m.*, c.fecha, c.tipo_codigo, c.consecutivo, c.descripcion as comp_desc,
                    t.razon_social as tercero_nom
             FROM movimientos m
             JOIN comprobantes c ON c.id=m.comprobante_id
             LEFT JOIN terceros t ON t.id=m.tercero_id
             WHERE m.cuenta_codigo LIKE ? AND c.estado='ACTIVO'"""
    params = [codigo + "%"]
    if fecha_ini:
        sql += " AND c.fecha>=?"
        params.append(fecha_ini)
    if fecha_fin:
        sql += " AND c.fecha<=?"
        params.append(fecha_fin)
    sql += " ORDER BY c.fecha, c.id, m.id"
    return db.fetchall(sql, params)


def get_parametros(db, anio=2026):
    r = db.fetchone("SELECT * FROM parametros_impuestos WHERE anio=?", (anio,))
    if not r:
        r = db.fetchone("SELECT * FROM parametros_impuestos ORDER BY anio DESC LIMIT 1")
    return r
