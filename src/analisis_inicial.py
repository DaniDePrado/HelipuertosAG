import pandas as pd
import folium
from folium.plugins import HeatMap
import os

def generar_analisis_previo():
    print("--- GENERANDO MAPAS DE ANÁLISIS INICIAL ---")

    # 1. Configurar Rutas Relativas (Para que funcione en cualquier PC)
    # Detectamos dónde está este archivo script (carpeta src)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    # Subimos un nivel para encontrar 'data' y 'maps'
    DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
    MAPS_DIR = os.path.join(BASE_DIR, '..', 'maps')

    # Asegurarnos de que la carpeta maps existe
    if not os.path.exists(MAPS_DIR):
        os.makedirs(MAPS_DIR)

    ruta_municipios = os.path.join(DATA_DIR, 'datos_municipios.csv')
    ruta_candidatos = os.path.join(DATA_DIR, 'candidatos.csv')

    # Verificar archivos
    if not os.path.exists(ruta_municipios) or not os.path.exists(ruta_candidatos):
        print(f"❌ ERROR: No encuentro los archivos en {DATA_DIR}")
        return

    # Cargar datos
    df_municipios = pd.read_csv(ruta_municipios)
    df_candidatos = pd.read_csv(ruta_candidatos)

    # --- MAPA 1: SITUACIÓN INICIAL (Candidatos y Municipios Grandes) ---
    print("Generando mapa de situación inicial...")
    mapa = folium.Map(location=[41.6, -4.7], zoom_start=7)

    # Pintar Candidatos (Rojo)
    for _, row in df_candidatos.iterrows():
        folium.Marker(
            location=[row['latitud'], row['longitud']],
            popup=row['nombre'],
            icon=folium.Icon(color='red', icon='helicopter', prefix='fa')
        ).add_to(mapa)

    # Pintar Municipios Grandes (Azul) - Filtro > 1000 hab
    municipios_grandes = df_municipios[df_municipios['poblacion'] > 1000]
    for _, row in municipios_grandes.iterrows():
        folium.CircleMarker(
            location=[row['latitud'], row['longitud']],
            radius=3, color='blue', fill=True, fill_color='blue',
            popup=f"{row['municipio']} ({row['poblacion']} hab)"
        ).add_to(mapa)

    salida_inicial = os.path.join(MAPS_DIR, 'mapa_inicial_cyl.html')
    mapa.save(salida_inicial)
    print(f"✅ Mapa inicial guardado en: {salida_inicial}")

    # --- MAPA 2: MAPA DE CALOR Y COBERTURA TEÓRICA ---
    print("Generando mapa de calor y cobertura teórica...")
    mapa_calor = folium.Map(location=[41.6, -4.7], zoom_start=7, tiles='CartoDB positron')

    # Capa de Calor (Densidad de Población)
    datos_calor = df_municipios[['latitud', 'longitud', 'poblacion']].values.tolist()
    HeatMap(datos_calor, radius=15, blur=20, max_zoom=1).add_to(mapa_calor)

    # Círculos de Cobertura Teórica (40km) alrededor de los candidatos
    for _, row in df_candidatos.iterrows():
        folium.Circle(
            location=[row['latitud'], row['longitud']],
            radius=40000,  # 40 km
            color='green', fill=True, fill_opacity=0.2,
            popup='Cobertura Teórica 40km'
        ).add_to(mapa_calor)
        
        # Marcador pequeño
        folium.CircleMarker(
            location=[row['latitud'], row['longitud']],
            radius=2, color='red', fill=True
        ).add_to(mapa_calor)

    salida_calor = os.path.join(MAPS_DIR, 'mapa_analisis_cobertura.html')
    mapa_calor.save(salida_calor)
    print(f"✅ Mapa de calor guardado en: {salida_calor}")

if __name__ == "__main__":
    generar_analisis_previo()