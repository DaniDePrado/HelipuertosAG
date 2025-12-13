# src/visualizacion.py
import pandas as pd
import folium
from folium.plugins import HeatMap
import matplotlib.pyplot as plt
import seaborn as sns
import os

# CONFIGURACIÓN VISUAL
RADIO_CIRCULO_METROS = 40000 

def generar_mapas_y_graficos(ruta_csv_solucion):
    print(f"Procesando visualización para: {os.path.basename(ruta_csv_solucion)}...")
    
    if not ruta_csv_solucion or not os.path.exists(ruta_csv_solucion):
        print(" No se encontró el archivo de solución.")
        return

    # 1. DEFINIR RUTAS DINÁMICAS
    nombre_base = os.path.splitext(os.path.basename(ruta_csv_solucion))[0]
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MAPS_DIR = os.path.join(BASE_DIR, '..', 'maps')
    if not os.path.exists(MAPS_DIR):
        os.makedirs(MAPS_DIR)

    # Ahora los nombres de salida INCLUYEN el nombre del escenario
    MAPA_ARANA = os.path.join(MAPS_DIR, f"Mapa_Araña_{nombre_base}.html")
    MAPA_COBERTURA = os.path.join(MAPS_DIR, f"Mapa_Cobertura_{nombre_base}.html")
    GRAFICO_1 = os.path.join(MAPS_DIR, f"Grafico_Poblacion_{nombre_base}.png")
    GRAFICO_2 = os.path.join(MAPS_DIR, f"Grafico_Municipios_{nombre_base}.png")

    # Cargar datos
    df = pd.read_csv(ruta_csv_solucion)
    bases_activas = df[['helipuerto_nombre', 'lat_heli', 'lon_heli']].drop_duplicates()

    # --- MAPA 1: ARAÑA ---
    center_lat = df['lat_muni'].mean()
    center_lon = df['lon_muni'].mean()
    mapa_1 = folium.Map(location=[center_lat, center_lon], zoom_start=7, tiles='CartoDB positron')

    for _, row in df.iterrows():
        color = 'green'
        if row['distancia_km'] > 45: color = 'red'
        elif row['distancia_km'] > 30: color = 'orange'
        folium.PolyLine(
            locations=[[row['lat_muni'], row['lon_muni']], [row['lat_heli'], row['lon_heli']]],
            color=color, weight=0.5, opacity=0.4
        ).add_to(mapa_1)

    for _, row in bases_activas.iterrows():
        folium.Marker(
            location=[row['lat_heli'], row['lon_heli']],
            popup=row['helipuerto_nombre'],
            icon=folium.Icon(color='blue', icon='helicopter', prefix='fa')
        ).add_to(mapa_1)

    mapa_1.save(MAPA_ARANA)

    # MAPA 2: COBERTURA 
    mapa_2 = folium.Map(location=[center_lat, center_lon], zoom_start=7, tiles='CartoDB positron')

    # Calor de población
    datos_calor = df[['lat_muni', 'lon_muni', 'poblacion']].values.tolist()
    HeatMap(datos_calor, radius=15, blur=20).add_to(mapa_2)

    # Círculos
    for _, row in bases_activas.iterrows():
        folium.Circle(
            location=[row['lat_heli'], row['lon_heli']],
            radius=RADIO_CIRCULO_METROS,
            color='green', fill=True, fill_color='green', fill_opacity=0.2,
            popup='Cobertura 40km'
        ).add_to(mapa_2)
        
        folium.Marker(
            location=[row['lat_heli'], row['lon_heli']],
            popup=f"BASE: {row['helipuerto_nombre']}",
            icon=folium.Icon(color='blue', icon='helicopter', prefix='fa')
        ).add_to(mapa_2)

    mapa_2.save(MAPA_COBERTURA)

    # --- GRÁFICOS ---
    resumen = df.groupby('helipuerto_nombre').agg({
        'poblacion': 'sum',
        'municipio_id': 'count' 
    }).reset_index().sort_values('poblacion', ascending=False)
    
    resumen.rename(columns={'municipio_id': 'num_municipios'}, inplace=True)
    sns.set_theme(style="whitegrid")

    # Gráfico 1
    plt.figure(figsize=(10, 6))
    sns.barplot(data=resumen, x='poblacion', y='helipuerto_nombre', palette='viridis', hue='helipuerto_nombre', legend=False)
    plt.title(f'Población Cubierta - {nombre_base}')
    plt.tight_layout()
    plt.savefig(GRAFICO_1)
    plt.close()

    # Gráfico 2
    resumen = resumen.sort_values('num_municipios', ascending=False)
    plt.figure(figsize=(10, 6))
    sns.barplot(data=resumen, x='num_municipios', y='helipuerto_nombre', palette='magma', hue='helipuerto_nombre', legend=False)
    plt.title(f'Municipios Asignados - {nombre_base}')
    plt.tight_layout()
    plt.savefig(GRAFICO_2)
    plt.close()

    print(f" Generados mapas y gráficos para: {nombre_base}")