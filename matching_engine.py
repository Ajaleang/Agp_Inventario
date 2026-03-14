"""
Matching Engine para AGP - Emparejamiento de Pedidos Incompletos

Este módulo contiene la lógica de negocio para emparejar pedidos incompletos
según las reglas de AGP:
  1. Mismo Customer
  2. Mismo Vehicle
  3. Mismo Product
  4. Prioridad FIFO (mayor DaysStored primero)
"""

import pandas as pd
from typing import Tuple


def emparejar_pedidos(filepath: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Empareja pedidos incompletos que cumplen las 3 reglas de negocio.
    
    Args:
        filepath: Ruta al archivo Excel con los datos de pedidos
        
    Returns:
        Tupla con 3 DataFrames:
          - df_pares: Pedidos emparejados listos para completar
          - df_sin_par: Pedidos incompletos que no encontraron par
          - df_datos_problema: Registros con Customer o Vehicle nulos
    """
    # Cargar datos del Excel
    df = pd.read_excel(filepath, engine='openpyxl')
    
    # Normalizar nombres de columnas (trim y lowercase para consistencia)
    df.columns = df.columns.str.strip()
    
    # Identificar registros con datos faltantes (no procesables automáticamente)
    df_datos_problema = df[
        df['Customer'].isna() | 
        df['Vehicle'].isna() |
        (df['Customer'].astype(str).str.strip() == '') |
        (df['Vehicle'].astype(str).str.strip() == '')
    ].copy()
    
    # Filtrar solo registros procesables (con Customer y Vehicle válidos)
    df_procesables = df[
        df['Customer'].notna() & 
        df['Vehicle'].notna() &
        (df['Customer'].astype(str).str.strip() != '') &
        (df['Vehicle'].astype(str).str.strip() != '')
    ].copy()
    
    # Filtrar solo pedidos Incomplete
    df_incomplete = df_procesables[df_procesables['SetStatus'] == 'Incomplete'].copy()
    
    # Si no hay incompletos, retornar vacíos
    if df_incomplete.empty:
        return pd.DataFrame(), pd.DataFrame(), df_datos_problema
    
    # Normalizar campos de agrupamiento (trim y uppercase para evitar duplicados por case)
    df_incomplete['Customer_norm'] = df_incomplete['Customer'].astype(str).str.strip().str.upper()
    df_incomplete['Vehicle_norm'] = df_incomplete['Vehicle'].astype(str).str.strip().str.upper()
    df_incomplete['Product_norm'] = df_incomplete['Product'].astype(str).str.strip().str.upper()
    
    # Ordenar por DaysStored DESC (FIFO: los más antiguos primero)
    df_incomplete = df_incomplete.sort_values('DaysStored', ascending=False)
    
    # Lista para almacenar los pares formados
    pares_list = []
    sin_par_list = []
    
    # Agrupar por las 3 claves de negocio
    grupos = df_incomplete.groupby(['Customer_norm', 'Vehicle_norm', 'Product_norm'])
    
    for nombre_grupo, grupo_df in grupos:
        customer, vehicle, product = nombre_grupo
        
        # Obtener registros del grupo (ya ordenados por DaysStored DESC)
        registros = grupo_df.copy()
        total_registros = len(registros)
        
        # Emparejar de 2 en 2 (0-1, 2-3, 4-5...)
        idx = 0
        while idx < total_registros:
            if idx + 1 < total_registros:
                # Tenemos par: registro[idx] + registro[idx+1]
                pedido1 = registros.iloc[idx]
                pedido2 = registros.iloc[idx + 1]
                
                par = {
                    'Grupo_Customer': customer,
                    'Grupo_Vehicle': vehicle,
                    'Grupo_Product': product,
                    'Pedido_1_ID': pedido1['ID'],
                    'Pedido_1_OrderID': pedido1['OrderID'],
                    'Pedido_1_Serial': pedido1['Serial'],
                    'Pedido_1_Invoice': pedido1['Invoice'],
                    'Pedido_1_DaysStored': pedido1['DaysStored'],
                    'Pedido_2_ID': pedido2['ID'],
                    'Pedido_2_OrderID': pedido2['OrderID'],
                    'Pedido_2_Serial': pedido2['Serial'],
                    'Pedido_2_Invoice': pedido2['Invoice'],
                    'Pedido_2_DaysStored': pedido2['DaysStored'],
                    'Total_DaysStored_Promedio': (pedido1['DaysStored'] + pedido2['DaysStored']) / 2,
                    'Numero_Par': len(pares_list) + 1
                }
                pares_list.append(par)
                idx += 2
            else:
                # Registro sin par (último impar del grupo)
                registro = registros.iloc[idx]
                sin_par = {
                    'ID': registro['ID'],
                    'OrderID': registro['OrderID'],
                    'Serial': registro['Serial'],
                    'Customer': registro['Customer'],
                    'Vehicle': registro['Vehicle'],
                    'Product': registro['Product'],
                    'Invoice': registro['Invoice'],
                    'DaysStored': registro['DaysStored'],
                    'Motivo': 'Sin par disponible en este grupo'
                }
                sin_par_list.append(sin_par)
                idx += 1
    
    # Crear DataFrames de resultado
    if pares_list:
        df_pares = pd.DataFrame(pares_list)
        # Ordenar por DaysStored del primer pedido (FIFO)
        df_pares = df_pares.sort_values('Pedido_1_DaysStored', ascending=False)
        df_pares = df_pares.reset_index(drop=True)
    else:
        df_pares = pd.DataFrame()
    
    if sin_par_list:
        df_sin_par = pd.DataFrame(sin_par_list)
        df_sin_par = df_sin_par.sort_values('DaysStored', ascending=False)
        df_sin_par = df_sin_par.reset_index(drop=True)
    else:
        df_sin_par = pd.DataFrame()
    
    # Limpiar columnas temporales (no se incluyen en el output)
    # df_datos_problema ya está limpio
    
    return df_pares, df_sin_par, df_datos_problema


def generar_resumen_estadistico(df_pares: pd.DataFrame, 
                                  df_sin_par: pd.DataFrame,
                                  df_datos_problema: pd.DataFrame,
                                  df_original: pd.DataFrame) -> dict:
    """
    Genera un resumen estadístico del proceso de emparejamiento.
    
    Args:
        df_pares: DataFrame con los pares formados
        df_sin_par: DataFrame con pedidos sin par
        df_datos_problema: DataFrame con registros con datos faltantes
        df_original: DataFrame original cargado del Excel
        
    Returns:
        Diccionario con estadísticas clave
    """
    total_incomplete_original = len(df_original[df_original['SetStatus'] == 'Incomplete'])
    total_pares = len(df_pares) if not df_pares.empty else 0
    total_sin_par = len(df_sin_par) if not df_sin_par.empty else 0
    total_datos_problema = len(df_datos_problema)
    
    # Calcular inventario liberado (en días de almacenamiento)
    if not df_pares.empty:
        dias_promedio_liberados = df_pares['Total_DaysStored_Promedio'].mean()
        dias_maximo_liberado = df_pares['Pedido_1_DaysStored'].max()
    else:
        dias_promedio_liberados = 0
        dias_maximo_liberado = 0
    
    return {
        'total_registros_original': len(df_original),
        'total_incomplete_original': total_incomplete_original,
        'total_pares_formados': total_pares,
        'pedidos_completados': total_pares * 2,  # Cada par son 2 pedidos
        'pedidos_sin_par': total_sin_par,
        'registros_con_datos_faltantes': total_datos_problema,
        'porcentaje_aprovechado': round((total_pares * 2 / total_incomplete_original * 100) if total_incomplete_original > 0 else 0, 2),
        'dias_promedio_inventario_liberado': round(dias_promedio_liberados, 1),
        'dias_maximo_inventario_liberado': int(dias_maximo_liberado),
    }
