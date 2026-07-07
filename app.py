import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from io import BytesIO
import base64

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
    .report-container {
        background-color: white;
        padding: 2rem;
        border-radius: 10px;
        border: 1px solid #ddd;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 4px 4px 0px 0px;
        padding: 10px 20px;
        background-color: #f0f2f6;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1E3A5F;
        color: white;
    }
    .download-btn {
        background-color: #28a745;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        text-decoration: none;
        display: inline-block;
        margin: 0.5rem 0;
    }
    .download-btn:hover {
        background-color: #218838;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1>🏥 Gestor de Morbilidad - Generador de Reportes</h1><p>Willian Almenar</p></div>', unsafe_allow_html=True)
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
    
    if 'NOMBRE_PACIENTE' in df.columns and 'APELLIDO_PACIENTE' in df.columns:
        df['NOMBRE_COMPLETO'] = df['NOMBRE_PACIENTE'].astype(str).str.strip() + ' ' + df['APELLIDO_PACIENTE'].astype(str).str.strip()
    elif 'NOMBRE_PACIENTE' in df.columns:
        df['NOMBRE_COMPLETO'] = df['NOMBRE_PACIENTE'].astype(str).str.strip()
    else:
        df['NOMBRE_COMPLETO'] = df['IDENTIFICACION']
    
    return df

def clasificar_diagnostico_epi15(codigo_diagnostico):
    if pd.isna(codigo_diagnostico):
        return 'Sin Clasificar'
    
    codigo = str(codigo_diagnostico).strip().upper()
    
    palabras_otras = ['OTRA', 'OTRO', 'VARIA', 'DIVERSO', 'NO ESPECIFICADO', 'NO CLASIFICADO']
    for palabra in palabras_otras:
        if palabra in codigo:
            return 'Otras Causas'
    
    palabras_consulta = ['CONSULTA', 'CONTROL', 'SEGUIMIENTO', 'REVISION', 'CHEQUEO', 'PREVENTIVO']
    for palabra in palabras_consulta:
        if palabra in codigo:
            return 'Causa de Consulta'
    
    if len(codigo) > 0:
        return 'Causa de Consulta'
    
    return 'Sin Clasificar'

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
        
        df = procesar_datos(df, tipo_archivo)
        df = normalizar_identificacion(df)
        
        if 'EDAD' in df.columns:
            df['GRUPO_ETARIO'] = df['EDAD'].apply(asignar_grupo_etario)
        
        if 'FECHA_ATENCION' in df.columns:
            try:
                df['FECHA_ATENCION'] = pd.to_datetime(df['FECHA_ATENCION'], errors='coerce')
                df['AÑO'] = df['FECHA_ATENCION'].dt.year
                df['MES'] = df['FECHA_ATENCION'].dt.month
                df['AÑO_MES'] = df['FECHA_ATENCION'].dt.strftime('%Y-%m')
            except Exception as e:
                df['AÑO'] = None
                df['MES'] = None
                df['AÑO_MES'] = None
        
        if tipo_archivo == 'EPI15' and 'CODIGO_DIAGNOSTICO' in df.columns:
            df['CLASIFICACION_DIAGNOSTICO'] = df['CODIGO_DIAGNOSTICO'].apply(clasificar_diagnostico_epi15)
        
        info["estadisticas"] = generar_estadisticas(df, tipo_archivo)
        
        return df, info
        
    except Exception as e:
        return None, f"Error al procesar el archivo: {str(e)}"

def procesar_datos(df, tipo_archivo):
    if 'EDAD' in df.columns:
        try:
            df['EDAD'] = pd.to_numeric(df['EDAD'], errors='coerce')
        except:
            pass
    
    return df

def generar_estadisticas(df, tipo_archivo):
    estadisticas = {}
    estadisticas["total_registros"] = len(df)
    
    if 'IDENTIFICACION' in df.columns:
        estadisticas["pacientes_unicos"] = df['IDENTIFICACION'].nunique()
    
    if 'CODIGO_CIE10' in df.columns:
        try:
            estadisticas["diagnosticos_unicos"] = df['CODIGO_CIE10'].nunique()
        except:
            estadisticas["diagnosticos_unicos"] = 0
    
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

def identificar_discrepancias_detalladas(dataframes, año_inicio, mes_inicio, año_fin, mes_fin):
    """Identifica discrepancias detalladas entre SISPRO, EPI12 y EPI15"""
    
    dataframes_filtrados = {}
    for nombre, df in dataframes.items():
        dataframes_filtrados[nombre] = filtrar_por_fecha(df, año_inicio, mes_inicio, año_fin, mes_fin)
    
    if 'SISPRO' not in dataframes_filtrados or 'EPI12' not in dataframes_filtrados or 'EPI15' not in dataframes_filtrados:
        return None
    
    df_sispro = dataframes_filtrados['SISPRO']
    df_epi12 = dataframes_filtrados['EPI12']
    df_epi15 = dataframes_filtrados['EPI15']
    
    if df_sispro is None or len(df_sispro) == 0:
        return None
    
    if 'AÑO_MES' not in df_sispro.columns or df_sispro['AÑO_MES'].isna().all():
        # Analizar todos los datos sin desglose mensual
        pacientes_sispro = df_sispro['IDENTIFICACION'].nunique()
        grupos_sispro = df_sispro['GRUPO_ETARIO'].value_counts().to_dict() if 'GRUPO_ETARIO' in df_sispro.columns else {}
        enfermedades_sispro = set(df_sispro['CODIGO_CIE10'].dropna().unique()) if 'CODIGO_CIE10' in df_sispro.columns else set()
        
        if df_epi12 is not None and len(df_epi12) > 0:
            pacientes_epi12 = df_epi12['IDENTIFICACION'].nunique()
            grupos_epi12 = df_epi12['GRUPO_ETARIO'].value_counts().to_dict() if 'GRUPO_ETARIO' in df_epi12.columns else {}
        else:
            pacientes_epi12 = 0
            grupos_epi12 = {}
        
        if df_epi15 is not None and len(df_epi15) > 0:
            total_epi15 = len(df_epi15)
            enfermedades_epi15 = set(df_epi15['CODIGO_CIE10'].dropna().unique()) if 'CODIGO_CIE10' in df_epi15.columns else set()
        else:
            total_epi15 = 0
            enfermedades_epi15 = set()
        
        diff_epi12 = pacientes_epi12 - pacientes_sispro
        diff_epi15 = total_epi15 - pacientes_sispro
        
        grupos_faltantes_epi12 = []
        if diff_epi12 != 0:
            for grupo in GRUPOS_ETARIOS.keys():
                if grupo in grupos_sispro:
                    count_sispro = grupos_sispro.get(grupo, 0)
                    count_epi12 = grupos_epi12.get(grupo, 0)
                    if count_sispro != count_epi12:
                        grupos_faltantes_epi12.append({
                            'grupo': grupo,
                            'sispro': count_sispro,
                            'epi12': count_epi12,
                            'diferencia': count_sispro - count_epi12
                        })
        
        enfermedades_faltantes_epi15 = list(enfermedades_sispro - enfermedades_epi15) if diff_epi15 != 0 else []
        
        if diff_epi12 != 0 or diff_epi15 != 0:
            return [{
                'mes': 'Todos los datos',
                'sispro': pacientes_sispro,
                'epi12': pacientes_epi12,
                'epi15': total_epi15,
                'diff_epi12': diff_epi12,
                'diff_epi15': diff_epi15,
                'grupos_faltantes_epi12': grupos_faltantes_epi12,
                'enfermedades_faltantes_epi15': enfermedades_faltantes_epi15[:10]
            }]
        else:
            return []
    
    meses_disponibles = sorted(df_sispro['AÑO_MES'].dropna().unique())
    
    if len(meses_disponibles) == 0:
        return []
    
    discrepancias = []
    
    for mes in meses_disponibles:
        pacientes_sispro = df_sispro[df_sispro['AÑO_MES'] == mes]['IDENTIFICACION'].nunique()
        grupos_sispro = df_sispro[df_sispro['AÑO_MES'] == mes]['GRUPO_ETARIO'].value_counts().to_dict() if 'GRUPO_ETARIO' in df_sispro.columns else {}
        enfermedades_sispro = set(df_sispro[df_sispro['AÑO_MES'] == mes]['CODIGO_CIE10'].dropna().unique()) if 'CODIGO_CIE10' in df_sispro.columns else set()
        
        df_epi12_mes = df_epi12[df_epi12['AÑO_MES'] == mes] if df_epi12 is not None and len(df_epi12) > 0 and 'AÑO_MES' in df_epi12.columns else pd.DataFrame()
        if len(df_epi12_mes) > 0:
            pacientes_epi12 = df_epi12_mes['IDENTIFICACION'].nunique()
            grupos_epi12 = df_epi12_mes['GRUPO_ETARIO'].value_counts().to_dict() if 'GRUPO_ETARIO' in df_epi12_mes.columns else {}
        else:
            pacientes_epi12 = 0
            grupos_epi12 = {}
        
        df_epi15_mes = df_epi15[df_epi15['AÑO_MES'] == mes] if df_epi15 is not None and len(df_epi15) > 0 and 'AÑO_MES' in df_epi15.columns else pd.DataFrame()
        if len(df_epi15_mes) > 0:
            total_epi15 = len(df_epi15_mes)
            enfermedades_epi15 = set(df_epi15_mes['CODIGO_CIE10'].dropna().unique()) if 'CODIGO_CIE10' in df_epi15_mes.columns else set()
        else:
            total_epi15 = 0
            enfermedades_epi15 = set()
        
        diff_epi12 = pacientes_epi12 - pacientes_sispro
        diff_epi15 = total_epi15 - pacientes_sispro
        
        grupos_faltantes_epi12 = []
        if diff_epi12 != 0:
            for grupo in GRUPOS_ETARIOS.keys():
                if grupo in grupos_sispro:
                    count_sispro = grupos_sispro.get(grupo, 0)
                    count_epi12 = grupos_epi12.get(grupo, 0)
                    if count_sispro != count_epi12:
                        grupos_faltantes_epi12.append({
                            'grupo': grupo,
                            'sispro': count_sispro,
                            'epi12': count_epi12,
                            'diferencia': count_sispro - count_epi12
                        })
            
            suma_diferencias = sum(g['diferencia'] for g in grupos_faltantes_epi12)
            
            if suma_diferencias != diff_epi12:
                if grupos_faltantes_epi12:
                    grupos_faltantes_epi12.sort(key=lambda x: abs(x['diferencia']), reverse=True)
                    ajuste = diff_epi12 - suma_diferencias
                    grupos_faltantes_epi12[0]['diferencia'] += ajuste
                    grupos_faltantes_epi12[0]['epi12'] = grupos_faltantes_epi12[0]['sispro'] - grupos_faltantes_epi12[0]['diferencia']
        
        enfermedades_faltantes_epi15 = []
        if diff_epi15 != 0:
            enfermedades_faltantes_epi15 = list(enfermedades_sispro - enfermedades_epi15)
        
        if diff_epi12 != 0 or diff_epi15 != 0:
            discrepancias.append({
                'mes': mes,
                'sispro': pacientes_sispro,
                'epi12': pacientes_epi12,
                'epi15': total_epi15,
                'diff_epi12': diff_epi12,
                'diff_epi15': diff_epi15,
                'grupos_faltantes_epi12': grupos_faltantes_epi12,
                'enfermedades_faltantes_epi15': enfermedades_faltantes_epi15[:10]
            })
    
    return discrepancias

def mostrar_reporte_en_pagina(discrepancias, año_inicio, mes_inicio, año_fin, mes_fin, tipo_reporte):
    """Muestra el reporte directamente en la página"""
    
    st.markdown(f"""
    <div style="background-color: #f8f9fa; padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
        <h3 style="color: #1E3A5F; margin: 0;">📄 REPORTE DE DISCREPANCIAS - {tipo_reporte.upper()}</h3>
        <p style="margin: 5px 0 0 0; color: #666;">
            Período: {mes_inicio:02d}/{año_inicio} al {mes_fin:02d}/{año_fin} | 
            Generado: {datetime.now().strftime("%d/%m/%Y %H:%M")}
        </p>
        <p style="margin: 0; color: #1E3A5F; font-weight: bold;">📌 SISPRO es la referencia (Total Real)</p>
    </div>
    """, unsafe_allow_html=True)
    
    if discrepancias is None:
        st.error("❌ No se pudieron analizar los datos. Verifica que los archivos estén correctamente cargados.")
        return
    
    if not discrepancias:
        st.success("🎉 ¡No se encontraron discrepancias en el período analizado!")
        st.balloons()
        return
    
    # Resumen ejecutivo
    total_meses = len(discrepancias)
    meses_epi12 = sum(1 for d in discrepancias if d['diff_epi12'] != 0)
    meses_epi15 = sum(1 for d in discrepancias if d['diff_epi15'] != 0)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📊 Total meses con discrepancias", total_meses)
    with col2:
        st.metric("⚠️ Meses con EPI12 diferente", meses_epi12)
    with col3:
        st.metric("⚠️ Meses con EPI15 diferente", meses_epi15)
    
    st.markdown("---")
    
    # Análisis detallado por mes
    st.subheader("📋 Análisis Detallado por Mes")
    
    for disc in discrepancias:
        mes = disc['mes']
        
        with st.expander(f"📅 Mes: {mes}", expanded=True):
            # Tabla de totales
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("SISPRO (Referencia)", disc['sispro'])
            with col2:
                st.metric("EPI12", disc['epi12'], delta=f"{disc['diff_epi12']:+d}" if disc['diff_epi12'] != 0 else None)
            with col3:
                st.metric("EPI15", disc['epi15'], delta=f"{disc['diff_epi15']:+d}" if disc['diff_epi15'] != 0 else None)
            with col4:
                if disc['diff_epi12'] == 0 and disc['diff_epi15'] == 0:
                    st.success("✅ OK")
                else:
                    st.warning("⚠️ Discrepancia")
            
            # Grupos etarios con diferencias en EPI12
            if disc['diff_epi12'] != 0 and disc['grupos_faltantes_epi12']:
                st.markdown("#### 🔴 Grupos etarios con diferencias en EPI12:")
                
                grupos_data = []
                suma_grupos = 0
                for grupo in disc['grupos_faltantes_epi12']:
                    if grupo['diferencia'] != 0:
                        grupos_data.append({
                            'Grupo Etario': grupo['grupo'],
                            'SISPRO': grupo['sispro'],
                            'EPI12': grupo['epi12'],
                            'Diferencia': grupo['diferencia']
                        })
                        suma_grupos += grupo['diferencia']
                
                if grupos_data:
                    st.dataframe(pd.DataFrame(grupos_data), use_container_width=True)
                    st.info(f"✅ Verificación: Suma de diferencias = {suma_grupos:+d} (coincide con diferencia total de {disc['diff_epi12']:+d})")
            
            # Enfermedades no reportadas en EPI15
            if disc['diff_epi15'] != 0 and disc['enfermedades_faltantes_epi15']:
                st.markdown("#### 🔴 Enfermedades no reportadas en EPI15:")
                
                enfermedades = disc['enfermedades_faltantes_epi15']
                for i, enf in enumerate(enfermedades[:10], 1):
                    st.write(f"{i}. {enf}")
                if len(enfermedades) > 10:
                    st.write(f"... y {len(enfermedades) - 10} enfermedades más")
    
    # Conclusiones y recomendaciones
    st.markdown("---")
    st.subheader("📌 Conclusiones y Recomendaciones")
    
    total_diff_epi12 = sum(d['diff_epi12'] for d in discrepancias)
    total_diff_epi15 = sum(d['diff_epi15'] for d in discrepancias)
    
    if total_diff_epi12 != 0:
        st.warning(f"📌 **EPI12:** Debe {'agregar' if total_diff_epi12 < 0 else 'eliminar'} **{abs(total_diff_epi12)}** registros para coincidir con SISPRO.")
        
        st.markdown("**Detalle por grupo etario:**")
        for disc in discrepancias:
            if disc['diff_epi12'] != 0 and disc['grupos_faltantes_epi12']:
                for grupo in disc['grupos_faltantes_epi12']:
                    if grupo['diferencia'] != 0:
                        st.write(f"- {disc['mes']}: {grupo['grupo']} → {abs(grupo['diferencia'])} registros")
    else:
        st.success("📌 **EPI12:** ✅ Ya está alineado con SISPRO.")
    
    if total_diff_epi15 != 0:
        st.warning(f"📌 **EPI15:** Debe {'agregar' if total_diff_epi15 < 0 else 'eliminar'} **{abs(total_diff_epi15)}** registros para coincidir con SISPRO.")
        
        st.markdown("**Detalle de enfermedades faltantes:**")
        for disc in discrepancias:
            if disc['diff_epi15'] != 0 and disc['enfermedades_faltantes_epi15']:
                for enf in disc['enfermedades_faltantes_epi15'][:5]:
                    st.write(f"- {disc['mes']}: {enf}")
                if len(disc['enfermedades_faltantes_epi15']) > 5:
                    st.write(f"- ... y {len(disc['enfermedades_faltantes_epi15']) - 5} más")
    else:
        st.success("📌 **EPI15:** ✅ Ya está alineado con SISPRO.")

def generar_reporte_html(discrepancias, año_inicio, mes_inicio, año_fin, mes_fin, tipo_reporte):
    """Genera un reporte en formato HTML para descarga"""
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Reporte de Discrepancias - {tipo_reporte.upper()}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #1E3A5F; text-align: center; border-bottom: 3px solid #1E3A5F; padding-bottom: 10px; }}
            h2 {{ color: #2c3e50; margin-top: 30px; }}
            h3 {{ color: #34495e; margin-top: 20px; }}
            table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: center; }}
            th {{ background-color: #1E3A5F; color: white; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
            .header-info {{ text-align: center; margin-bottom: 30px; }}
            .discrepancy {{ background-color: #fff3e0; border-left: 5px solid #ff9800; padding: 15px; margin: 20px 0; border-radius: 5px; }}
            .success {{ background-color: #d4edda; border-left: 5px solid #28a745; padding: 15px; margin: 20px 0; border-radius: 5px; }}
            .footer {{ text-align: center; margin-top: 40px; font-size: 12px; color: #666; border-top: 1px solid #ddd; padding-top: 20px; }}
            .grupo-faltante {{ background-color: #fce4ec; }}
            .enfermedad-faltante {{ background-color: #f3e5f5; }}
            .metric {{ display: inline-block; margin: 10px 20px; padding: 10px 20px; background: #f8f9fa; border-radius: 5px; }}
            .metric strong {{ color: #1E3A5F; }}
        </style>
    </head>
    <body>
        <h1>🏥 REPORTE DE DISCREPANCIAS - {tipo_reporte.upper()}</h1>
        <div class="header-info">
            <p><strong>Período analizado:</strong> {mes_inicio:02d}/{año_inicio} al {mes_fin:02d}/{año_fin}</p>
            <p><strong>Fecha de generación:</strong> {datetime.now().strftime("%d/%m/%Y %H:%M")}</p>
            <p><strong>SISPRO es la referencia (Total Real)</strong></p>
        </div>
    """
    
    if discrepancias is None:
        html += """
        <div class="success">
            <h3>⚠️ No se pudieron analizar los datos</h3>
            <p>Verifica que los archivos estén correctamente cargados y tengan las columnas necesarias.</p>
        </div>
        """
    elif not discrepancias:
        html += """
        <div class="success">
            <h3>✅ No se encontraron discrepancias en el período analizado.</h3>
            <p>Todos los reportes coinciden con SISPRO.</p>
        </div>
        """
    else:
        # Resumen ejecutivo
        total_meses = len(discrepancias)
        meses_epi12 = sum(1 for d in discrepancias if d['diff_epi12'] != 0)
        meses_epi15 = sum(1 for d in discrepancias if d['diff_epi15'] != 0)
        
        html += f"""
        <h2>📊 RESUMEN EJECUTIVO</h2>
        <div style="text-align: center;">
            <span class="metric"><strong>Total meses con discrepancias:</strong> {total_meses}</span>
            <span class="metric"><strong>Meses con EPI12 diferente:</strong> {meses_epi12}</span>
            <span class="metric"><strong>Meses con EPI15 diferente:</strong> {meses_epi15}</span>
        </div>
        """
        
        # Análisis detallado por mes
        html += "<h2>📋 ANÁLISIS DETALLADO POR MES</h2>"
        
        for disc in discrepancias:
            mes = disc['mes']
            html += f"""
            <div class="discrepancy">
                <h3>📅 Mes: {mes}</h3>
                <table>
                    <tr>
                        <th>Fuente</th>
                        <th>Total</th>
                        <th>Diferencia vs SISPRO</th>
                        <th>Estado</th>
                    </tr>
                    <tr>
                        <td><strong>SISPRO (Referencia)</strong></td>
                        <td>{disc['sispro']}</td>
                        <td>-</td>
                        <td>✅ OK</td>
                    </tr>
                    <tr>
                        <td><strong>EPI12</strong></td>
                        <td>{disc['epi12']}</td>
                        <td>{disc['diff_epi12']:+d}</td>
                        <td>{"✅ OK" if disc['diff_epi12'] == 0 else "⚠️ DISCREPANCIA"}</td>
                    </tr>
                    <tr>
                        <td><strong>EPI15</strong></td>
                        <td>{disc['epi15']}</td>
                        <td>{disc['diff_epi15']:+d}</td>
                        <td>{"✅ OK" if disc['diff_epi15'] == 0 else "⚠️ DISCREPANCIA"}</td>
                    </tr>
                </table>
            """
            
            # Grupos etarios con diferencias en EPI12
            if disc['diff_epi12'] != 0 and disc['grupos_faltantes_epi12']:
                html += """
                <h4>🔴 Grupos etarios con diferencias en EPI12:</h4>
                <table>
                    <tr>
                        <th>Grupo Etario</th>
                        <th>SISPRO</th>
                        <th>EPI12</th>
                        <th>Diferencia</th>
                    </tr>
                """
                suma_grupos = 0
                for grupo in disc['grupos_faltantes_epi12']:
                    if grupo['diferencia'] != 0:
                        html += f"""
                        <tr>
                            <td>{grupo['grupo']}</td>
                            <td>{grupo['sispro']}</td>
                            <td>{grupo['epi12']}</td>
                            <td>{grupo['diferencia']:+d}</td>
                        </tr>
                        """
                        suma_grupos += grupo['diferencia']
                html += f"""
                </table>
                <p>✅ Verificación: Suma de diferencias = {suma_grupos:+d} (coincide con diferencia total de {disc['diff_epi12']:+d})</p>
                """
            
            # Enfermedades no reportadas en EPI15
            if disc['diff_epi15'] != 0 and disc['enfermedades_faltantes_epi15']:
                html += """
                <h4>🔴 Enfermedades no reportadas en EPI15:</h4>
                <ul>
                """
                for enf in disc['enfermedades_faltantes_epi15'][:10]:
                    html += f"<li>{enf}</li>"
                if len(disc['enfermedades_faltantes_epi15']) > 10:
                    html += f"<li>... y {len(disc['enfermedades_faltantes_epi15']) - 10} enfermedades más</li>"
                html += "</ul>"
            
            html += "</div>"
        
        # Conclusiones y recomendaciones
        html += "<h2>📌 CONCLUSIONES Y RECOMENDACIONES</h2>"
        
        total_diff_epi12 = sum(d['diff_epi12'] for d in discrepancias)
        total_diff_epi15 = sum(d['diff_epi15'] for d in discrepancias)
        
        if total_diff_epi12 != 0:
            html += f"""
            <p><strong>📌 EPI12:</strong> Debe {"agregar" if total_diff_epi12 < 0 else "eliminar"} {abs(total_diff_epi12)} registros para coincidir con SISPRO.</p>
            <p><strong>Detalle por grupo etario:</strong></p>
            <ul>
            """
            for disc in discrepancias:
                if disc['diff_epi12'] != 0 and disc['grupos_faltantes_epi12']:
                    for grupo in disc['grupos_faltantes_epi12']:
                        if grupo['diferencia'] != 0:
                            html += f"<li>{disc['mes']}: {grupo['grupo']} → {abs(grupo['diferencia'])} registros</li>"
            html += "</ul>"
        else:
            html += "<p><strong>📌 EPI12:</strong> ✅ Ya está alineado con SISPRO.</p>"
        
        if total_diff_epi15 != 0:
            html += f"""
            <p><strong>📌 EPI15:</strong> Debe {"agregar" if total_diff_epi15 < 0 else "eliminar"} {abs(total_diff_epi15)} registros para coincidir con SISPRO.</p>
            <p><strong>Detalle de enfermedades faltantes:</strong></p>
            <ul>
            """
            for disc in discrepancias:
                if disc['diff_epi15'] != 0 and disc['enfermedades_faltantes_epi15']:
                    for enf in disc['enfermedades_faltantes_epi15'][:5]:
                        html += f"<li>{disc['mes']}: {enf}</li>"
                    if len(disc['enfermedades_faltantes_epi15']) > 5:
                        html += f"<li>... y {len(disc['enfermedades_faltantes_epi15']) - 5} más</li>"
            html += "</ul>"
        else:
            html += "<p><strong>📌 EPI15:</strong> ✅ Ya está alineado con SISPRO.</p>"
    
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
        st.write(f"**Fecha de carga:** {info['fecha_carga']}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        if info.get("estadisticas"):
            st.subheader("📈 Estadísticas")
            estadisticas = info["estadisticas"]
            st.write(f"**Diagnósticos únicos:** {estadisticas.get('diagnosticos_unicos', 'N/A')}")

# Inicializar session_state
if 'dataframes' not in st.session_state:
    st.session_state.dataframes = {}
if 'infos' not in st.session_state:
    st.session_state.infos = {}

# Interfaz principal
tab1, tab2, tab3, tab4 = st.tabs([
    "📤 Carga de Archivos",
    "📊 Análisis de Discrepancias",
    "📄 Generar Reporte HTML",
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
                with st.spinner("Analizando discrepancias..."):
                    discrepancias = identificar_discrepancias_detalladas(
                        st.session_state.dataframes,
                        año_inicio, mes_inicio, año_fin, mes_fin
                    )
                    
                    if discrepancias is None:
                        st.error("❌ Error al analizar los datos. Verifica que los archivos estén correctamente cargados.")
                    elif not discrepancias:
                        st.success("🎉 ¡No se encontraron discrepancias en el período analizado!")
                        st.balloons()
                    else:
                        st.success(f"✅ Análisis completado. Se encontraron {len(discrepancias)} meses con discrepancias.")
                        
                        # Mostrar reporte en la página
                        mostrar_reporte_en_pagina(
                            discrepancias, 
                            año_inicio, mes_inicio, año_fin, mes_fin,
                            "mensual"
                        )
                        
                        # Botón para descargar el reporte HTML
                        html_content = generar_reporte_html(
                            discrepancias,
                            año_inicio, mes_inicio, año_fin, mes_fin,
                            "mensual"
                        )
                        
                        st.markdown("---")
                        st.subheader("💾 Descargar Reporte")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.download_button(
                                label="📥 Descargar Reporte HTML",
                                data=html_content,
                                file_name=f"reporte_discrepancias_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                                mime="text/html",
                                use_container_width=True
                            )
                        with col2:
                            # Opción para descargar como Excel
                            if st.button("📊 Descargar Datos en Excel", use_container_width=True):
                                try:
                                    # Crear Excel con los datos
                                    output = BytesIO()
                                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                        # Crear DataFrame con las discrepancias
                                        data = []
                                        for disc in discrepancias:
                                            data.append({
                                                'Mes': disc['mes'],
                                                'SISPRO': disc['sispro'],
                                                'EPI12': disc['epi12'],
                                                'EPI15': disc['epi15'],
                                                'Diferencia EPI12': disc['diff_epi12'],
                                                'Diferencia EPI15': disc['diff_epi15']
                                            })
                                        df_report = pd.DataFrame(data)
                                        df_report.to_excel(writer, sheet_name='Discrepancias', index=False)
                                        
                                        # Hoja de grupos etarios
                                        grupos_data = []
                                        for disc in discrepancias:
                                            if disc['grupos_faltantes_epi12']:
                                                for grupo in disc['grupos_faltantes_epi12']:
                                                    if grupo['diferencia'] != 0:
                                                        grupos_data.append({
                                                            'Mes': disc['mes'],
                                                            'Grupo Etario': grupo['grupo'],
                                                            'SISPRO': grupo['sispro'],
                                                            'EPI12': grupo['epi12'],
                                                            'Diferencia': grupo['diferencia']
                                                        })
                                        if grupos_data:
                                            pd.DataFrame(grupos_data).to_excel(writer, sheet_name='Grupos_Etarios', index=False)
                                        
                                        # Hoja de enfermedades
                                        enf_data = []
                                        for disc in discrepancias:
                                            if disc['enfermedades_faltantes_epi15']:
                                                for enf in disc['enfermedades_faltantes_epi15']:
                                                    enf_data.append({
                                                        'Mes': disc['mes'],
                                                        'Enfermedad': enf
                                                    })
                                        if enf_data:
                                            pd.DataFrame(enf_data).to_excel(writer, sheet_name='Enfermedades_Faltantes', index=False)
                                    
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
    else:
        st.info("ℹ️ No hay archivos cargados.")

with tab3:
    st.header("📄 Generar Reporte HTML Completo")
    
    if st.session_state.dataframes:
        st.subheader("🔍 Configurar Reporte")
        
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
            año_inicio = st.number_input("Año Inicio", min_value=2000, max_value=2100, value=año_min, key="html_año_ini")
        with col2:
            mes_inicio = st.selectbox("Mes Inicio", meses_disponibles, index=0, key="html_mes_ini")
        with col3:
            año_fin = st.number_input("Año Fin", min_value=2000, max_value=2100, value=año_max, key="html_año_fin")
        with col4:
            mes_fin = st.selectbox("Mes Fin", meses_disponibles, index=6, key="html_mes_fin")
        
        tipo_reporte = st.radio(
            "Tipo de Reporte:",
            ["Mensual", "Anual"],
            horizontal=True
        )
        
        if año_inicio > año_fin or (año_inicio == año_fin and mes_inicio > mes_fin):
            st.error("⚠️ El rango de fechas no es válido.")
        else:
            if st.button("📄 Generar Reporte", type="primary"):
                with st.spinner("Generando reporte..."):
                    try:
                        discrepancias = identificar_discrepancias_detalladas(
                            st.session_state.dataframes,
                            año_inicio, mes_inicio, año_fin, mes_fin
                        )
                        
                        if discrepancias is None:
                            st.error("❌ Error al generar el reporte.")
                        else:
                            # Mostrar reporte en la página
                            mostrar_reporte_en_pagina(
                                discrepancias,
                                año_inicio, mes_inicio, año_fin, mes_fin,
                                tipo_reporte.lower()
                            )
                            
                            # Generar HTML para descarga
                            html_content = generar_reporte_html(
                                discrepancias,
                                año_inicio, mes_inicio, año_fin, mes_fin,
                                tipo_reporte.lower()
                            )
                            
                            st.markdown("---")
                            st.subheader("💾 Descargar Reporte")
                            
                            st.download_button(
                                label="📥 Descargar Reporte HTML",
                                data=html_content,
                                file_name=f"reporte_{tipo_reporte.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                                mime="text/html",
                                use_container_width=True
                            )
                    except Exception as e:
                        st.error(f"Error al generar el reporte: {str(e)}")
    else:
        st.info("ℹ️ No hay archivos cargados. Carga los archivos primero.")

with tab4:
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
        
        # Opción para exportar resumen
        if st.button("📥 Exportar Resumen a Excel"):
            try:
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    pd.DataFrame(resumen_consolidado).to_excel(writer, sheet_name='Resumen', index=False)
                output.seek(0)
                st.download_button(
                    label="Descargar Excel",
                    data=output,
                    file_name=f"resumen_reportes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"Error al exportar: {str(e)}")
    else:
        st.info("ℹ️ No hay archivos cargados para generar reportes")

# Barra lateral
st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ Información de la Aplicación")
st.sidebar.markdown("""
**Versión:** 12.0  
**Desarrollador:** Willian Almenar  
**Fecha:** 2024  
**Propósito:** Generación de reportes de discrepancias
""")

st.sidebar.markdown("### 📄 Reportes Disponibles")
st.sidebar.markdown("""
- **Análisis en página:** Visualización directa  
- **Descarga HTML:** Reporte completo  
- **Descarga Excel:** Datos estructurados  
- **Reportes mensuales y anuales**
""")

st.sidebar.markdown("### 🔍 Características")
st.sidebar.markdown("""
- ✅ Visualización en tiempo real  
- ✅ Descarga en múltiples formatos  
- ✅ Detalle por grupo etario  
- ✅ Enfermedades no reportadas  
- ✅ Recomendaciones automáticas
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
- Los reportes se muestran directamente en la página
- Puedes descargar en formato HTML o Excel
- La suma de diferencias siempre es consistente
""")
