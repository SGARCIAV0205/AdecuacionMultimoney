# Procesador de Variables - Modelo Multimoney

## Descripción

Este proyecto procesa archivos JSON provenientes de consultas de Buró de Crédito y extrae las variables definidas como "Entrada 0" para el modelo Multimoney, generando un XML en formato GMR_DATALIST listo para scoring.

El sistema utiliza el `numeroControlConsulta` del Buró como identificador único de cada solicitud.

## Características Principales

### Filtrado Inteligente de Variables
- Las variables sin información válida (valores NaN, vacíos o nulos) NO se incluyen en la salida
- Se generan advertencias específicas para cada variable excluida
- Solo se exportan variables con datos reales y utilizables

### Variables Procesadas

El sistema extrae y procesa las siguientes variables en formato XML:

- **IDCLIENTE**: Identificador único (numeroControlConsulta del Buró)
- **CREDMAXAUTCONS**: Crédito máximo autorizado en consumo
- **MONTOPAGARCONS**: Monto a pagar en consumo
- **SALDOACTCONS**: Saldo actual en consumo
- **CREDMAXAUTREV**: Crédito máximo autorizado revolvente
- **SALDOACTREV**: Saldo actual revolvente
- **LIMITECREDITO**: Límite de crédito
- **SALDOACTTDC**: Saldo actual en tarjetas de crédito
- **CREDMAXAUTTOTAL**: Crédito máximo autorizado total
- **SALDOVENCTOTAL**: Saldo vencido total
- **FECHAREPORTE**: Fecha de solicitud más reciente
- **FECHAULTCONSULTA**: Fecha de última consulta
- **PEORMOP**: Peor MOP (Manner of Payment)
- **PEORHIST01** a **PEORHIST24**: Histórico de pagos por mes

## Uso

### Modo Script (Python)

```bash
# Uso básico (usa IDCLIENTE del Buró en GMR_IDELEMENTO)
python procesador_variables.py

# Con IDSOLICITUD personalizado para trazabilidad
python procesador_variables.py --idsolicitud "SOL-2026-001"

# Especificando archivos de entrada y salida
python procesador_variables.py --input mi_archivo.json --output salida.xml --idsolicitud "SOL-123"
```

Parámetros disponibles:
- `--input` o `-i`: Ruta del archivo JSON de entrada (default: json/RCO_Int_007_Hawk_Response.json)
- `--output` o `-o`: Ruta del archivo XML de salida (default: output_modelo_multimoney.xml)
- `--idsolicitud` o `-id`: ID de solicitud externo para GMR_IDELEMENTO (opcional)

El script generará:
- Archivo de salida XML con el formato GMR_DATALIST
- Advertencias en consola sobre variables excluidas
- Confirmación del IDSOLICITUD o IDCLIENTE usado en GMR_IDELEMENTO

### Modo Aplicación Web (Streamlit)

```bash
streamlit run app.py
```

La aplicación web permite:
- Ingresar un IDSOLICITUD personalizado para trazabilidad
- Cargar múltiples archivos JSON
- Visualizar resultados en tabla
- Ver advertencias de variables faltantes
- Descargar resultados en CSV o XML

El IDSOLICITUD ingresado se usará en el campo GMR_IDELEMENTO del XML para todos los archivos procesados en esa sesión.

## Ejemplo de Salida

### XML generado (sin IDSOLICITUD personalizado):
```xml
<GMR_DATALIST>
  <GMR_DATA>
    <GMR_HEADER>
      <GMR_FLOW>1</GMR_FLOW>
      <GMR_VERSION>0</GMR_VERSION>
      <GMR_RESERVED>00</GMR_RESERVED>
      <GMR_LEVELS>1</GMR_LEVELS>
      <GMR_IDELEMENTO>2424563619</GMR_IDELEMENTO>
    </GMR_HEADER>
    <ClienteIn>
      <IDCLIENTE>2424563619</IDCLIENTE>
      <CREDMAXAUTCONS>1060020</CREDMAXAUTCONS>
      <MONTOPAGARCONS>23730</MONTOPAGARCONS>
      <SALDOACTCONS>596709</SALDOACTCONS>
      <FECHAREPORTE>20260127</FECHAREPORTE>
      <PEORMOP>96</PEORMOP>
      <PEORHIST01>6</PEORHIST01>
      <PEORHIST02>7</PEORHIST02>
      <!-- ... más variables ... -->
    </ClienteIn>
  </GMR_DATA>
</GMR_DATALIST>
```

### XML generado (con IDSOLICITUD personalizado "SOL-2026-001"):
```xml
<GMR_DATALIST>
  <GMR_DATA>
    <GMR_HEADER>
      <GMR_FLOW>1</GMR_FLOW>
      <GMR_VERSION>0</GMR_VERSION>
      <GMR_RESERVED>00</GMR_RESERVED>
      <GMR_LEVELS>1</GMR_LEVELS>
      <GMR_IDELEMENTO>SOL-2026-001</GMR_IDELEMENTO>
    </GMR_HEADER>
    <ClienteIn>
      <IDCLIENTE>2424563619</IDCLIENTE>
      <!-- ... variables ... -->
    </ClienteIn>
  </GMR_DATA>
</GMR_DATALIST>
```

### Advertencias generadas:
```
⚠ No se encontró 'numeroControlConsulta' en el JSON. Se usará 'id_no_disponible' como identificador
⚠ Variable 'CREDMAXAUTREV' no tiene información disponible y no será incluida en la salida
⚠ Variable 'SALDOACTTDC' no tiene información disponible y no será incluida en la salida
⚠ Variable 'FECHAULTCONSULTA' no tiene información disponible y no será incluida en la salida
```

## Instalación

```bash
pip install -r requirements.txt
```

## Estructura del Proyecto

```
.
├── procesador_variables.py    # Script principal de procesamiento
├── procesador_variables.ipynb # Notebook con documentación detallada
├── app.py                      # Aplicación web Streamlit
├── requirements.txt            # Dependencias del proyecto
└── json/                       # Carpeta con archivos JSON de entrada
```

## Metodología de Cálculo

1. **Limpieza de montos**: Eliminación de símbolos y normalización
2. **Agregación por tipo de contrato**: Según Anexo 3 del Manual API Reporte de Crédito
   - **CONSUMO** (AN, AG, AL, AP, AU, etc.): CREDMAXAUTCONS, MONTOPAGARCONS, SALDOACTCONS
   - **REVOLVENTE** (CL, LR): CREDMAXAUTREV, SALDOACTREV
   - **TDC** (CC, SC, TE): SALDOACTTDC, LIMITECREDITO
3. **Cálculo de PEORMOP**: Máximo entre formaPagoActual y mopHistoricoMorosidadMasGrave
4. **Cálculo de PEOR_HIST_1 a 24**: Últimos 24 caracteres de historicoPagos, alineados desde el mes más reciente

## Notas Importantes

- El sistema utiliza el `numeroControlConsulta` del Buró como IDCLIENTE
- Si no se encuentra el `numeroControlConsulta`, se genera una advertencia y se usa "id_no_disponible"
- El campo GMR_IDELEMENTO puede usar:
  - IDSOLICITUD personalizado (si se proporciona como parámetro) para trazabilidad adicional
  - IDCLIENTE del Buró (si no se proporciona IDSOLICITUD)
- Solo se incluyen variables con información válida en el XML
- Las advertencias ayudan a identificar datos faltantes en el JSON de origen
- El IDCLIENTE siempre se incluye en ClienteIn
- La salida es un archivo XML en formato GMR_DATALIST compatible con el modelo de scoring

