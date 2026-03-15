import pandas as pd
from typing import Tuple

REQUIRED_COLS = [
    'ID', 'OrderID', 'Serial', 'Vehicle', 'Product',
    'Invoice', 'Customer', 'DaysStored', 'SetStatus'
]


def emparejar_pedidos(
    df: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    df = df.copy()
    df.columns = df.columns.str.strip()

    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(
            f"El archivo Excel no contiene las columnas requeridas: "
            f"{missing}. "
            f"Columnas encontradas: {list(df.columns)}"
        )

    df_datos_problema = df[
        df['Customer'].isna() |
        df['Vehicle'].isna() |
        (df['Customer'].astype(str).str.strip() == '') |
        (df['Vehicle'].astype(str).str.strip() == '')
    ].copy()

    df_procesables = df[
        df['Customer'].notna() &
        df['Vehicle'].notna() &
        (df['Customer'].astype(str).str.strip() != '') &
        (df['Vehicle'].astype(str).str.strip() != '')
    ].copy()

    df_incomplete = df_procesables[
        df_procesables['SetStatus'] == 'Incomplete'
    ].copy()
    if df_incomplete.empty:
        return pd.DataFrame(), pd.DataFrame(), df_datos_problema
    df_incomplete['Customer_norm'] = (
        df_incomplete['Customer'].astype(str).str.strip().str.upper()
    )
    df_incomplete['Vehicle_norm'] = (
        df_incomplete['Vehicle'].astype(str).str.strip().str.upper()
    )
    df_incomplete['Product_norm'] = (
        df_incomplete['Product'].astype(str).str.strip().str.upper()
    )

    df_incomplete = df_incomplete.sort_values('DaysStored', ascending=False)
    pares_list = []
    sin_par_list = []
    grupos = df_incomplete.groupby([
        'Customer_norm',
        'Vehicle_norm',
        'Product_norm'
    ])

    for nombre_grupo, grupo_df in grupos:
        customer, vehicle, product = nombre_grupo

        registros = grupo_df.copy()
        total_registros = len(registros)
        idx = 0
        while idx < total_registros:
            if idx + 1 < total_registros:
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
                    'Total_DaysStored_Promedio': (
                        pedido1['DaysStored'] + pedido2['DaysStored']
                    ) / 2,
                    'Numero_Par': len(pares_list) + 1
                }
                pares_list.append(par)
                idx += 2
            else:
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

    if pares_list:
        df_pares = pd.DataFrame(pares_list)
        df_pares = df_pares.sort_values(
            'Pedido_1_DaysStored',
            ascending=False
        ).reset_index(drop=True)
    else:
        df_pares = pd.DataFrame()

    if sin_par_list:
        df_sin_par = pd.DataFrame(sin_par_list)
        df_sin_par = df_sin_par.sort_values(
            'DaysStored',
            ascending=False
        ).reset_index(drop=True)
    else:
        df_sin_par = pd.DataFrame()

    return df_pares, df_sin_par, df_datos_problema


def generar_resumen_estadistico(
    df_pares: pd.DataFrame,
    df_sin_par: pd.DataFrame,
    df_datos_problema: pd.DataFrame,
    df_original: pd.DataFrame
) -> dict:
    total_incomplete_original = len(
        df_original[df_original['SetStatus'] == 'Incomplete']
    )
    total_pares = len(df_pares) if not df_pares.empty else 0
    total_sin_par = len(df_sin_par) if not df_sin_par.empty else 0
    total_datos_problema = len(df_datos_problema)
    if (
        not df_pares.empty
        and 'Total_DaysStored_Promedio' in df_pares.columns
        and 'Pedido_1_DaysStored' in df_pares.columns
    ):
        dias_promedio_liberados = df_pares[
            'Total_DaysStored_Promedio'
        ].mean()
        dias_maximo_liberado = df_pares['Pedido_1_DaysStored'].max()
    else:
        dias_promedio_liberados = 0
        dias_maximo_liberado = 0

    return {
        'total_registros_original': len(df_original),
        'total_incomplete_original': total_incomplete_original,
        'total_pares_formados': total_pares,
        'pedidos_completados': total_pares * 2,
        'pedidos_sin_par': total_sin_par,
        'registros_con_datos_faltantes': total_datos_problema,
        'porcentaje_aprovechado': round(
            (total_pares * 2 / total_incomplete_original * 100)
            if total_incomplete_original > 0 else 0,
            2
        ),
        'dias_promedio_inventario_liberado': round(
            dias_promedio_liberados,
            1
        ),
        'dias_maximo_inventario_liberado': int(dias_maximo_liberado),
    }
