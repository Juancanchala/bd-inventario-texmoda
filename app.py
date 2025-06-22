import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns

from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Dashboard Inventario Mujer", layout="wide")

# Cargar datos
@st.cache_data
def load_data():
    return pd.read_csv("data/inventario_mujer.csv", parse_dates=["fecha_ingreso"])

df = load_data()
df["valor_total"] = df["stock"] * df["costo_unitario"]

# KPIs
total_stock = int(df["stock"].sum())
valor_total = df["valor_total"].sum()
productos_bajo_stock = (df["stock"] < df["stock_minimo"]).sum()

# Título centrado
st.markdown(
    "<h1 style='text-align: center; margin-bottom: 30px;'>🧵 Dashboard de Inventario Textil – Línea Mujer (2023 - 2024)</h1>",
    unsafe_allow_html=True
)

# ========================================
# KPIs EN LA PARTE SUPERIOR (3 columnas centradas)
# ========================================
col_kpi1, col_kpi2, col_kpi3 = st.columns([1, 1, 1])

card_style = """
    background-color: #1c1c1e;
    padding: 15px;
    border-radius: 10px;
    box-shadow: 2px 2px 8px rgba(0,0,0,0.3);
    text-align: center;
    height: 100px;
    display: flex;
    flex-direction: column;
    justify-content: center;
"""

with col_kpi1:
    st.markdown(
        f"""<div style="{card_style}">
                <h5 style='color:#f4c542; margin: 0;'>🧶 Total Stock</h5>
                <h3 style='color:white; margin: 5px 0;'>{total_stock:,}</h3>
            </div>""",
        unsafe_allow_html=True
    )

with col_kpi2:
    st.markdown(
        f"""<div style="{card_style}">
                <h5 style='color:#f4c542; margin: 0;'>💰 Valor Total</h5>
                <h3 style='color:white; margin: 5px 0;'>${valor_total:,.0f}</h3>
            </div>""",
        unsafe_allow_html=True
    )

with col_kpi3:
    st.markdown(
        f"""<div style="{card_style}">
                <h5 style='color:#f4c542; margin: 0;'>⚠️ Bajo Stock</h5>
                <h3 style='color:white; margin: 5px 0;'>{productos_bajo_stock}</h3>
            </div>""",
        unsafe_allow_html=True
    )

st.markdown("<br>", unsafe_allow_html=True)

# ========================================
# FILTROS EN SIDEBAR (más compactos)
# ========================================
with st.sidebar:
    st.markdown("### 🔧 Filtros")
    
    # Filtro de año
    df["año"] = df["fecha_ingreso"].dt.year
    años_disponibles = sorted(df["año"].unique())
    año_seleccionado = st.selectbox("📅 Año:", años_disponibles)
    
    # Filtro de tienda
    tiendas = df["tienda"].unique().tolist()
    tienda_seleccionada = st.selectbox("🏬 Tienda:", ["Todas"] + tiendas)
    
    # Filtro de categoría
    categorias = df["categoria"].unique().tolist()
    categoria_seleccionada = st.selectbox("🧵 Categoría:", ["Todas"] + categorias)
    
    if st.button("🧼 Limpiar Filtros"):
        st.rerun()

# ========================================
# PREPARACIÓN DE DATOS
# ========================================
# Filtrar por año
df_filtrado = df[df["año"] == año_seleccionado].copy()

# Aplicar filtros adicionales
if tienda_seleccionada != "Todas":
    df_filtrado = df_filtrado[df_filtrado["tienda"] == tienda_seleccionada]

if categoria_seleccionada != "Todas":
    df_filtrado = df_filtrado[df_filtrado["categoria"] == categoria_seleccionada]

# Preparar datos para gráficas
df_filtrado["mes"] = df_filtrado["fecha_ingreso"].dt.month
df_filtrado["Año/Mes"] = df_filtrado["año"].astype(str) + "-" + df_filtrado["mes"].astype(str).str.zfill(2)

# ========================================
# LAYOUT 2x2 PARA GRÁFICAS
# ========================================

# FILA 1: Mapa de Calor + Mapa de Zonas
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("#### 🔥 Mapa de Calor de Demanda")
    
    # Datos para heatmap
    base = df_filtrado.groupby(["categoria", "Año/Mes"]).size().reset_index(name="conteo")
    heatmap_data = base.pivot(index="categoria", columns="Año/Mes", values="conteo").fillna(0)
    
    if not heatmap_data.empty:
        fig, ax = plt.subplots(figsize=(8, 3.8))  # Altura exacta para uniformidad
        fig.patch.set_facecolor('#0e1117')
        ax.set_facecolor('#0e1117')
        
        heatmap = sns.heatmap(
            heatmap_data,
            cmap="YlOrRd",
            linewidths=0.5,
            annot=True,
            fmt='.0f',
            cbar_kws={"label": "Demanda"},
            ax=ax
        )
        
        ax.set_xlabel("Período", fontsize=10, color='white')
        ax.set_ylabel("Categoría", fontsize=10, color='white')
        ax.tick_params(colors='white', labelsize=8)
        
        # Colorbar styling
        cbar = heatmap.collections[0].colorbar
        cbar.ax.yaxis.label.set_color('white')
        cbar.ax.tick_params(colors='white', labelsize=8)
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.info("No hay datos para mostrar en el mapa de calor")

with col2:
    st.markdown("#### 📍 Mapa de Zonas de Inventario")
    
    # Datos para mapa
    zonas = df_filtrado.groupby("tienda")["stock"].sum().reset_index()
    zonas["lat"] = zonas["tienda"].map({
        "Medellín": 6.2442, "Bogotá": 4.7110,
        "Barranquilla": 10.9639, "Cali": 3.4516
    })
    zonas["lon"] = zonas["tienda"].map({
        "Medellín": -75.5812, "Bogotá": -74.0721,
        "Barranquilla": -74.7964, "Cali": -76.5320
    })
    
    if not zonas.empty:
        fig_map = px.scatter_mapbox(
            zonas,
            lat="lat", lon="lon", 
            size="stock", 
            color="tienda",
            hover_name="tienda",
            hover_data={"stock": True, "lat": False, "lon": False},
            zoom=4, 
            height=300,
            title=""
        )
        fig_map.update_layout(
            mapbox_style="open-street-map",
            margin={"r":0,"t":0,"l":0,"b":0},
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.info("No hay datos para mostrar en el mapa")

# FILA 2: Tendencia de Stock + Top Productos
col3, col4 = st.columns([1, 1])

with col3:
    st.markdown("#### 📈 Tendencia de Stock por Mes")
    
    df_mes = df_filtrado.groupby("mes")["stock"].sum().reset_index()
    df_mes["mes_nombre"] = df_mes["mes"].map({
        1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
        7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"
    })
    
    if not df_mes.empty:
        fig_line = px.line(
            df_mes, 
            x="mes_nombre", 
            y="stock",
            markers=True,
            title="",
            height=300
        )
        fig_line.update_layout(
            xaxis_title="Mes",
            yaxis_title="Stock Total",
            margin={"r":0,"t":20,"l":0,"b":0}
        )
        fig_line.update_traces(
            line=dict(color='#f4c542', width=3),
            marker=dict(size=8)
        )
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("No hay datos para mostrar la tendencia")

with col4:
    st.markdown("#### 📊 Stock por Categoría")
    
    # Agrupar por categoría para evitar el error de columna "producto"
    stock_categoria = df_filtrado.groupby("categoria")["stock"].sum().reset_index()
    stock_categoria = stock_categoria.sort_values("stock", ascending=True)
    
    if not stock_categoria.empty:
        fig_bar = px.bar(
            stock_categoria,
            x="stock",
            y="categoria",
            orientation="h",
            height=300,
            title="",
            color="stock",
            color_continuous_scale="viridis"
        )
        fig_bar.update_layout(
            xaxis_title="Stock Total",
            yaxis_title="",
            margin={"r":0,"t":20,"l":0,"b":0},
            showlegend=False,
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No hay datos para mostrar")

# ========================================
# TABLA RESUMEN (más compacta)
# ========================================
st.markdown("#### 📋 Resumen de Productos")

# Mostrar solo las columnas más importantes
columnas_importantes = ["categoria", "tienda", "stock", "stock_minimo", "costo_unitario"]
df_tabla = df_filtrado[columnas_importantes].copy()

# Agregar indicador de estado
df_tabla["Estado"] = df_tabla.apply(
    lambda row: "🔴 Bajo Stock" if row["stock"] < row["stock_minimo"] else "🟢 OK", 
    axis=1
)

# Renombrar columnas para mejor presentación
df_tabla = df_tabla.rename(columns={
    "categoria": "Categoría",
    "tienda": "Tienda", 
    "stock": "Stock",
    "stock_minimo": "Stock Mín",
    "costo_unitario": "Costo Unit"
})

# Mostrar tabla con altura limitada
st.dataframe(
    df_tabla, 
    use_container_width=True,
    height=200,
    hide_index=True
)