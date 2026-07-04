import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io

st.set_page_config(page_title="Gestor de Morbilidad - Willian Almenar", layout="wide")

# Estilos CSS personalizados
st.markdown("""
    <style>
    .main-header {
        background-color: #1E3A5F;
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #28a745;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #ffc107;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1>🏥 Gestor de Morbilidad</h1><p>Willian Almenar</p></div>', unsafe_allow_html=True)
st.markdown("---")

# Diccionario de mapeo de columnas esperadas para cada tipo de archivo
EXPECTED_COLUMNS = {
    "SISPRO": [
        "CODIGO_EPS", "NOMBRE_EPS", "TIPO_DOCUMENTO", "NUMERO_DOCUMENTO", 
        "NOMBRE_PACIENTE", "APELLIDO_PACIENTE", "FECHA_ATENCION", 
        "CODIGO_DIAGNOSTICO", "DESCRIPCION_DIAGNOSTICO", "CODIGO_CIE10",
        "SEXO", "EDAD", "MUNICIPIO", "DEPARTAMENTO"
    ],
    "EPI12": [
        "CODIGO_EPS", "NOMBRE_EPS", "TIPO_DOCUMENTO", "NUMERO_DOCUMENTO",
        "NOMBRE_PACIENTE", "APELLIDO_PACIENTE", "FECHA_ATENCION",
        "CODIGO_DIAGNOSTICO", "DESCRIPCION_DIAGNOSTICO", "CODIGO_CIE10",
        "PROCEDIMIENTO", "DESCRIPCION_PROCEDIMIENTO", "SEXO", "EDAD"
    ],
    "EPI15": [
        "CODIGO_EPS", "NOMBRE_EPS", "TIPO_DOCUMENTO", "NUMERO_DOCUMENTO",
        "NOMBRE_PACIENTE", "APELLIDO_PACIENTE", "FECHA_ATENCION",
        "CODIGO_DIAGNOSTICO", "DESCRIPCION_DIAGNOSTICO", "CODIGO_CIE10",
        "SERVICIO", "SEXO", "EDAD", "MUNICIPIO"
    ]
}

def analizar_archivo(file, tipo_archivo):
    """
    Analiza y procesa un archivo Excel con validación específica para cada tipo
    """
    if file is None:
        return None, "No se ha subido ningún archivo"
    
    try:
        # Detectar el motor de lectura
        if file.name.endswith('.xls'):
            df = pd.read_excel(file, engine='xlrd', header=0)
        else:
            df = pd.read_excel(file, engine='openpyxl', header=0)
        
        # Limpiar nombres de columnas (quitar espacios, mayúsculas)
        df.columns = df.columns.str.strip().str.upper()
        
        # Información básica
        info = {
            "filas": df.shape[0],
            "columnas": df.shape[1],
            "nombres_columnas": list(df.columns),
            "tipos_datos": df.dtypes.to_dict(),
            "valores_nulos": df.isnull().sum().to_dict(),
            "fecha_carga": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Validar columnas esperadas
        columnas_esperadas = EXPECTED_COLUMNS.get(tipo_archivo, [])
        columnas_encontradas = []
        columnas_faltantes = []
        
        for col in columnas_esperadas:
            if col in df.columns:
                columnas_encontradas.append(col)
            else:
                # Buscar coincidencias parciales
                coincidencias = [c for c in df.columns if col in c or c in col]
                if coincidencias:
                    columnas_encontradas.append(coincidencias[0])
                else:
                    columnas_faltantes.append(col)
        
        info["columnas_encontradas"] = columnas_encontradas
        info["columnas_faltantes"] = columnas_faltantes
        
        # Análisis de datos según el tipo
        if tipo_archivo == "SISPRO":
            df = procesar_sispro(df)
        elif tipo_archivo == "EPI12":
            df = procesar_epi12(df)
        elif tipo_archivo == "EPI15":
            df = procesar_epi15(df)
        
        # Estadísticas adicionales
        info["estadisticas"] = generar_estadisticas(df, tipo_archivo)
        
        return df, info
        
    except Exception as e:
        return None, f"Error al procesar el archivo: {str(e)}"

def procesar_sispro(df):
    """Procesa específicamente datos de SISPRO"""
    # Convertir fechas si existe la columna
    if 'FECHA_ATENCION' in df.columns:
        try:
            df['FECHA_ATENCION'] = pd.to_datetime(df['FECHA_ATENCION'], errors='coerce')
        except:
            pass
    
    # Crear columna de año y mes para análisis
    if 'FECHA_ATENCION' in df.columns:
        df['AÑO'] = df['FECHA_ATENCION'].dt.year
        df['MES'] = df['FECHA_ATENCION'].dt.month
    
    return df

def procesar_epi12(df):
    """Procesa específicamente datos de EPI12"""
    # Similar al procesamiento de SISPRO
    if 'FECHA_ATENCION' in df.columns:
        try:
            df['FECHA_ATENCION'] = pd.to_datetime(df['FECHA_ATENCION'], errors='coerce')
            df['AÑO'] = df['FECHA_ATENCION'].dt.year
            df['MES'] = df['FECHA_ATENCION'].dt.month
        except:
            pass
    return df

def procesar_epi15(df):
    """Procesa específicamente datos de EPI15"""
    if 'FECHA_ATENCION' in df.columns:
        try:
            df['FECHA_ATENCION'] = pd.to_datetime(df['FECHA_ATENCION'], errors='coerce')
            df['AÑO'] = df['FECHA_ATENCION'].dt.year
            df['MES'] = df['FECHA_ATENCION'].dt.month
        except:
            pass
    return df

def generar_estadisticas(df, tipo_archivo):
    """Genera estadísticas relevantes para cada tipo de archivo"""
    estadisticas = {}
    
    # Estadísticas generales
    estadisticas["total_registros"] = len(df)
    estadisticas["columnas_totales"] = len(df.columns)
    
    # Estadísticas por tipo
    if 'CODIGO_CIE10' in df.columns:
        estadisticas["diagnosticos_unicos"] = df['CODIGO_CIE10'].nunique()
    
    if 'SEXO' in df.columns:
        estadisticas["distribucion_sexo"] = df['SEXO'].value_counts().to_dict()
    
    if 'EDAD' in df.columns:
        try:
            df['EDAD'] = pd.to_numeric(df['EDAD'], errors='coerce')
            estadisticas["edad_promedio"] = round(df['EDAD'].mean(), 2)
            estadisticas["edad_min"] = df['EDAD'].min()
            estadisticas["edad_max"] = df['EDAD'].max()
        except:
            pass
    
    if 'AÑO' in df.columns:
        estadisticas["años_disponibles"] = df['AÑO'].dropna().unique().tolist()
    
    return estadisticas

def mostrar_analisis(df, info, tipo_archivo):
    """Muestra el análisis detallado del archivo"""
    
    if info is None:
        st.error("No se pudo cargar el archivo")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        st.subheader("📊 Resumen del Archivo")
        st.write(f"**Tipo:** {tipo_archivo}")
        st.write(f"**Registros:** {info['filas']:,}")
        st.write(f"**Columnas:** {info['columnas']}")
        st.write(f"**Fecha de carga:** {info['fecha_carga']}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        if info.get("estadisticas"):
            st.subheader("📈 Estadísticas")
            estadisticas = info["estadisticas"]
            st.write(f"**Diagnósticos únicos:** {estadisticas.get('diagnosticos_unicos', 'N/A')}")
            if 'edad_promedio' in estadisticas:
                st.write(f"**Edad promedio:** {estadisticas['edad_promedio']} años")
            if 'distribucion_sexo' in estadisticas:
                st.write("**Distribución por sexo:**")
                for sexo, count in estadisticas['distribucion_sexo'].items():
                    st.write(f"- {sexo}: {count}")
    
    # Mostrar información de columnas
    with st.expander("🔍 Detalle de Columnas"):
        col_faltantes = info.get('columnas_faltantes', [])
        col_encontradas = info.get('columnas_encontradas', [])
        
        if col_faltantes:
            st.warning(f"⚠️ Columnas no encontradas: {', '.join(col_faltantes)}")
        else:
            st.success("✅ Todas las columnas esperadas fueron encontradas")
        
        st.write("**Columnas disponibles:**")
        st.write(info['nombres_columnas'])
    
    # Vista previa de datos
    with st.expander("👁️ Vista Previa de Datos"):
        st.dataframe(df.head(10), use_container_width=True)
        
        # Mostrar información de tipos de datos
        st.write("**Tipos de datos:**")
        tipos_df = pd.DataFrame({
            'Columna': df.columns,
            'Tipo': [str(dtype) for dtype in df.dtypes.values],
            'Nulos': df.isnull().sum().values
        })
        st.dataframe(tipos_df, use_container_width=True)

# Interfaz principal
tab1, tab2, tab3 = st.tabs(["📤 Carga de Archivos", "📊 Análisis Consolidado", "📋 Reportes"])

with tab1:
    st.header("Carga de Archivos SISPRO, EPI12 y EPI15")
    st.markdown("""
    <div class="warning-box">
    ⚠️ <b>Recomendación:</b> Asegúrate de que los archivos tengan las columnas esperadas para cada tipo de formato.
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    # Almacenar dataframes en session_state
    if 'dataframes' not in st.session_state:
        st.session_state.dataframes = {}
    if 'infos' not in st.session_state:
        st.session_state.infos = {}
    
    with col1:
        st.subheader("🏥 SISPRO")
        file_sispro = st.file_uploader("Subir archivo SISPRO", type=['xls', 'xlsx'], key="sispro")
        if file_sispro:
            with st.spinner("Procesando archivo SISPRO..."):
                df, info = analizar_archivo(file_sispro, "SISPRO")
                if isinstance(info, dict):
                    st.session_state.dataframes['SISPRO'] = df
                    st.session_state.infos['SISPRO'] = info
                    st.success(f"✅ SISPRO cargado exitosamente - {info['filas']} registros")
                    mostrar_analisis(df, info, "SISPRO")
                else:
                    st.error(f"❌ {info}")
    
    with col2:
        st.subheader("📋 EPI12")
        file_epi12 = st.file_uploader("Subir archivo EPI12", type=['xls', 'xlsx'], key="epi12")
        if file_epi12:
            with st.spinner("Procesando archivo EPI12..."):
                df, info = analizar_archivo(file_epi12, "EPI12")
                if isinstance(info, dict):
                    st.session_state.dataframes['EPI12'] = df
                    st.session_state.infos['EPI12'] = info
                    st.success(f"✅ EPI12 cargado exitosamente - {info['filas']} registros")
                    mostrar_analisis(df, info, "EPI12")
                else:
                    st.error(f"❌ {info}")
    
    with col3:
        st.subheader("📊 EPI15")
        file_epi15 = st.file_uploader("Subir archivo EPI15", type=['xls', 'xlsx'], key="epi15")
        if file_epi15:
            with st.spinner("Procesando archivo EPI15..."):
                df, info = analizar_archivo(file_epi15, "EPI15")
                if isinstance(info, dict):
                    st.session_state.dataframes['EPI15'] = df
                    st.session_state.infos['EPI15'] = info
                    st.success(f"✅ EPI15 cargado exitosamente - {info['filas']} registros")
                    mostrar_analisis(df, info, "EPI15")
                else:
                    st.error(f"❌ {info}")

with tab2:
    st.header("Análisis Consolidado de Todos los Archivos")
    
    if st.session_state.dataframes:
        # Mostrar resumen de todos los archivos cargados
        st.subheader("📊 Resumen General")
        
        resumen_data = []
        for nombre, df in st.session_state.dataframes.items():
            info = st.session_state.infos.get(nombre, {})
            resumen_data.append({
                "Archivo": nombre,
                "Registros": len(df),
                "Columnas": len(df.columns),
                "Fecha Carga": info.get('fecha_carga', 'N/A')
            })
        
        resumen_df = pd.DataFrame(resumen_data)
        st.dataframe(resumen_df, use_container_width=True)
        
        # Comparativa de diagnósticos
        st.subheader("🔍 Comparativa de Diagnósticos")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Top 10 diagnósticos más comunes (SISPRO)
            if 'SISPRO' in st.session_state.dataframes:
                df_sispro = st.session_state.dataframes['SISPRO']
                if 'CODIGO_CIE10' in df_sispro.columns:
                    top_diagnosticos = df_sispro['CODIGO_CIE10'].value_counts().head(10)
                    st.write("**Top 10 Diagnósticos - SISPRO**")
                    st.bar_chart(top_diagnosticos)
        
        with col2:
            if 'EPI12' in st.session_state.dataframes:
                df_epi12 = st.session_state.dataframes['EPI12']
                if 'CODIGO_CIE10' in df_epi12.columns:
                    top_diagnosticos = df_epi12['CODIGO_CIE10'].value_counts().head(10)
                    st.write("**Top 10 Diagnósticos - EPI12**")
                    st.bar_chart(top_diagnosticos)
        
        # Opciones de descarga
        st.subheader("💾 Exportar Datos")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Exportar Todos los Datos a Excel"):
                with pd.ExcelWriter('datos_consolidados.xlsx') as writer:
                    for nombre, df in st.session_state.dataframes.items():
                        df.to_excel(writer, sheet_name=nombre[:31], index=False)
                st.success("Archivo exportado exitosamente!")
        
        with col2:
            if st.button("Generar Reporte Resumen"):
                # Crear reporte en formato texto
                reporte = "REPORTE CONSOLIDADO DE MORBILIDAD\n"
                reporte += "="*50 + "\n\n"
                for nombre, df in st.session_state.dataframes.items():
                    reporte += f"📊 {nombre}\n"
                    reporte += f"Total registros: {len(df)}\n"
                    reporte += f"Columnas: {len(df.columns)}\n"
                    reporte += "-"*30 + "\n"
                
                st.download_button(
                    label="📥 Descargar Reporte",
                    data=reporte,
                    file_name="reporte_morbilidad.txt",
                    mime="text/plain"
                )
    else:
        st.info("ℹ️ No hay archivos cargados. Por favor, carga archivos en la pestaña 'Carga de Archivos'")

with tab3:
    st.header("📋 Generación de Reportes")
    st.info("🚧 Módulo de reportes en desarrollo...")
    
    # Aquí puedes agregar funcionalidades adicionales de reportes

# Barra lateral
st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ Información de la Aplicación")
st.sidebar.markdown("""
**Versión:** 2.0  
**Desarrollador:** Willian Almenar  
**Fecha:** 2024  
**Propósito:** Gestión y análisis de datos de morbilidad
""")

st.sidebar.markdown("### 📚 Formatos Soportados")
st.sidebar.markdown("""
- **SISPRO:** Sistema de Información de Protección Social  
- **EPI12:** Encuesta de Prevalencia Institucional 12  
- **EPI15:** Encuesta de Prevalencia Institucional 15
""")

st.sidebar.markdown("### 🛠️ Funcionalidades")
st.sidebar.markdown("""
- ✅ Carga de archivos Excel (.xls, .xlsx)  
- ✅ Análisis automático de datos  
- ✅ Validación de columnas  
- ✅ Estadísticas descriptivas  
- ✅ Vista previa de datos  
- ✅ Exportación de datos consolidados
""")

if st.sidebar.button("🔄 Limpiar todos los datos"):
    st.session_state.dataframes = {}
    st.session_state.infos = {}
    st.sidebar.success("Datos limpiados exitosamente!")
    st.rerun()
