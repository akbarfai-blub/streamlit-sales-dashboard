# --- Import Library Utama ---
import streamlit as st 
import pandas as pd
import numpy as np 
from utils.loader import load_model
import plotly.express as px 
import plotly.graph_objects as go 
from datetime import datetime, timedelta

# --- Konfigurasi Halaman ---
st.set_page_config(
    page_title="Toko Online Dashboard",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Load Model ---
try:
    sales_prediction_model, base_month_ordinal, model_features = load_model()
except FileNotFoundError:
    st.error("Model file tidak ditemukan. Pastikan file model_sales.pkl ada di folder 'models'.")
    st.stop()

# --- Judul & Deskripsi Halaman ---
st.title("Dashboard Penjualan Toko Online")
st.markdown(
    "Dashboard ini interaktif, menampilkan performa penjualan, tren, distribusi, dan fitur prediksi sederhana."
)

# --- Load Data CSV ---
@st.cache_data
def load_csv():
    return pd.read_csv("data/data_dummy_retail_store.csv")

df = load_csv()
df['Tanggal_Pesanan'] = pd.to_datetime(df['Tanggal_Pesanan'])

# --- Sidebar Navigasi ---
st.sidebar.header("📋 Navigasi")
page_selection = st.sidebar.radio(
    "Pilih Halaman:",
    ["Overview Dashboard", "Prediksi Penjualan"]
)

# --- Sidebar Filter Wilayah & Kategori ---
st.sidebar.header("📊 Filter Data")

# Filter Wilayah
regions = df['Wilayah'].dropna().unique().tolist()
regions.sort()
selected_region = st.sidebar.selectbox(
    "Pilih Wilayah:",
    options=["Semua Wilayah"] + regions
)

# Filter Kategori Produk
categories = df['Kategori'].dropna().unique().tolist()
categories.sort()
selected_categories = st.sidebar.multiselect(
    "Pilih Kategori Produk:",
    options=categories,
    default=categories
)

# --- Halaman Overview Dashboard ---
if page_selection == "Overview Dashboard":
    st.sidebar.markdown("### 📅 Filter Tanggal")

    # Filter Tanggal
    min_date = df['Tanggal_Pesanan'].min().date()
    max_date = df['Tanggal_Pesanan'].max().date()

    date_range = st.sidebar.date_input(
        "Rentang Tanggal:",
        value=[min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )

    if len(date_range) == 2:
        start_date = datetime.combine(date_range[0], datetime.min.time())
        end_date = datetime.combine(date_range[1], datetime.max.time())
        filtered_df = df[(df['Tanggal_Pesanan'] >= start_date) & (df['Tanggal_Pesanan'] <= end_date)]
    else:
        filtered_df = df
        st.warning("Tanggal tidak dipilih lengkap. Menampilkan seluruh data.")

    # Filter Wilayah
    if selected_region != "Semua Wilayah":
        filtered_df = filtered_df[filtered_df['Wilayah'] == selected_region]

    # Filter Kategori
    if selected_categories:
        filtered_df = filtered_df[filtered_df['Kategori'].isin(selected_categories)]
    else:
        st.warning("Tidak ada kategori yang dipilih. Menampilkan seluruh data.")
        
    st.subheader("📈 Ringkasan Performa Penjualan")

    # Kolom layout untuk metrics
    col1, col2, col3, col4 = st.columns(4)

    # Agregat metrics
    total_sales = filtered_df['Total_Penjualan'].sum()
    total_orders = filtered_df['OrderID'].nunique()
    average_order_value = total_sales / total_orders if total_orders > 0 else 0
    total_products_sold = filtered_df['Jumlah'].sum()

    # Tampilkan metric ke dalam layout
    with col1:
        st.metric(label="Total Penjualan", value=f"Rp {total_sales:,.2f}")
    with col2:
        st.metric(label="Jumlah Pesanan", value=f"{total_orders:,}")
    with col3:
        st.metric(label="Avg. Order Value", value=f"Rp {average_order_value:,.2f}")
    with col4:
        st.metric(label="Jumlah Produk Terjual", value=f"{total_products_sold:,}")
        
    # Tren Penjualan
    st.subheader("📊 Tren Penjualan Bulanan")
    sales_by_month = filtered_df.groupby('Bulan')['Total_Penjualan'].sum().reset_index()

    # agregat sales per bulan
    try:
        sales_by_month['Bulan'] = pd.to_datetime(sales_by_month['Bulan'], format="%Y-%m")
    except:
        pass  # kalau sudah datetime, biarkan saja

    # Urutkan berdasarkan bulan
    sales_by_month = sales_by_month.sort_values('Bulan')

    # Buat line chart dengan Plotly
    fig_tren_penjualan = px.line(
        sales_by_month,
        x='Bulan',
        y='Total_Penjualan',
        markers=True,
        title="Tren Total Penjualan per Bulan",
        labels={"Bulan": "Bulan", "Total_Penjualan": "Total Penjualan (Rp)"},
        template="plotly_white"
    )

    fig_tren_penjualan.update_traces(line=dict(color='royalblue', width=3))
    fig_tren_penjualan.update_layout(xaxis_title="Bulan", yaxis_title="Total Penjualan", title_x=0.3)

    # Tampilkan chart di Streamlit
    st.plotly_chart(fig_tren_penjualan, use_container_width=True)
    
    # --- Penjualan & Produk Terlaris ---
    st.subheader("🏆 Produk Terlaris")

    # Agregasi nilai penjualan per produk
    top_sales_product = (
        filtered_df.groupby('Produk')['Total_Penjualan']
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )

    # Agregasi jumlah produk terjual
    top_quantity_product = (
        filtered_df.groupby('Produk')['Jumlah']
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Berdasarkan Total Penjualan (Rp)**")
        fig_sales = px.bar(
            top_sales_product,
            x='Total_Penjualan',
            y='Produk',
            orientation='h',
            color='Total_Penjualan',
            color_continuous_scale='Blues',
            template='plotly_white'
        )
        fig_sales.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_sales, use_container_width=True)

    with col2:
        st.markdown("**Berdasarkan Jumlah Produk Terjual**")
        fig_quantity = px.bar(
            top_quantity_product,
            x='Jumlah',
            y='Produk',
            orientation='h',
            color='Jumlah',
            color_continuous_scale='Greens',
            template='plotly_white'
        )
        fig_quantity.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_quantity, use_container_width=True)
    
    # --- Distribusi Penjualan Berdasarkan Kategori ---
    st.subheader("🧩 Distribusi Penjualan per Kategori")

    sales_by_category = (
        filtered_df.groupby('Kategori')['Total_Penjualan']
        .sum()
        .reset_index()
    )

    fig_pie = px.pie(
        sales_by_category,
        names='Kategori',
        values='Total_Penjualan',
        title="Proporsi Total Penjualan per Kategori",
        color_discrete_sequence=px.colors.sequential.RdBu,
        hole=0.4  # biar jadi donut chart, bisa dihilangkan kalau mau full pie
    )

    st.plotly_chart(fig_pie, use_container_width=True)
    
    # Penjualan Berdasarkan metode Pembayaran dan Wilayah

else:
    # Halaman Prediksi (bisa diisi logic nanti)
    filtered_df = df.copy()
    