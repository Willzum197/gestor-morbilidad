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

st.markdown('<div class="main-header"><h1>Gestor de Morbilidad - Validacion de Reportes</h1><p>Willian Almenar</p></div>', unsafe_allow_html=True)
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
    '0-4 anos': (0, 4),
    '5-9 anos': (5, 9),
    '10-14 anos': (10, 14),
    '15-19 anos': (15, 19),
    '20-24 anos': (20, 24),
    '25-29 anos': (25, 29),
    '30-34 anos': (30, 34),
    '35-39 anos': (35, 39),
    '40-44 anos': (40, 44),
    '45-49 anos': (45, 49),
    '50-54 anos': (50, 54),
    '55-59 anos': (55, 59),
    '60-64 anos': (60, 64),
    '65+ anos': (65, 150)
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
        'FECHA_ATENCION', 'FECHA ATENCION', 'FECHADEATENCION', 'FECHA_ATENCION',
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
            return fechas, "Conversion automatica"
    except:
        pass
    
    return None, "No se pudieron convertir las fechas"

def analizar_archivo(file, tipo_archivo):
    if file is None:
        return None, "No se ha subido ningun archivo"
    
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
                df['ANO'] = df['FECHA_ATENCION'].dt.year
                df['MES'] = df['FECHA_ATENCION'].dt.month
                df['ANO_MES'] = df['FECHA_ATENCION'].dt.strftime('%Y-%m')
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

# ============ FUNCIONES DE VALIDACION ============

def validar_mes(df_sispro, df_epi12, df_epi15, ano, mes):
    """Valida un mes especifico"""
    
    mask_sispro = (df_sispro['ANO'] == ano) & (df_sispro['MES'] == mes)
    mask_epi12 = (df_epi12['ANO'] == ano) & (df_epi12['MES'] == mes)
    mask_epi15 = (df_epi15['ANO'] == ano) & (df_epi15['MES'] == mes)
    
    df_sispro_mes = df_sispro[mask_sispro].copy()
    df_epi12_mes = df_epi12[mask_epi12].copy()
    df_epi15_mes = df_epi15[mask_epi15].copy()
    
    if len(df_sispro_mes) == 0:
        return None
    
    total_sispro = df_sispro_mes['IDENTIFICACION'].nunique()
    grupos_sispro = df_sispro_mes['GRUPO_ETARIO'].value_counts().to_dict()
    
    if len(df_epi12_mes) > 0:
        total_epi12 = df_epi12_mes['IDENTIFICACION'].nunique()
        grupos_epi12 = df_epi12_mes['GRUPO_ETARIO'].value_counts().to_dict()
    else:
        total_epi12 = 0
        grupos_epi12 = {}
    
    if len(df_epi15_mes) > 0:
        total_epi15 = len(df_epi15_mes)
        if 'CLASIFICACION_DIAGNOSTICO' in df_epi15_mes.columns:
            clasificacion_epi15 = df_epi15_mes['CLASIFICACION_DIAGNOSTICO'].value_counts().to_dict()
        else:
            clasificacion_epi15 = {}
    else:
        total_epi15 = 0
        clasificacion_epi15 = {}
    
    diff_epi12 = total_epi12 - total_sispro
    diff_epi15 = total_epi15 - total_sispro
    
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
    
    return {
        'mes': f"{mes:02d}/{ano}",
        'sispro': total_sispro,
        'epi12': total_epi12,
        'epi15': total_epi15,
        'diff_epi12': diff_epi12,
        'diff_epi15': diff_epi15,
        'grupos_sispro': grupos_sispro,
        'grupos_epi12': grupos_epi12,
        'grupos_diferencia_epi12': grupos_diferencia_epi12,
        'clasificacion_epi15': clasificacion_epi15,
        'epi12_coincide': diff_epi12 == 0,
        'epi15_coincide': diff_epi15 == 0
    }

def validar_periodo(df_sispro, df_epi12, df_epi15, ano_inicio, mes_inicio, ano_fin, mes_fin):
    """Valida un periodo de meses"""
    
    resultados = []
    
    # Generar lista de meses en el periodo
    fecha_actual = datetime(ano_inicio, mes_inicio, 1)
    fecha_fin = datetime(ano_fin, mes_fin, 1)
    
    while fecha_actual <= fecha_fin:
        ano = fecha_actual.year
        mes = fecha_actual.month
        
        resultado = validar_mes(df_sispro, df_epi12, df_epi15, ano, mes)
        if resultado:
            resultados.append(resultado)
        
        # Avanzar al siguiente mes
        if mes == 12:
            fecha_actual = datetime(ano + 1, 1, 1)
        else:
            fecha_actual = datetime(ano, mes + 1, 1)
    
    return resultados

def mostrar_validacion_periodo(resultados, ano_inicio, mes_inicio, ano_fin, mes_fin):
    """Muestra la validacion de un periodo"""
    
    if not resultados:
        st.warning("No hay datos para el periodo seleccionado")
        return
    
    nombres_meses = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
    
    st.markdown(f"""
    <div class="mes-box">
        <h2 style="margin: 0; color: #1E3A5F;">Periodo: {nombres_meses[mes_inicio-1]} {ano_inicio} - {nombres_meses[mes_fin-1]} {ano_fin}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # ============ TABLA RESUMEN ============
    st.subheader("Resumen del Periodo")
    
    resumen_data = []
    for r in resultados:
        estado_epi12 = "OK" if r['epi12_coincide'] else "ERR"
        estado_epi15 = "OK" if r['epi15_coincide'] else "ERR"
        resumen_data.append({
            'Mes': r['mes'],
            'SISPRO': r['sispro'],
            'EPI12': r['epi12'],
            'Diff EPI12': r['diff_epi12'],
            'Estado EPI12': estado_epi12,
            'EPI15': r['epi15'],
            'Diff EPI15': r['diff_epi15'],
            'Estado EPI15': estado_epi15
        })
    
    df_resumen = pd.DataFrame(resumen_data)
    st.dataframe(df_resumen, use_container_width=True, hide_index=True)
    
    # ============ GRAFICOS ============
    st.subheader("Comparativa Mensual")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**SISPRO vs EPI12**")
        chart1 = df_resumen.set_index('Mes')[['SISPRO', 'EPI12']]
        st.bar_chart(chart1)
    
    with col2:
        st.write("**SISPRO vs EPI15**")
        chart2 = df_resumen.set_index('Mes')[['SISPRO', 'EPI15']]
        st.bar_chart(chart2)
    
    # ============ MESES CON ERRORES ============
    meses_con_error = [r for r in resultados if not r['epi12_coincide'] or not r['epi15_coincide']]
    
    if meses_con_error:
        st.markdown("---")
        st.subheader("Meses con Discrepancias")
        
        for r in meses_con_error:
            st.markdown(f"""
            <div class="discrepancy-box">
                <h4 style="margin: 0; color: #c62828;">{r['mes']}</h4>
            """, unsafe_allow_html=True)
            
            if not r['epi12_coincide']:
                st.warning(f"EPI12: {r['diff_epi12']:+d} pacientes")
                if r['grupos_diferencia_epi12']:
                    st.write("Grupos etarios con diferencias:")
                    df_grupos = pd.DataFrame(r['grupos_diferencia_epi12'])
                    st.dataframe(df_grupos, use_container_width=True, hide_index=True)
            
            if not r['epi15_coincide']:
                st.warning(f"EPI15: {r['diff_epi15']:+d} Causas de Consulta")
                if r['clasificacion_epi15']:
                    df_clasif = pd.DataFrame({
                        'Categoria': list(r['clasificacion_epi15'].keys()),
                        'Cantidad': list(r['clasificacion_epi15'].values())
                    })
                    st.dataframe(df_clasif, use_container_width=True, hide_index=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="match-box">
            <h3 style="margin: 0; color: #2e7d32;">Todos los meses coinciden correctamente</h3>
        </div>
        """, unsafe_allow_html=True)
    
    # ============ RESUMEN TOTAL ============
    st.markdown("---")
    st.subheader("Resumen Total del Periodo")
    
    total_sispro = sum(r['sispro'] for r in resultados)
    total_epi12 = sum(r['epi12'] for r in resultados)
    total_epi15 = sum(r['epi15'] for r in resultados)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total SISPRO", f"{total_sispro:,}")
    with col2:
        st.metric("Total EPI12", f"{total_epi12:,}", delta=f"{total_epi12 - total_sispro:+,}")
    with col3:
        st.metric("Total EPI15", f"{total_epi15:,}", delta=f"{total_epi15 - total_sispro:+,}")
    
    # ============ BOTON DE DESCARGA ============
    st.markdown("---")
    st.subheader("Descargar Reporte")
    
    if st.button("Descargar Reporte Periodo", key="btn_descargar_periodo"):
        try:
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_resumen.to_excel(writer, sheet_name='Resumen_Periodo', index=False)
                
                # Detalle de errores
                if meses_con_error:
                    errores_data = []
                    for r in meses_con_error:
                        if not r['epi12_coincide'] and r['grupos_diferencia_epi12']:
                            for g in r['grupos_diferencia_epi12']:
                                errores_data.append({
                                    'Mes': r['mes'],
                                    'Fuente': 'EPI12',
                                    'Grupo Etario': g['grupo'],
                                    'SISPRO': g['sispro'],
                                    'EPI12': g['epi12'],
                                    'Diferencia': g['diferencia']
                                })
                        if not r['epi15_coincide']:
                            for cat, count in r['clasificacion_epi15'].items():
                                errores_data.append({
                                    'Mes': r['mes'],
                                    'Fuente': 'EPI15',
                                    'Categoria': cat,
                                    'Cantidad': count
                                })
                    if errores_data:
                        pd.DataFrame(errores_data).to_excel(writer, sheet_name='Detalle_Discrepancias', index=False)
            
            output.seek(0)
            st.download_button(
                label="Descargar Excel",
                data=output,
                file_name=f"validacion_periodo_{ano_inicio}_{mes_inicio:02d}_a_{ano_fin}_{mes_fin:02d}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.success("Reporte exportado exitosamente!")
        except Exception as e:
            st.error(f"Error al exportar: {str(e)}")

def mostrar_analisis(df, info, tipo_archivo):
    if info is None or df is None:
        st.error("No se pudo cargar el archivo")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        st.subheader("Resumen del Archivo")
        st.write(f"**Tipo:** {tipo_archivo}")
        st.write(f"**Registros:** {info['filas']:,}")
        st.write(f"**Pacientes unicos:** {info.get('estadisticas', {}).get('pacientes_unicos', 'N/A')}")
        
        if info.get('fechas_ok', False):
            st.write(f"**Columna de fecha:** {info.get('columna_fecha_detectada', 'N/A')}")
            st.write(f"**Fechas validas:** {info.get('fechas_validas', 0)} de {info['filas']}")
        else:
            st.warning(f" {info.get('error_fechas', 'Problema con fechas')}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        if info.get("estadisticas"):
            st.subheader("Estadisticas")
            estadisticas = info["estadisticas"]
            st.write(f"**Fecha de carga:** {info['fecha_carga']}")

# ============ INICIALIZACION ============

if 'dataframes' not in st.session_state:
    st.session_state.dataframes = {}
if 'infos' not in st.session_state:
    st.session_state.infos = {}

# ============ INTERFAZ PRINCIPAL ============

tab1, tab2, tab3, tab4 = st.tabs([
    "Carga de Archivos",
    "Validacion por Mes",
    "Validacion por Periodo (NUEVO)",
    "Reporte Consolidado"
])

with tab1:
    st.header("Carga de Archivos SISPRO, EPI12 y EPI15")
    st.markdown("""
    <div class="info-box">
    Instrucciones: Sube los archivos Excel (.xls o .xlsx) correspondientes a cada tipo de formato.
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("SISPRO")
        file_sispro = st.file_uploader("Subir archivo SISPRO", type=['xls', 'xlsx'], key="sispro")
        if file_sispro:
            with st.spinner("Procesando archivo SISPRO..."):
                df, info = analizar_archivo(file_sispro, "SISPRO")
                if isinstance(info, dict):
                    st.session_state.dataframes['SISPRO'] = df
                    st.session_state.infos['SISPRO'] = info
                    st.success(f"SISPRO cargado exitosamente - {info['filas']} registros")
                    mostrar_analisis(df, info, "SISPRO")
                else:
                    st.error(f"Error: {info}")
    
    with col2:
        st.subheader("EPI12")
        file_epi12 = st.file_uploader("Subir archivo EPI12", type=['xls', 'xlsx'], key="epi12")
        if file_epi12:
            with st.spinner("Procesando archivo EPI12..."):
                df, info = analizar_archivo(file_epi12, "EPI12")
                if isinstance(info, dict):
                    st.session_state.dataframes['EPI12'] = df
                    st.session_state.infos['EPI12'] = info
                    st.success(f"EPI12 cargado exitosamente - {info['filas']} registros")
                    mostrar_analisis(df, info, "EPI12")
                else:
                    st.error(f"Error: {info}")
    
    with col3:
        st.subheader("EPI15")
        file_epi15 = st.file_uploader("Subir archivo EPI15", type=['xls', 'xlsx'], key="epi15")
        if file_epi15:
            with st.spinner("Procesando archivo EPI15..."):
                df, info = analizar_archivo(file_epi15, "EPI15")
                if isinstance(info, dict):
                    st.session_state.dataframes['EPI15'] = df
                    st.session_state.infos['EPI15'] = info
                    st.success(f"EPI15 cargado exitosamente - {info['filas']} registros")
                    mostrar_analisis(df, info, "EPI15")
                else:
                    st.error(f"Error: {info}")

with tab2:
    st.header("Validacion por Mes")
    st.markdown("""
    <div class="info-box">
    Selecciona un mes especifico para validar que EPI12 y EPI15 coincidan con SISPRO.
    </div>
    """, unsafe_allow_html=True)
    
    if 'SISPRO' in st.session_state.dataframes and 'EPI12' in st.session_state.dataframes and 'EPI15' in st.session_state.dataframes:
        df_sispro = st.session_state.dataframes['SISPRO']
        df_epi12 = st.session_state.dataframes['EPI12']
        df_epi15 = st.session_state.dataframes['EPI15']
        
        if 'FECHA_ATENCION' in df_sispro.columns and not df_sispro['FECHA_ATENCION'].isna().all():
            anos_disponibles = sorted(df_sispro['ANO'].dropna().unique().astype(int).tolist())
            
            if anos_disponibles:
                col1, col2 = st.columns(2)
                
                with col1:
                    ano_seleccionado = st.selectbox(
                        "Seleccionar Año:",
                        anos_disponibles,
                        key="ano_validacion"
                    )
                
                with col2:
                    meses_ano = sorted(df_sispro[df_sispro['ANO'] == ano_seleccionado]['MES'].dropna().unique().astype(int).tolist())
                    nombres_meses = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
                    mes_seleccionado = st.selectbox(
                        "Seleccionar Mes:",
                        meses_ano,
                        format_func=lambda x: f"{x:02d} - {nombres_meses[x-1]}",
                        key="mes_validacion"
                    )
                
                mes_nombre = nombres_meses[mes_seleccionado - 1]
                
                if st.button("Validar Mes", type="primary", key="btn_validar_mes"):
                    with st.spinner(f"Validando {mes_nombre} {ano_seleccionado}..."):
                        resultado = validar_mes(
                            df_sispro,
                            df_epi12,
                            df_epi15,
                            ano_seleccionado,
                            mes_seleccionado
                        )
                        
                        if resultado:
                            # Mostrar resultado del mes
                            st.markdown(f"""
                            <div class="mes-box">
                                <h2 style="margin: 0; color: #1E3A5F;">{mes_nombre} {ano_seleccionado}</h2>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("SISPRO", resultado['sispro'])
                            with col2:
                                st.metric("EPI12", resultado['epi12'], delta=f"{resultado['diff_epi12']:+d}")
                            with col3:
                                st.metric("EPI15", resultado['epi15'], delta=f"{resultado['diff_epi15']:+d}")
                            
                            if resultado['epi12_coincide'] and resultado['epi15_coincide']:
                                st.success("Todos los reportes coinciden")
                            else:
                                if not resultado['epi12_coincide']:
                                    st.warning(f"EPI12: {resultado['diff_epi12']:+d} pacientes")
                                    if resultado['grupos_diferencia_epi12']:
                                        st.dataframe(pd.DataFrame(resultado['grupos_diferencia_epi12']))
                                if not resultado['epi15_coincide']:
                                    st.warning(f"EPI15: {resultado['diff_epi15']:+d} Causas de Consulta")
                        else:
                            st.warning("No hay datos para el mes seleccionado")
            else:
                st.warning("No se encontraron años disponibles")
        else:
            st.warning("No se encontraron fechas validas en SISPRO")
    else:
        st.info("Primero carga los archivos SISPRO, EPI12 y EPI15")

# ============ NUEVA PESTAÑA: VALIDACION POR PERIODO ============

with tab3:
    st.header("Validacion por Periodo")
    st.markdown("""
    <div class="info-box">
    Selecciona un rango de meses para validar que EPI12 y EPI15 coincidan con SISPRO en todo el periodo.
    </div>
    """, unsafe_allow_html=True)
    
    if 'SISPRO' in st.session_state.dataframes and 'EPI12' in st.session_state.dataframes and 'EPI15' in st.session_state.dataframes:
        df_sispro = st.session_state.dataframes['SISPRO']
        df_epi12 = st.session_state.dataframes['EPI12']
        df_epi15 = st.session_state.dataframes['EPI15']
        
        if 'FECHA_ATENCION' in df_sispro.columns and not df_sispro['FECHA_ATENCION'].isna().all():
            anos_disponibles = sorted(df_sispro['ANO'].dropna().unique().astype(int).tolist())
            
            if anos_disponibles:
                col1, col2, col3, col4 = st.columns(4)
                nombres_meses = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
                
                with col1:
                    ano_inicio = st.number_input(
                        "Año Inicio",
                        min_value=min(anos_disponibles),
                        max_value=max(anos_disponibles),
                        value=min(anos_disponibles),
                        key="ano_inicio_periodo"
                    )
                
                with col2:
                    mes_inicio = st.selectbox(
                        "Mes Inicio",
                        range(1, 13),
                        format_func=lambda x: f"{x:02d} - {nombres_meses[x-1]}",
                        key="mes_inicio_periodo"
                    )
                
                with col3:
                    ano_fin = st.number_input(
                        "Año Fin",
                        min_value=min(anos_disponibles),
                        max_value=max(anos_disponibles),
                        value=max(anos_disponibles),
                        key="ano_fin_periodo"
                    )
                
                with col4:
                    mes_fin = st.selectbox(
                        "Mes Fin",
                        range(1, 13),
                        format_func=lambda x: f"{x:02d} - {nombres_meses[x-1]}",
                        key="mes_fin_periodo"
                    )
                
                if ano_inicio > ano_fin or (ano_inicio == ano_fin and mes_inicio > mes_fin):
                    st.error("El rango de fechas no es valido. El mes de inicio debe ser anterior o igual al mes final.")
                else:
                    if st.button("Validar Periodo", type="primary", key="btn_validar_periodo"):
                        with st.spinner(f"Validando periodo..."):
                            resultados = validar_periodo(
                                df_sispro,
                                df_epi12,
                                df_epi15,
                                ano_inicio, mes_inicio,
                                ano_fin, mes_fin
                            )
                            
                            if resultados:
                                mostrar_validacion_periodo(resultados, ano_inicio, mes_inicio, ano_fin, mes_fin)
                            else:
                                st.warning("No hay datos para el periodo seleccionado")
            else:
                st.warning("No se encontraron años disponibles")
        else:
            st.warning("No se encontraron fechas validas en SISPRO")
    else:
        st.info("Primero carga los archivos SISPRO, EPI12 y EPI15")

with tab4:
    st.header("Reporte Consolidado")
    
    if st.session_state.dataframes:
        st.subheader("Resumen General de Todos los Reportes")
        
        resumen_consolidado = []
        for nombre, df in st.session_state.dataframes.items():
            info = st.session_state.infos.get(nombre, {})
            estadisticas = info.get('estadisticas', {})
            
            resumen_consolidado.append({
                'Fuente': nombre,
                'Registros': len(df),
                'Pacientes Unicos': estadisticas.get('pacientes_unicos', 'N/A'),
                'Fechas Validas': info.get('fechas_validas', 'N/A')
            })
        
        st.dataframe(pd.DataFrame(resumen_consolidado), use_container_width=True)
    else:
        st.info("No hay archivos cargados")

# Barra lateral
st.sidebar.markdown("---")
st.sidebar.markdown("### Informacion de la Aplicacion")
st.sidebar.markdown("""
**Version:** 7.0  
**Desarrollador:** Willian Almenar  
**Fecha:** 2024  
**Proposito:** Validacion de reportes
""")

st.sidebar.markdown("### Validacion Realizada")
st.sidebar.markdown("""
- **SISPRO:** Referencia (Total Real)
- **EPI12:** Pacientes por grupo etario
- **EPI15:** Total de Causas de Consulta
- **Discrepancias identificadas**
""")

st.sidebar.markdown("### Opciones de Validacion")
st.sidebar.markdown("""
- **Por Mes:** Un mes especifico
- **Por Periodo:** Rango de meses (NUEVO)
""")

total_archivos = len(st.session_state.dataframes)
st.sidebar.markdown(f"### Archivos cargados: {total_archivos}/3")
if total_archivos > 0:
    for nombre in st.session_state.dataframes.keys():
        st.sidebar.success(f"OK {nombre}")

if st.sidebar.button("Limpiar todos los datos"):
    st.session_state.dataframes = {}
    st.session_state.infos = {}
    st.sidebar.success("Datos limpiados exitosamente!")
    st.rerun()
