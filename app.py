import streamlit as st
import pandas as pd

st.set_page_config(page_title="Gestor de Morbilidad - Willian Almenar", layout="wide")

st.title("Gestor de Morbilidad - Willian Almenar")
st.markdown("---")

def procesar_archivo(file):
    if file is not None:
        try:
            # Detectar si es formato antiguo (.xls) o nuevo (.xlsx)
            if file.name.endswith('.xls'):
                df = pd.read_excel(file, engine='xlrd')
            else:
                df = pd.read_excel(file, engine='openpyxl')
            return df
        except Exception as e:
            st.error(f"Error al leer el archivo {file.name}: {e}")
    return None

tab1, tab2 = st.tabs(["Carga de Reportes", "Consolidación"])

with tab1:
    st.header("Carga de archivos (Formatos 2003-2026)")
    col1, col2, col3 = st.columns(3)
    
    file_sispro = col1.file_uploader("Subir Sispro (.xls, .xlsx)", type=['xls', 'xlsx'])
    file_epi12 = col2.file_uploader("Subir EPI12 (.xls, .xlsx)", type=['xls', 'xlsx'])
    file_epi15 = col3.file_uploader("Subir EPI15 (.xls, .xlsx)", type=['xls', 'xlsx'])

    if file_sispro and file_epi12 and file_epi15:
        df_sispro = procesar_archivo(file_sispro)
        st.success("Archivos cargados correctamente.")
        if df_sispro is not None:
            st.write("Vista previa:", df_sispro.head())

st.sidebar.markdown("---")
st.sidebar.markdown("### Aplicación creada por Willian Almenar")
