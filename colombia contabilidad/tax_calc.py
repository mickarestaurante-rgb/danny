#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cálculos Tributarios Colombia 2026
IVA, Retención en la Fuente, ICA, GMF, Renta
Según normativa DIAN y Estatuto Tributario
"""
from decimal import Decimal, ROUND_HALF_UP

# ─── TARIFAS IVA ──────────────────────────────────────────────────────────────
IVA_GENERAL = 19.0          # Tarifa general Ley 1819/2016
IVA_REDUCIDA = 5.0          # Tarifa reducida
IVA_EXENTO = 0.0            # Bienes exentos (en la norma, tarifa 0 con derecho a descuento)
IVA_EXCLUIDO = None         # Excluidos: no causa IVA, no hay descuento

# Bienes y servicios gravados al 5%
BIENES_IVA_5 = [
    "Café sin tostar ni descafeinar", "Maíz para uso industrial",
    "Bienes inmuebles de uso residencial", "Seguros de vida",
    "Computadores y tabletas hasta $50M",
    "Motocicletas hasta 200cc", "Bicicletas hasta $1.5M",
    "Almacenamiento en la nube", "Planes telefonía 4G/5G",
]

# ─── RETEIVA ──────────────────────────────────────────────────────────────────
RETEIVA_TARIFA = 0.15  # 15% del IVA (Art. 437-1 ET)

# Agentes de retención de IVA (grandes contribuyentes, RUT código 15)
# Aplican ReteIVA al comprar a no responsables de IVA

# ─── GMF (GRAVAMEN MOVIMIENTOS FINANCIEROS) ───────────────────────────────────
GMF_TARIFA = 0.004  # 4x1000 = 0.4%
# Exenciones GMF principales:
# - Primeras 350 UVT/mes en una sola cuenta de ahorros
# - Cuentas AFC, cuentas FNA
# - Desembolsos de créditos

# ─── ICA (INDUSTRIA Y COMERCIO) ───────────────────────────────────────────────
# Tarifas por actividad (por mil) - principales municipios
ICA_BOGOTA = {
    "industrial": 0.00414,     # 4.14 x 1000
    "comercio": 0.00414,       # 4.14 x 1000
    "servicios": 0.00966,      # 9.66 x 1000
    "financiero": 0.01188,     # 11.88 x 1000
    "salud": 0.00276,          # 2.76 x 1000
}

ICA_MEDELLIN = {
    "industrial": 0.004,
    "comercio": 0.005,
    "servicios": 0.010,
    "financiero": 0.012,
}

ICA_CALI = {
    "industrial": 0.003,
    "comercio": 0.005,
    "servicios": 0.009,
    "financiero": 0.011,
}

# ─── IMPUESTO DE RENTA ────────────────────────────────────────────────────────
TASA_RENTA_EMPRESA = 0.35   # 35% Ley 2277/2022 (vigente 2024 en adelante)
TASA_RENTA_ZONA_FRANCA = 0.20  # Zonas francas

# Tabla de renta personas naturales 2026 (UVT)
# Renta liquida gravable anual en UVT
TABLA_RENTA_PN = [
    (0, 1090, 0, 0),               # 0%
    (1090, 1700, 0.19, 0),         # 19%
    (1700, 4100, 0.28, 116.10),    # 28%
    (4100, 8670, 0.33, 788.10),    # 33%
    (8670, 18970, 0.35, 1297.20),  # 35%
    (18970, 31000, 0.37, 3766.00), # 37%
    (31000, float("inf"), 0.39, 8206.00),  # 39%
]

# ─── RETENCIÓN EN LA FUENTE ───────────────────────────────────────────────────
# Bases mínimas en UVT (2026)
BASES_RETENCION_UVT = {
    "honorarios": 0,        # Sin base mínima para PJ
    "servicios": 4,         # 4 UVT
    "compras": 27,          # 27 UVT (~$1,344,573 en 2026)
    "arrendamiento": 0,     # Sin base mínima
    "transporte": 4,        # 4 UVT
    "rendimientos": 0,      # Sin base mínima
    "comisiones": 0,        # Sin base mínima
}


def calcular_iva(base: float, tarifa: float = 19.0) -> float:
    """Calcula el IVA sobre una base"""
    return round(base * tarifa / 100)


def calcular_reteiva(iva_valor: float) -> float:
    """Calcula ReteIVA = 15% del valor del IVA"""
    return round(iva_valor * RETEIVA_TARIFA)


def calcular_gmf(valor: float) -> float:
    """Calcula GMF 4x1000"""
    return round(valor * GMF_TARIFA)


def calcular_ica(base_ingresos: float, tipo_actividad: str = "servicios",
                 municipio: str = "BOGOTA") -> float:
    """Calcula ICA según municipio y tipo de actividad"""
    tablas = {
        "BOGOTA": ICA_BOGOTA,
        "MEDELLIN": ICA_MEDELLIN,
        "CALI": ICA_CALI,
    }
    tabla = tablas.get(municipio.upper(), ICA_BOGOTA)
    tarifa = tabla.get(tipo_actividad.lower(), tabla.get("servicios", 0.00966))
    return round(base_ingresos * tarifa)


def calcular_reteica(base: float, tipo_actividad: str = "servicios",
                     municipio: str = "BOGOTA") -> float:
    """ReteICA = ICA sobre el pago"""
    return calcular_ica(base, tipo_actividad, municipio)


def calcular_retencion_fuente(base: float, tarifa_pct: float,
                               base_minima_uvt: float = 0,
                               uvt: float = 49799) -> float:
    """
    Calcula retención en la fuente.
    Solo aplica si base >= base_minima_uvt * uvt
    """
    base_minima = base_minima_uvt * uvt
    if base < base_minima:
        return 0.0
    return round(base * tarifa_pct / 100)


def calcular_renta_empresa(utilidad_fiscal: float) -> float:
    """Impuesto de renta para personas jurídicas"""
    return round(utilidad_fiscal * TASA_RENTA_EMPRESA)


def calcular_renta_persona_natural(renta_liquida_uvt: float,
                                    uvt: float = 49799) -> float:
    """
    Impuesto de renta para personas naturales.
    renta_liquida_uvt: renta líquida gravable expresada en UVT
    """
    impuesto_uvt = 0.0
    for desde, hasta, tarifa, descuento in TABLA_RENTA_PN:
        if renta_liquida_uvt > desde:
            base = min(renta_liquida_uvt, hasta) - desde
            if tarifa > 0:
                impuesto_uvt = (renta_liquida_uvt - desde) * tarifa - descuento
                # Usar la tabla correcta
                break

    # Método correcto: tabla marginal acumulada
    impuesto_uvt = 0.0
    for desde, hasta, tarifa, _ in TABLA_RENTA_PN:
        if renta_liquida_uvt <= desde:
            break
        exceso_uvt = min(renta_liquida_uvt, hasta) - desde
        impuesto_uvt += exceso_uvt * tarifa

    return round(impuesto_uvt * uvt)


def calcular_anticipo_renta(impuesto_anio_anterior: float,
                             impuesto_anio_corriente: float = None,
                             primer_anio: bool = False) -> float:
    """
    Calcula anticipo del impuesto de renta.
    - Primer año: 25% del impuesto neto del año
    - Segundo año: 50%
    - Tercer año en adelante: 75%
    """
    if primer_anio:
        return round(impuesto_anio_anterior * 0.25)
    if impuesto_anio_corriente:
        return round((impuesto_anio_anterior + impuesto_anio_corriente) / 2 * 0.75)
    return round(impuesto_anio_anterior * 0.75)


def calculo_iva_declaracion(ventas_gravadas_19: float, ventas_gravadas_5: float,
                              compras_gravadas_19: float, compras_gravadas_5: float,
                              iva_retenido_a_favor: float = 0,
                              saldo_favor_anterior: float = 0) -> dict:
    """
    Calcula el saldo a pagar o a favor de IVA para declaración.
    """
    iva_generado_19 = round(ventas_gravadas_19 * 0.19)
    iva_generado_5 = round(ventas_gravadas_5 * 0.05)
    iva_generado = iva_generado_19 + iva_generado_5

    iva_descontable_19 = round(compras_gravadas_19 * 0.19)
    iva_descontable_5 = round(compras_gravadas_5 * 0.05)
    iva_descontable = iva_descontable_19 + iva_descontable_5

    saldo_bruto = iva_generado - iva_descontable - iva_retenido_a_favor - saldo_favor_anterior

    return {
        "iva_generado_19": iva_generado_19,
        "iva_generado_5": iva_generado_5,
        "iva_generado_total": iva_generado,
        "iva_descontable_19": iva_descontable_19,
        "iva_descontable_5": iva_descontable_5,
        "iva_descontable_total": iva_descontable,
        "iva_retenido_a_favor": iva_retenido_a_favor,
        "saldo_favor_anterior": saldo_favor_anterior,
        "impuesto_cargo": max(0, saldo_bruto),
        "saldo_favor": abs(min(0, saldo_bruto)),
    }


# ─── Periodos de declaración IVA ─────────────────────────────────────────────
def get_periodo_iva(tipo: str = "BIMESTRAL") -> list:
    """Retorna los periodos de declaración según tipo de contribuyente"""
    if tipo == "BIMESTRAL":  # Grandes contribuyentes y responsables período cuota
        return [
            (1, "Enero-Febrero"),
            (2, "Marzo-Abril"),
            (3, "Mayo-Junio"),
            (4, "Julio-Agosto"),
            (5, "Septiembre-Octubre"),
            (6, "Noviembre-Diciembre"),
        ]
    elif tipo == "CUATRIMESTRAL":  # Pequeños contribuyentes
        return [
            (1, "Enero-Abril"),
            (2, "Mayo-Agosto"),
            (3, "Septiembre-Diciembre"),
        ]
    else:  # ANUAL - régimen SIMPLE
        return [(1, "Año completo")]


# ─── Formularios DIAN ─────────────────────────────────────────────────────────
FORMULARIOS_DIAN = {
    "F300": "Declaración IVA Bimestral",
    "F310": "Declaración IVA Cuatrimestral",
    "F350": "Declaración Retención en la Fuente",
    "F490": "Recibo de Pago",
    "F110": "Declaración Renta Personas Jurídicas",
    "F210": "Declaración Renta Personas Naturales",
    "F220": "Certificado Ingresos y Retenciones",
    "F1001": "Información Exógena - Pagos o abonos en cuenta",
    "F1002": "Información Exógena - Retenciones",
    "F1004": "Información Exógena - Socios y accionistas",
    "F1007": "Información Exógena - Ingresos",
    "F1008": "Información Exógena - Saldos",
    "F2275": "Información Exógena - Empleados",
}

# ─── Códigos de retención (información exógena) ───────────────────────────────
CODIGOS_RETENCION = {
    "1001": "Honorarios y comisiones",
    "1002": "Salarios y pagos laborales",
    "1003": "Comisiones",
    "1004": "Servicios técnicos y mantenimiento",
    "1005": "Servicios generales",
    "1006": "Compras",
    "1007": "Dividendos y participaciones",
    "1008": "Arrendamientos",
    "1009": "Transporte",
    "1010": "Rendimientos financieros",
    "1011": "Enajenación de activos fijos PN",
    "1012": "Ingresos de menores",
    "1013": "Emolumentos eclesiásticos",
    "1014": "Servicios de hotel y restaurante",
    "1015": "Consultorías y contratos de obra",
    "1016": "Otros pagos a personas naturales",
    "1017": "Ingresos a domiciliarios",
    "1018": "Servicios de aseo y vigilancia",
    "1019": "Transporte de carga",
    "1020": "Compras con tarjeta débito/crédito",
    "1040": "Ingresos obtenidos en el exterior",
    "1050": "Loterías, rifas y apuestas",
    "1060": "Premios por concursos",
}
