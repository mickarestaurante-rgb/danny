#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cálculos de Nómina Colombia 2026
Según legislación laboral vigente y Código Sustantivo del Trabajo
"""
import math


# ─── Parámetros 2026 (actualizable) ──────────────────────────────────────────
SMLV_2026 = 1_600_000        # Salario Mínimo Legal Vigente 2026 (estimado)
AUXILIO_TRANSPORTE_2026 = 202_000   # Auxilio de transporte 2026 (estimado)
SMLV_2025 = 1_423_500
AUXILIO_TRANSPORTE_2025 = 179_013
UVT_2026 = 49_799

# Tasas de aportes (%)
SALUD_EMPLEADO = 0.04        # 4%
PENSION_EMPLEADO = 0.04      # 4%
SALUD_EMPRESA = 0.085        # 8.5%
PENSION_EMPRESA = 0.12       # 12%
CAJA_COMPENSACION = 0.04     # 4%
SENA = 0.02                  # 2%
ICBF = 0.03                  # 3%

# Recargos horas extra
FACTOR_HED = 0.25    # Hora extra diurna: 25% adicional
FACTOR_HEN = 0.75    # Hora extra nocturna: 75% adicional
FACTOR_HRN = 0.35    # Hora recargo nocturno: 35% adicional
FACTOR_HEF = 1.0     # Hora extra festiva diurna: 100% adicional
FACTOR_HEFN = 1.5    # Hora extra festiva nocturna: 150% adicional
FACTOR_HTD = 0.75    # Hora trabajo dominical/festivo diurno: 75% adicional
FACTOR_HTN = 1.10    # Hora trabajo dominical/festivo nocturno: 110% adicional

# Prestaciones sociales
PRIMA_FACTOR = 1/12           # Prima: 1 mes por año = 8.33% mensual
CESANTIAS_FACTOR = 1/12       # Cesantías: 1 mes por año = 8.33% mensual
INT_CESANTIAS_FACTOR = 0.12   # Intereses sobre cesantías: 12% anual
VACACIONES_FACTOR = 15/360    # Vacaciones: 15 días hábiles / 360 días


def get_params(anio=2026):
    """Retorna parámetros del año"""
    if anio >= 2026:
        return {
            "smlv": SMLV_2026,
            "auxilio_transporte": AUXILIO_TRANSPORTE_2026,
            "uvt": UVT_2026
        }
    return {
        "smlv": SMLV_2025,
        "auxilio_transporte": AUXILIO_TRANSPORTE_2025,
        "uvt": UVT_2026
    }


def calcular_nomina_empleado(
    salario_basico: float,
    dias_trabajados: int = 30,
    auxilio_transporte: bool = True,
    horas_extra_diurnas: float = 0,
    horas_extra_nocturnas: float = 0,
    horas_extra_dominicales: float = 0,
    recargo_nocturno_horas: float = 0,
    comisiones: float = 0,
    bonificaciones: float = 0,
    otros_devengados: float = 0,
    incapacidad_dias: int = 0,
    licencia_remunerada: float = 0,
    prestamo: float = 0,
    libranza: float = 0,
    otras_deducciones: float = 0,
    nivel_riesgo: int = 1,
    anio: int = 2026,
    exonerado_parafiscales: bool = None
) -> dict:
    """
    Calcula la nómina completa de un empleado según la ley colombiana.

    Exoneración parafiscales: empresas cuyo empleado gana <= 10 SMLV
    quedan exoneradas de SENA e ICBF (Ley 1607/2012, Art. 25)
    """
    params = get_params(anio)
    smlv = params["smlv"]
    aux_transporte = params["auxilio_transporte"]

    # ── DEVENGADO ─────────────────────────────────────────────────────────────
    # Salario proporcional a días trabajados
    salario_proporcional = round(salario_basico * dias_trabajados / 30)

    # Auxilio de transporte (solo si salario <= 2 SMLV)
    aux_trans_valor = 0.0
    if auxilio_transporte and salario_basico <= (2 * smlv):
        aux_trans_valor = round(aux_transporte * dias_trabajados / 30)

    # Valor hora ordinaria
    valor_hora = salario_basico / 240  # 30 días * 8 horas

    # Horas extra
    val_hed = round(horas_extra_diurnas * valor_hora * (1 + FACTOR_HED))
    val_hen = round(horas_extra_nocturnas * valor_hora * (1 + FACTOR_HEN))
    val_hef = round(horas_extra_dominicales * valor_hora * (1 + FACTOR_HEF))
    val_hrn = round(recargo_nocturno_horas * valor_hora * FACTOR_HRN)

    total_devengado = (
        salario_proporcional + aux_trans_valor +
        val_hed + val_hen + val_hef + val_hrn +
        comisiones + bonificaciones + otros_devengados + licencia_remunerada
    )

    # ── DEDUCCIONES ───────────────────────────────────────────────────────────
    # Base para aportes (sin auxilio de transporte)
    base_aportes = (
        salario_proporcional + val_hed + val_hen + val_hef + val_hrn +
        comisiones + bonificaciones + otros_devengados + licencia_remunerada
    )

    salud_empleado = round(base_aportes * SALUD_EMPLEADO)
    pension_empleado = round(base_aportes * PENSION_EMPLEADO)

    # Fondo de Solidaridad Pensional (FSP)
    # Aplica cuando salario >= 4 SMLV
    fsp = 0.0
    if salario_basico >= 4 * smlv:
        fsp_pct = 0.01
        if salario_basico >= 16 * smlv:
            fsp_pct = 0.012
        elif salario_basico >= 17 * smlv:
            fsp_pct = 0.014
        elif salario_basico >= 18 * smlv:
            fsp_pct = 0.016
        elif salario_basico >= 19 * smlv:
            fsp_pct = 0.018
        elif salario_basico >= 20 * smlv:
            fsp_pct = 0.02
        fsp = round(base_aportes * fsp_pct)

    total_deducciones = (
        salud_empleado + pension_empleado + fsp +
        prestamo + libranza + otras_deducciones
    )

    neto_pagar = total_devengado - total_deducciones

    # ── APORTES EMPRESA ───────────────────────────────────────────────────────
    salud_empresa = round(base_aportes * SALUD_EMPRESA)
    pension_empresa = round(base_aportes * PENSION_EMPRESA)

    # ARL según nivel de riesgo
    tasas_arl = {1: 0.00522, 2: 0.01044, 3: 0.02436, 4: 0.04350, 5: 0.06960}
    tasa_arl = tasas_arl.get(nivel_riesgo, 0.00522)
    arl = round(base_aportes * tasa_arl)

    caja_comp = round(base_aportes * CAJA_COMPENSACION)

    # Exoneración SENA e ICBF (Ley 1607/2012)
    # Empresas con empleados que ganan <= 10 SMLV quedan exoneradas
    if exonerado_parafiscales is None:
        exonerado = salario_basico <= (10 * smlv)
    else:
        exonerado = exonerado_parafiscales

    sena_valor = 0.0 if exonerado else round(base_aportes * SENA)
    icbf_valor = 0.0 if exonerado else round(base_aportes * ICBF)

    total_aportes_empresa = (
        salud_empresa + pension_empresa + arl +
        caja_comp + sena_valor + icbf_valor
    )

    # ── PROVISIONES PRESTACIONES ──────────────────────────────────────────────
    # Base para prestaciones (salario + auxilio de transporte)
    base_prest = salario_proporcional + aux_trans_valor

    prima_prop = round(base_prest * PRIMA_FACTOR)
    cesantias_prop = round(base_prest * CESANTIAS_FACTOR)
    int_cesantias_prop = round(cesantias_prop * INT_CESANTIAS_FACTOR / 12)
    vacaciones_prop = round(salario_proporcional * VACACIONES_FACTOR)

    return {
        "salario_basico": salario_basico,
        "salario_proporcional": salario_proporcional,
        "dias_trabajados": dias_trabajados,
        "auxilio_transporte": aux_trans_valor,
        "horas_extras_diurnas_val": val_hed,
        "horas_extras_nocturnas_val": val_hen,
        "horas_extras_dominicales_val": val_hef,
        "recargo_nocturno_val": val_hrn,
        "comisiones": comisiones,
        "bonificaciones": bonificaciones,
        "otros_devengados": otros_devengados,
        "licencia_remunerada": licencia_remunerada,
        "total_devengado": total_devengado,
        # Deducciones
        "salud_empleado": salud_empleado,
        "pension_empleado": pension_empleado,
        "fondo_solidaridad": fsp,
        "prestamo": prestamo,
        "libranza": libranza,
        "otras_deducciones": otras_deducciones,
        "retencion_fuente_nomina": 0,  # se calcula aparte
        "total_deducciones": total_deducciones,
        "neto_pagar": neto_pagar,
        # Aportes empresa
        "salud_empresa": salud_empresa,
        "pension_empresa": pension_empresa,
        "arl_empresa": arl,
        "caja_compensacion": caja_comp,
        "sena": sena_valor,
        "icbf": icbf_valor,
        "total_aportes_empresa": total_aportes_empresa,
        # Provisiones prestaciones
        "prima_proporcional": prima_prop,
        "cesantias_proporcional": cesantias_prop,
        "intereses_cesantias_prop": int_cesantias_prop,
        "vacaciones_proporcional": vacaciones_prop,
        "costo_total_empresa": total_devengado - salud_empleado - pension_empleado - fsp + total_aportes_empresa,
    }


def calcular_prima_servicios(salario_basico: float, aux_transporte: float,
                              dias_trabajados: int, anio: int = 2026) -> float:
    """Prima de servicios: 15 días de salario por semestre"""
    base = salario_basico + aux_transporte
    return round(base * dias_trabajados / 360)


def calcular_cesantias(salario_basico: float, aux_transporte: float,
                       dias_trabajados: int) -> float:
    """Cesantías: 1 mes de salario por año"""
    base = salario_basico + aux_transporte
    return round(base * dias_trabajados / 360)


def calcular_intereses_cesantias(cesantias: float, dias: int = 360) -> float:
    """Intereses sobre cesantías: 12% anual"""
    return round(cesantias * 0.12 * dias / 360)


def calcular_vacaciones(salario_basico: float, dias_trabajados: int) -> float:
    """Vacaciones: 15 días hábiles por año (solo sobre salario básico)"""
    return round(salario_basico * dias_trabajados / 720)


def calcular_liquidacion_definitiva(
    salario_basico: float,
    fecha_ingreso: str,
    fecha_retiro: str,
    aux_transporte_aplica: bool = True,
    cesantias_acumuladas: float = 0,
    vacaciones_acumuladas: float = 0,
    anio: int = 2026
) -> dict:
    """
    Calcula la liquidación definitiva al retiro del empleado.
    """
    from datetime import datetime, date
    params = get_params(anio)
    smlv = params["smlv"]
    aux_trans = params["auxilio_transporte"] if aux_transporte_aplica and salario_basico <= 2 * smlv else 0

    fi = datetime.strptime(fecha_ingreso, "%Y-%m-%d").date()
    fr = datetime.strptime(fecha_retiro, "%Y-%m-%d").date()
    delta = fr - fi
    dias_totales = delta.days
    anios = dias_totales / 365
    dias_ultimo_anio = dias_totales % 365

    # Cesantías pendientes
    cesantias = round((salario_basico + aux_trans) * dias_ultimo_anio / 360)
    int_ces = round(cesantias * 0.12 * (dias_ultimo_anio / 360))

    # Prima pendiente (de 1 de julio al retiro, si es 2do semestre)
    prima = round((salario_basico + aux_trans) * dias_ultimo_anio / 360)

    # Vacaciones pendientes (días no disfrutados)
    dias_vac = round(15 * dias_ultimo_anio / 360)
    vac_valor = round(salario_basico * dias_vac / 30)

    total = cesantias + int_ces + prima + vac_valor

    return {
        "dias_laborados_ultimo_periodo": dias_ultimo_anio,
        "cesantias": cesantias,
        "intereses_cesantias": int_ces,
        "prima_servicios": prima,
        "vacaciones": vac_valor,
        "dias_vacaciones": dias_vac,
        "total_liquidacion": total,
    }


# ─── Tabla de retención en la fuente sobre salarios (UVT 2026) ───────────────
# Procedimiento 2 (simplificado, Art. 386 ET)
def calcular_retencion_salario(
    salario_mensual: float,
    deduccion_dependientes: bool = False,
    cesantias_intereses: float = 0,
    medicina_prepagada: float = 0,
    uvt: float = UVT_2026
) -> float:
    """
    Cálculo de retención en la fuente sobre salarios (Procedimiento 1).
    Tabla progresiva según el Art. 383 E.T.
    """
    # Deducciones permitidas
    deduccion_dep = salario_mensual * 0.10 if deduccion_dependientes else 0
    renta_exenta_laboral = salario_mensual * 0.25  # 25% renta exenta laboral, max 240 UVT/mes

    max_renta_exenta = 240 * uvt / 12  # mensual
    renta_exenta_laboral = min(renta_exenta_laboral, max_renta_exenta)

    base_retencion = (salario_mensual - deduccion_dep -
                      cesantias_intereses - medicina_prepagada -
                      renta_exenta_laboral)
    base_retencion = max(0, base_retencion)

    # Convertir base a UVT mensuales
    base_uvt = base_retencion / uvt * 12  # anualizar para tabla

    # Tabla Art. 383 ET (rangos en UVT anuales)
    # Rango: desde - hasta | tarifa marginal | UVT a deducir
    tabla = [
        (0, 1090, 0, 0),
        (1090, 1700, 0.19, 1090),
        (1700, 4100, 0.28, 1700),
        (4100, 8670, 0.33, 4100),
        (8670, 18970, 0.35, 8670),
        (18970, 31000, 0.37, 18970),
        (31000, float("inf"), 0.39, 31000),
    ]

    retencion_anual_uvt = 0
    for desde, hasta, tarifa, deduccion_tabla in tabla:
        if base_uvt > desde:
            exceso = min(base_uvt, hasta) - desde
            if tarifa == 0 and desde == 0:
                retencion_anual_uvt = 0
            else:
                # Tabla simplificada: retención = (base - limite_inf) * tarifa + monto_fijo
                rango_anterior = sum(
                    (t[1] - t[0]) * t[2] for t in tabla if t[0] < desde and t[2] > 0
                )
                retencion_anual_uvt = (base_uvt - deduccion_tabla) * tarifa
                break

    # Convertir a valor mensual en pesos
    retencion_mensual = round((retencion_anual_uvt * uvt) / 12)
    return max(0, retencion_mensual)
