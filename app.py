import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from io import BytesIO

st.set_page_config(page_title="Gestor de Morbilidad - Willian Almenar", layout="wide")

# Estilos CSS
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
    .match-box {
        background-color: #e8f5e9;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #2e7d32;
        margin-bottom: 1rem;
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
        padding: 0.5rem 1rem;
        border-radius: 5px;
        margin: 0.2rem 0;
        border-left: 3px solid #1976d2;
    }
    .total-box {
        background-color: #e8f5e9;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #2e7d32;
        margin: 1rem 0;
    }
    .mes-box {
        background-color: #fff3e0;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border: 2px solid #ff9800;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1>🏥 Gestor de Morbilidad - Validación de Reportes</h1><p>Willian Almenar</p></div>', unsafe_allow_html=True)
st.markdown("---")

# ============ DICCIONARIOS Y FUNCIONES BASE ============

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

def detectar_columna_fecha(df):
    posibles_fechas = [
        'FECHA_ATENCION', 'FECHA ATENCION', 'FECHADEATENCION', 'FECHA_ATENCIÓN',
        'FECHA_CONSULTA', 'FECHA CONSULTA', 'FECHACONSULTA',
        'FECHA_DE_ATENCION', 'FECHA_DE_CONSULTA',
        'FECHA_REGISTRO', 'FECHA REGISTRO', 'FECHAREGISTRO',
        'FECHA', 'FECH', 'DATE'
    ]
    
    for col in df.columns:
        col_upper = col.upper()
        for fecha in posibles_fechas:
            if col_upper == fecha or col_upper == fecha.replace(' ', '_'):
                return col
    
    for col in df.columns:
        if 'FECHA' in col.upper() or 'DATE' in col.upper():
            return col
    
    return None

def convertir_fechas(df, columna_fecha):
    if columna_fecha is None:
        return None, "No se encontró columna de fecha"
    
    formatos = [
        '%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d', '%d-%m-%Y', 
        '%d.%m.%Y', '%Y/%m/%d', '%d/%m/%y', '%m/%d/%y',
        '%Y-%m-%d %H:%M:%S', '%d/%m/%Y %H:%M:%S'
    ]
    
    for formato in formatos:
        try:
            fechas = pd.to_datetime(df[columna_fecha], format=formato, errors='coerce')
            if fechas.notna().sum() > 0:
                return fechas, f"Formato detectado: {formato}"
        except:
            continue
    
    try:
        fechas = pd.to_datetime(df[columna_fecha], errors='coerce')
        if fechas.notna().sum() > 0:
            return fechas, "Conversión automática"
    except:
        pass
    
    return None, "No se pudieron convertir las fechas"

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
        
        df = normalizar_identificacion(df)
        
        if 'EDAD' in df.columns:
            df['GRUPO_ETARIO'] = df['EDAD'].apply(asignar_grupo_etario)
        
        columna_fecha = detectar_columna_fecha(df)
        info["columna_fecha_detectada"] = columna_fecha
        
        if columna_fecha:
            fechas, mensaje = convertir_fechas(df, columna_fecha)
            if fechas is not None:
                df['FECHA_ATENCION'] = fechas
                df['AÑO'] = df['FECHA_ATENCION'].dt.year
                df['MES'] = df['FECHA_ATENCION'].dt.month
                df['AÑO_MES'] = df['FECHA_ATENCION'].dt.strftime('%Y-%m')
                info["fechas_ok"] = True
                info["fechas_validas"] = fechas.notna().sum()
            else:
                info["fechas_ok"] = False
                info["error_fechas"] = mensaje
        else:
            info["fechas_ok"] = False
            info["error_fechas"] = "No se encontró columna de fecha"
        
        if tipo_archivo == 'EPI15' and 'CODIGO_DIAGNOSTICO' in df.columns:
            df['CLASIFICACION_DIAGNOSTICO'] = df['CODIGO_DIAGNOSTICO'].apply(clasificar_diagnostico_epi15)
        
        info["estadisticas"] = {
            "total_registros": len(df),
            "pacientes_unicos": df['IDENTIFICACION'].nunique() if 'IDENTIFICACION' in df.columns else 0
        }
        
        return df, info
        
    except Exception as e:
        return None, f"Error al procesar el archivo: {str(e)}"

# ============ FUNCIÓN PRINCIPAL: VALIDACIÓN EPI12 Y EPI15 vs SISPRO ============

def validar_epi12_y_epi15_vs_sispro(df_sispro, df_epi12, df_epi15, año, mes):
    """
    Valida que EPI12 y EPI15 coincidan con SISPRO en un mes específico
    - EPI12: Pacientes únicos por grupo etario
    - EPI15: Total de Causas de Consulta
    """
    
    # Filtrar por mes y año
    mask_sispro = (df_sispro['AÑO'] == año) & (df_sispro['MES'] == mes)
    mask_epi12 = (df_epi12['AÑO'] == año) & (df_epi12['MES'] == mes)
    mask_epi15 = (df_epi15['AÑO'] == año) & (df_epi15['MES'] == mes)
    
    df_sispro_mes = df_sispro[mask_sispro].copy()
    df_epi12_mes = df_epi12[mask_epi12].copy()
    df_epi15_mes = df_epi15[mask_epi15].copy()
    
    if len(df_sispro_mes) == 0:
        return None, f"No hay datos de SISPRO para {mes:02d}/{año}"
    
    # ============ SISPRO (REFERENCIA) ============
    total_sispro = df_sispro_mes['IDENTIFICACION'].nunique()
    grupos_sispro = df_sispro_mes['GRUPO_ETARIO'].value_counts().to_dict()
    
    # ============ EPI12 ============
    if len(df_epi12_mes) > 0:
        total_epi12 = df_epi12_mes['IDENTIFICACION'].nunique()
        grupos_epi12 = df_epi12_mes['GRUPO_ETARIO'].value_counts().to_dict()
    else:
        total_epi12 = 0
        grupos_epi12 = {}
    
    # ============ EPI15 - TOTAL DE CAUSAS DE CONSULTA ============
    if len(df_epi15_mes) > 0:
        total_epi15 = len(df_epi15_mes)
        # Clasificación de EPI15 (si existe)
        if 'CLASIFICACION_DIAGNOSTICO' in df_epi15_mes.columns:
            clasificacion_epi15 = df_epi15_mes['CLASIFICACION_DIAGNOSTICO'].value_counts().to_dict()
        else:
            clasificacion_epi15 = {}
    else:
        total_epi15 = 0
        clasificacion_epi15 = {}
    
    # ============ CALCULAR DISCREPANCIAS ============
    diff_epi12 = total_epi12 - total_sispro
    diff_epi15 = total_epi15 - total_sispro
    
    # ============ GRUPOS ETARIOS CON DIFERENCIAS (EPI12) ============
    grupos_diferencia_epi12 = []
    if diff_epi12 != 0:
        for grupo in GRUPOS_ETARIOS.keys():
            count_sispro = grupos_sispro.get(grupo, 0)
            count_epi12 = grupos_epi12.get(grupo, 0)
            if count_sispro != count_epi12:
                grupos_diferencia_epi12.append({
                    'grupo': grupo,
                    'sispro': count_sispro,
                    'epi12': count_epi12,
                    'diferencia': count_sispro - count_epi12
                })
    
    # ============ CLASIFICACIÓN EPI15 CON DIFERENCIAS ============
    clasificacion_diferencia_epi15 = []
    if diff_epi15 != 0:
        # Solo mostrar las categorías que existen
        for cat in ['Causa de Consulta', 'Otras Causas', 'Sin Clasificar']:
            count_epi15 = clasificacion_epi15.get(cat, 0)
            if count_epi15 > 0:
                clasificacion_diferencia_epi15.append({
                    'categoria': cat,
                    'epi15': count_epi15
                })
    
    return {
        'mes': f"{mes:02d}/{año}",
        'sispro': total_sispro,
        'epi12': total_epi12,
        'epi15': total_epi15,
        'diff_epi12': diff_epi12,
        'diff_epi15': diff_epi15,
        'grupos_sispro': grupos_sispro,
        'grupos_epi12': grupos_epi12,
        'grupos_diferencia_epi12': grupos_diferencia_epi12,
        'clasificacion_epi15': clasificacion_epi15,
        'clasificacion_diferencia_epi15': clasificacion_diferencia_epi15,
        'epi12_coincide': diff_epi12 == 0,
        'epi15_coincide': diff_epi15 == 0,
        'todos_coinciden': diff_epi12 == 0 and diff_epi15 == 0
    }, None

def mostrar_validacion(resultado, mes_nombre, año):
    """Muestra los resultados de la validación"""
    
    if resultado is None:
        return
    
    st.markdown(f"""
    <div class="mes-box">
        <h2 style="margin: 0; color: #1E3A5F;">📅 {mes_nombre} {año}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # ============ RESUMEN GENERAL ============
    st.subheader("📊 Resumen General del Mes")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="total-box">
            <h4 style="margin: 0; color: #1E3A5F;">SISPRO (Referencia)</h4>
            <p style="font-size: 2.5rem; margin: 0; color: #2e7d32; text-align: center;">
                {resultado['sispro']:,}
            </p>
            <p style="margin: 0; text-align: center; color: #666;">Pacientes únicos</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        diff12 = resultado['diff_epi12']
        color12 = "#2e7d32" if diff12 == 0 else "#c62828"
        icono12 = "✅" if diff12 == 0 else "⚠️"
        st.markdown(f"""
        <div class="total-box" style="border-left-color: {color12};">
            <h4 style="margin: 0; color: #1E3A5F;">EPI12</h4>
            <p style="font-size: 2.5rem; margin: 0; color: {color12}; text-align: center;">
                {resultado['epi12']:,}
            </p>
            <p style="margin: 0; text-align: center; color: #666;">
                {icono12} Diferencia: {diff12:+d}
            </p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        diff15 = resultado['diff_epi15']
        color15 = "#2e7d32" if diff15 == 0 else "#c62828"
        icono15 = "✅" if diff15 == 0 else "⚠️"
        st.markdown(f"""
        <div class="total-box" style="border-left-color: {color15};">
            <h4 style="margin: 0; color: #1E3A5F;">EPI15 (Causas Consulta)</h4>
            <p style="font-size: 2.5rem; margin: 0; color: {color15}; text-align: center;">
                {resultado['epi15']:,}
            </p>
            <p style="margin: 0; text-align: center; color: #666;">
                {icono15} Diferencia: {diff15:+d}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # ============ ESTADO GENERAL ============
    if resultado['todos_coinciden']:
        st.markdown(f"""
        <div class="match-box">
            <h3 style="margin: 0; color: #2e7d32;">✅ ¡Todos los reportes coinciden correctamente!</h3>
            <p style="margin: 0.5rem 0;">EPI12 y EPI15 están alineados con SISPRO.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="discrepancy-box">
            <h3 style="margin: 0; color: #c62828;">⚠️ Se encontraron discrepancias</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # ============ DISCREPANCIAS EPI12 ============
        if not resultado['epi12_coincide']:
            st.subheader("🔴 Discrepancias en EPI12")
            
            st.warning(f"EPI12 tiene {resultado['diff_epi12']:+d} pacientes comparado con SISPRO")
            
            if resultado['grupos_diferencia_epi12']:
                st.write("**Grupos etarios con diferencias:**")
                df_grupos = pd.DataFrame(resultado['grupos_diferencia_epi12'])
                st.dataframe(df_grupos, use_container_width=True, hide_index=True)
                
                st.write("**📌 Recomendaciones para EPI12:**")
                for g in resultado['grupos_diferencia_epi12']:
                    if g['diferencia'] < 0:
                        st.warning(f"- {g['grupo']}: Agregar {abs(g['diferencia'])} pacientes")
                    else:
                        st.warning(f"- {g['grupo']}: Eliminar {g['diferencia']} pacientes")
            else:
                st.info("No se identificaron grupos etarios específicos con diferencias")
        
        # ============ DISCREPANCIAS EPI15 ============
        if not resultado['epi15_coincide']:
            st.subheader("🔴 Discrepancias en EPI15")
            
            st.warning(f"EPI15 tiene {resultado['diff_epi15']:+d} Causas de Consulta comparado con SISPRO")
            
            if resultado['clasificacion_diferencia_epi15']:
                st.write("**Clasificación de Causas de Consulta en EPI15:**")
                df_clasif = pd.DataFrame(resultado['clasificacion_diferencia_epi15'])
                st.dataframe(df_clasif, use_container_width=True, hide_index=True)
            
            st.write("**📌 Recomendaciones para EPI15:**")
            if resultado['diff_epi15'] < 0:
                st.warning(f"- Agregar {abs(resultado['diff_epi15'])} Causas de Consulta para igualar a SISPRO")
            else:
                st.warning(f"- Eliminar {resultado['diff_epi15']} Causas de Consulta para igualar a SISPRO")
    
    # ============ DETALLE DE GRUPOS ETARIOS (SISPRO vs EPI12) ============
    st.markdown("---")
    st.subheader("📊 Detalle de Grupos Etarios (SISPRO vs EPI12)")
    
    # Crear tabla comparativa de grupos
    grupos_data = []
    for grupo in GRUPOS_ETARIOS.keys():
        count_sispro = resultado['grupos_sispro'].get(grupo, 0)
        count_epi12 = resultado['grupos_epi12'].get(grupo, 0)
        if count_sispro > 0 or count_epi12 > 0:
            diff = count_epi12 - count_sispro
            estado = "✅" if diff == 0 else "⚠️"
            grupos_data.append({
                'Grupo Etario': grupo,
                'SISPRO': count_sispro,
                'EPI12': count_epi12,
                'Diferencia': diff,
                'Estado': estado
            })
    
    if grupos_data:
        df_grupos_comp = pd.DataFrame(grupos_data)
        st.dataframe(df_grupos_comp, use_container_width=True, hide_index=True)
        
        # Gráfico de grupos
        st.write("**📊 Comparativa por Grupo Etario**")
        chart_grupos = df_grupos_comp.set_index('Grupo Etario')[['SISPRO', 'EPI12']]
        st.bar_chart(chart_grupos)
    
    # ============ DETALLE DE EPI15 ============
    st.markdown("---")
    st.subheader("📊 Detalle de EPI15 - Causas de Consulta")
    
    if resultado['clasificacion_epi15']:
        df_clasif_total = pd.DataFrame({
            'Categoría': list(resultado['clasificacion_epi15'].keys()),
            'Cantidad': list(resultado['clasificacion_epi15'].values())
        })
        st.dataframe(df_clasif_total, use_container_width=True, hide_index=True)
        
        st.write(f"**Total de Causas de Consulta en EPI15:** {resultado['epi15']:,}")
        
        # Comparativa con SISPRO
        st.write(f"**SISPRO (Referencia):** {resultado['sispro']:,} pacientes")
        st.write(f"**Diferencia:** {resultado['diff_epi15']:+d}")
    
    # ============ BOTÓN DE DESCARGA ============
    st.markdown("---")
    st.subheader("💾 Descargar Reporte")
    
    if st.button("📥 Descargar Validación", key="btn_descargar_validacion"):
        try:
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Hoja: Resumen
                resumen = pd.DataFrame([
                    {'Métrica': 'Mes', 'Valor': f"{mes_nombre} {año}"},
                    {'Métrica': 'SISPRO (Referencia)', 'Valor': resultado['sispro']},
                    {'Métrica': 'EPI12', 'Valor': resultado['epi12'], 'Diferencia': resultado['diff_epi12']},
                    {'Métrica': 'EPI15 (Causas Consulta)', 'Valor': resultado['epi15'], 'Diferencia': resultado['diff_epi15']}
                ])
                resumen.to_excel(writer, sheet_name='Resumen', index=False)
                
                # Hoja: Grupos Etarios
                if grupos_data:
                    pd.DataFrame(grupos_data).to_excel(writer, sheet_name='Grupos_Etarios', index=False)
                
                # Hoja: Discrepancias EPI12
                if resultado['grupos_diferencia_epi12']:
                    pd.DataFrame(resultado['grupos_diferencia_epi12']).to_excel(writer, sheet_name='Discrepancias_EPI12', index=False)
                
                # Hoja: Clasificación EPI15
                if resultado['clasificacion_epi15']:
                    pd.DataFrame(df_clasif_total).to_excel(writer, sheet_name='Clasificacion_EPI15', index=False)
            
            output.seek(0)
            st.download_button(
                label="📥 Descargar Excel",
                data=output,
                file_name=f"validacion_{año}_{mes:02d}_{mes_nombre}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.success("✅ Reporte exportado exitosamente!")
        except Exception as e:
            st.error(f"Error al exportar: {str(e)}")

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
        
        if info.get('fechas_ok', False):
            st.write(f"**Columna de fecha:** {info.get('columna_fecha_detectada', 'N/A')}")
            st.write(f"**Fechas válidas:** {info.get('fechas_validas', 0)} de {info['filas']}")
        else:
            st.warning(f"⚠️ {info.get('error_fechas', 'Problema con fechas')}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        if info.get("estadisticas"):
            st.subheader("📈 Estadísticas")
            estadisticas = info["estadisticas"]
            st.write(f"**Fecha de carga:** {info['fecha_carga']}")

# ============ INICIALIZACIÓN ============

if 'dataframes' not in st.session_state:
    st.session_state.dataframes = {}
if 'infos' not in st.session_state:
    st.session_state.infos = {}

# ============ INTERFAZ PRINCIPAL ============

tab1, tab2, tab3 = st.tabs([
    "📤 Carga de Archivos",
    "📊 Validación EPI12 y EPI15 vs SISPRO (NUEVO)",
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
    st.header("📊 Validación EPI12 y EPI15 vs SISPRO")
    st.markdown("""
    <div class="info-box">
    💡 <b>Instrucciones:</b> Selecciona un mes para validar que EPI12 y EPI15 coincidan con SISPRO.
    </div>
    """, unsafe_allow_html=True)
    
    if 'SISPRO' in st.session_state.dataframes and 'EPI12' in st.session_state.dataframes and 'EPI15' in st.session_state.dataframes:
        df_sispro = st.session_state.dataframes['SISPRO']
        df_epi12 = st.session_state.dataframes['EPI12']
        df_epi15 = st.session_state.dataframes['EPI15']
        
        if 'FECHA_ATENCION' in df_sispro.columns and not df_sispro['FECHA_ATENCION'].isna().all():
            años_disponibles = sorted(df_sispro['AÑO'].dropna().unique().astype(int).tolist())
            
            if años_disponibles:
                col1, col2 = st.columns(2)
                
                with col1:
                    año_seleccionado = st.selectbox(
                        "Seleccionar Año:",
                        años_disponibles,
                        key="año_validacion"
                    )
                
                with col2:
                    meses_año = sorted(df_sispro[df_sispro['AÑO'] == año_seleccionado]['MES'].dropna().unique().astype(int).tolist())
                    nombres_meses = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
                    mes_seleccionado = st.selectbox(
                        "Seleccionar Mes:",
                        meses_año,
                        format_func=lambda x: f"{x:02d} - {nombres_meses[x-1]}",
                        key="mes_validacion"
                    )
                
                mes_nombre = nombres_meses[mes_seleccionado - 1]
                
                if st.button("🔍 Validar Reportes", type="primary", key="btn_validar"):
                    with st.spinner(f"Validando {mes_nombre} {año_seleccionado}..."):
                        resultado, error = validar_epi12_y_epi15_vs_sispro(
                            df_sispro,
                            df_epi12,
                            df_epi15,
                            año_seleccionado,
                            mes_seleccionado
                        )
                        
                        if error:
                            st.error(f"❌ {error}")
                        else:
                            mostrar_validacion(resultado, mes_nombre, año_seleccionado)
            else:
                st.warning("No se encontraron años disponibles")
        else:
            st.warning("No se encontraron fechas válidas en SISPRO")
    else:
        st.info("ℹ️ Primero carga los archivos SISPRO, EPI12 y EPI15")

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
                'Pacientes Únicos': estadisticas.get('pacientes_unicos', 'N/A'),
                'Fechas Válidas': info.get('fechas_validas', 'N/A')
            })
        
        st.dataframe(pd.DataFrame(resumen_consolidado), use_container_width=True)
    else:
        st.info("ℹ️ No hay archivos cargados")

# Barra lateral
st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ Información de la Aplicación")
st.sidebar.markdown("""
**Versión:** 6.0  
**Desarrollador:** Willian Almenar  
**Fecha:** 2024  
**Propósito:** Validación de reportes
""")

st.sidebar.markdown("### 📊 Validación Realizada")
st.sidebar.markdown("""
- **SISPRO:** Referencia (Total Real)
- **EPI12:** Pacientes por grupo etario
- **EPI15:** Total de Causas de Consulta
- **Discrepancias identificadas**
""")

st.sidebar.markdown("### 📅 Grupos Etarios")
st.sidebar.markdown("""
- 0-4 años
- 5-9 años
- 10-14 años
- 15-19 años
- 20-24 años
- 25-29 años
- 30-34 años
- 35-39 años
- 40-44 años
- 45-49 años
- 50-54 años
- 55-59 años
- 60-64 años
- 65+ años
""")

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
🎯 Lo que hace esta nueva versión:
1. Validación Completa por Mes
SISPRO: Total de pacientes (referencia)

EPI12: Total de pacientes y desglose por grupo etario

EPI15: Total de Causas de Consulta y clasificación

2. Identificación de Discrepancias
EPI12: Muestra qué grupo etario tiene diferencias

EPI15: Muestra el total de Causas de Consulta y su clasificación

3. Recomendaciones
Indica exactamente qué corregir en cada reporte

Cuántos pacientes/causas agregar o eliminar

4. Visualización
Tabla comparativa de grupos etarios

Gráfico de barras comparativo

Resumen claro de estado

📊 Ejemplo de resultado:
text
📅 Enero 2026

📊 Resumen General del Mes
| SISPRO | EPI12 | EPI15 |
| 65     | 63    | 63    |

⚠️ Se encontraron discrepancias

🔴 Discrepancias en EPI12
EPI12 tiene -2 pacientes comparado con SISPRO

Grupos etarios con diferencias:
| Grupo Etario | SISPRO | EPI12 | Diferencia |
| 0-4 años     | 15     | 13    | -2         |

📌 Recomendaciones para EPI12:
- 0-4 años: Agregar 2 pacientes

🔴 Discrepancias en EPI15
EPI15 tiene -2 Causas de Consulta comparado con SISPRO

📌 Recomendaciones para EPI15:
- Agregar 2 Causas de Consulta para igualar a SISPRO
Ahora la aplicación valida que EPI12 y EPI15 coincidan con SISPRO mes a mes. 🚀

