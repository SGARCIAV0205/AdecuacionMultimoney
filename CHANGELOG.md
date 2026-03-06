# Registro de Cambios - Procesador de Variables Buró

## Versión 2.0 - Marzo 2026

### Nuevas Funcionalidades

#### 1. Formato de Salida XML
- ✅ Cambio de formato JSON a XML (GMR_DATALIST)
- ✅ Estructura compatible con modelo de scoring
- ✅ Header GMR con metadatos estándar
- ✅ Sección ClienteIn con variables del modelo

#### 2. Identificadores de Trazabilidad
- ✅ **IDCLIENTE**: Extraído del `numeroControlConsulta` del Buró
- ✅ **IDSOLICITUD**: Parámetro opcional para trazabilidad personalizada
- ✅ GMR_IDELEMENTO usa IDSOLICITUD (si existe) o IDCLIENTE

#### 3. Nomenclatura de Variables Actualizada
- ✅ `id_solicitud` → `IDCLIENTE`
- ✅ `FECHA` → `FECHAREPORTE`
- ✅ `PEOR_HIST_1` a `PEOR_HIST_24` → `PEORHIST01` a `PEORHIST24`

#### 4. Sistema de Validación y Advertencias
- ✅ Filtrado automático de variables sin información válida
- ✅ Advertencias específicas por variable excluida
- ✅ Validación de `numeroControlConsulta`
- ✅ Advertencias para JSON sin cuentas o consultas

#### 5. Interfaz de Línea de Comandos
- ✅ Argumentos para especificar archivos de entrada/salida
- ✅ Parámetro `--idsolicitud` para trazabilidad
- ✅ Ayuda integrada (`--help`)
- ✅ Mensajes informativos de procesamiento

#### 6. Aplicación Web Mejorada
- ✅ Campo de entrada para IDSOLICITUD
- ✅ Descarga de XML en lugar de JSON
- ✅ Visualización de advertencias
- ✅ Soporte para múltiples archivos

### Mejoras Técnicas

#### Procesamiento de Datos
- Validación robusta de tipos de datos
- Manejo de valores NaN y nulos
- Formateo correcto de números en XML
- Normalización de fechas a formato YYYYMMDD

#### Documentación
- README.md actualizado con ejemplos completos
- GUIA_RAPIDA.md para referencia rápida
- Notebook con documentación detallada
- Comentarios en código mejorados

### Archivos Modificados

```
procesador_variables.py      - Script principal con CLI
procesador_variables.ipynb   - Notebook con documentación
app.py                       - Aplicación web Streamlit
README.md                    - Documentación principal
GUIA_RAPIDA.md              - Guía de uso rápido
CHANGELOG.md                - Este archivo
```

### Compatibilidad

- Python 3.7+
- Dependencias: numpy, pandas, streamlit, xml.etree.ElementTree
- Compatible con formato JSON del Buró de Crédito (API Reporte de Crédito)

### Ejemplos de Uso

#### Script
```bash
# Básico
python procesador_variables.py

# Con IDSOLICITUD
python procesador_variables.py --idsolicitud "SOL-2026-001"

# Personalizado
python procesador_variables.py -i input.json -o output.xml -id "CLI-123"
```

#### Aplicación Web
```bash
streamlit run app.py
```

### Notas de Migración

Si estabas usando la versión anterior (JSON):
1. La salida ahora es XML en lugar de JSON
2. Los nombres de variables han cambiado (ver sección 3)
3. Usa el parámetro `--idsolicitud` para trazabilidad adicional
4. Las variables sin datos ya no aparecen en la salida

### Próximas Mejoras Planificadas

- [ ] Validación de esquema XML
- [ ] Soporte para múltiples formatos de entrada
- [ ] API REST para procesamiento
- [ ] Dashboard de monitoreo
- [ ] Exportación a otros formatos (CSV mejorado, Excel)

---

**Fecha de Actualización**: Marzo 5, 2026
**Autor**: Equipo de Desarrollo Multimoney
