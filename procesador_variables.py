import json
import hashlib
import re
import numpy as np
from datetime import datetime

# Configuración Anexo 3
CONSUMO = ["AN", "AG", "AL", "AP", "AU", "BD", "BT", "CE", "CF", "CO", "CS", "CT", "DE", "EQ"
           , "FI", "FT", "HA", "HE", "HI", "LS", "MI", "OA", "PA", "PB", "PG", "PL","PN", "PQ",
           "PR", "PS", "RC", "RD", "RE", "RF", "RN", "RV", "SE", "SG", "SM", "ST", "UK", "US"]
REVOLVENTE = ["CL", "LR"]
TDC = ["CC", "SC", "TE"]

# Funciones y Utilidades
def limpiar_numero(valor):

    if valor is None or valor == "":
        return np.nan

    valor = str(valor).replace("+", "").strip()

    try:
        return int(valor)
    except:
        return np.nan


def normalizar_fecha(fecha):

    """
    Convierte fechas a formato YYYYMMDD.
    Si no puede interpretarse, devuelve NaN.
    """

    if fecha is None or fecha == "":
        return np.nan

    fecha = str(fecha)

    formatos = [
        "%d%m%Y",
        "%Y%m%d",
        "%Y-%m-%d",
        "%d-%m-%Y"
    ]

    for f in formatos:
        try:
            return datetime.strptime(fecha, f).strftime("%Y%m%d")
        except:
            pass

    return np.nan


def generar_id_anonimo(json_data):

    try:
        base = json_data["respuesta"]["persona"]["encabezado"].get(
            "numeroReferenciaOperador", ""
        )
        return hashlib.sha256(base.encode()).hexdigest()[:16]

    except:
        return "id_no_disponible"


def cargar_json_seguro(path_json):

    with open(path_json, "r", encoding="utf-8") as f:
        contenido = f.read()

    try:
        return json.loads(contenido)

    except json.JSONDecodeError:

        contenido = re.sub(
            r'("valorScore"\s*:\s*"\d+")\s*("codigoRazon")',
            r'\1,\2',
            contenido
        )

        return json.loads(contenido)


def peor_mop(cuentas):

    peor = np.nan

    for c in cuentas:

        for campo in ["formaPagoActual", "mopHistoricoMorosidadMasGrave"]:

            mop = c.get(campo)

            if mop and str(mop).isdigit():

                mop = int(mop)

                if np.isnan(peor) or mop > peor:
                    peor = mop

    return peor


def fecha_ult_consulta(consultas):

    fechas = []

    for c in consultas:

        fecha = c.get("fechaConsulta")

        if fecha:
            try:
                fechas.append(datetime.strptime(str(fecha), "%d%m%Y"))
            except:
                try:
                    fechas.append(datetime.strptime(str(fecha), "%Y%m%d"))
                except:
                    pass

    if fechas:
        return max(fechas).strftime("%Y%m%d")

    return np.nan


def calcular_peor_historico_1_24(cuentas):

    peor_por_mes = [np.nan] * 24

    for c in cuentas:

        hist = str(c.get("historicoPagos", ""))

        if hist == "":
            continue

        ultimos_24 = hist[-24:].rjust(24, "0")

        for i in range(24):

            ch = ultimos_24[-(i + 1)]

            if ch.isdigit():

                ch = int(ch)

                if np.isnan(peor_por_mes[i]) or ch > peor_por_mes[i]:
                    peor_por_mes[i] = ch

    resultado = {}

    for i in range(24):
        resultado[f"PEOR_HIST_{i+1}"] = peor_por_mes[i]

    return resultado


def procesar_json(path_json):

    warnings = []

    data = cargar_json_seguro(path_json)

    try:
        persona = data["respuesta"]["persona"]
    except:
        raise ValueError("El JSON no contiene la estructura esperada del Buró")

    cuentas = persona.get("cuentas", [])
    consultas = persona.get("consultaEfectuadas", [])
    resumen = persona.get("resumenReporte", [{}])[0]

    if not cuentas:
        warnings.append("El JSON no contiene cuentas reportadas")

    if not consultas:
        warnings.append("El JSON no contiene historial de consultas")

    id_solicitud = generar_id_anonimo(data)

    CREDMAXAUTCONS = np.nan
    MONTOPAGARCONS = np.nan
    SALDOACTCONS = np.nan
    CREDMAXAUTREV = np.nan
    SALDOACTREV = np.nan
    LIMITECREDITO = np.nan
    SALDOACTTDC = np.nan
    CREDMAXAUTTOTAL = np.nan
    SALDOVENCTOTAL = np.nan

    for c in cuentas:

        tipo = c.get("tipoContrato")

        creditoMaximo = limpiar_numero(c.get("creditoMaximo"))
        saldoActual = limpiar_numero(c.get("saldoActual"))
        saldoVencido = limpiar_numero(c.get("saldoVencido"))
        limiteCredito = limpiar_numero(c.get("limiteCredito"))
        montoPagar = limpiar_numero(c.get("montoPagar"))

        if not np.isnan(creditoMaximo):
            CREDMAXAUTTOTAL = np.nansum([CREDMAXAUTTOTAL, creditoMaximo])

        if not np.isnan(saldoVencido):
            SALDOVENCTOTAL = np.nansum([SALDOVENCTOTAL, saldoVencido])

        if tipo in CONSUMO:

            CREDMAXAUTCONS = np.nansum([CREDMAXAUTCONS, creditoMaximo])
            MONTOPAGARCONS = np.nansum([MONTOPAGARCONS, montoPagar])
            SALDOACTCONS = np.nansum([SALDOACTCONS, saldoActual])

        if tipo in REVOLVENTE:

            CREDMAXAUTREV = np.nansum([CREDMAXAUTREV, creditoMaximo])
            SALDOACTREV = np.nansum([SALDOACTREV, saldoActual])
            LIMITECREDITO = np.nansum([LIMITECREDITO, limiteCredito])

        if tipo in TDC:

            SALDOACTTDC = np.nansum([SALDOACTTDC, saldoActual])

    resultado = {
        "id_solicitud": id_solicitud,
        "CREDMAXAUTCONS": CREDMAXAUTCONS,
        "MONTOPAGARCONS": MONTOPAGARCONS,
        "SALDOACTCONS": SALDOACTCONS,
        "CREDMAXAUTREV": CREDMAXAUTREV,
        "SALDOACTREV": SALDOACTREV,
        "LIMITECREDITO": LIMITECREDITO,
        "SALDOACTTDC": SALDOACTTDC,
        "CREDMAXAUTTOTAL": CREDMAXAUTTOTAL,
        "SALDOVENCTOTAL": SALDOVENCTOTAL,
        "FECHA": normalizar_fecha(resumen.get("fechaSolicitudReporteMasReciente")),
        "FECHAULTCONSULTA": fecha_ult_consulta(consultas),
        "PEORMOP": peor_mop(cuentas)
    }

    resultado.update(calcular_peor_historico_1_24(cuentas))

    return resultado, warnings
