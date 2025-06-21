import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Dashboard Inventario Mujer", layout="wide")

# Título
st.title("📦 Dashboard de Inventario Textil - Línea Mujer (2023 - 2024)")

@st.cache_data
def load_data():
    return pd.read_csv("data/inventario_mujer.csv", parse_dates=["fecha_ingreso"])

df = load_data()

    # Simulación en línea: normalmente aquí iría un archivo CSV o base de datos
    url = "https://raw.githubusercontent.com/Juancanchala/sistema-abastecimiento-oltp/main/data/inventario_mujer.csv"
    return pd.read_csv(url, parse_dates=['fecha_ingreso'])

# Para demo usamos el dataframe generado previamente
from datetime import timedelta
import numpy as np
import random

categorias = ['Vestido', 'Blusa', 'Pantalón', 'Falda', 'Chaqueta']
tiendas = ['Medellín', 'Bogotá', 'Barranquilla', 'Cali']

def generar_fecha_ponderada():
    meses = [1]*8 + [2]*8 + [3]*8 + [4]*8 + [5]*8 + [6]*6 + [7]*6 + [8]*6 + [9]*6 + [10]*8 + [11]*10 + [12]*25
    mes = random.choice(meses)
    dia = np.random.randint(1, 29)
    año = 2023 if mes != 6 else 2024 if random.random() > 0.5 else 2023
    return datetime(año, mes, dia)

productos = []
for i in range(1, 501):
    categoria = random.choice(categorias)
    fecha_ingreso = generar_fecha_ponderada()
    producto = {
        'producto_id': f"P{i:04}",
        'nombre': f"{categoria} Mujer {i}",
        'categoria': categoria,
        'tienda': random.choice(tiendas),
        'stock': np.random.randint(0, 300),
        'stock_minimo': np.random.randint(10, 100),
        'costo_unitario': round(np.random.uniform(10, 120), 2),
        'fecha_ingreso': fecha_ingreso
    }
    productos.append(producto)

df = pd.DataFrame(productos)

# KPIs
col1, col2, col3 = st.columns(3)
col1.metric("Total Stock", f"{int(df['stock'].sum()):,}")
df['valor_total'] = df['stock'] * df['costo_unitario']
col2.metric("Valor Total Inventario", f"${df['valor_total'].sum():,.2f}")
col3.metric("Productos Bajo Stock Mínimo", f"{(df['stock'] < df['stock_minimo']).sum()}")

# Mapa de inventario por tienda
zonas = df.groupby("tienda")["stock"].sum().reset_index()
zonas["lat"] = zonas["tienda"].map({"Medellín": 6.2442, "Bogotá": 4.7110, "Barranquilla": 10.9639, "Cali": 3.4516})
zonas["lon"] = zonas["tienda"].map({"Medellín": -75.5812, "Bogotá": -74.0721, "Barranquilla": -74.7964, "Cali": -76.5320})

st.subheader("📍 Mapa de Zonas de Inventario")
fig_map = px.scatter_mapbox(
    zonas,
    lat="lat", lon="lon", size="stock", color="tienda",
    hover_name="tienda", zoom=4, height=400
)
fig_map.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0})
st.plotly_chart(fig_map, use_container_width=True)

# Filtros
st.sidebar.header("🎛️ Filtros")
tiendas_sel = st.sidebar.multiselect("Tiendas", tiendas, default=tiendas)
categorias_sel = st.sidebar.multiselect("Categorías", categorias, default=categorias)

df_filtrado = df[
    (df['tienda'].isin(tiendas_sel)) &
    (df['categoria'].isin(categorias_sel))
]

# Gráfico de tendencia mensual
df_filtrado['mes'] = df_filtrado['fecha_ingreso'].dt.to_period("M").astype(str)
df_mes = df_filtrado.groupby("mes")["stock"].sum().reset_index()
fig_line = px.line(df_mes, x="mes", y="stock", title="📈 Tendencia de Stock por Mes")
st.plotly_chart(fig_line, use_container_width=True)

# Tabla final
st.subheader("📋 Detalle de Productos Filtrados")
st.dataframe(df_filtrado.drop(columns=['valor_total', 'mes']), use_container_width=True)
