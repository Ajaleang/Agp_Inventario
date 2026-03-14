import streamlit as st
import pandas as pd
import io
import os
import base64
from matching_engine import emparejar_pedidos, generar_resumen_estadistico

# Configuración de la página
st.set_page_config(
    page_title="AGP - Optimizador de Inventario",
    page_icon="🔍",
    layout="wide"
)

# Estilos CSS personalizados para mejorar la UI
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        border-top: 4px solid #8abfcb;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: 900;
        color: #4d4d4d;
    }
    .metric-label {
        font-size: 1.1rem;
        color: #666;
        font-weight: 600;
    }
    .warning-text {
        color: #e74c3c;
    }
    .success-text {
        color: #8abfcb;
    }
    
    /* Traducción del File Uploader */
    [data-testid="stFileUploadDropzone"] div div::before {color:#4d4d4d; content:"Arrastra y suelta el archivo aquí"; display:block; font-weight:600;}
    [data-testid="stFileUploadDropzone"] div div span {display:none;}
    [data-testid="stFileUploadDropzone"] div div::after {color:#666; content:"Límite 200MB por archivo • XLSX"; display:block; font-size: .8em;}
    [data-testid="stFileUploadDropzone"] div div small {display:none;}
    
    /* Ocultar texto original del botón y poner el nuevo */
    [data-testid="stBaseButton-secondary"] p {visibility: hidden;}
    [data-testid="stBaseButton-secondary"] p::after {
        content: "Explorar archivos";
        visibility: visible;
        display: block;
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Título y descripción con Logo
logo_path = "logo.png"

# SVG Fallback logo parecido al original
svg_logo = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 100" width="200" height="auto">
  <path d="M 15 50 Q 150 5 285 50 Q 150 15 15 50 Z" fill="#8abfcb" />
  <text x="150" y="80" font-family="Arial, Helvetica, sans-serif" font-size="45" font-weight="900" letter-spacing="12" fill="#4d4d4d" text-anchor="middle">AGP</text>
</svg>
"""

col1, col2 = st.columns([1, 4])
with col1:
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    elif os.path.exists("logo.jpg"):
        st.image("logo.jpg", use_container_width=True)
    else:
        # Render SVG fallback
        b64 = base64.b64encode(svg_logo.encode('utf-8')).decode('utf-8')
        html = f'<img src="data:image/svg+xml;base64,{b64}" width="200" style="margin-top: 10px;">'
        st.markdown(html, unsafe_allow_html=True)
        
with col2:
    st.markdown("""
    <div style="padding-top: 10px;">
        <h1 style="color: #4d4d4d; margin-bottom: 0; padding-bottom: 0;">Optimizador de Inventario</h1>
        <p style="color: #666; font-size: 1.1rem; margin-top: 5px;">Sube tu archivo Excel para encontrar pares de piezas 'Incomplete' y listos para despachar.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Sección de subida de archivo
uploaded_file = st.file_uploader("Sube el archivo Mock_Data.xlsx (o similar)", type=['xlsx'])

if uploaded_file is not None:
    # 1. Procesamiento de datos
    with st.spinner("Procesando datos y buscando pares..."):
        try:
            # Para el engine, necesitamos pasarle un objeto similar a archivo (ya manejado por pandas read_excel con openpyxl)
            # Modificamos temporalmente el comportamiento si filepath es subido desde streamlit
            
            # Cargar el DF original para cálculos
            df_original = pd.read_excel(uploaded_file, engine='openpyxl')
            
            # Rebobinar el archivo para pasarlo a la función
            uploaded_file.seek(0)
            
            # Llamar a la lógica core (el filepath puede ser un file-like object)
            df_pares, df_sin_par, df_problemas = emparejar_pedidos(uploaded_file)
            resumen = generar_resumen_estadistico(df_pares, df_sin_par, df_problemas, df_original)
            
            st.success("¡Análisis completado!")
            
            # 2. Mostrar KPIs
            st.header("Resumen del Emparejamiento")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Pares Formados</div>
                    <div class="metric-value success-text">{resumen['total_pares_formados']}</div>
                    <div style="font-size: 0.9em; color: #666;">({resumen['pedidos_completados']} pedidos listos)</div>
                </div>
                """, unsafe_allow_html=True)
                
            with col2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Sin Par (Incompletos)</div>
                    <div class="metric-value">{resumen['pedidos_sin_par']}</div>
                    <div style="font-size: 0.9em; color: #666;">Pendientes de otra pieza</div>
                </div>
                """, unsafe_allow_html=True)
                
            with col3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Datos Problemáticos</div>
                    <div class="metric-value warning-text">{resumen['registros_con_datos_faltantes']}</div>
                    <div style="font-size: 0.9em; color: #666;">Falta Customer o Vehicle</div>
                </div>
                """, unsafe_allow_html=True)
                
            with col4:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Días Máx. Liberados</div>
                    <div class="metric-value" style="color:#f39c12;">{resumen['dias_maximo_inventario_liberado']}</div>
                    <div style="font-size: 0.9em; color: #666;">Días en stock del pedido más viejo</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # 3. Mostrar Tablas
            tab1, tab2, tab3 = st.tabs(["✅ Pares Formados", "⏳ Pedidos sin Par", "⚠️ Datos con Problemas"])
            
            with tab1:
                st.subheader("Pedidos emparejados — del más antiguo al más reciente")
                if not df_pares.empty:
                    # Columnas más relevantes para mostrar al equipo comercial
                    columnas_pares = [
                        'Numero_Par',
                        'Grupo_Customer', 'Grupo_Vehicle', 'Grupo_Product',
                        'Pedido_1_ID', 'Pedido_1_DaysStored',
                        'Pedido_2_ID', 'Pedido_2_DaysStored'
                    ]
                    st.dataframe(df_pares[columnas_pares], use_container_width=True)
                else:
                    st.info("No se encontraron pares.")
            
            with tab2:
                st.subheader("Pedidos que aún no pueden completarse")
                if not df_sin_par.empty:
                    st.dataframe(df_sin_par, use_container_width=True)
                else:
                    st.info("No hay pedidos solitarios.")
                    
            with tab3:
                st.subheader("Registros excluidos temporalmente (Datos Faltantes)")
                st.markdown("Estos pedidos no tienen asignado un **Customer** o un **Vehicle**, por lo tanto, no se pueden emparejar de forma segura. Por favor, corrígelos en SAP e intenta de nuevo.")
                if not df_problemas.empty:
                    st.dataframe(df_problemas, use_container_width=True)
                else:
                    st.success("¡Excelente! Todos los registros tienen sus datos de Customer y Vehicle completos.")
            
            # 4. Exportar a Excel
            st.markdown("---")
            st.subheader("Exportar Resultados")
            
            # Función para convertir DFs a un archivo Excel en memoria
            def convert_df_to_excel():
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    if not df_pares.empty:
                        df_pares.to_excel(writer, index=False, sheet_name='Pares Formados')
                    if not df_sin_par.empty:
                        df_sin_par.to_excel(writer, index=False, sheet_name='Pedidos Sin Par')
                    if not df_problemas.empty:
                        df_problemas.to_excel(writer, index=False, sheet_name='Datos con Problemas')
                processed_data = output.getvalue()
                return processed_data
                
            excel_data = convert_df_to_excel()
            
            st.download_button(
                label="📥 Descargar Reporte en Excel",
                data=excel_data,
                file_name="AGP_Reporte_Cruce.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Descarga un archivo con 3 hojas: Pares Formados, Sin Par y Datos con Problemas."
            )
            
        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")
            st.info("Asegúrate de que estás subiendo el archivo correcto con el formato esperado (y que las columnas ID, Customer, Vehicle, Product, SetStatus y DaysStored existan).")

else:
    # Estado inicial cuando no hay archivo
    st.info("👆 Por favor, carga un archivo Excel para continuar.")
    
    with st.expander("ℹ️ ¿Cómo funciona este optimizador?"):
        st.markdown("""
        Esta herramienta aplica automáticamente las reglas de negocio de AGP:
        1. **Busca pedidos "Incomplete".**
        2. **Garantiza 3 coincidencias exactas:** Mismo Cliente, Mismo Vehículo, Mismo Producto.
        3. **Prioriza lo más antiguo:** Las piezas con más tiempo en bodega siempre se despachan primero.
        4. **Aísla los errores:** Separa los registros sin Cliente o Vehículo para que no se mezclen por accidente.
        """)
