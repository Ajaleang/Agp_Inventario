# AGP — Optimizador de Inventario

> **Propuesta Tecnológica · Armando Alean · 2026**  
> Solución para la gestión automatizada de pedidos incompletos en bodega — AGP México

---

## El Problema

AGP mantiene más de **3,800 piezas de vidrio blindado** en su bodega de Ciudad de México. El proceso actual para emparejar pedidos incompletos es **100% manual**: el equipo comercial los busca en Excel, valida por correo y confirma con logística.

| Métrica del Problema | Valor |
|---|---|
| Piezas en inventario | **3,838** |
| Pedidos incompletos (no despachables) | **2,121 (55.3%)** |
| Antigüedad promedio en bodega | **970 días (~2.7 años)** |
| Antigüedad máxima registrada | **1,847 días (~5 años)** |
| Tiempo manual por persona/semana | **8–10 horas** |

---

## La Solución

Una **herramienta web automatizada** que empareja pedidos incompletos aplicando las reglas de negocio de AGP en segundos, sin instalación y con exportación directa al equipo de almacén.

### Reglas de Negocio Implementadas
1. **Mismo Cliente** — nunca se mezclan pedidos de clientes distintos
2. **Mismo Vehículo** — triple coincidencia exacta obligatoria
3. **Mismo Producto** — referencia de vidrio idéntica
4. **Antigüedad primero** — siempre se despacha la pieza con más días en bodega

---

## Impacto

```
ANTES:  8–10 horas / semana  →  DESPUÉS:  < 5 segundos
                                           99% reducción
```


---

## Cómo ejecutar la app

```bash
pip install -r requirements.txt
streamlit run app.py
```

Una vez levantada la app de Streamlit:

1. Abre la URL local que muestra la consola (por defecto `http://localhost:8501`).
2. Sube el archivo `Mock_Data.xlsx` desde el panel lateral o el botón de carga.
3. Configura, si aplica, filtros básicos (cliente, rango de fechas, etc.).
4. Haz clic en el botón de procesamiento para que se ejecuten las reglas de negocio.

La herramienta genera automáticamente:
- **Pares formados** — listos para despachar, ordenados del más antiguo al más reciente.
- **Pedidos sin par** — esperando otra pieza compatible.
- **Datos con problemas** — registros sin Cliente o Vehículo (u otros campos clave), para corrección en SAP.

---

## Funcionamiento de la aplicación

```
┌─────────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│  Interfaz Web       │────▶│  Motor de Reglas      │────▶│  Exportación    │
│  Streamlit          │     │  matching_engine.py   │     │  Excel (.xlsx)  │
│  app.py             │     │  Python + Pandas      │     │  3 hojas        │
└─────────────────────┘     └──────────────────────┘     └─────────────────┘
       ▲
  URL pública · Sin instalación · En español
```

El flujo general es:

1. **Carga de datos**  
   `app.py` lee el archivo Excel usando `pandas` y valida columnas mínimas (`Cliente`, `Vehículo`, `Producto`, fechas, etc.).

2. **Aplicación de reglas**  
   Los datos limpios se envían al motor de reglas en `matching_engine.py`, que:
   - Filtra registros inválidos o incompletos.
   - Agrupa por cliente, vehículo y producto.
   - Ordena por antigüedad para siempre proponer primero la pieza más vieja.
   - Forma pares de pedidos compatibles según las reglas de negocio descritas arriba.

3. **Generación de resultados**  
   El motor devuelve tres `DataFrame` principales:
   - `pares_formados`
   - `pedidos_sin_par`
   - `datos_con_problemas`

4. **Presentación y exportación**  
   `app.py` muestra tablas interactivas en Streamlit y ofrece un botón para descargar un Excel con tres hojas (una por cada resultado). Este archivo es el que se comparte con el equipo de almacén y comercial.

El motor (`matching_engine.py`) está completamente separado de la UI. En una fase futura puede convertirse en una API REST (FastAPI) para integración directa con SAP.

---

## Detalles del código

- **`app.py` (capa de presentación)**  
  - Define la interfaz de usuario en Streamlit (título, descripción, formulario de carga del archivo).  
  - Llama a funciones de `matching_engine.py` pasando los `DataFrame` leídos desde Excel.  
  - Controla el flujo de la sesión (qué mostrar en pantalla según el estado del procesamiento).  
  - Renderiza tablas, métricas resumidas y el botón de descarga de resultados.

- **`matching_engine.py` (capa de negocio)**  
  - Contiene funciones puras de Python que reciben y devuelven `DataFrame` de `pandas`.  
  - Aplica las reglas de negocio de AGP (mismo cliente, mismo vehículo, mismo producto, antigüedad).  
  - Separa datos inconsistentes o incompletos para que puedan corregirse en los sistemas de origen.  
  - Está diseñado para poder ser importado desde otros contextos (scripts, notebooks, futura API REST).

- **`requirements.txt`**  
  - Lista las versiones mínimas de librerías necesarias (`streamlit`, `pandas`, `openpyxl`, etc.).  
  - Permite replicar el entorno fácilmente ejecutando `pip install -r requirements.txt`.

---

## Stack Tecnológico

| Capa | Tecnología | Justificación |
|---|---|---|
| UI | `streamlit >= 1.32` | Sin HTML/CSS, URL pública, sin instalación para el usuario |
| Lógica | `pandas >= 2.0` + Python 3.10+ | Manipulación de datos tabulares, sin dependencias externas |
| Almacenamiento | `openpyxl >= 3.1` | Lectura/escritura Excel sin servidor |
| Deploy | Streamlit Community Cloud | Gratis, acceso por URL, sin infraestructura |

---

## Estructura del Proyecto

```
AGP/
├── app.py                 # Interfaz Streamlit (UI)
├── matching_engine.py     # Motor de emparejamiento (lógica de negocio)
├── requirements.txt       # Dependencias
└── Mock_Data.xlsx         # Datos de inventario (3,838 registros)
```

---
