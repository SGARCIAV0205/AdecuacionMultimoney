import streamlit as st
import pandas as pd
import json
import tempfile
import os
import numpy as np

from procesador_variables import procesar_json, generar_xml


# ----------------------------------------------------
# CONFIGURACIÓN DE USUARIO
# ----------------------------------------------------
USERNAME = "MMUser26"
PASSWORD = "MultiM0neY3uR0"


# ----------------------------------------------------
# ESTILO VISUAL BLANCO / NEGRO
# ----------------------------------------------------
st.set_page_config(
    page_title="Procesador JSON Buró → Modelo Ubimia",
    layout="wide"
)

st.markdown("""
<style>

/* Fondo completo blanco */
html, body, [data-testid="stAppViewContainer"], .main {
    background-color: white !important;
}

/* Texto general */
body, p, div, span, label {
    color: black !important;
}

/* Botones normales */
.stButton button {
    background-color: black !important;
    color: white !important;
    border-radius: 6px;
    border: none;
}

/* Texto dentro del botón */
.stButton button p {
    color: white !important;
}

/* Botones de descarga */
.stDownloadButton button {
    background-color: black !important;
    color: white !important;
    border-radius: 6px;
    border: none;
}

.stDownloadButton button p {
    color: white !important;
}

/* File uploader */
[data-testid="stFileUploader"] section {
    background-color: white;
    border: 2px solid black;
}

/* Botón Browse */
[data-testid="stFileUploader"] button {
    background-color: black !important;
    color: white !important;
}

[data-testid="stFileUploader"] button p {
    color: white !important;
}

/* Barra progreso */
[data-testid="stProgressBar"] > div > div {
    background-color: black;
}

/* Tabla */
[data-testid="stDataFrame"] {
    background-color: white;
}

</style>
""", unsafe_allow_html=True)


st.markdown("""
<style>

html, body, [class*="css"] {
    font-family: Arial, Helvetica, sans-serif;
}

h1, h2, h3 {
    color: black;
}

.stButton>button {
    background-color: black;
    color: white;
    border-radius: 6px;
}

.stDownloadButton>button {
    background-color: black;
    color: white;
}

.block-container {
    padding-top: 2rem;
}

</style>
""", unsafe_allow_html=True)


# ----------------------------------------------------
# LOGIN
# ----------------------------------------------------
def login():

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    st.image("logo_chico.jpg", width=180)

    st.title("Acceso a Procesador JSON Buró")

    user = st.text_input("Usuario")
    pwd = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):

        if user == USERNAME and pwd == PASSWORD:
            st.session_state.authenticated = True
            st.rerun()

        else:
            st.error("Usuario o contraseña incorrectos")

    return False


# ----------------------------------------------------
# CONTROL DE ACCESO
# ----------------------------------------------------
if not login():
    st.stop()


# ----------------------------------------------------
# HEADER PRINCIPAL
# ----------------------------------------------------
col1, col2 = st.columns([1,6])

with col1:
    st.image("logo_chico.jpg", width=120)

with col2:
    st.title("Procesador de JSON Buró de Crédito")


st.markdown("""
Procesador de archivos JSON provenientes de consultas  de **Buró de Crédito** para la extracción exclusiva de las variables requeridas para el **Modelo Genérico de Buró creado por Ubimia**.
""")

st.divider()


# ----------------------------------------------------
# CARGA DE ARCHIVOS
# ----------------------------------------------------
st.subheader("Configuración")

# Campo para IDSOLICITUD
id_solicitud_input = st.text_input(
    "IDSOLICITUD (opcional)",
    help="ID de solicitud externo que se usará en GMR_IDELEMENTO para trazabilidad. Si no se proporciona, se usará el IDCLIENTE del Buró."
)

st.divider()

uploaded_files = st.file_uploader(
    "Cargar uno o varios archivos JSON",
    type=["json"],
    accept_multiple_files=True
)


# ----------------------------------------------------
# PROCESAMIENTO
# ----------------------------------------------------
if uploaded_files:

    resultados = []
    warnings_global = []

    progress = st.progress(0)
    total = len(uploaded_files)
    
    # Preparar IDSOLICITUD si fue proporcionado
    id_solicitud_externo = id_solicitud_input.strip() if id_solicitud_input else None

    for i, uploaded_file in enumerate(uploaded_files):

        try:

            with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

            output = procesar_json(tmp_path, id_solicitud_externo)

            if isinstance(output, tuple):
                resultado, warnings = output
            else:
                resultado = output
                warnings = []

            resultado["archivo_origen"] = uploaded_file.name

            resultados.append(resultado)

            for w in warnings:
                warnings_global.append(f"{uploaded_file.name}: {w}")

            os.remove(tmp_path)

        except Exception as e:
            st.error(f"Error procesando {uploaded_file.name}: {e}")

        progress.progress((i + 1) / total)


    if resultados:

        df = pd.DataFrame(resultados)

        st.success("Procesamiento completado correctamente.")

        st.subheader("Vista previa")

        st.dataframe(df, use_container_width=True)

        st.divider()


        # ----------------------------------------------------
        # ADVERTENCIAS
        # ----------------------------------------------------
        if warnings_global:

            st.subheader("Advertencias detectadas")

            for w in warnings_global:
                st.warning(w)


        st.divider()


        # ----------------------------------------------------
        # DESCARGA CSV
        # ----------------------------------------------------
        csv = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Descargar CSV",
            data=csv,
            file_name="output_modelo_multimoney.csv",
            mime="text/csv"
        )


        # ----------------------------------------------------
        # DESCARGA XML
        # ----------------------------------------------------
        # Generar XML para cada resultado
        xml_outputs = []
        for resultado in resultados:
            # Remover el campo archivo_origen antes de generar XML
            datos_xml = {k: v for k, v in resultado.items() if k != "archivo_origen"}
            xml_outputs.append(generar_xml(datos_xml))
        
        # Si hay múltiples archivos, combinar los XMLs
        if len(xml_outputs) == 1:
            xml_final = xml_outputs[0]
        else:
            # Para múltiples archivos, crear un XML con múltiples GMR_DATA
            xml_final = "<GMR_DATALIST>\n"
            for xml_str in xml_outputs:
                # Extraer solo el contenido GMR_DATA de cada XML
                import re
                match = re.search(r'<GMR_DATA>.*?</GMR_DATA>', xml_str, re.DOTALL)
                if match:
                    xml_final += "  " + match.group(0).replace("\n", "\n  ") + "\n"
            xml_final += "</GMR_DATALIST>"

        st.download_button(
            label="Descargar XML",
            data=xml_final,
            file_name="output_modelo_multimoney.xml",
            mime="application/xml"
        )


else:

    st.info("Cargue uno o más archivos JSON para comenzar.")
