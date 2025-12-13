import pandas as pd
import folium
from folium.plugins import HeatMap
import matplotlib.pyplot as plt
import seaborn as sns
import os

# radio de 40km
RADIO_CIRCULO_METROS = 40000 

def generar_mapas_y_graficos(ruta_csv_solucion, nombre_escenario=None):
    # aviso por consola
    print(f"Creando visualisacion para: {os.path.basename(ruta_csv_solucion)}")
    
    if not ruta_csv_solucion or not os.path.exists(ruta_csv_solucion):
        print("Error: No encuentro el csv.")
        return

    # si no pasan nombre, lo saco del archivo
    if not nombre_escenario:
        nombre_base = os.path.splitext(os.path.basename(ruta_csv_solucion))[0]
        # quito lo de solucion_ para q quede mejor
        nombre_escenario = nombre_base.replace("solucion_", "")
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MAPS_DIR = os.path.join(BASE_DIR, '..', 'maps')
    if not os.path.exists(MAPS_DIR):
        os.makedirs(MAPS_DIR)

    # rutas de los archivos que vamos a crear
    MAPA_ARANA = os.path.join(MAPS_DIR, f"Mapa_{nombre_escenario}_Arana.html")
    MAPA_COBERTURA = os.path.join(MAPS_DIR, f"Mapa_{nombre_escenario}_Cobertura.html")
    GRAFICO_1 = os.path.join(MAPS_DIR, f"Grafico_{nombre_escenario}_Poblacion.png")
    GRAFICO_2 = os.path.join(MAPS_DIR, f"Grafico_{nombre_escenario}_Municipios.png")

    # intento leer el csv, a veces viene con ; y otras con ,
    try:
        df = pd.read_csv(ruta_csv_solucion, sep=',')
        if 'lat_muni' not in df.columns:
            df = pd.read_csv(ruta_csv_solucion, sep=';')
    except Exception as e:
        print(f"Fallo al cargar csv: {e}")
        return

    # compruebo que esten las columnas
    req_cols = ['lat_muni', 'lon_muni', 'lat_heli', 'lon_heli', 'helipuerto_nombre']
    if not all(c in df.columns for c in req_cols):
        print(f"Faltan columnas en el archivo")
        return

    bases_activas = df[['helipuerto_nombre', 'lat_heli', 'lon_heli']].drop_duplicates()

    # --- MAPA 1: LINEAS ---
    center_lat = df['lat_muni'].mean()
    center_lon = df['lon_muni'].mean()
    mapa_1 = folium.Map(location=[center_lat, center_lon], zoom_start=7, tiles='CartoDB positron')

    for _, row in df.iterrows():
        color = 'green'
        # calculo color segun distancia
        dist = row.get('distancia_km', 0)
        if dist > 45: color = 'red'
        elif dist > 30: color = 'orange'
        
        folium.PolyLine(
            locations=[[row['lat_muni'], row['lon_muni']], [row['lat_heli'], row['lon_heli']]],
            color=color, weight=0.5, opacity=0.3
        ).add_to(mapa_1)

    for _, row in bases_activas.iterrows():
        folium.Marker(
            location=[row['lat_heli'], row['lon_heli']],
            popup=row['helipuerto_nombre'],
            icon=folium.Icon(color='blue', icon='helicopter', prefix='fa')
        ).add_to(mapa_1)

    mapa_1.save(MAPA_ARANA)

    # --- MAPA 2: CALOR ---
    mapa_2 = folium.Map(location=[center_lat, center_lon], zoom_start=7, tiles='CartoDB positron')

    datos_calor = df[['lat_muni', 'lon_muni', 'poblacion']].values.tolist()
    HeatMap(datos_calor, radius=15, blur=20, max_zoom=1).add_to(mapa_2)

    for _, row in bases_activas.iterrows():
        # circulo verde
        folium.Circle(
            location=[row['lat_heli'], row['lon_heli']],
            radius=RADIO_CIRCULO_METROS,
            color='green', fill=True, fill_color='green', fill_opacity=0.2,
            popup='Cobertura 40km'
        ).add_to(mapa_2)
        
        folium.Marker(
            location=[row['lat_heli'], row['lon_heli']],
            popup=f"BASE: {row['helipuerto_nombre']}",
            icon=folium.Icon(color='darkblue', icon='helicopter', prefix='fa')
        ).add_to(mapa_2)

    mapa_2.save(MAPA_COBERTURA)

    # --- GRAFICOS ---
    try:
        plt.switch_backend('Agg') # para que no falle sin pantalla
        
        resumen = df.groupby('helipuerto_nombre').agg({
            'poblacion': 'sum',
            'municipio_id': 'count' 
        }).reset_index().sort_values('poblacion', ascending=False)
        
        col_count = 'municipio_id' if 'municipio_id' in resumen.columns else 'num_municipios'
        resumen.rename(columns={col_count: 'num_municipios'}, inplace=True)
        
        sns.set_theme(style="whitegrid")

        # grafico de gente cubierta
        plt.figure(figsize=(10, 6))
        sns.barplot(data=resumen, x='poblacion', y='helipuerto_nombre', palette='viridis')
        plt.title(f'Poblacion Cubierta - {nombre_escenario}')
        plt.tight_layout()
        plt.savefig(GRAFICO_1)
        plt.close()

        # grafico de cuantos municipios tocan
        resumen = resumen.sort_values('num_municipios', ascending=False)
        plt.figure(figsize=(10, 6))
        sns.barplot(data=resumen, x='num_municipios', y='helipuerto_nombre', palette='magma')
        plt.title(f'Municipios Asignados - {nombre_escenario}')
        plt.tight_layout()
        plt.savefig(GRAFICO_2)
        plt.close()
        
        print(f"   Mapas guardado en maps/ para {nombre_escenario}")

    except Exception as e:
        print(f"   Problema con los graficos: {e}")