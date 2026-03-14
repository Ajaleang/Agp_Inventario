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

## Demo

```bash
pip install -r requirements.txt
streamlit run app.py
```

Sube el archivo `Mock_Data.xlsx` y la herramienta genera automáticamente:
- **Pares formados** — listos para despachar, ordenados del más antiguo al más reciente
- **Pedidos sin par** — esperando otra pieza compatible
- **Datos con problemas** — registros sin Cliente o Vehículo, para corrección en SAP

---

## Arquitectura

```
┌─────────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│  Interfaz Web       │────▶│  Motor de Reglas      │────▶│  Exportación    │
│  Streamlit          │     │  matching_engine.py   │     │  Excel (.xlsx)  │
│  app.py             │     │  Python + Pandas      │     │  3 hojas        │
└─────────────────────┘     └──────────────────────┘     └─────────────────┘
       ▲
  URL pública · Sin instalación · En español
```

El motor (`matching_engine.py`) está completamente separado de la UI. En una fase futura puede convertirse en una API REST (FastAPI) para integración directa con SAP.

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

## Roadmap

| Fase | Estado | Descripción |
|---|---|---|
| **Fase 1 — Prototipo** | ✅ Disponible | Motor Python + Streamlit + exportación Excel |
| **Fase 2 — SAP** | Planificada Q2 2026 | Lectura automática desde SAP vía API RFC |
| **Fase 3 — Automatización** | Planificada Q3 2026 | Ejecución diaria + alertas por email |
| **Fase 4 — Inteligencia** | Planificada Q4 2026 | ML para predicción de completitud de pedidos |

---

> **Esta solución ya existe. Está probada. Está lista.**  
> El prototipo procesa los 3,838 registros reales de AGP e identifica los 471 pares despachables en menos de 5 segundos. El equipo comercial puede empezar a usarlo mañana, desde un enlace web, sin instalar nada.
