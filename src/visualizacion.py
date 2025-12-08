import pandas as pd
import folium
from folium.plugins import HeatMap
import matplotlib.pyplot as plt
import seaborn as sns
import os


RADIO_CIRCULO_METROS = 40000  # 40 km (Mismo radio que en el mapa de analisis)

def generar_mapas_y_graficos(ruta_csv_solucion):
    print("--- INICIANDO VISUALIZACIÓN ---")
    
    if not ruta_csv_solucion or not os.path.exists(ruta_csv_solucion):
        print("❌ No se encontró el archivo de solución.")
        return

    # 1. DEFINIR RUTAS (Carpeta ../maps)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MAPS_DIR = os.path.join(BASE_DIR, '..', 'maps')
    if not os.path.exists(MAPS_DIR):
        os.makedirs(MAPS_DIR)

    # Nombres de archivos
    MAPA_ARANA = os.path.join(MAPS_DIR, "Mapa_Final_Asignaciones.html")
    MAPA_COBERTURA = os.path.join(MAPS_DIR, "Mapa_Solucion_Cobertura.html") # <--- ESTE ES EL NUEVO
    GRAFICO_1 = os.path.join(MAPS_DIR, "grafico_poblacion.png")
    GRAFICO_2 = os.path.join(MAPS_DIR, "grafico_municipios.png")

    # Cargar datos
    df = pd.read_csv(ruta_csv_solucion)
    
    # Preparamos las bases elegidas (unicas)
    bases_activas = df[['helipuerto_nombre', 'lat_heli', 'lon_heli']].drop_duplicates()

    # -------------------------------------------------------------------------
    # MAPA 1: ARAÑA (Líneas de conexión) - Útil para ver asignaciones exactas
    # -------------------------------------------------------------------------
    print("Generando Mapa de Araña...")
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

    # Marcadores de bases en el mapa de araña
    for _, row in bases_activas.iterrows():
        folium.Marker(
            location=[row['lat_heli'], row['lon_heli']],
            popup=row['helipuerto_nombre'],
            icon=folium.Icon(color='blue', icon='helicopter', prefix='fa')
        ).add_to(mapa_1)

    mapa_1.save(MAPA_ARANA)
    print(f"✅ Mapa Araña guardado: {MAPA_ARANA}")

    # -------------------------------------------------------------------------
    # MAPA 2: Mapa de calor 
    # -------------------------------------------------------------------------
    print("Generando Mapa de Cobertura Final (Estilo Análisis)...")
    mapa_2 = folium.Map(location=[center_lat, center_lon], zoom_start=7, tiles='CartoDB positron')

    # CAPA A: MAPA DE CALOR DE POBLACIÓN (Igual que en analisis_inicial.py)
    # Usamos la columna 'poblacion' del CSV de solución
    # Normalizamos un poco para que se vea bien
    max_pob = df['poblacion'].max()
    datos_calor = df[['lat_muni', 'lon_muni', 'poblacion']].values.tolist()
    
    # Truco: Si pasamos la población tal cual, folium la usa como "peso".
    # Usamos los mismos parámetros visuales que tu primer mapa (radius=15, blur=20)
    # NOTA: Para que quede idéntico, asegurate de que los datos_calor tengan el peso normalizado si lo hiciste antes.
    # Aquí lo haremos simple pasando [lat, lon, poblacion] directo, Folium lo gestiona.
    HeatMap(datos_calor, radius=15, blur=20, max_zoom=1).add_to(mapa_2)

    # CAPA B: CÍRCULOS DE COBERTURA (Solo de las bases elegidas)
    for _, row in bases_activas.iterrows():
        # 1. El Círculo Verde (Radio 40km)
        folium.Circle(
            location=[row['lat_heli'], row['lon_heli']],
            radius=RADIO_CIRCULO_METROS,  # 40000 metros
            color='green',
            fill=True,
            fill_color='green',
            fill_opacity=0.2, # Transparente para ver el calor debajo
            popup='Cobertura 40km'
        ).add_to(mapa_2)

        # 2. El Icono del Helicóptero
        folium.Marker(
            location=[row['lat_heli'], row['lon_heli']],
            popup=f"BASE ACTIVA: {row['helipuerto_nombre']}",
            icon=folium.Icon(color='blue', icon='helicopter', prefix='fa')
        ).add_to(mapa_2)

    mapa_2.save(MAPA_COBERTURA)
    print(f"✅ Mapa Cobertura Final guardado: {MAPA_COBERTURA}")

    # -------------------------------------------------------------------------
    # GRÁFICOS ESTADÍSTICOS
    # -------------------------------------------------------------------------
    print("Generando gráficos...")
    resumen = df.groupby('helipuerto_nombre').agg({
        'poblacion': 'sum',
        'municipio_id': 'count' # Asegúrate que tu CSV tiene esta columna o usa 'municipio'
    }).reset_index().sort_values('poblacion', ascending=False)
    
    # Renombrar para claridad
    col_conteo = 'municipio_id' if 'municipio_id' in df.columns else 'municipio'
    resumen.rename(columns={col_conteo: 'num_municipios'}, inplace=True)
    
    sns.set_theme(style="whitegrid")

    # Gráfico Población
    plt.figure(figsize=(10, 6))
    sns.barplot(data=resumen, x='poblacion', y='helipuerto_nombre', palette='viridis')
    plt.title('Población Cubierta por Base')
    plt.tight_layout()
    plt.savefig(GRAFICO_1)
    plt.close()

    # Gráfico Municipios
    resumen = resumen.sort_values('num_municipios', ascending=False)
    plt.figure(figsize=(10, 6))
    sns.barplot(data=resumen, x='num_municipios', y='helipuerto_nombre', palette='magma')
    plt.title('Municipios Asignados por Base')
    plt.tight_layout()
    plt.savefig(GRAFICO_2)
    plt.close()

    print(f"✅ Gráficos guardados en: {MAPS_DIR}")