import streamlit as st
import pandas as pd

st.set_page_config(page_title="Gestor de Morbilidad - Willian Almenar", layout="wide")

st.title("Gestor de Morbilidad - Willian Almenar")
st.markdown("---")

def analizar_archivo(file):
    if file is not None:
        try:
            # Leer dependiendo de la extensión
            if file.name.endswith('.xls'):
                df = pd.read_excel(file, engine='xlrd')
            else:
                df = pd.read_excel(file, engine='openpyxl')
            
            # Devolvemos el dataframe y un pequeño resumen
            resumen = {
                "filas": df.shape[0],
                "columnas": df.shape[1],
                "columnas_nombres": list(df.columns)
            }
            return df, resumen
        except Exception as e:
            return None, str(e)
    return None, None

tab1, tab2 = st.tabs(["Carga y Análisis", "Consolidación"])

with tab1:
    st.header("Carga de archivos")
    col1, col2, col3 = st.columns(3)
    
    file_sispro = col1.file_uploader("Subir Sispro", type=['xls', 'xlsx'])
    file_epi12 = col2.file_uploader("Subir EPI12", type=['xls', 'xlsx'])
    file_epi15 = col3.file_uploader("Subir EPI15", type=['xls', 'xlsx'])

    if file_sispro:
        df, info = analizar_archivo(file_sispro)
        if isinstance(info, dict):
            st.success(f"SISPRO cargado: {info['filas']} registros detectados.")
            st.write("Columnas encontradas:", info['columnas_nombres'])
        else:
            st.error(f"Error en SISPRO: {info}")

    if file_epi12:
        df, info = analizar_archivo(file_epi12)
        if isinstance(info, dict):
            st.success(f"EPI12 cargado: {info['filas']} registros detectados.")
        else:
            st.error(f"Error en EPI12: {info}")

    if file_epi15:
        df, info = analizar_archivo(file_epi15)
        if isinstance(info, dict):
            st.success(f"EPI15 cargado: {info['filas']} registros detectados.")
        else:
            st.error(f"Error en EPI15: {info}")

st.sidebar.markdown("---")
st.sidebar.markdown("### Aplicación creada por Willian Almenar")
