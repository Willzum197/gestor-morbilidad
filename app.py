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

st.markdown('<div class="main-header"><h1>🏥 Gestor de Morbilidad - Validación de Datos</h1><p>Willian Almenar</p></div>', unsafe_allow_html=True)
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
        
        # Extraer año y mes para comparaciones temporales
        if 'FECHA_ATENCION' in df.columns:
            try:
                df['AÑO'] = df['FECHA_ATENCION'].dt.year
                df['MES'] = df['FECHA_ATENCION'].dt.month
                df['AÑO_MES'] = df['FECHA_ATENCION'].dt.strftime('%Y-%m')
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
            'registros_unicos': duplicados_identificacion['IDENTIFICACION'].nunique(),
            'ejemplos': duplicados_identificacion[['IDENTIFICACION', 'NOMBRE_COMPLETO']].head(10).to_dict('records')
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
        except:
            estadisticas["diagnosticos_unicos"] = 0
    
    if 'SEXO' in df.columns:
        try:
            estadisticas["distribucion_sexo"] = df['SEXO'].value_counts().to_dict()
        except:
            pass
    
    if 'EDAD' in df.columns:
        try:
            df_edad = df['EDAD'].dropna()
            if len(df_edad) > 0:
                estadisticas["edad_promedio"] = round(df_edad.mean(), 2)
                estadisticas["edad_min"] = df_edad.min()
                estadisticas["edad_max"] = df_edad.max()
        except:
            pass
    
    if 'GRUPO_ETARIO' in df.columns:
        try:
            estadisticas["distribucion_grupo_etario"] = df['GRUPO_ETARIO'].value_counts().to_dict()
        except:
            pass
    
    # Estadísticas temporales (mensuales y anuales)
    if 'AÑO' in df.columns and 'MES' in df.columns:
        try:
            # Conteo anual
            estadisticas["conteo_anual"] = df['AÑO'].value_counts().sort_index().to_dict()
            
            # Conteo mensual (agrupado por año y mes)
            conteo_mensual = df.groupby(['AÑO', 'MES']).size().reset_index(name='conteo')
            estadisticas["conteo_mensual"] = conteo_mensual.to_dict('records')
            
            # Conteo mensual por fuente (para comparación)
            estadisticas["conteo_por_mes"] = df.groupby(['AÑO', 'MES']).size().to_dict()
        except:
            pass
    
    return estadisticas

def comparar_registros_temporales(dataframes):
    """Compara los registros mensual y anualmente entre las tres fuentes"""
    
    st.subheader("📊 Comparación Mensual y Anual entre Reportes")
    
    if len(dataframes) < 2:
        st.warning("Se necesitan al menos 2 fuentes para comparar")
        return
    
    # Extraer datos temporales de cada fuente
    datos_temporales = {}
    
    for nombre, df in dataframes.items():
        if 'AÑO' in df.columns and 'MES' in df.columns:
            # Conteo mensual
            mensual = df.groupby(['AÑO', 'MES']).size().reset_index(name='conteo')
            mensual['PERIODO'] = mensual['AÑO'].astype(str) + '-' + mensual['MES'].astype(str).str.zfill(2)
            
            # Conteo anual
            anual = df['AÑO'].value_counts().sort_index().reset_index()
            anual.columns = ['AÑO', 'conteo']
            
            datos_temporales[nombre] = {
                'mensual': mensual,
                'anual': anual,
                'total': len(df)
            }
    
    if len(datos_temporales) < 2:
        st.warning("No se encontraron datos temporales (año/mes) en los reportes")
        return
    
    fuentes = list(datos_temporales.keys())
    
    # 1. COMPARACIÓN ANUAL
    st.write("### 📅 Comparación Anual")
    
    # Crear tabla comparativa anual
    anual_comparativa = {}
    for fuente in fuentes:
        anual_df = datos_temporales[fuente]['anual']
        for _, row in anual_df.iterrows():
            año = int(row['AÑO'])
            if año not in anual_comparativa:
                anual_comparativa[año] = {}
            anual_comparativa[año][fuente] = row['conteo']
    
    # Completar años faltantes
    todos_años = sorted(set([año for año in anual_comparativa.keys()]))
    df_anual = pd.DataFrame(anual_comparativa).T.fillna(0)
    df_anual.index.name = 'Año'
    
    st.dataframe(df_anual, use_container_width=True)
    
    # Gráfico de barras anual
    st.bar_chart(df_anual)
    
    # Detectar inconsistencias anuales
    st.write("### ⚠️ Inconsistencias Anuales")
    
    inconsistencias_anuales = []
    for año in df_anual.index:
        valores = df_anual.loc[año].values
        if len(set(valores)) > 1:
            max_val = max(valores)
            min_val = min(valores)
            if max_val > 0:
                diff_pct = ((max_val - min_val) / max_val) * 100
                inconsistencias_anuales.append({
                    'Año': año,
                    'Diferencia': max_val - min_val,
                    'Porcentaje': f"{diff_pct:.1f}%",
                    'Detalle': {fuente: int(val) for fuente, val in df_anual.loc[año].items()}
                })
    
    if inconsistencias_anuales:
        st.markdown('<div class="danger-box">', unsafe_allow_html=True)
        st.write(f"**⚠️ Se encontraron {len(inconsistencias_anuales)} años con inconsistencias**")
        
        for inc in inconsistencias_anuales:
            st.write(f"**Año {inc['Año']}:** Diferencia de {inc['Diferencia']:,} registros ({inc['Porcentaje']})")
            for fuente, valor in inc['Detalle'].items():
                st.write(f"  - {fuente}: {valor:,} registros")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.success("✅ Todos los años tienen la misma cantidad de registros en todas las fuentes")
    
    # 2. COMPARACIÓN MENSUAL
    st.write("### 📆 Comparación Mensual")
    
    # Crear tabla comparativa mensual
    mensual_comparativa = {}
    for fuente in fuentes:
        mensual_df = datos_temporales[fuente]['mensual']
        for _, row in mensual_df.iterrows():
            periodo = row['PERIODO']
            if periodo not in mensual_comparativa:
                mensual_comparativa[periodo] = {}
            mensual_comparativa[periodo][fuente] = row['conteo']
    
    # Completar periodos faltantes
    todos_periodos = sorted(mensual_comparativa.keys())
    df_mensual = pd.DataFrame(mensual_comparativa).T.fillna(0)
    df_mensual.index.name = 'Periodo'
    
    # Mostrar solo los primeros 12 periodos para no saturar
    if len(df_mensual) > 12:
        st.write(f"Mostrando los últimos 12 meses (total {len(df_mensual)} meses)")
        df_mensual_mostrar = df_mensual.tail(12)
    else:
        df_mensual_mostrar = df_mensual
    
    st.dataframe(df_mensual_mostrar, use_container_width=True)
    
    # Gráfico de barras mensual
    st.bar_chart(df_mensual_mostrar)
    
    # Detectar inconsistencias mensuales
    st.write("### ⚠️ Inconsistencias Mensuales")
    
    inconsistencias_mensuales = []
    for periodo in df_mensual.index:
        valores = df_mensual.loc[periodo].values
        if len(set(valores)) > 1:
            max_val = max(valores)
            min_val = min(valores)
            if max_val > 0:
                diff_pct = ((max_val - min_val) / max_val) * 100
                inconsistencias_mensuales.append({
                    'Periodo': periodo,
                    'Diferencia': max_val - min_val,
                    'Porcentaje': f"{diff_pct:.1f}%",
                    'Detalle': {fuente: int(val) for fuente, val in df_mensual.loc[periodo].items()}
                })
    
    if inconsistencias_mensuales:
        st.markdown('<div class="danger-box">', unsafe_allow_html=True)
        st.write(f"**⚠️ Se encontraron {len(inconsistencias_mensuales)} meses con inconsistencias**")
        
        # Mostrar solo los primeros 10 para no saturar
        for inc in inconsistencias_mensuales[:10]:
            st.write(f"**{inc['Periodo']}:** Diferencia de {inc['Diferencia']:,} registros ({inc['Porcentaje']})")
            for fuente, valor in inc['Detalle'].items():
                st.write(f"  - {fuente}: {valor:,} registros")
        
        if len(inconsistencias_mensuales) > 10:
            st.write(f"... y {len(inconsistencias_mensuales) - 10} meses más con inconsistencias")
        
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.success("✅ Todos los meses tienen la misma cantidad de registros en todas las fuentes")
    
    # 3. REPORTE DE INCONSISTENCIAS
    st.write("### 📋 Reporte de Inconsistencias")
    
    if inconsistencias_anuales or inconsistencias_mensuales:
        reporte = "REPORTE DE INCONSISTENCIAS TEMPORALES\n"
        reporte += "="*60 + "\n"
        reporte += f"Fecha de generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        if inconsistencias_anuales:
            reporte += "📅 INCONSISTENCIAS ANUALES:\n"
            reporte += "-"*40 + "\n"
            for inc in inconsistencias_anuales:
                reporte += f"\nAño {inc['Año']}:\n"
                reporte += f"  Diferencia: {inc['Diferencia']} registros ({inc['Porcentaje']})\n"
                for fuente, valor in inc['Detalle'].items():
                    reporte += f"  - {fuente}: {valor} registros\n"
        
        if inconsistencias_mensuales:
            reporte += "\n📆 INCONSISTENCIAS MENSUALES (primeros 20):\n"
            reporte += "-"*40 + "\n"
            for inc in inconsistencias_mensuales[:20]:
                reporte += f"\n{inc['Periodo']}:\n"
                reporte += f"  Diferencia: {inc['Diferencia']} registros ({inc['Porcentaje']})\n"
                for fuente, valor in inc['Detalle'].items():
                    reporte += f"  - {fuente}: {valor} registros\n"
        
        st.download_button(
            label="📥 Descargar Reporte de Inconsistencias",
            data=reporte,
            file_name=f"reporte_inconsistencias_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )
    else:
        st.success("🎉 ¡No se encontraron inconsistencias! Todos los reportes coinciden mensual y anualmente.")

def verificar_igualdad_pacientes(dataframes):
    """Verifica específicamente si la cantidad de pacientes es igual en los tres reportes"""
    
    st.subheader("✅ Verificación de Igualdad de Pacientes")
    
    if len(dataframes) < 3:
        st.warning("Se necesitan los 3 reportes para verificar igualdad")
        return
    
    pacientes_por_fuente = {}
    for nombre, df in dataframes.items():
        if 'IDENTIFICACION' in df.columns:
            pacientes_por_fuente[nombre] = df['IDENTIFICACION'].nunique()
    
    if len(pacientes_por_fuente) == 3:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("SISPRO", f"{pacientes_por_fuente.get('SISPRO', 0):,}")
        with col2:
            st.metric("EPI12", f"{pacientes_por_fuente.get('EPI12', 0):,}")
        with col3:
            st.metric("EPI15", f"{pacientes_por_fuente.get('EPI15', 0):,}")
        
        valores = list(pacientes_por_fuente.values())
        if len(set(valores)) == 1:
            st.success("🎉 ¡TODOS LOS REPORTES TIENEN LA MISMA CANTIDAD DE PACIENTES!")
            st.balloons()
        else:
            st.warning("⚠️ Los reportes tienen DIFERENTE cantidad de pacientes")
            
            # Mostrar diferencias detalladas
            max_pac = max(valores)
            min_pac = min(valores)
            
            st.write(f"**Diferencia máxima:** {max_pac - min_pac:,} pacientes")
            st.write(f"**Porcentaje de diferencia:** {((max_pac - min_pac) / max_pac) * 100:.2f}%")
            
            # Identificar qué fuente tiene más/menos
            for nombre, cantidad in pacientes_por_fuente.items():
                if cantidad == max_pac:
                    st.info(f"📈 **{nombre}** tiene la mayor cantidad: {cantidad:,} pacientes")
                elif cantidad == min_pac:
                    st.warning(f"📉 **{nombre}** tiene la menor cantidad: {cantidad:,} pacientes")

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
                st.write(f"**Rango de edad:** {estadisticas.get('edad_min', 'N/A')} - {estadisticas.get('edad_max', 'N/A')} años")

# Inicializar session_state
if 'dataframes' not in st.session_state:
    st.session_state.dataframes = {}
if 'infos' not in st.session_state:
    st.session_state.infos = {}

# Interfaz principal
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📤 Carga de Archivos", 
    "📊 Análisis por Fuente", 
    "🔍 Validación de Consistencia",
    "📈 Grupos Etarios y Enfermedades",
    "📋 Reporte Consolidado"
])

with tab1:
    st.header("Carga de Archivos SISPRO, EPI12 y EPI15")
    st.markdown("""
    <div class="info-box">
    💡 <b>Instrucciones:</b> Sube los archivos Excel (.xls o .xlsx) correspondientes a cada tipo de formato.
    La aplicación validará automáticamente las columnas, detectará duplicados y generará estadísticas.
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
    st.header("🔍 Validación de Consistencia de Datos")
    
    if st.session_state.dataframes:
        # Verificar igualdad de pacientes
        verificar_igualdad_pacientes(st.session_state.dataframes)
        
        st.markdown("---")
        
        # Comparar registros temporales (mensual y anual)
        comparar_registros_temporales(st.session_state.dataframes)
    else:
        st.info("ℹ️ No hay archivos cargados para validar")

with tab4:
    st.header("📈 Análisis por Grupos Etarios y Enfermedades")
    
    if st.session_state.dataframes:
        # Mostrar comparativa de grupos etarios
        st.subheader("📊 Comparativa por Grupo Etario")
        
        comparativa_data = []
        for nombre, df in st.session_state.dataframes.items():
            if 'GRUPO_ETARIO' in df.columns:
                distribucion = df['GRUPO_ETARIO'].value_counts()
                for grupo, count in distribucion.items():
                    if grupo != 'Sin dato':
                        comparativa_data.append({
                            'Fuente': nombre,
                            'Grupo Etario': grupo,
                            'Cantidad': count
                        })
        
        if comparativa_data:
            comparativa_df = pd.DataFrame(comparativa_data)
            pivot_df = comparativa_df.pivot(index='Grupo Etario', columns='Fuente', values='Cantidad').fillna(0)
            st.dataframe(pivot_df, use_container_width=True)
            st.bar_chart(pivot_df)
        else:
            st.warning("No se encontraron datos de grupos etarios")
        
        st.markdown("---")
        
        # Mostrar comparativa de enfermedades
        st.subheader("🔍 Comparativa de Enfermedades por Fuente")
        
        for nombre, df in st.session_state.dataframes.items():
            if 'CODIGO_CIE10' in df.columns:
                st.write(f"**{nombre}** - Top 10 Diagnósticos")
                top = df['CODIGO_CIE10'].value_counts().head(10)
                col1, col2 = st.columns(2)
                with col1:
                    st.dataframe(top, use_container_width=True)
                with col2:
                    st.bar_chart(top)
    else:
        st.info("ℹ️ No hay archivos cargados para analizar")

with tab5:
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
                'Diagnósticos Únicos': estadisticas.get('diagnosticos_unicos', 'N/A'),
                'Edad Promedio': estadisticas.get('edad_promedio', 'N/A')
            })
        
        st.dataframe(pd.DataFrame(resumen_consolidado), use_container_width=True)
        
        # Opciones de exportación
        st.subheader("💾 Exportar Reportes")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Exportar Datos Consolidados a Excel"):
                try:
                    from io import BytesIO
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        for nombre, df in st.session_state.dataframes.items():
                            df.to_excel(writer, sheet_name=nombre[:31], index=False)
                        
                        resumen_df = pd.DataFrame(resumen_consolidado)
                        resumen_df.to_excel(writer, sheet_name='Resumen', index=False)
                    
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
**Versión:** 5.0  
**Desarrollador:** Willian Almenar  
**Fecha:** 2024  
**Propósito:** Validación y análisis de datos de morbilidad
""")

st.sidebar.markdown("### 📚 Formatos Soportados")
st.sidebar.markdown("""
- **SISPRO:** Sistema de Información de Protección Social  
- **EPI12:** Encuesta de Prevalencia Institucional 12  
- **EPI15:** Encuesta de Prevalencia Institucional 15
""")

st.sidebar.markdown("### 🛠️ Funcionalidades")
st.sidebar.markdown("""
- ✅ Detección de pacientes duplicados  
- ✅ Comparación entre fuentes  
- ✅ Verificación de igualdad de pacientes  
- ✅ Comparación mensual y anual  
- ✅ Generación de reportes de inconsistencias
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

st.sidebar.markdown("---")
st.sidebar.markdown("### 📝 Nota")
st.sidebar.markdown("""
Este sistema valida la consistencia de los datos entre SISPRO, EPI12 y EPI15,
comparando mensual y anualmente los registros para identificar inconsistencias.
""")
