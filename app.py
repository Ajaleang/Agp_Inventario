"""
AGP - Sistema de Emparejamiento de Pedidos Incompletos
"""

import streamlit as st
import pandas as pd
import io
import base64
from matching_engine import emparejar_pedidos, generar_resumen_estadistico

# Configuración de la página
st.set_page_config(
    page_title="AGP - Emparejamiento de Pedidos",
    page_icon="📦",
    layout="wide"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        text-align: center;
        border-top: 4px solid #1f77b4;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 2.5em;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-label {
        font-size: 0.9em;
        color: #666;
        margin-top: 5px;
    }
    .success-text {
        color: #28a745;
    }
    .warning-text {
        color: #dc3545;
    }
</style>
""", unsafe_allow_html=True)

# Logo SVG fallback
svg_logo = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 100" width="200">
  <path d="M 15 50 Q 150 5 285 50 Q 150 15 15 50 Z" fill="#8abfcb" />
  <text x="150" y="80" font-family="Arial" font-size="45"
        font-weight="900" fill="#4d4d4d" text-anchor="middle">AGP</text>
</svg>
"""

# Encabezado con logo
col1, col2 = st.columns([1, 4])
with col1:
    b64 = base64.b64encode(svg_logo.encode('utf-8')).decode('utf-8')
    html = f'<img src="data:image/svg+xml;base64,{b64}" width="200">'
    st.markdown(html, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="padding-top: 10px;">
        <h1 style="color: #4d4d4d;">Optimizador de Inventario</h1>
        <p style="color: #666; font-size: 1.1rem;">
            Completa pedidos incompletos automáticamente
        </p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# Sidebar con instrucciones
with st.sidebar:
    st.header("📋 Instrucciones")
    st.markdown("""
    1. **Carga** tu archivo Excel
    2. **Revisa** los KPIs y resultados
    3. **Exporta** el reporte para el almacén

    ---

    **Reglas de Emparejamiento:**
    - ✅ Mismo Customer
    - ✅ Mismo Vehicle
    - ✅ Mismo Producto

    **Prioridad:** Mayor DaysStored primero
    """)

# Estado de sesión
if 'df_pares' not in st.session_state:
    st.session_state.df_pares = None
if 'df_sin_par' not in st.session_state:
    st.session_state.df_sin_par = None
if 'df_datos_problema' not in st.session_state:
    st.session_state.df_datos_problema = None
if 'resumen' not in st.session_state:
    st.session_state.resumen = None
if 'df_original' not in st.session_state:
    st.session_state.df_original = None

# Carga de archivo
st.header("1️⃣ Cargar Archivo Excel")

uploaded_file = st.file_uploader(
    "Selecciona el archivo .xlsx con los pedidos",
    type=['xlsx'],
    help="El archivo debe contener: ID, OrderID, Vehicle, Product, "
         + "Customer, DaysStored, SetStatus"
)

if uploaded_file is not None:
    try:
        # Leer el archivo Excel
        st.session_state.df_original = pd.read_excel(
            uploaded_file,
            engine='openpyxl'
        )

        st.success(
            f" Archivo cargado: **{uploaded_file.name}** "
            + f"({len(st.session_state.df_original)} registros)"
        )

        # Ejecutar el emparejamiento
        with st.spinner("🔄 Procesando pedidos incompletos..."):
            df_pares, df_sin_par, df_datos_problema = emparejar_pedidos(
                uploaded_file
            )

            st.session_state.df_pares = df_pares
            st.session_state.df_sin_par = df_sin_par
            st.session_state.df_datos_problema = df_datos_problema

            # Generar resumen estadístico
            st.session_state.resumen = generar_resumen_estadistico(
                df_pares, df_sin_par, df_datos_problema,
                st.session_state.df_original
            )

        st.divider()

        # KPIs en recuadros
        st.header("2️⃣ Resumen del Procesamiento")

        resumen = st.session_state.resumen

        # Fila 1 de KPIs (4 columnas)
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">📊 Pares Formados</div>
                    <div class="metric-value success-text">
                        {resumen['total_pares_formados']}
                    </div>
                    <div style="font-size: 0.85em; color: #666; margin-top: 8px;">
                        ({resumen['pedidos_completados']} pedidos listos)
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">✅ Pedidos Completados</div>
                    <div class="metric-value success-text">
                        {resumen['pedidos_completados']}
                    </div>
                    <div style="font-size: 0.85em; color: #666; margin-top: 8px;">
                        De {resumen['total_incomplete_original']} incompletos
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">⚠️ Pedidos Sin Par</div>
                    <div class="metric-value">
                        {resumen['pedidos_sin_par']}
                    </div>
                    <div style="font-size: 0.85em; color: #666; margin-top: 8px;">
                        Pendientes de otra pieza
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">❌ Datos con Problemas</div>
                    <div class="metric-value warning-text">
                        {resumen['registros_con_datos_faltantes']}
                    </div>
                    <div style="font-size: 0.85em; color: #666; margin-top: 8px;">
                        Falta Customer o Vehicle
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # Fila 2 de KPIs (3 columnas)
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        col5, col6, col7 = st.columns(3)

        with col5:
            st.markdown(f"""
                <div class="metric-card" style="border-top-color: #28a745;">
                    <div class="metric-label">📈 Porcentaje Aprovechado</div>
                    <div class="metric-value success-text">
                        {resumen['porcentaje_aprovechado']}%
                    </div>
                    <div style="font-size: 0.85em; color: #666; margin-top: 8px;">
                        De incompletos originales
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with col6:
            st.markdown(f"""
                <div class="metric-card" style="border-top-color: #17a2b8;">
                    <div class="metric-label">🕐 Días Promedio Liberado</div>
                    <div class="metric-value" style="color: #17a2b8;">
                        {resumen['dias_promedio_inventario_liberado']}
                    </div>
                    <div style="font-size: 0.85em; color: #666; margin-top: 8px;">
                        Promedio de antigüedad
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with col7:
            st.markdown(f"""
                <div class="metric-card" style="border-top-color: #fd7e14;">
                    <div class="metric-label">🔥 Días Máximo Liberado</div>
                    <div class="metric-value" style="color: #fd7e14;">
                        {resumen['dias_maximo_inventario_liberado']}
                    </div>
                    <div style="font-size: 0.85em; color: #666; margin-top: 8px;">
                        El pedido más antiguo
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # Caja de información destacada
        if resumen['pedidos_completados'] > 0:
            st.markdown(f"""
                <div style="background-color: #d4edda; border: 1px solid #c3e6cb;
                    border-radius: 5px; padding: 15px; margin: 10px 0;">
                    <strong>🎉 Impacto del Emparejamiento:</strong><br>
                    Se completaron
                    <strong>{resumen['pedidos_completados']} pedidos</strong>
                    ({resumen['total_pares_formados']} pares),
                    liberando inventario con promedio de
                    <strong>{resumen['dias_promedio_inventario_liberado']} días</strong>
                    en bodega. El pedido más antiguo liberado tenía
                    <strong>{resumen['dias_maximo_inventario_liberado']} días</strong>.
                </div>
            """, unsafe_allow_html=True)

        st.divider()

        # Pestañas de resultados
        st.header("3️⃣ Resultados Detallados")

        tab1, tab2, tab3 = st.tabs([
            "📦 Pares Formados",
            "⚠️ Pedidos Sin Par",
            "❌ Datos con Problemas"
        ])

        with tab1:
            st.subheader("Pares de Pedidos para Completar")
            st.markdown("Ordenados por antigüedad en el inventario")

            if not df_pares.empty:
                columnas_mostrar = [
                    'Numero_Par',
                    'Grupo_Customer',
                    'Grupo_Vehicle',
                    'Grupo_Product',
                    'Pedido_1_OrderID',
                    'Pedido_1_DaysStored',
                    'Pedido_2_OrderID',
                    'Pedido_2_DaysStored',
                    'Total_DaysStored_Promedio'
                ]

                df_display = df_pares[columnas_mostrar].copy()
                df_display.columns = [
                    'N° Par', 'Cliente', 'Vehículo', 'Producto',
                    'Pedido 1', 'Días (1)', 'Pedido 2', 'Días (2)',
                    'Promedio Días'
                ]

                st.dataframe(
                    df_display,
                    use_container_width=True,
                    hide_index=True,
                    height=500
                )

                # Estadísticas adicionales
                st.markdown("##### 📊 Estadísticas de Pares")
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.write(f"**Total pares:** {len(df_pares)}")
                with col_c:
                    max_dias = df_pares['Pedido_1_DaysStored'].max()
                    st.write(f"**Días máximo (1er):** {max_dias:.0f}")
            else:
                st.warning("No se formaron pares con los datos proporcionados.")

        with tab2:
            st.subheader("Pedidos Incompletos Sin Coincidencia")
            st.markdown(
                "No encontraron otro pedido con mismo "
                + "Customer + Vehicle + Product"
            )

            if not df_sin_par.empty:
                df_display = df_sin_par[[
                    'OrderID', 'Serial', 'Customer', 'Vehicle',
                    'Product', 'DaysStored', 'Motivo'
                ]].copy()
                df_display.columns = [
                    'OrderID', 'Serial', 'Cliente', 'Vehículo',
                    'Producto', 'Días Almacenado', 'Motivo'
                ]

                st.dataframe(
                    df_display,
                    use_container_width=True,
                    hide_index=True,
                    height=500
                )
            else:
                st.success(
                    "¡Todos los pedidos incompletos fueron emparejados!"
                )

        with tab3:
            st.subheader("Registros con Datos Faltantes")
            st.markdown("""
                Estos registros **no se procesaron** porque les falta información:
                - **Customer** vacío → No se puede determinar el cliente
                - **Vehicle** vacío → No se puede determinar el vehículo

                **Acción requerida:** Revisar manualmente en SAP.
            """)

            if not df_datos_problema.empty:
                df_display = df_datos_problema[[
                    'ID', 'OrderID', 'Serial', 'Customer', 'Vehicle',
                    'Product', 'DaysStored', 'SetStatus'
                ]].copy()
                df_display.columns = [
                    'ID', 'OrderID', 'Serial', 'Cliente', 'Vehículo',
                    'Producto', 'Días', 'Estado'
                ]

                # Añadir columna indicando qué falta
                def indicar_faltante(row):
                    faltantes = []
                    if pd.isna(row['Cliente']) or str(
                        row['Cliente']
                    ).strip() == '':
                        faltantes.append('Customer')
                    if pd.isna(row['Vehículo']) or str(
                        row['Vehículo']
                    ).strip() == '':
                        faltantes.append('Vehicle')
                    return ', '.join(faltantes)

                df_display['Falta'] = df_display.apply(
                    indicar_faltante,
                    axis=1
                )

                st.dataframe(
                    df_display,
                    use_container_width=True,
                    hide_index=True,
                    height=500
                )

                # Resumen de problemas
                st.markdown("##### 📋 Resumen de Problemas")
                total_sin_customer = df_datos_problema[
                    df_datos_problema['Customer'].isna() |
                    (df_datos_problema['Customer'].astype(
                        str
                    ).str.strip() == '')
                ].shape[0]
                total_sin_vehicle = df_datos_problema[
                    df_datos_problema['Vehicle'].isna() |
                    (df_datos_problema['Vehicle'].astype(
                        str
                    ).str.strip() == '')
                ].shape[0]

                col_x, col_y = st.columns(2)
                with col_x:
                    st.write(f"**Registros sin Customer:** {total_sin_customer}")
                with col_y:
                    st.write(f"**Registros sin Vehicle:** {total_sin_vehicle}")
            else:
                st.success("Todos los registros tienen datos completos.")

        st.divider()

        # Exportación
        st.header("4️⃣ Exportar Resultados")

        # Crear archivo Excel con múltiples hojas
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            if not df_pares.empty:
                df_pares.to_excel(
                    writer,
                    sheet_name='Pares_Formados',
                    index=False
                )
            if not df_sin_par.empty:
                df_sin_par.to_excel(
                    writer,
                    sheet_name='Sin_Par',
                    index=False
                )
            if not df_datos_problema.empty:
                df_datos_problema.to_excel(
                    writer,
                    sheet_name='Datos_Problema',
                    index=False
                )

            resumen_df = pd.DataFrame([
                {
                    'Métrica': 'Total registros originales',
                    'Valor': resumen['total_registros_original']
                },
                {
                    'Métrica': 'Total pedidos incompletos',
                    'Valor': resumen['total_incomplete_original']
                },
                {
                    'Métrica': 'Pares formados',
                    'Valor': resumen['total_pares_formados']
                },
                {
                    'Métrica': 'Pedidos completados',
                    'Valor': resumen['pedidos_completados']
                },
                {
                    'Métrica': 'Pedidos sin par',
                    'Valor': resumen['pedidos_sin_par']
                },
                {
                    'Métrica': 'Registros con datos faltantes',
                    'Valor': resumen['registros_con_datos_faltantes']
                },
                {
                    'Métrica': 'Porcentaje aprovechado',
                    'Valor': f"{resumen['porcentaje_aprovechado']}%"
                },
                {
                    'Métrica': 'Días promedio liberado',
                    'Valor': resumen['dias_promedio_inventario_liberado']
                },
                {
                    'Métrica': 'Días máximo liberado',
                    'Valor': resumen['dias_maximo_inventario_liberado']
                },
            ])
            resumen_df.to_excel(
                writer,
                sheet_name='Resumen',
                index=False
            )

        output.seek(0)

        st.download_button(
            label="📥 Descargar Excel",
            data=output,
            file_name=(
                f"AGP_Emparejamiento_"
                f"{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            ),
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            help=(
                "Descarga un archivo Excel con 4 hojas: "
                + "Pares_Formados, Sin_Par, Datos_Problema, Resumen"
            )
        )

        st.markdown("""
        **El archivo exportado incluye:**
        -  **Pares_Formados**: Lista completa de pares para el almacén
        -  **Sin_Par**: Pedidos que requieren acción manual
        -  **Datos_Problema**: Registros que necesitan corrección en SAP
        -  **Resumen**: KPIs del procesamiento
        """)

    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {str(e)}")
        st.markdown("""
        **Posibles causas:**
        - El archivo no tiene el formato esperado
        - Faltan columnas requeridas
        - El archivo está corrupto

        **Columnas requeridas:** ID, OrderID, Serial, Vehicle, Product,
        Invoice, InvoiceCost, Customer, DaysStored, SetStatus
        """)
else:
    # Estado inicial
    st.info("👆 Carga un archivo Excel para comenzar el procesamiento")

    st.markdown("""
    ### ¿Cómo funciona este sistema?

    1. **Carga** el archivo excel con el inventario
    2. El sistema **filtra** solo los pedidos "Incomplete"
    3. **Agrupa** por Customer + Vehicle + Product
    4. **Prioriza lo más antiguo:** Las piezas con más tiempo
       en bodega se despachan primero
    5. **Exporta** un reporte listo para el almacén
    """)

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9em;">
    <strong>AGP - Sistema de Emparejamiento de Pedidos</strong><br>
    Desarrollado para el equipo comercial | 2026
</div>
""", unsafe_allow_html=True)
