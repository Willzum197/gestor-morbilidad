import streamlit as st
import pandas as pd

# Configuración inicial de la página
st.set_page_config(page_title="Gestor de Morbilidad - Willian Almenar", layout="wide")

st.title("Gestor de Morbilidad - Willian Almenar")
st.markdown("---")

# Pestañas de trabajo
tab1, tab2 = st.tabs(["Carga y Validación Individual", "Consolidación General"])

# Función para cargar y limpiar datos
def procesar_archivo(file):
    if file is not None:
        df = pd.read_excel(file)
        return df
    return None

with tab1:
    st.header("1. Carga de Reportes")
    col1, col2, col3 = st.columns(3)
    
    file_sispro = col1.file_uploader("Subir Sispro", type=['xlsx'])
    file_epi12 = col2.file_uploader("Subir EPI12", type=['xlsx'])
    file_epi15 = col3.file_uploader("Subir EPI15", type=['xlsx'])

    if file_sispro and file_epi12 and file_epi15:
        df_sispro = procesar_archivo(file_sispro)
        df_epi12 = procesar_archivo(file_epi12)
        df_epi15 = procesar_archivo(file_epi15)
        
        st.success("Archivos cargados. Listos para auditoría.")
        st.write("Vista previa (Sispro):", df_sispro.head())

with tab2:
    st.header("2. Consolidación General")
    st.info("Aquí verás la comparativa mensual y anual de los tres formatos.")
    
    if 'df_sispro' in locals():
        # Lógica de comparación simple (placeholder para tu estructura)
        st.write("Comparativa de totales:")
        # Aquí programaremos la lógica de cruce de datos
        st.warning("Próximo paso: Integración del motor de comparación.")

# Pie de página
st.sidebar.markdown("---")
st.sidebar.markdown("### Aplicación creada por Willian Almenar")
