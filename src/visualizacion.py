# src/visualizacion.py
import pandas as pd
import folium
import matplotlib.pyplot as plt
import seaborn as sns
import os

def generar_mapas_y_graficos(ruta_csv_solucion):
    """
    Lee el CSV de solución y genera:
    1. Mapa HTML de araña.
    2. Gráficos PNG de estadísticas.
    """
    print("--- INICIANDO VISUALIZACIÓN ---")
    
    if not ruta_csv_solucion or not os.path.exists(ruta_csv_solucion):
        print("No se encontró el archivo de solución. No se pueden generar mapas.")
        return

    # Definir rutas de salida
    DATA_DIR = os.path.dirname(ruta_csv_solucion)
    MAPA_FILE = os.path.join(DATA_DIR, "Mapa_Final_Asignaciones.html")
    GRAFICO_1 = os.path.join(DATA_DIR, "grafico_poblacion.png")
    GRAFICO_2 = os.path.join(DATA_DIR, "grafico_municipios.png")

    # Cargar datos
    df = pd.read_csv(ruta_csv_solucion)

    # --- 1. GENERAR MAPA (Araña) ---
    print("Generando mapa interactivo...")
    # Centrar mapa (media de coordenadas)
    center_lat = df['lat_muni'].mean()
    center_lon = df['lon_muni'].mean()
    mapa = folium.Map(location=[center_lat, center_lon], zoom_start=7, tiles='CartoDB positron')

    # Líneas de conexión
    for _, row in df.iterrows():
        color = 'green'
        if row['distancia_km'] > 45: color = 'red'
        elif row['distancia_km'] > 30: color = 'orange'

        folium.PolyLine(
            locations=[[row['lat_muni'], row['lon_muni']], [row['lat_heli'], row['lon_heli']]],
            color=color, weight=0.5, opacity=0.5
        ).add_to(mapa)

    # Marcadores de Helipuertos (usamos drop_duplicates para no pintar el mismo 100 veces)
    bases = df[['helipuerto_nombre', 'lat_heli', 'lon_heli']].drop_duplicates()
    for _, row in bases.iterrows():
        folium.Marker(
            location=[row['lat_heli'], row['lon_heli']],
            popup=f"BASE: {row['helipuerto_nombre']}",
            icon=folium.Icon(color='red', icon='helicopter', prefix='fa')
        ).add_to(mapa)

    mapa.save(MAPA_FILE)
    print(f"Mapa guardado en: {MAPA_FILE}")

    # --- 2. GENERAR GRÁFICOS ---
    print("Generando gráficos estadísticos...")
    
    # Agrupar datos
    resumen = df.groupby('helipuerto_nombre').agg({
        'poblacion': 'sum',
        'municipio_id': 'count'
    }).reset_index().sort_values('poblacion', ascending=False)
    
    resumen.rename(columns={'municipio_id': 'num_municipios'}, inplace=True)

    # Configurar estilo
    sns.set_theme(style="whitegrid")

    # Gráfico 1: Población
    plt.figure(figsize=(10, 6))
    sns.barplot(data=resumen, x='poblacion', y='helipuerto_nombre', hue='helipuerto_nombre', legend=False, palette='viridis')
    plt.title('Población Cubierta por Base')
    plt.xlabel('Habitantes')
    plt.tight_layout()
    plt.savefig(GRAFICO_1)
    plt.close()

    # Gráfico 2: Municipios
    resumen = resumen.sort_values('num_municipios', ascending=False)
    plt.figure(figsize=(10, 6))
    sns.barplot(data=resumen, x='num_municipios', y='helipuerto_nombre', hue='helipuerto_nombre', legend=False, palette='magma')
    plt.title('Municipios Asignados por Base')
    plt.xlabel('Cantidad de Municipios')
    plt.tight_layout()
    plt.savefig(GRAFICO_2)
    plt.close()

    print(f"Gráficos guardados en: {DATA_DIR}")