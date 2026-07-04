import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

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
    # Crear una columna de identificación única
    if 'NUMERO_DOCUMENTO' in df.columns:
        df['IDENTIFICACION'] = df['NUMERO_DOCUMENTO'].astype(str).str.strip()
    elif 'DOCUMENTO' in df.columns:
        df['IDENTIFICACION'] = df['DOCUMENTO'].astype(str).str.strip()
    else:
        df['IDENTIFICACION'] = df.index.astype(str)
    
    # Crear nombre completo para comparación adicional
    if 'NOMBRE_PACIENTE' in df.columns and 'APELLIDO_PACIENTE' in df.columns:
        df['NOMBRE_COMPLETO'] = df['NOMBRE_PACIENTE'].astype(str).str.strip() + ' ' + df['APELLIDO_PACIENTE'].astype(str).str.strip()
    elif 'NOMBRE_PACIENTE' in df.columns:
        df['NOMBRE_COMPLETO'] = df['NOMBRE_PACIENTE'].astype(str).str.strip()
    else:
        df['NOMBRE_COMPLETO'] = df['IDENTIFICACION']
    
    return df

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
        
        # Procesar datos según el tipo
        df = procesar_datos(df, tipo_archivo)
        
        # Normalizar identificación
        df = normalizar_identificacion(df)
        
        # Agregar grupo etario si existe columna EDAD
        if 'EDAD' in df.columns:
            df['GRUPO_ETARIO'] = df['EDAD'].apply(asignar_grupo_etario)
        
        # Detectar duplicados
        info["duplicados"] = detectar_duplicados(df)
        
        # Estadísticas adicionales
        info["estadisticas"] = generar_estadisticas(df, tipo_archivo)
        
        return df, info
        
    except Exception as e:
        return None, f"Error al procesar el archivo: {str(e)}"

def detectar_duplicados(df):
    """Detecta registros duplicados en el dataframe"""
    duplicados_info = {}
    
    # Duplicados por identificación
    if 'IDENTIFICACION' in df.columns:
        duplicados_identificacion = df[df.duplicated(subset=['IDENTIFICACION'], keep=False)]
        duplicados_info['por_identificacion'] = {
            'cantidad': len(duplicados_identificacion),
            'registros_unicos': duplicados_identificacion['IDENTIFICACION'].nunique(),
            'ejemplos': duplicados_identificacion[['IDENTIFICACION', 'NOMBRE_COMPLETO']].head(10).to_dict('records')
        }
    
    # Duplicados exactos (todas las columnas)
    duplicados_exactos = df[df.duplicated(keep=False)]
    duplicados_info['exactos'] = {
        'cantidad': len(duplicados_exactos),
        'registros_unicos': len(duplicados_exactos) // 2 if len(duplicados_exactos) > 0 else 0
    }
    
    return duplicados_info

def procesar_datos(df, tipo_archivo):
    """Procesa datos según el tipo de archivo"""
    # Convertir fechas si existe la columna
    if 'FECHA_ATENCION' in df.columns:
        try:
            df['FECHA_ATENCION'] = pd.to_datetime(df['FECHA_ATENCION'], errors='coerce')
            df['AÑO'] = df['FECHA_ATENCION'].dt.year
            df['MES'] = df['FECHA_ATENCION'].dt.month
        except:
            pass
    
    # Convertir EDAD a numérico
    if 'EDAD' in df.columns:
        try:
            df['EDAD'] = pd.to_numeric(df['EDAD'], errors='coerce')
        except:
            pass
    
    return df

def generar_estadisticas(df, tipo_archivo):
    """Genera estadísticas relevantes para cada tipo de archivo"""
    estadisticas = {}
    
    # Estadísticas generales
    estadisticas["total_registros"] = len(df)
    estadisticas["columnas_totales"] = len(df.columns)
    
    # Pacientes únicos
    if 'IDENTIFICACION' in df.columns:
        estadisticas["pacientes_unicos"] = df['IDENTIFICACION'].nunique()
    
    # Estadísticas por tipo
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
    
    if 'EDAD' in df.columns:
        try:
            df_edad = df['EDAD'].dropna()
            if len(df_edad) > 0:
                estadisticas["edad_promedio"] = round(df_edad.mean(), 2)
                estadisticas["edad_min"] = df_edad.min()
                estadisticas["edad_max"] = df_edad.max()
                estadisticas["edad_mediana"] = df_edad.median()
        except:
            pass
    
    # Distribución por grupo etario
    if 'GRUPO_ETARIO' in df.columns:
        try:
            estadisticas["distribucion_grupo_etario"] = df['GRUPO_ETARIO'].value_counts().to_dict()
        except:
            pass
    
    return estadisticas

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
                st.write(f"**Edad mediana:** {estadisticas.get('edad_mediana', 'N/A')} años")
            if 'distribucion_sexo' in estadisticas:
                st.write("**Distribución por sexo:**")
                for sexo, count in estadisticas['distribucion_sexo'].items():
                    st.write(f"- {sexo}: {count}")

def validar_consistencia_pacientes(dataframes):
    """Valida la consistencia de pacientes entre las tres fuentes"""
    
    if len(dataframes) < 2:
        st.warning("Se necesitan al menos 2 fuentes para comparar")
        return
    
    st.subheader("🔍 Validación de Consistencia de Pacientes")
    
    # Extraer identificaciones de cada fuente
    identificaciones = {}
    nombres_completos = {}
    
    for nombre, df in dataframes.items():
        if 'IDENTIFICACION' in df.columns:
            identificaciones[nombre] = set(df['IDENTIFICACION'].dropna().astype(str))
            if 'NOMBRE_COMPLETO' in df.columns:
                # Crear un diccionario de identificación -> nombre
                nombres_completos[nombre] = df.set_index('IDENTIFICACION')['NOMBRE_COMPLETO'].to_dict()
    
    if len(identificaciones) >= 2:
        # Análisis de conjuntos
        fuentes = list(identificaciones.keys())
        
        # Pacientes únicos por fuente
        st.write("### 📊 Resumen de Pacientes por Fuente")
        resumen_pacientes = []
        for fuente in fuentes:
            resumen_pacientes.append({
                'Fuente': fuente,
                'Pacientes únicos': len(identificaciones[fuente]),
                'Total registros': len(dataframes[fuente])
            })
        st.dataframe(pd.DataFrame(resumen_pacientes), use_container_width=True)
        
        # Comparaciones entre pares
        st.write("### 🔄 Comparación entre Fuentes")
        
        for i in range(len(fuentes)):
            for j in range(i+1, len(fuentes)):
                fuente1, fuente2 = fuentes[i], fuentes[j]
                set1, set2 = identificaciones[fuente1], identificaciones[fuente2]
                
                # Calcular intersecciones y diferencias
                comunes = set1 & set2
                solo_fuente1 = set1 - set2
                solo_fuente2 = set2 - set1
                
                # Crear métricas visuales
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"**{fuente1} vs {fuente2}**")
                
                with col2:
                    st.metric(
                        "Pacientes comunes",
                        f"{len(comunes):,}",
                        f"{len(comunes)/len(set1)*100:.1f}% del total"
                    )
                
                with col3:
                    st.metric(
                        f"Solo en {fuente1}",
                        f"{len(solo_fuente1):,}",
                        f"{len(solo_fuente1)/len(set1)*100:.1f}%"
                    )
                
                with col4:
                    st.metric(
                        f"Solo en {fuente2}",
                        f"{len(solo_fuente2):,}",
                        f"{len(solo_fuente2)/len(set2)*100:.1f}%"
                    )
                
                # Mostrar ejemplos de pacientes no comunes
                with st.expander(f"Ver detalles de pacientes no comunes entre {fuente1} y {fuente2}"):
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        if solo_fuente1:
                            st.write(f"**Pacientes solo en {fuente1} (primeros 10):**")
                            ejemplos_solo1 = list(solo_fuente1)[:10]
                            for ident in ejemplos_solo1:
                                nombre = nombres_completos.get(fuente1, {}).get(ident, ident)
                                st.write(f"- {nombre} (ID: {ident})")
                    
                    with col_b:
                        if solo_fuente2:
                            st.write(f"**Pacientes solo en {fuente2} (primeros 10):**")
                            ejemplos_solo2 = list(solo_fuente2)[:10]
                            for ident in ejemplos_solo2:
                                nombre = nombres_completos.get(fuente2, {}).get(ident, ident)
                                st.write(f"- {nombre} (ID: {ident})")
        
        # Análisis de consistencia general
        st.write("### 📈 Análisis de Consistencia General")
        
        # Encontrar pacientes en todas las fuentes
        if len(fuentes) >= 3:
            conjunto_todas = set.intersection(*[identificaciones[f] for f in fuentes])
            st.metric("Pacientes presentes en todas las fuentes", len(conjunto_todas))
            
            # Encontrar pacientes en al menos 2 fuentes
            conjunto_al_menos_dos = set()
            for i in range(len(fuentes)):
                for j in range(i+1, len(fuentes)):
                    conjunto_al_menos_dos.update(identificaciones[fuentes[i]] & identificaciones[fuentes[j]])
            
            st.metric("Pacientes en al menos 2 fuentes", len(conjunto_al_menos_dos))
        
        # Diagrama de Venn (textual)
        st.write("### 🎯 Resumen de Intersecciones")
        
        # Crear tabla de intersecciones
        intersecciones_data = []
        for fuente in fuentes:
            intersecciones_data.append({
                'Fuente': fuente,
                'Total únicos': len(identificaciones[fuente]),
                'Comunes con otras': sum([len(identificaciones[fuente] & identificaciones[otra]) for otra in fuentes if otra != fuente]),
                'Exclusivos': len(identificaciones[fuente] - set.union(*[identificaciones[otra] for otra in fuentes if otra != fuente]))
            })
        
        st.dataframe(pd.DataFrame(intersecciones_data), use_container_width=True)

def detectar_posibles_duplicados(dataframes):
    """Detecta posibles datos duplicados o multiplicados en los reportes"""
    
    st.subheader("⚠️ Detección de Posibles Duplicados o Multiplicados")
    
    for nombre, df in dataframes.items():
        st.write(f"### 📋 {nombre}")
        
        # 1. Duplicados por identificación
        if 'IDENTIFICACION' in df.columns:
            duplicados_id = df[df.duplicated(subset=['IDENTIFICACION'], keep=False)]
            
            if len(duplicados_id) > 0:
                st.markdown(f'<div class="danger-box">', unsafe_allow_html=True)
                st.write(f"**⚠️ Se encontraron {len(duplicados_id):,} registros con identificación duplicada**")
                st.write(f"**Pacientes con duplicados:** {duplicados_id['IDENTIFICACION'].nunique():,}")
                
                # Mostrar estadísticas de duplicados
                duplicados_stats = duplicados_id.groupby('IDENTIFICACION').size().reset_index(name='conteo')
                duplicados_stats = duplicados_stats[duplicados_stats['conteo'] > 1]
                
                st.write("**Frecuencia de duplicados:**")
                freq_duplicados = duplicados_stats['conteo'].value_counts().sort_index()
                st.dataframe(pd.DataFrame({
                    'Veces repetido': freq_duplicados.index,
                    'Número de pacientes': freq_duplicados.values
                }), use_container_width=True)
                
                # Mostrar ejemplos
                with st.expander(f"Ver ejemplos de pacientes duplicados (primeros 10)"):
                    ejemplos = duplicados_id[['IDENTIFICACION', 'NOMBRE_COMPLETO']].drop_duplicates().head(10)
                    for idx, row in ejemplos.iterrows():
                        count = len(duplicados_id[duplicados_id['IDENTIFICACION'] == row['IDENTIFICACION']])
                        st.write(f"- {row['NOMBRE_COMPLETO']} (ID: {row['IDENTIFICACION']}) - aparece {count} veces")
                
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.success("✅ No se encontraron duplicados por identificación")
        
        # 2. Duplicados exactos (todas las columnas)
        duplicados_exactos = df[df.duplicated(keep=False)]
        if len(duplicados_exactos) > 0:
            st.markdown(f'<div class="warning-box">', unsafe_allow_html=True)
            st.write(f"**⚠️ Se encontraron {len(duplicados_exactos):,} registros exactamente duplicados**")
            st.write(f"**Registros únicos duplicados:** {len(duplicados_exactos) // 2}")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.success("✅ No se encontraron duplicados exactos")
        
        # 3. Posibles multiplicación por EPS o diagnóstico
        if 'CODIGO_EPS' in df.columns and 'IDENTIFICACION' in df.columns:
            # Verificar si un paciente aparece en múltiples EPS
            pacientes_multi_eps = df.groupby('IDENTIFICACION')['CODIGO_EPS'].nunique()
            pacientes_multi_eps = pacientes_multi_eps[pacientes_multi_eps > 1]
            
            if len(pacientes_multi_eps) > 0:
                st.markdown(f'<div class="warning-box">', unsafe_allow_html=True)
                st.write(f"**⚠️ {len(pacientes_multi_eps):,} pacientes aparecen en múltiples EPS**")
                
                with st.expander("Ver ejemplos"):
                    ejemplos_multi = pacientes_multi_eps.head(10)
                    for ident, num_eps in ejemplos_multi.items():
                        eps_list = df[df['IDENTIFICACION'] == ident]['CODIGO_EPS'].unique()
                        st.write(f"- ID: {ident} - {num_eps} EPS: {', '.join(eps_list)}")
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        # 4. Verificar proporción registros vs pacientes únicos
        if 'IDENTIFICACION' in df.columns:
            total_registros = len(df)
            pacientes_unicos = df['IDENTIFICACION'].nunique()
            ratio = total_registros / pacientes_unicos if pacientes_unicos > 0 else 0
            
            st.write("**📊 Proporción Registros/Pacientes:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Registros", f"{total_registros:,}")
            with col2:
                st.metric("Pacientes Únicos", f"{pacientes_unicos:,}")
            with col3:
                st.metric("Ratio", f"{ratio:.2f} registros/paciente")
            
            if ratio > 2:
                st.warning(f"⚠️ El ratio es alto ({ratio:.2f}). Puede indicar multiplicación de datos.")
            elif ratio > 1.5:
                st.info(f"ℹ️ El ratio es moderado ({ratio:.2f}). Puede haber algunos pacientes con múltiples atenciones.")
            else:
                st.success(f"✅ El ratio es bajo ({ratio:.2f}). La mayoría de pacientes tienen una atención.")

def verificar_consistencia_totales(dataframes):
    """Verifica la consistencia en los totales entre los tres reportes"""
    
    if len(dataframes) < 2:
        return
    
    st.subheader("📊 Verificación de Consistencia de Totales")
    
    # Crear tabla comparativa de totales
    comparativa_totales = []
    
    for nombre, df in dataframes.items():
        total_registros = len(df)
        pacientes_unicos = df['IDENTIFICACION'].nunique() if 'IDENTIFICACION' in df.columns else 0
        diagnosticos_unicos = df['CODIGO_CIE10'].nunique() if 'CODIGO_CIE10' in df.columns else 0
        
        comparativa_totales.append({
            'Fuente': nombre,
            'Total Registros': total_registros,
            'Pacientes Únicos': pacientes_unicos,
            'Diagnósticos Únicos': diagnosticos_unicos,
            'Promedio Atenciones/Paciente': round(total_registros / pacientes_unicos, 2) if pacientes_unicos > 0 else 0
        })
    
    df_comparativa = pd.DataFrame(comparativa_totales)
    
    # Mostrar tabla
    st.dataframe(df_comparativa, use_container_width=True)
    
    # Verificar diferencias significativas
    if len(df_comparativa) >= 2:
        st.write("### 📈 Análisis de Diferencias")
        
        # Calcular diferencias porcentuales
        totales = df_comparativa['Total Registros'].values
        promedio = np.mean(totales)
        
        for idx, row in df_comparativa.iterrows():
            diferencia = ((row['Total Registros'] - promedio) / promedio) * 100
            color = "🟢" if abs(diferencia) < 5 else "🟡" if abs(diferencia) < 15 else "🔴"
            
            st.write(f"{color} **{row['Fuente']}:** {row['Total Registros']:,} registros "
                    f"({diferencia:+.1f}% del promedio de {promedio:,.0f})")
            
            if abs(diferencia) > 15:
                st.warning(f"⚠️ {row['Fuente']} muestra una diferencia significativa del {diferencia:.1f}% respecto al promedio")
        
        # Comparativa de pacientes únicos
        st.write("### 👥 Comparativa de Pacientes Únicos")
        
        pacientes = df_comparativa['Pacientes Únicos'].values
        promedio_pacientes = np.mean(pacientes)
        
        for idx, row in df_comparativa.iterrows():
            diferencia = ((row['Pacientes Únicos'] - promedio_pacientes) / promedio_pacientes) * 100
            color = "🟢" if abs(diferencia) < 5 else "🟡" if abs(diferencia) < 15 else "🔴"
            
            st.write(f"{color} **{row['Fuente']}:** {row['Pacientes Únicos']:,} pacientes "
                    f"({diferencia:+.1f}% del promedio de {promedio_pacientes:,.0f})")

def mostrar_analisis_detallado(df, info, tipo_archivo):
    """Muestra análisis detallado incluyendo distribución de grupos etarios"""
    
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
                st.write(f"**Edad mediana:** {estadisticas.get('edad_mediana', 'N/A')} años")
            if 'distribucion_sexo' in estadisticas:
                st.write("**Distribución por sexo:**")
                for sexo, count in estadisticas['distribucion_sexo'].items():
                    st.write(f"- {sexo}: {count}")
    
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
            
            # Mostrar análisis completo
            mostrar_analisis_detallado(df, info, fuente_seleccionada)
            
            # Mostrar detección de duplicados
            if info.get("duplicados"):
                st.subheader("🔍 Detección de Duplicados")
                duplicados = info["duplicados"]
                
                if duplicados.get('por_identificacion', {}).get('cantidad', 0) > 0:
                    st.warning(f"⚠️ Se encontraron {duplicados['por_identificacion']['cantidad']} registros con identificación duplicada")
                else:
                    st.success("✅ No se encontraron duplicados por identificación")
                
                if duplicados.get('exactos', {}).get('cantidad', 0) > 0:
                    st.warning(f"⚠️ Se encontraron {duplicados['exactos']['cantidad']} registros exactamente duplicados")
                else:
                    st.success("✅ No se encontraron duplicados exactos")
    else:
        st.info("ℹ️ No hay archivos cargados. Por favor, carga archivos en la pestaña 'Carga de Archivos'")

with tab3:
    st.header("🔍 Validación de Consistencia de Datos")
    
    if st.session_state.dataframes:
        # Validar consistencia de pacientes
        validar_consistencia_pacientes(st.session_state.dataframes)
        
        st.markdown("---")
        
        # Detectar posibles duplicados
        detectar_posibles_duplicados(st.session_state.dataframes)
        
        st.markdown("---")
        
        # Verificar consistencia de totales
        verificar_consistencia_totales(st.session_state.dataframes)
    else:
        st.info("ℹ️ No hay archivos cargados para validar")

with tab4:
    st.header("📈 Análisis por Grupos Etarios y Enfermedades")
    
    if st.session_state.dataframes:
        # Mostrar comparativa de grupos etarios
        st.subheader("📊 Comparativa por Grupo Etario")
        
        # Preparar datos para comparativa de grupos etarios
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
        
        # Crear resumen consolidado
        resumen_consolidado = []
        for nombre, df in st.session_state.dataframes.items():
            info = st.session_state.infos.get(nombre, {})
            estadisticas = info.get('estadisticas', {})
            
            resumen_consolidado.append({
                'Fuente': nombre,
                'Registros': len(df),
                'Pacientes Únicos': estadisticas.get('pacientes_unicos', 'N/A'),
                'Diagnósticos Únicos': estadisticas.get('diagnosticos_unicos', 'N/A'),
                'Edad Promedio': estadisticas.get('edad_promedio', 'N/A'),
                'Rango Edad': f"{estadisticas.get('edad_min', 'N/A')} - {estadisticas.get('edad_max', 'N/A')}" if 'edad_min' in estadisticas else 'N/A'
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
                        
                        # Añadir hoja de resumen
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
        
        with col2:
            # Generar reporte de validación
            if st.button("📄 Generar Reporte de Validación"):
                reporte = "REPORTE DE VALIDACIÓN DE DATOS\n"
                reporte += "="*60 + "\n"
                reporte += f"Fecha de generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                
                for nombre, df in st.session_state.dataframes.items():
                    info = st.session_state.infos.get(nombre, {})
                    estadisticas = info.get('estadisticas', {})
                    duplicados = info.get('duplicados', {})
                    
                    reporte += f"📊 {nombre}\n"
                    reporte += "-"*40 + "\n"
                    reporte += f"Total registros: {len(df)}\n"
                    reporte += f"Pacientes únicos: {estadisticas.get('pacientes_unicos', 'N/A')}\n"
                    reporte += f"Diagnósticos únicos: {estadisticas.get('diagnosticos_unicos', 'N/A')}\n"
                    reporte += f"Edad promedio: {estadisticas.get('edad_promedio', 'N/A')} años\n"
                    
                    # Información de duplicados
                    if duplicados:
                        por_id = duplicados.get('por_identificacion', {})
                        exactos = duplicados.get('exactos', {})
                        reporte += f"\n⚠️ DUPLICADOS:\n"
                        reporte += f"  - Por identificación: {por_id.get('cantidad', 0)} registros\n"
                        reporte += f"  - Exactos: {exactos.get('cantidad', 0)} registros\n"
                    
                    reporte += "\n"
                
                # Agregar comparativa de pacientes
                reporte += "\n" + "="*60 + "\n"
                reporte += "COMPARATIVA DE PACIENTES ENTRE FUENTES\n"
                reporte += "="*60 + "\n"
                
                identificaciones = {}
                for nombre, df in st.session_state.dataframes.items():
                    if 'IDENTIFICACION' in df.columns:
                        identificaciones[nombre] = set(df['IDENTIFICACION'].dropna().astype(str))
                
                if len(identificaciones) >= 2:
                    fuentes = list(identificaciones.keys())
                    for i in range(len(fuentes)):
                        for j in range(i+1, len(fuentes)):
                            f1, f2 = fuentes[i], fuentes[j]
                            comunes = identificaciones[f1] & identificaciones[f2]
                            solo_f1 = identificaciones[f1] - identificaciones[f2]
                            solo_f2 = identificaciones[f2] - identificaciones[f1]
                            
                            reporte += f"\n{f1} vs {f2}:\n"
                            reporte += f"  - Pacientes comunes: {len(comunes)}\n"
                            reporte += f"  - Solo en {f1}: {len(solo_f1)}\n"
                            reporte += f"  - Solo en {f2}: {len(solo_f2)}\n"
                
                st.download_button(
                    label="📥 Descargar Reporte de Validación",
                    data=reporte,
                    file_name=f"reporte_validacion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
    else:
        st.info("ℹ️ No hay archivos cargados para generar reportes")

# Barra lateral
st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ Información de la Aplicación")
st.sidebar.markdown("""
**Versión:** 4.0  
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

st.sidebar.markdown("### 🛠️ Funcionalidades de Validación")
st.sidebar.markdown("""
- ✅ Detección de pacientes duplicados  
- ✅ Comparación entre fuentes  
- ✅ Identificación de datos omitidos  
- ✅ Análisis de consistencia  
- ✅ Exportación de reportes
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
identificando pacientes duplicados, omitidos y verificando que los totales coincidan.
""")
