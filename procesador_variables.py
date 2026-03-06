import json
import re
import numpy as np
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom

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


def obtener_id_consulta(json_data, warnings):

    try:
        id_consulta = json_data["respuesta"]["persona"]["encabezado"].get("numeroControlConsulta")
        
        if id_consulta is None or id_consulta == "":
            warnings.append("No se encontró 'numeroControlConsulta' en el JSON. Se usará 'id_no_disponible' como identificador")
            return "id_no_disponible"
        
        return id_consulta

    except:
        warnings.append("Error al acceder a 'numeroControlConsulta' en el JSON. Se usará 'id_no_disponible' como identificador")
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


def procesar_json(path_json, id_solicitud_externo=None):

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

    id_cliente = obtener_id_consulta(data, warnings)

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

        if tipo in TDC:

            SALDOACTTDC = np.nansum([SALDOACTTDC, saldoActual])
            LIMITECREDITO = np.nansum([LIMITECREDITO, limiteCredito])

    # Preparar todas las variables con sus valores
    variables_completas = {
        "IDCLIENTE": id_solicitud_externo if id_solicitud_externo else "imputado_no_disponible",
        "CREDMAXAUTCONS": CREDMAXAUTCONS,
        "MONTOPAGARCONS": MONTOPAGARCONS,
        "SALDOACTCONS": SALDOACTCONS,
        "CREDMAXAUTREV": CREDMAXAUTREV,
        "SALDOACTREV": SALDOACTREV,
        "LIMITECREDITO": LIMITECREDITO,
        "SALDOACTTDC": SALDOACTTDC,
        "CREDMAXAUTTOTAL": CREDMAXAUTTOTAL,
        "SALDOVENCTOTAL": SALDOVENCTOTAL,
        "FECHAREPORTE": normalizar_fecha(resumen.get("fechaSolicitudReporteMasReciente")),
        "FECHAULTCONSULTA": fecha_ult_consulta(consultas),
        "PEORMOP": peor_mop(cuentas)
    }

    # Agregar PEORHIST01 a PEORHIST24
    peor_hist = calcular_peor_historico_1_24(cuentas)
    for i in range(1, 25):
        old_key = f"PEOR_HIST_{i}"
        new_key = f"PEORHIST{i:02d}"
        variables_completas[new_key] = peor_hist.get(old_key, np.nan)

    # Filtrar variables: solo incluir las que tienen información válida
    resultado = {}
    
    for variable, valor in variables_completas.items():
        # Siempre incluir IDCLIENTE
        if variable == "IDCLIENTE":
            resultado[variable] = valor
        # Para el resto, verificar si tiene información válida
        elif isinstance(valor, (int, float)) and not np.isnan(valor):
            resultado[variable] = valor
        elif isinstance(valor, str) and valor != "":
            resultado[variable] = valor
        else:
            # Generar advertencia para variables sin información
            warnings.append(f"Variable '{variable}' no tiene información disponible y no será incluida en la salida")

    # Agregar GMR_NUMERO_CONTROL (numeroControlConsulta) para GMR_IDELEMENTO
    resultado["GMR_NUMERO_CONTROL"] = id_cliente
    
    # Agregar IDSOLICITUD si fue proporcionado
    if id_solicitud_externo:
        resultado["IDSOLICITUD"] = id_solicitud_externo

    return resultado, warnings


def generar_xml(datos):
    """
    Genera XML en el formato GMR_DATALIST requerido
    """
    # Crear estructura raíz
    root = ET.Element("GMR_DATALIST")
    gmr_data = ET.SubElement(root, "GMR_DATA")
    
    # Header
    gmr_header = ET.SubElement(gmr_data, "GMR_HEADER")
    ET.SubElement(gmr_header, "GMR_FLOW").text = "1"
    ET.SubElement(gmr_header, "GMR_VERSION").text = "0"
    ET.SubElement(gmr_header, "GMR_RESERVED").text = "00"
    ET.SubElement(gmr_header, "GMR_LEVELS").text = "1"
    
    # GMR_IDELEMENTO: usar numeroControlConsulta del Buró
    # Necesitamos agregar id_cliente (numeroControlConsulta) a los datos
    gmr_idelemento = datos.get("GMR_NUMERO_CONTROL", "0")
    ET.SubElement(gmr_header, "GMR_IDELEMENTO").text = str(gmr_idelemento)
    
    # ClienteIn con los datos
    cliente_in = ET.SubElement(gmr_data, "ClienteIn")
    
    # Orden específico de las variables según el formato requerido
    orden_variables = [
        "IDCLIENTE", "CREDMAXAUTCONS", "MONTOPAGARCONS", "SALDOACTCONS",
        "CREDMAXAUTREV", "SALDOACTREV", "LIMITECREDITO", "SALDOACTTDC",
        "CREDMAXAUTTOTAL", "SALDOVENCTOTAL", "FECHAREPORTE", "FECHAULTCONSULTA",
        "PEORMOP"
    ]
    
    # Agregar PEORHIST01 a PEORHIST24
    for i in range(1, 25):
        orden_variables.append(f"PEORHIST{i:02d}")
    
    # Agregar elementos en orden (IDSOLICITUD no se incluye en ClienteIn, solo en GMR_IDELEMENTO)
    for variable in orden_variables:
        if variable in datos:
            valor = datos[variable]
            # Formatear valores numéricos
            if isinstance(valor, float):
                # Si es entero, mostrar sin decimales
                if valor.is_integer():
                    valor_str = str(int(valor))
                else:
                    valor_str = f"{valor:.2f}"
            else:
                valor_str = str(valor)
            
            ET.SubElement(cliente_in, variable).text = valor_str
    
    # Convertir a string con formato bonito
    xml_str = minidom.parseString(ET.tostring(root, encoding='unicode')).toprettyxml(indent="  ")
    
    # Eliminar la declaración XML si existe y líneas vacías
    lines = [line for line in xml_str.split('\n') if line.strip()]
    if lines and lines[0].startswith('<?xml'):
        lines = lines[1:]
    
    return '\n'.join(lines)


# Ejecución de prueba
if __name__ == "__main__":
    import sys
    import argparse
    
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description='Procesador de JSON Buró de Crédito a XML')
    parser.add_argument('--input', '-i', default="json/RCO_Int_007_Hawk_Response.json",
                        help='Ruta del archivo JSON de entrada')
    parser.add_argument('--output', '-o', default="entradaWSubimia.xml",
                        help='Ruta del archivo XML de salida')
    parser.add_argument('--idsolicitud', '-id', default=None,
                        help='ID de solicitud externo para GMR_IDELEMENTO (opcional)')
    
    args = parser.parse_args()
    
    input_path = args.input
    output_path = args.output
    id_solicitud_externo = args.idsolicitud
    
    try:
        resultado, warnings = procesar_json(input_path, id_solicitud_externo)
        
        # Mostrar advertencias si existen
        if warnings:
            print("\n=== ADVERTENCIAS ===")
            for w in warnings:
                print(f"⚠ {w}")
            print()
        
        # Generar XML
        xml_output = generar_xml(resultado)
        
        # Guardar resultado
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(xml_output)
        
        print(f"✓ Procesamiento completado exitosamente")
        print(f"✓ Variables incluidas en la salida: {len(resultado)}")
        if id_solicitud_externo:
            print(f"✓ IDSOLICITUD (GMR_IDELEMENTO): {id_solicitud_externo}")
        else:
            print(f"✓ GMR_IDELEMENTO: {resultado.get('IDCLIENTE', 'N/A')}")
        print(f"✓ Archivo guardado en: {output_path}")
        
    except Exception as e:
        print(f"✗ Error al procesar: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
