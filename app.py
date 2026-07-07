import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from io import BytesIO

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
    .discrepancy-box {
        background-color: #fff3e0;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #ff9800;
        margin-bottom: 1rem;
    }
    .grupo-box {
        background-color: #e3f2fd;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.2rem 0;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1>🏥 Gestor de Morbilidad - Análisis de Discrepancias</h1><p>Willian Almenar</p></div>', unsafe_allow_html=True)
st.markdown("---")

# Diccionario de mapeo de columnas esperadas
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
        "SERVICIO", "SEXO", "EDAD", "MUNICIPIO", "CAUSA_CONSULTA"
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
    if 'NUMERO_DOCUMENTO' in df.columns:
        df['IDENTIFICACION'] = df['NUMERO_DOCUMENTO'].astype(str).str.strip()
    elif 'DOCUMENTO' in df.columns:
        df['IDENTIFICACION'] = df['DOCUMENTO'].astype(str).str.strip()
    else:
        df['IDENTIFICACION'] = df.index.astype(str)
    return df

def analizar_archivo(file, tipo_archivo):
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
        
        df = normalizar_identificacion(df)
        
        if 'EDAD' in df.columns:
            df['GRUPO_ETARIO'] = df['EDAD'].apply(asignar_grupo_etario)
        
        if 'FECHA_ATENCION' in df.columns:
            try:
                df['FECHA_ATENCION'] = pd.to_datetime(df['FECHA_ATENCION'], errors='coerce')
                df['AÑO'] = df['FECHA_ATENCION'].dt.year
                df['MES'] = df['FECHA_ATENCION'].dt.month
                df['AÑO_MES'] = df['FECHA_ATENCION'].dt.strftime('%Y-%m')
                df['MES_NOMBRE'] = df['FECHA_ATENCION'].dt.strftime('%B')
            except:
                df['AÑO'] = None
                df['MES'] = None
                df['AÑO_MES'] = None
                df['MES_NOMBRE'] = None
        
        info["estadisticas"] = generar_estadisticas(df, tipo_archivo)
        
        return df, info
        
    except Exception as e:
        return None, f"Error al procesar el archivo: {str(e)}"

def generar_estadisticas(df, tipo_archivo):
    estadisticas = {}
    estadisticas["total_registros"] = len(df)
    
    if 'IDENTIFICACION' in df.columns:
        estadisticas["pacientes_unicos"] = df['IDENTIFICACION'].nunique()
    
    return estadisticas

def filtrar_por_fecha(df, año_inicio, mes_inicio, año_fin, mes_fin):
    if df is None or 'AÑO' not in df.columns or 'MES' not in df.columns:
        return df
    
    if df['AÑO'].isna().all():
        return df
    
    try:
        if 'FECHA_ATENCION' in df.columns:
            fecha_inicio = datetime(año_inicio, mes_inicio, 1)
            if mes_fin == 12:
                fecha_fin = datetime(año_fin, mes_fin, 31)
            else:
                fecha_fin = datetime(año_fin, mes_fin + 1, 1) - pd.Timedelta(days=1)
            
            mask = (df['FECHA_ATENCION'] >= fecha_inicio) & (df['FECHA_ATENCION'] <= fecha_fin)
            df_filtrado = df[mask].copy()
            return df_filtrado
    except:
        pass
    
    return df

def analizar_totales(dataframes, año_inicio, mes_inicio, año_fin, mes_fin):
    """
    Analiza totales de SISPRO, EPI12 y EPI15
    - SISPRO: Total pacientes por mes/año y grupo etario
    - EPI12: Total pacientes por mes/año y grupo etario
    - EPI15: Total de Causas de Consulta por mes/año
    """
    
    dataframes_filtrados = {}
    for nombre, df in dataframes.items():
        dataframes_filtrados[nombre] = filtrar_por_fecha(df, año_inicio, mes_inicio, año_fin, mes_fin)
    
    if 'SISPRO' not in dataframes_filtrados or 'EPI12' not in dataframes_filtrados or 'EPI15' not in dataframes_filtrados:
        return None, "Faltan archivos para el análisis"
    
    df_sispro = dataframes_filtrados['SISPRO']
    df_epi12 = dataframes_filtrados['EPI12']
    df_epi15 = dataframes_filtrados['EPI15']
    
    if df_sispro is None or len(df_sispro) == 0:
        return None, "No hay datos de SISPRO para el período seleccionado"
    
    # Obtener meses disponibles
    if 'AÑO_MES' not in df_sispro.columns or df_sispro['AÑO_MES'].isna().all():
        return None, "No se encontraron fechas válidas en SISPRO"
    
    meses_disponibles = sorted(df_sispro['AÑO_MES'].dropna().unique())
    
    if len(meses_disponibles) == 0:
        return None, "No se encontraron meses con datos en SISPRO"
    
    resultados = []
    
    for mes in meses_disponibles:
        # ============ SISPRO ============
        df_sispro_mes = df_sispro[df_sispro['AÑO_MES'] == mes]
        total_sispro = df_sispro_mes['IDENTIFICACION'].nunique()
        grupos_sispro = df_sispro_mes['GRUPO_ETARIO'].value_counts().to_dict()
        
        # ============ EPI12 ============
        if df_epi12 is not None and len(df_epi12) > 0 and 'AÑO_MES' in df_epi12.columns:
            df_epi12_mes = df_epi12[df_epi12['AÑO_MES'] == mes]
            total_epi12 = df_epi12_mes['IDENTIFICACION'].nunique() if len(df_epi12_mes) > 0 else 0
            grupos_epi12 = df_epi12_mes['GRUPO_ETARIO'].value_counts().to_dict() if len(df_epi12_mes) > 0 else {}
        else:
            total_epi12 = 0
            grupos_epi12 = {}
        
        # ============ EPI15 ============
        if df_epi15 is not None and len(df_epi15) > 0 and 'AÑO_MES' in df_epi15.columns:
            df_epi15_mes = df_epi15[df_epi15['AÑO_MES'] == mes]
            total_epi15 = len(df_epi15_mes) if len(df_epi15_mes) > 0 else 0
        else:
            total_epi15 = 0
        
        # ============ CALCULAR DISCREPANCIAS ============
        diff_epi12 = total_epi12 - total_sispro
        diff_epi15 = total_epi15 - total_sispro
        
        # ============ GRUPOS ETARIOS ============
        grupos_diferencia = []
        if diff_epi12 != 0:
            for grupo in GRUPOS_ETARIOS.keys():
                count_sispro = grupos_sispro.get(grupo, 0)
                count_epi12 = grupos_epi12.get(grupo, 0)
                if count_sispro != count_epi12:
                    grupos_diferencia.append({
                        'grupo': grupo,
                        'sispro': count_sispro,
                        'epi12': count_epi12,
                        'diferencia': count_sispro - count_epi12
                    })
        
        resultados.append({
            'mes': mes,
            'sispro': total_sispro,
            'epi12': total_epi12,
            'epi15': total_epi15,
            'diff_epi12': diff_epi12,
            'diff_epi15': diff_epi15,
            'grupos_sispro': grupos_sispro,
            'grupos_epi12': grupos_epi12,
            'grupos_diferencia': grupos_diferencia
        })
    
    # ============ ANÁLISIS ANUAL ============
    # Agrupar por año
    años_disponibles = sorted(df_sispro['AÑO'].dropna().unique())
    resultados_anuales = []
    
    for año in años_disponibles:
        # SISPRO anual
        df_sispro_año = df_sispro[df_sispro['AÑO'] == año]
        total_sispro_año = df_sispro_año['IDENTIFICACION'].nunique()
        grupos_sispro_año = df_sispro_año['GRUPO_ETARIO'].value_counts().to_dict()
        
        # EPI12 anual
        if df_epi12 is not None and len(df_epi12) > 0 and 'AÑO' in df_epi12.columns:
            df_epi12_año = df_epi12[df_epi12['AÑO'] == año]
            total_epi12_año = df_epi12_año['IDENTIFICACION'].nunique() if len(df_epi12_año) > 0 else 0
            grupos_epi12_año = df_epi12_año['GRUPO_ETARIO'].value_counts().to_dict() if len(df_epi12_año) > 0 else {}
        else:
            total_epi12_año = 0
            grupos_epi12_año = {}
        
        # EPI15 anual
        if df_epi15 is not None and len(df_epi15) > 0 and 'AÑO' in df_epi15.columns:
            df_epi15_año = df_epi15[df_epi15['AÑO'] == año]
            total_epi15_año = len(df_epi15_año) if len(df_epi15_año) > 0 else 0
        else:
            total_epi15_año = 0
        
        # Diferencias anuales
        diff_epi12_año = total_epi12_año - total_sispro_año
        diff_epi15_año = total_epi15_año - total_sispro_año
        
        # Grupos etarios anuales
        grupos_diferencia_año = []
        if diff_epi12_año != 0:
            for grupo in GRUPOS_ETARIOS.keys():
                count_sispro = grupos_sispro_año.get(grupo, 0)
                count_epi12 = grupos_epi12_año.get(grupo, 0)
                if count_sispro != count_epi12:
                    grupos_diferencia_año.append({
                        'grupo': grupo,
                        'sispro': count_sispro,
                        'epi12': count_epi12,
                        'diferencia': count_sispro - count_epi12
                    })
        
        resultados_anuales.append({
            'año': año,
            'sispro': total_sispro_año,
            'epi12': total_epi12_año,
            'epi15': total_epi15_año,
            'diff_epi12': diff_epi12_año,
            'diff_epi15': diff_epi15_año,
            'grupos_sispro': grupos_sispro_año,
            'grupos_epi12': grupos_epi12_año,
            'grupos_diferencia': grupos_diferencia_año
        })
    
    return {
        'mensual': resultados,
        'anual': resultados_anuales
    }, None

def mostrar_reporte(resultados, año_inicio, mes_inicio, año_fin, mes_fin):
    """Muestra el reporte completo"""
    
    if resultados is None:
        return
    
    st.markdown(f"""
    <div style="background-color: #f8f9fa; padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
        <h3 style="color: #1E3A5F; margin: 0;">📄 REPORTE DE DISCREPANCIAS</h3>
        <p style="margin: 5px 0 0 0; color: #666;">
            Período: {mes_inicio:02d}/{año_inicio} al {mes_fin:02d}/{año_fin} | 
            Generado: {datetime.now().strftime("%d/%m/%Y %H:%M")}
        </p>
        <p style="margin: 0; color: #1E3A5F; font-weight: bold;">📌 SISPRO es la referencia (Total Real)</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ============ MENSUAL ============
    st.subheader("📊 ANÁLISIS MENSUAL")
    
    # Tabla comparativa mensual
    comparativa_data = []
    for d in resultados['mensual']:
        comparativa_data.append({
            'Mes': d['mes'],
            'SISPRO': d['sispro'],
            'EPI12': d['epi12'],
            'EPI15 (Causas Consulta)': d['epi15'],
            'Dif. EPI12': d['diff_epi12'],
            'Dif. EPI15': d['diff_epi15']
        })
    
    df_comparativa = pd.DataFrame(comparativa_data)
    st.dataframe(df_comparativa, use_container_width=True)
    
    # Gráfico mensual
    st.write("**📊 Gráfico Mensual**")
    chart_data = df_comparativa.set_index('Mes')[['SISPRO', 'EPI12', 'EPI15 (Causas Consulta)']]
    st.bar_chart(chart_data)
    
    # ============ DISCREPANCIAS MENSUALES ============
    st.markdown("---")
    st.subheader("⚠️ DISCREPANCIAS MENSUALES")
    
    meses_con_error = [d for d in resultados['mensual'] if d['diff_epi12'] != 0 or d['diff_epi15'] != 0]
    
    if not meses_con_error:
        st.success("✅ Todos los meses coinciden correctamente")
    else:
        st.warning(f"⚠️ Se encontraron {len(meses_con_error)} meses con discrepancias")
        
        for d in meses_con_error:
            st.markdown(f'<div class="discrepancy-box">', unsafe_allow_html=True)
            st.write(f"**📅 Mes: {d['mes']}**")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("SISPRO (Referencia)", d['sispro'])
            with col2:
                st.metric("EPI12", d['epi12'], delta=f"{d['diff_epi12']:+d}")
            with col3:
                st.metric("EPI15 (Causas Consulta)", d['epi15'], delta=f"{d['diff_epi15']:+d}")
            
            # Grupos etarios
            if d['diff_epi12'] != 0 and d['grupos_diferencia']:
                st.write("**🔴 Grupos etarios con diferencias en EPI12:**")
                grupos_df = pd.DataFrame(d['grupos_diferencia'])
                st.dataframe(grupos_df, use_container_width=True)
            
            # Recomendaciones
            if d['diff_epi12'] != 0:
                if d['diff_epi12'] < 0:
                    st.warning(f"📌 EPI12 debe agregar {abs(d['diff_epi12'])} registros")
                else:
                    st.warning(f"📌 EPI12 debe eliminar {d['diff_epi12']} registros")
            
            if d['diff_epi15'] != 0:
                if d['diff_epi15'] < 0:
                    st.warning(f"📌 EPI15 debe agregar {abs(d['diff_epi15'])} causas de consulta")
                else:
                    st.warning(f"📌 EPI15 debe eliminar {d['diff_epi15']} causas de consulta")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # ============ ANUAL ============
    st.markdown("---")
    st.subheader("📊 ANÁLISIS ANUAL")
    
    # Tabla comparativa anual
    anual_data = []
    for d in resultados['anual']:
        anual_data.append({
            'Año': d['año'],
            'SISPRO': d['sispro'],
            'EPI12': d['epi12'],
            'EPI15 (Causas Consulta)': d['epi15'],
            'Dif. EPI12': d['diff_epi12'],
            'Dif. EPI15': d['diff_epi15']
        })
    
    df_anual = pd.DataFrame(anual_data)
    st.dataframe(df_anual, use_container_width=True)
    
    # Gráfico anual
    st.write("**📊 Gráfico Anual**")
    chart_anual = df_anual.set_index('Año')[['SISPRO', 'EPI12', 'EPI15 (Causas Consulta)']]
    st.bar_chart(chart_anual)
    
    # ============ DISCREPANCIAS ANUALES ============
    st.markdown("---")
    st.subheader("⚠️ DISCREPANCIAS ANUALES")
    
    años_con_error = [d for d in resultados['anual'] if d['diff_epi12'] != 0 or d['diff_epi15'] != 0]
    
    if not años_con_error:
        st.success("✅ Todos los años coinciden correctamente")
    else:
        st.warning(f"⚠️ Se encontraron {len(años_con_error)} años con discrepancias")
        
        for d in años_con_error:
            st.markdown(f'<div class="discrepancy-box">', unsafe_allow_html=True)
            st.write(f"**📅 Año: {d['año']}**")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("SISPRO (Referencia)", d['sispro'])
            with col2:
                st.metric("EPI12", d['epi12'], delta=f"{d['diff_epi12']:+d}")
            with col3:
                st.metric("EPI15 (Causas Consulta)", d['epi15'], delta=f"{d['diff_epi15']:+d}")
            
            # Grupos etarios anuales
            if d['diff_epi12'] != 0 and d['grupos_diferencia']:
                st.write("**🔴 Grupos etarios con diferencias en EPI12:**")
                grupos_df = pd.DataFrame(d['grupos_diferencia'])
                st.dataframe(grupos_df, use_container_width=True)
            
            # Recomendaciones anuales
            if d['diff_epi12'] != 0:
                if d['diff_epi12'] < 0:
                    st.warning(f"📌 EPI12 debe agregar {abs(d['diff_epi12'])} registros")
                else:
                    st.warning(f"📌 EPI12 debe eliminar {d['diff_epi12']} registros")
            
            if d['diff_epi15'] != 0:
                if d['diff_epi15'] < 0:
                    st.warning(f"📌 EPI15 debe agregar {abs(d['diff_epi15'])} causas de consulta")
                else:
                    st.warning(f"📌 EPI15 debe eliminar {d['diff_epi15']} causas de consulta")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # ============ RESUMEN TOTAL ============
    st.markdown("---")
    st.subheader("📊 RESUMEN TOTAL DEL PERÍODO")
    
    total_sispro = sum(d['sispro'] for d in resultados['mensual'])
    total_epi12 = sum(d['epi12'] for d in resultados['mensual'])
    total_epi15 = sum(d['epi15'] for d in resultados['mensual'])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total SISPRO", f"{total_sispro:,}")
    with col2:
        st.metric("Total EPI12", f"{total_epi12:,}", delta=f"{total_epi12 - total_sispro:+,}")
    with col3:
        st.metric("Total EPI15 (Causas Consulta)", f"{total_epi15:,}", delta=f"{total_epi15 - total_sispro:+,}")
    with col4:
        if total_epi12 == total_sispro and total_epi15 == total_sispro:
            st.success("✅ Todos coinciden")
        else:
            st.warning("⚠️ Hay discrepancias")
    
    # ============ BOTONES DE DESCARGA ============
    st.markdown("---")
    st.subheader("💾 Descargar Reporte")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.download_button(
            label="📥 Descargar Reporte HTML",
            data=generar_html_reporte(resultados, año_inicio, mes_inicio, año_fin, mes_fin),
            file_name=f"reporte_discrepancias_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
            mime="text/html",
            use_container_width=True
        )
    
    with col2:
        if st.button("📊 Descargar Datos en Excel", use_container_width=True):
            try:
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_comparativa.to_excel(writer, sheet_name='Mensual', index=False)
                    df_anual.to_excel(writer, sheet_name='Anual', index=False)
                    
                    # Grupos etarios mensuales
                    grupos_data = []
                    for d in resultados['mensual']:
                        if d['grupos_diferencia']:
                            for g in d['grupos_diferencia']:
                                grupos_data.append({
                                    'Mes': d['mes'],
                                    'Grupo Etario': g['grupo'],
                                    'SISPRO': g['sispro'],
                                    'EPI12': g['epi12'],
                                    'Diferencia': g['diferencia']
                                })
                    if grupos_data:
                        pd.DataFrame(grupos_data).to_excel(writer, sheet_name='Grupos_Etarios_Mensual', index=False)
                    
                    # Grupos etarios anuales
                    grupos_data_anual = []
                    for d in resultados['anual']:
                        if d['grupos_diferencia']:
                            for g in d['grupos_diferencia']:
                                grupos_data_anual.append({
                                    'Año': d['año'],
                                    'Grupo Etario': g['grupo'],
                                    'SISPRO': g['sispro'],
                                    'EPI12': g['epi12'],
                                    'Diferencia': g['diferencia']
                                })
                    if grupos_data_anual:
                        pd.DataFrame(grupos_data_anual).to_excel(writer, sheet_name='Grupos_Etarios_Anual', index=False)
                    
                    # Resumen
                    resumen = pd.DataFrame([
                        {'Métrica': 'Total SISPRO', 'Valor': total_sispro},
                        {'Métrica': 'Total EPI12', 'Valor': total_epi12, 'Diferencia': total_epi12 - total_sispro},
                        {'Métrica': 'Total EPI15 (Causas Consulta)', 'Valor': total_epi15, 'Diferencia': total_epi15 - total_sispro}
                    ])
                    resumen.to_excel(writer, sheet_name='Resumen', index=False)
                
                output.seek(0)
                st.download_button(
                    label="📥 Descargar Excel",
                    data=output,
                    file_name=f"reporte_discrepancias_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Error al generar Excel: {str(e)}")

def generar_html_reporte(resultados, año_inicio, mes_inicio, año_fin, mes_fin):
    """Genera reporte HTML"""
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Reporte de Discrepancias</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #1E3A5F; text-align: center; border-bottom: 3px solid #1E3A5F; padding-bottom: 10px; }}
            h2 {{ color: #2c3e50; margin-top: 30px; }}
            table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: center; }}
            th {{ background-color: #1E3A5F; color: white; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
            .header-info {{ text-align: center; margin-bottom: 30px; }}
            .footer {{ text-align: center; margin-top: 40px; font-size: 12px; color: #666; border-top: 1px solid #ddd; padding-top: 20px; }}
            .discrepancy {{ background-color: #fff3e0; padding: 15px; margin: 20px 0; border-radius: 5px; }}
            .success {{ background-color: #d4edda; padding: 15px; margin: 20px 0; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <h1>🏥 REPORTE DE DISCREPANCIAS</h1>
        <div class="header-info">
            <p><strong>Período:</strong> {mes_inicio:02d}/{año_inicio} al {mes_fin:02d}/{año_fin}</p>
            <p><strong>Generado:</strong> {datetime.now().strftime("%d/%m/%Y %H:%M")}</p>
            <p><strong>SISPRO es la referencia (Total Real)</strong></p>
        </div>
    """
    
    # Tabla mensual
    html += "<h2>📊 ANÁLISIS MENSUAL</h2>"
    html += """
    <table>
        <tr>
            <th>Mes</th>
            <th>SISPRO</th>
            <th>EPI12</th>
            <th>EPI15 (Causas Consulta)</th>
            <th>Dif. EPI12</th>
            <th>Dif. EPI15</th>
        </tr>
    """
    for d in resultados['mensual']:
        html += f"""
        <tr>
            <td>{d['mes']}</td>
            <td>{d['sispro']}</td>
            <td>{d['epi12']}</td>
            <td>{d['epi15']}</td>
            <td>{d['diff_epi12']:+d}</td>
            <td>{d['diff_epi15']:+d}</td>
        </tr>
        """
    html += "</table>"
    
    # Tabla anual
    html += "<h2>📊 ANÁLISIS ANUAL</h2>"
    html += """
    <table>
        <tr>
            <th>Año</th>
            <th>SISPRO</th>
            <th>EPI12</th>
            <th>EPI15 (Causas Consulta)</th>
            <th>Dif. EPI12</th>
            <th>Dif. EPI15</th>
        </tr>
    """
    for d in resultados['anual']:
        html += f"""
        <tr>
            <td>{d['año']}</td>
            <td>{d['sispro']}</td>
            <td>{d['epi12']}</td>
            <td>{d['epi15']}</td>
            <td>{d['diff_epi12']:+d}</td>
            <td>{d['diff_epi15']:+d}</td>
        </tr>
        """
    html += "</table>"
    
    # Discrepancias
    meses_con_error = [d for d in resultados['mensual'] if d['diff_epi12'] != 0 or d['diff_epi15'] != 0]
    
    if meses_con_error:
        html += "<h2>⚠️ DISCREPANCIAS MENSUALES</h2>"
        for d in meses_con_error:
            html += f"""
            <div class="discrepancy">
                <h3>📅 Mes: {d['mes']}</h3>
                <p>SISPRO: {d['sispro']} | EPI12: {d['epi12']} ({d['diff_epi12']:+d}) | EPI15: {d['epi15']} ({d['diff_epi15']:+d})</p>
            """
            if d['diff_epi12'] != 0 and d['grupos_diferencia']:
                html += "<h4>Grupos etarios con diferencias en EPI12:</h4><ul>"
                for g in d['grupos_diferencia']:
                    html += f"<li>{g['grupo']}: SISPRO={g['sispro']}, EPI12={g['epi12']}, Diferencia={g['diferencia']:+d}</li>"
                html += "</ul>"
            html += "</div>"
    
    html += """
        <div class="footer">
            <p>Reporte generado por Gestor de Morbilidad - Willian Almenar</p>
        </div>
    </body>
    </html>
    """
    
    return html

def mostrar_analisis(df, info, tipo_archivo):
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
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        if info.get("estadisticas"):
            st.subheader("📈 Estadísticas")
            estadisticas = info["estadisticas"]
            st.write(f"**Fecha de carga:** {info['fecha_carga']}")

# Inicializar session_state
if 'dataframes' not in st.session_state:
    st.session_state.dataframes = {}
if 'infos' not in st.session_state:
    st.session_state.infos = {}

# Interfaz principal
tab1, tab2, tab3 = st.tabs([
    "📤 Carga de Archivos",
    "📊 Análisis de Discrepancias",
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
    st.header("📊 Análisis de Discrepancias")
    
    if st.session_state.dataframes:
        st.subheader("🔍 Seleccionar Período a Analizar")
        
        años_disponibles = []
        for nombre, df in st.session_state.dataframes.items():
            if 'AÑO' in df.columns:
                años = df['AÑO'].dropna().unique().tolist()
                años_disponibles.extend(años)
        
        if años_disponibles:
            años_disponibles = sorted(set([int(a) for a in años_disponibles]))
            año_min = min(años_disponibles)
            año_max = max(años_disponibles)
        else:
            año_min = 2024
            año_max = 2026
        
        meses_disponibles = list(range(1, 13))
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            año_inicio = st.number_input("Año Inicio", min_value=2000, max_value=2100, value=año_min)
        with col2:
            mes_inicio = st.selectbox("Mes Inicio", meses_disponibles, index=0)
        with col3:
            año_fin = st.number_input("Año Fin", min_value=2000, max_value=2100, value=año_max)
        with col4:
            mes_fin = st.selectbox("Mes Fin", meses_disponibles, index=6)
        
        if año_inicio > año_fin or (año_inicio == año_fin and mes_inicio > mes_fin):
            st.error("⚠️ El rango de fechas no es válido.")
        else:
            if st.button("🔍 Analizar Discrepancias", type="primary"):
                with st.spinner("Analizando datos..."):
                    resultados, error = analizar_totales(
                        st.session_state.dataframes,
                        año_inicio, mes_inicio, año_fin, mes_fin
                    )
                    
                    if error:
                        st.error(f"❌ {error}")
                    elif resultados is None:
                        st.error("❌ No se pudieron obtener resultados")
                    else:
                        mostrar_reporte(resultados, año_inicio, mes_inicio, año_fin, mes_fin)
    else:
        st.info("ℹ️ No hay archivos cargados. Carga los archivos primero.")

with tab3:
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
                'Pacientes Únicos': estadisticas.get('pacientes_unicos', 'N/A')
            })
        
        st.dataframe(pd.DataFrame(resumen_consolidado), use_container_width=True)
    else:
        st.info("ℹ️ No hay archivos cargados")

# Barra lateral
st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ Información de la Aplicación")
st.sidebar.markdown("""
**Versión:** 14.0  
**Desarrollador:** Willian Almenar  
**Fecha:** 2024  
**Propósito:** Análisis de discrepancias
""")

st.sidebar.markdown("### 📊 Análisis Realizado")
st.sidebar.markdown("""
- **SISPRO:** Total pacientes por grupo etario (mensual y anual)
- **EPI12:** Total pacientes por grupo etario (mensual y anual)
- **EPI15:** Total de Causas de Consulta (mensual y anual)
- **Discrepancias identificadas**
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
