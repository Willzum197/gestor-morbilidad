import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

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
    .danger-box {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #dc3545;
    }
    .info-box {
        background-color: #d1ecf1;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #17a2b8;
    }
    .comparison-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border: 2px solid #6c757d;
    }
    .metric-card {
        background-color: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1>🏥 Gestor de Morbilidad - Análisis Comparativo</h1><p>Willian Almenar</p></div>', unsafe_allow_html=True)
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

# Definición de grupos etarios
GRUPOS_ETARIOS = {
    '0-4 años': (0, 4),
    '5-9 años': (5, 9),
    '10-14 años': (10, 14),
    '15-19 años': (15, 19),
    '20-24 años': (20, 24),
    '25-29 años': (25, 29),
    '30-34 años': (30, 34),
    '35-39 años': (35, 39),
    '40-44 años': (40, 44),
    '45-49 años': (45, 49),
    '50-54 años': (50, 54),
    '55-59 años': (55, 59),
    '60-64 años': (60, 64),
    '65+ años': (65, 150)
}

def asignar_grupo_etario(edad):
    """Asigna un grupo etario según la edad"""
    if pd.isna(edad):
        return 'Sin dato'
    try:
        edad = float(edad)
        for grupo, (min_edad, max_edad) in GRUPOS_ETARIOS.items():
            if min_edad <= edad <= max_edad:
                return grupo
        return 'Sin dato'
    except:
        return 'Sin dato'

def normalizar_identificacion(df):
    """Normaliza la identificación del paciente para comparación"""
    if 'NUMERO_DOCUMENTO' in df.columns:
        df['IDENTIFICACION'] = df['NUMERO_DOCUMENTO'].astype(str).str.strip()
    elif 'DOCUMENTO' in df.columns:
        df['IDENTIFICACION'] = df['DOCUMENTO'].astype(str).str.strip()
    else:
        df['IDENTIFICACION'] = df.index.astype(str)
    
    if 'NOMBRE_PACIENTE' in df.columns and 'APELLIDO_PACIENTE' in df.columns:
        df['NOMBRE_COMPLETO'] = df['NOMBRE_PACIENTE'].astype(str).str.strip() + ' ' + df['APELLIDO_PACIENTE'].astype(str).str.strip()
    elif 'NOMBRE_PACIENTE' in df.columns:
        df['NOMBRE_COMPLETO'] = df['NOMBRE_PACIENTE'].astype(str).str.strip()
    else:
        df['NOMBRE_COMPLETO'] = df['IDENTIFICACION']
    
    return df

def analizar_archivo(file, tipo_archivo):
    """Analiza y procesa un archivo Excel con validación específica para cada tipo"""
    if file is None:
        return None, "No se ha subido ningún archivo"
    
    try:
        if file.name.endswith('.xls'):
            df = pd.read_excel(file, engine='xlrd', header=0)
        else:
            df = pd.read_excel(file, engine='openpyxl', header=0)
        
        df.columns = df.columns.str.strip().str.upper()
        
        info = {
            "filas": df.shape[0],
            "columnas": df.shape[1],
            "nombres_columnas": list(df.columns),
            "tipos_datos": df.dtypes.to_dict(),
            "valores_nulos": df.isnull().sum().to_dict(),
            "fecha_carga": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        columnas_esperadas = EXPECTED_COLUMNS.get(tipo_archivo, [])
        columnas_encontradas = []
        columnas_faltantes = []
        
        for col in columnas_esperadas:
            if col in df.columns:
                columnas_encontradas.append(col)
            else:
                coincidencias = [c for c in df.columns if col in c or c in col]
                if coincidencias:
                    columnas_encontradas.append(coincidencias[0])
                else:
                    columnas_faltantes.append(col)
        
        info["columnas_encontradas"] = columnas_encontradas
        info["columnas_faltantes"] = columnas_faltantes
        
        df = procesar_datos(df, tipo_archivo)
        df = normalizar_identificacion(df)
        
        if 'EDAD' in df.columns:
            df['GRUPO_ETARIO'] = df['EDAD'].apply(asignar_grupo_etario)
        
        if 'FECHA_ATENCION' in df.columns:
            try:
                df['AÑO'] = df['FECHA_ATENCION'].dt.year
                df['MES'] = df['FECHA_ATENCION'].dt.month
                df['AÑO_MES'] = df['FECHA_ATENCION'].dt.strftime('%Y-%m')
                df['MES_NOMBRE'] = df['FECHA_ATENCION'].dt.strftime('%B')
            except:
                pass
        
        info["duplicados"] = detectar_duplicados(df)
        info["estadisticas"] = generar_estadisticas(df, tipo_archivo)
        
        return df, info
        
    except Exception as e:
        return None, f"Error al procesar el archivo: {str(e)}"

def detectar_duplicados(df):
    """Detecta registros duplicados en el dataframe"""
    duplicados_info = {}
    
    if 'IDENTIFICACION' in df.columns:
        duplicados_identificacion = df[df.duplicated(subset=['IDENTIFICACION'], keep=False)]
        duplicados_info['por_identificacion'] = {
            'cantidad': len(duplicados_identificacion),
            'registros_unicos': duplicados_identificacion['IDENTIFICACION'].nunique()
        }
    
    duplicados_exactos = df[df.duplicated(keep=False)]
    duplicados_info['exactos'] = {
        'cantidad': len(duplicados_exactos),
        'registros_unicos': len(duplicados_exactos) // 2 if len(duplicados_exactos) > 0 else 0
    }
    
    return duplicados_info

def procesar_datos(df, tipo_archivo):
    """Procesa datos según el tipo de archivo"""
    if 'FECHA_ATENCION' in df.columns:
        try:
            df['FECHA_ATENCION'] = pd.to_datetime(df['FECHA_ATENCION'], errors='coerce')
        except:
            pass
    
    if 'EDAD' in df.columns:
        try:
            df['EDAD'] = pd.to_numeric(df['EDAD'], errors='coerce')
        except:
            pass
    
    return df

def generar_estadisticas(df, tipo_archivo):
    """Genera estadísticas relevantes para cada tipo de archivo"""
    estadisticas = {}
    
    estadisticas["total_registros"] = len(df)
    estadisticas["columnas_totales"] = len(df.columns)
    
    if 'IDENTIFICACION' in df.columns:
        estadisticas["pacientes_unicos"] = df['IDENTIFICACION'].nunique()
    
    if 'CODIGO_CIE10' in df.columns:
        try:
            estadisticas["diagnosticos_unicos"] = df['CODIGO_CIE10'].nunique()
            estadisticas["top_diagnosticos"] = df['CODIGO_CIE10'].value_counts().head(10).to_dict()
        except:
            estadisticas["diagnosticos_unicos"] = 0
    
    if 'SEXO' in df.columns:
        try:
            estadisticas["distribucion_sexo"] = df['SEXO'].value_counts().to_dict()
        except:
            pass
    
    if 'GRUPO_ETARIO' in df.columns:
        try:
            estadisticas["distribucion_grupo_etario"] = df['GRUPO_ETARIO'].value_counts().to_dict()
        except:
            pass
    
    return estadisticas

def comparar_grupos_etarios_sispro_epi12(df_sispro, df_epi12):
    """Compara y totaliza pacientes por grupo etario entre SISPRO y EPI12"""
    
    st.subheader("📊 Comparativa de Grupos Etarios: SISPRO vs EPI12")
    
    if df_sispro is None or df_epi12 is None:
        st.warning("Se necesitan los datos de SISPRO y EPI12 para esta comparación")
        return
    
    # Preparar datos de grupos etarios
    grupos_sispro = df_sispro['GRUPO_ETARIO'].value_counts() if 'GRUPO_ETARIO' in df_sispro.columns else pd.Series()
    grupos_epi12 = df_epi12['GRUPO_ETARIO'].value_counts() if 'GRUPO_ETARIO' in df_epi12.columns else pd.Series()
    
    # Crear DataFrame comparativo
    todos_grupos = sorted(set(grupos_sispro.index) | set(grupos_epi12.index))
    todos_grupos = [g for g in todos_grupos if g != 'Sin dato']
    
    comparativa_grupos = pd.DataFrame({
        'Grupo Etario': todos_grupos,
        'SISPRO': [grupos_sispro.get(g, 0) for g in todos_grupos],
        'EPI12': [grupos_epi12.get(g, 0) for g in todos_grupos]
    })
    
    # Calcular totales y diferencias
    comparativa_grupos['Total'] = comparativa_grupos['SISPRO'] + comparativa_grupos['EPI12']
    comparativa_grupos['Diferencia'] = comparativa_grupos['SISPRO'] - comparativa_grupos['EPI12']
    comparativa_grupos['% Diferencia'] = ((comparativa_grupos['Diferencia'].abs() / comparativa_grupos[['SISPRO', 'EPI12']].max(axis=1)) * 100).round(2)
    comparativa_grupos['% Diferencia'] = comparativa_grupos['% Diferencia'].fillna(0)
    
    # Mostrar tabla
    st.write("### 📋 Tabla Comparativa por Grupo Etario")
    st.dataframe(comparativa_grupos, use_container_width=True)
    
    # Gráfico de barras
    st.write("### 📊 Gráfico Comparativo")
    chart_data = comparativa_grupos.set_index('Grupo Etario')[['SISPRO', 'EPI12']]
    st.bar_chart(chart_data)
    
    # Resumen de totales
    st.write("### 📈 Resumen de Totales")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total SISPRO", f"{comparativa_grupos['SISPRO'].sum():,}")
    with col2:
        st.metric("Total EPI12", f"{comparativa_grupos['EPI12'].sum():,}")
    with col3:
        diff_total = comparativa_grupos['SISPRO'].sum() - comparativa_grupos['EPI12'].sum()
        st.metric("Diferencia Total", f"{diff_total:+,}", 
                  delta_color="inverse" if diff_total != 0 else "off")
    
    # Análisis mensual por grupo etario
    st.write("### 📅 Análisis Mensual por Grupo Etario")
    
    if 'AÑO_MES' in df_sispro.columns and 'AÑO_MES' in df_epi12.columns:
        # Seleccionar grupo etario para análisis mensual
        grupo_seleccionado = st.selectbox(
            "Seleccionar grupo etario para análisis mensual:",
            todos_grupos
        )
        
        if grupo_seleccionado:
            # Filtrar por grupo etario
            df_sispro_grupo = df_sispro[df_sispro['GRUPO_ETARIO'] == grupo_seleccionado]
            df_epi12_grupo = df_epi12[df_epi12['GRUPO_ETARIO'] == grupo_seleccionado]
            
            # Conteo mensual
            mensual_sispro = df_sispro_grupo.groupby('AÑO_MES').size().reset_index(name='SISPRO')
            mensual_epi12 = df_epi12_grupo.groupby('AÑO_MES').size().reset_index(name='EPI12')
            
            # Unir datos
            mensual_comparativa = pd.merge(mensual_sispro, mensual_epi12, on='AÑO_MES', how='outer').fillna(0)
            mensual_comparativa = mensual_comparativa.sort_values('AÑO_MES')
            
            # Mostrar datos mensuales
            st.write(f"**Análisis mensual para grupo {grupo_seleccionado}**")
            st.dataframe(mensual_comparativa, use_container_width=True)
            
            # Gráfico mensual
            if len(mensual_comparativa) > 0:
                chart_mensual = mensual_comparativa.set_index('AÑO_MES')[['SISPRO', 'EPI12']]
                st.bar_chart(chart_mensual)
    
    # Análisis anual por grupo etario
    st.write("### 📅 Análisis Anual por Grupo Etario")
    
    if 'AÑO' in df_sispro.columns and 'AÑO' in df_epi12.columns:
        # Seleccionar grupo etario para análisis anual
        grupo_anual = st.selectbox(
            "Seleccionar grupo etario para análisis anual:",
            todos_grupos,
            key="grupo_anual"
        )
        
        if grupo_anual:
            df_sispro_grupo = df_sispro[df_sispro['GRUPO_ETARIO'] == grupo_anual]
            df_epi12_grupo = df_epi12[df_epi12['GRUPO_ETARIO'] == grupo_anual]
            
            anual_sispro = df_sispro_grupo.groupby('AÑO').size().reset_index(name='SISPRO')
            anual_epi12 = df_epi12_grupo.groupby('AÑO').size().reset_index(name='EPI12')
            
            anual_comparativa = pd.merge(anual_sispro, anual_epi12, on='AÑO', how='outer').fillna(0)
            anual_comparativa = anual_comparativa.sort_values('AÑO')
            
            st.write(f"**Análisis anual para grupo {grupo_anual}**")
            st.dataframe(anual_comparativa, use_container_width=True)
            
            if len(anual_comparativa) > 0:
                chart_anual = anual_comparativa.set_index('AÑO')[['SISPRO', 'EPI12']]
                st.bar_chart(chart_anual)

def comparar_enfermedades_epi15_sispro(df_epi15, df_sispro):
    """Compara y totaliza datos por enfermedades entre EPI15 y SISPRO"""
    
    st.subheader("🔍 Comparativa de Enfermedades: EPI15 vs SISPRO")
    
    if df_epi15 is None or df_sispro is None:
        st.warning("Se necesitan los datos de EPI15 y SISPRO para esta comparación")
        return
    
    if 'CODIGO_CIE10' not in df_epi15.columns or 'CODIGO_CIE10' not in df_sispro.columns:
        st.warning("No se encontró la columna CODIGO_CIE10 en los archivos")
        return
    
    # Top enfermedades por cada fuente
    top_epi15 = df_epi15['CODIGO_CIE10'].value_counts().head(20)
    top_sispro = df_sispro['CODIGO_CIE10'].value_counts().head(20)
    
    # Crear DataFrame comparativo
    todos_codigos = sorted(set(top_epi15.index) | set(top_sispro.index))
    
    comparativa_enfermedades = pd.DataFrame({
        'Código CIE10': todos_codigos,
        'EPI15': [top_epi15.get(c, 0) for c in todos_codigos],
        'SISPRO': [top_sispro.get(c, 0) for c in todos_codigos]
    })
    
    comparativa_enfermedades['Total'] = comparativa_enfermedades['EPI15'] + comparativa_enfermedades['SISPRO']
    comparativa_enfermedades['Diferencia'] = comparativa_enfermedades['EPI15'] - comparativa_enfermedades['SISPRO']
    comparativa_enfermedades['% Diferencia'] = ((comparativa_enfermedades['Diferencia'].abs() / comparativa_enfermedades[['EPI15', 'SISPRO']].max(axis=1)) * 100).round(2)
    comparativa_enfermedades['% Diferencia'] = comparativa_enfermedades['% Diferencia'].fillna(0)
    
    # Ordenar por total
    comparativa_enfermedades = comparativa_enfermedades.sort_values('Total', ascending=False)
    
    # Mostrar tabla
    st.write("### 📋 Tabla Comparativa de Enfermedades (Top 20)")
    st.dataframe(comparativa_enfermedades, use_container_width=True)
    
    # Gráfico de barras
    st.write("### 📊 Gráfico Comparativo de Enfermedades")
    chart_enfermedades = comparativa_enfermedades.set_index('Código CIE10').head(10)[['EPI15', 'SISPRO']]
    st.bar_chart(chart_enfermedades)
    
    # Resumen de totales
    st.write("### 📈 Resumen de Totales por Enfermedad")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total EPI15", f"{comparativa_enfermedades['EPI15'].sum():,}")
    with col2:
        st.metric("Total SISPRO", f"{comparativa_enfermedades['SISPRO'].sum():,}")
    with col3:
        diff_enfermedades = comparativa_enfermedades['EPI15'].sum() - comparativa_enfermedades['SISPRO'].sum()
        st.metric("Diferencia Total", f"{diff_enfermedades:+,}")
    
    # Enfermedades exclusivas
    st.write("### 🔍 Enfermedades Exclusivas")
    col1, col2 = st.columns(2)
    
    with col1:
        exclusivas_epi15 = comparativa_enfermedades[comparativa_enfermedades['SISPRO'] == 0]
        st.write(f"**Enfermedades solo en EPI15:** {len(exclusivas_epi15)}")
        if len(exclusivas_epi15) > 0:
            st.dataframe(exclusivas_epi15[['Código CIE10', 'EPI15']].head(10), use_container_width=True)
    
    with col2:
        exclusivas_sispro = comparativa_enfermedades[comparativa_enfermedades['EPI15'] == 0]
        st.write(f"**Enfermedades solo en SISPRO:** {len(exclusivas_sispro)}")
        if len(exclusivas_sispro) > 0:
            st.dataframe(exclusivas_sispro[['Código CIE10', 'SISPRO']].head(10), use_container_width=True)
    
    # Enfermedades comunes
    comunes = comparativa_enfermedades[(comparativa_enfermedades['EPI15'] > 0) & (comparativa_enfermedades['SISPRO'] > 0)]
    st.write(f"### 📊 Enfermedades Comunes: {len(comunes)}")
    
    if len(comunes) > 0:
        st.dataframe(comunes.head(10), use_container_width=True)
        
        # Gráfico de enfermedades comunes
        st.write("**Top 10 Enfermedades Comunes**")
        chart_comunes = comunes.set_index('Código CIE10').head(10)[['EPI15', 'SISPRO']]
        st.bar_chart(chart_comunes)
    
    # Análisis mensual de enfermedades
    st.write("### 📅 Análisis Mensual de Enfermedades")
    
    if 'AÑO_MES' in df_epi15.columns and 'AÑO_MES' in df_sispro.columns:
        # Seleccionar enfermedad para análisis mensual
        codigos_disponibles = todos_codigos[:20]  # Top 20 para no saturar
        codigo_seleccionado = st.selectbox(
            "Seleccionar enfermedad (código CIE10) para análisis mensual:",
            codigos_disponibles
        )
        
        if codigo_seleccionado:
            df_epi15_enfermedad = df_epi15[df_epi15['CODIGO_CIE10'] == codigo_seleccionado]
            df_sispro_enfermedad = df_sispro[df_sispro['CODIGO_CIE10'] == codigo_seleccionado]
            
            mensual_epi15 = df_epi15_enfermedad.groupby('AÑO_MES').size().reset_index(name='EPI15')
            mensual_sispro = df_sispro_enfermedad.groupby('AÑO_MES').size().reset_index(name='SISPRO')
            
            mensual_enfermedad = pd.merge(mensual_epi15, mensual_sispro, on='AÑO_MES', how='outer').fillna(0)
            mensual_enfermedad = mensual_enfermedad.sort_values('AÑO_MES')
            
            st.write(f"**Análisis mensual para enfermedad {codigo_seleccionado}**")
            st.dataframe(mensual_enfermedad, use_container_width=True)
            
            if len(mensual_enfermedad) > 0:
                chart_mensual_enfermedad = mensual_enfermedad.set_index('AÑO_MES')[['EPI15', 'SISPRO']]
                st.bar_chart(chart_mensual_enfermedad)

def mostrar_analisis(df, info, tipo_archivo):
    """Muestra el análisis detallado del archivo"""
    
    if info is None or df is None:
        st.error("No se pudo cargar el archivo")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        st.subheader("📊 Resumen del Archivo")
        st.write(f"**Tipo:** {tipo_archivo}")
        st.write(f"**Registros:** {info['filas']:,}")
        st.write(f"**Pacientes únicos:** {info.get('estadisticas', {}).get('pacientes_unicos', 'N/A')}")
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

# Inicializar session_state
if 'dataframes' not in st.session_state:
    st.session_state.dataframes = {}
if 'infos' not in st.session_state:
    st.session_state.infos = {}

# Interfaz principal
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📤 Carga de Archivos", 
    "📊 Análisis por Fuente",
    "👥 Grupos Etarios SISPRO vs EPI12",
    "🔬 Enfermedades EPI15 vs SISPRO",
    "🔍 Validación de Consistencia",
    "📋 Reporte Consolidado"
])

with tab1:
    st.header("Carga de Archivos SISPRO, EPI12 y EPI15")
    st.markdown("""
    <div class="info-box">
    💡 <b>Instrucciones:</b> Sube los archivos Excel (.xls o .xlsx) correspondientes a cada tipo de formato.
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
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
    st.header("Análisis por Fuente")
    
    if st.session_state.dataframes:
        fuente_seleccionada = st.selectbox(
            "Seleccionar fuente para análisis detallado:",
            list(st.session_state.dataframes.keys())
        )
        
        if fuente_seleccionada:
            df = st.session_state.dataframes[fuente_seleccionada]
            info = st.session_state.infos.get(fuente_seleccionada, {})
            
            st.subheader(f"📊 Análisis Detallado - {fuente_seleccionada}")
            mostrar_analisis(df, info, fuente_seleccionada)
            
            # Mostrar distribución de grupos etarios
            if 'GRUPO_ETARIO' in df.columns:
                st.subheader("📊 Distribución por Grupo Etario")
                distribucion = df['GRUPO_ETARIO'].value_counts()
                distribucion = distribucion[distribucion.index != 'Sin dato']
                
                if len(distribucion) > 0:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.dataframe(distribucion, use_container_width=True)
                    with col2:
                        st.bar_chart(distribucion)
    else:
        st.info("ℹ️ No hay archivos cargados. Por favor, carga archivos en la pestaña 'Carga de Archivos'")

with tab3:
    st.header("👥 Comparativa de Grupos Etarios: SISPRO vs EPI12")
    
    if 'SISPRO' in st.session_state.dataframes and 'EPI12' in st.session_state.dataframes:
        df_sispro = st.session_state.dataframes['SISPRO']
        df_epi12 = st.session_state.dataframes['EPI12']
        comparar_grupos_etarios_sispro_epi12(df_sispro, df_epi12)
    else:
        st.warning("⚠️ Se necesitan los archivos SISPRO y EPI12 para esta comparación")
        st.info("Por favor, carga ambos archivos en la pestaña 'Carga de Archivos'")

with tab4:
    st.header("🔬 Comparativa de Enfermedades: EPI15 vs SISPRO")
    
    if 'EPI15' in st.session_state.dataframes and 'SISPRO' in st.session_state.dataframes:
        df_epi15 = st.session_state.dataframes['EPI15']
        df_sispro = st.session_state.dataframes['SISPRO']
        comparar_enfermedades_epi15_sispro(df_epi15, df_sispro)
    else:
        st.warning("⚠️ Se necesitan los archivos EPI15 y SISPRO para esta comparación")
        st.info("Por favor, carga ambos archivos en la pestaña 'Carga de Archivos'")

with tab5:
    st.header("🔍 Validación de Consistencia de Datos")
    
    if st.session_state.dataframes:
        st.info("🔍 Módulo de validación de consistencia en desarrollo")
    else:
        st.info("ℹ️ No hay archivos cargados para validar")

with tab6:
    st.header("📋 Reporte Consolidado")
    
    if st.session_state.dataframes:
        st.subheader("📊 Resumen General de Todos los Reportes")
        
        resumen_consolidado = []
        for nombre, df in st.session_state.dataframes.items():
            info = st.session_state.infos.get(nombre, {})
            estadisticas = info.get('estadisticas', {})
            
            resumen_consolidado.append({
                'Fuente': nombre,
                'Registros': len(df),
                'Pacientes Únicos': estadisticas.get('pacientes_unicos', 'N/A'),
                'Diagnósticos Únicos': estadisticas.get('diagnosticos_unicos', 'N/A')
            })
        
        st.dataframe(pd.DataFrame(resumen_consolidado), use_container_width=True)
        
        # Opciones de exportación
        st.subheader("💾 Exportar Reportes")
        
        if st.button("📥 Exportar Datos Consolidados a Excel"):
            try:
                from io import BytesIO
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    for nombre, df in st.session_state.dataframes.items():
                        df.to_excel(writer, sheet_name=nombre[:31], index=False)
                output.seek(0)
                st.download_button(
                    label="Descargar Excel",
                    data=output,
                    file_name=f"reporte_consolidado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                st.success("Reporte exportado exitosamente!")
            except Exception as e:
                st.error(f"Error al exportar: {str(e)}")
    else:
        st.info("ℹ️ No hay archivos cargados para generar reportes")

# Barra lateral
st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ Información de la Aplicación")
st.sidebar.markdown("""
**Versión:** 6.0  
**Desarrollador:** Willian Almenar  
**Fecha:** 2024  
**Propósito:** Análisis comparativo de datos de morbilidad
""")

st.sidebar.markdown("### 📚 Comparaciones Disponibles")
st.sidebar.markdown("""
- **SISPRO vs EPI12:** Grupos etarios  
- **EPI15 vs SISPRO:** Enfermedades  
- **Análisis mensual y anual**
""")

# Contador de archivos cargados
total_archivos = len(st.session_state.dataframes)
st.sidebar.markdown(f"### 📁 Archivos cargados: {total_archivos}/3")
if total_archivos > 0:
    for nombre in st.session_state.dataframes.keys():
        st.sidebar.success(f"✅ {nombre}")

if st.sidebar.button("🔄 Limpiar todos los datos"):
    st.session_state.dataframes = {}
    st.session_state.infos = {}
    st.sidebar.success("Datos limpiados exitosamente!")
    st.rerun()
