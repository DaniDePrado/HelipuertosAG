# src/analisis_inicial.py
import pandas as pd
import folium
from folium.plugins import HeatMap
import numpy as np  # Necesario para el cálculo logarítmico
import os

def cargar_csv_robusto(ruta):
    """Carga el CSV intentando adivinar el separador (; o ,)"""
    if not os.path.exists(ruta):
        return pd.DataFrame()
    
    try:
        # Intento 1: Separador punto y coma
        df = pd.read_csv(ruta, sep=';', encoding='utf-8')
        if len(df.columns) > 1: return df
        
        # Intento 2: Separador coma
        df = pd.read_csv(ruta, sep=',', encoding='utf-8')
        return df
    except:
        return pd.DataFrame()

def generar_analisis_previo():
    print("   -> Generando mapas PREVIOS (Análisis Inicial)...")

    # 1. Configurar Rutas
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
    MAPS_DIR = os.path.join(BASE_DIR, '..', 'maps')

    if not os.path.exists(MAPS_DIR):
        os.makedirs(MAPS_DIR)

    # 2. Cargar Archivos
    ruta_muni = os.path.join(DATA_DIR, 'municipios_cyl.csv')
    if not os.path.exists(ruta_muni): 
        ruta_muni = os.path.join(DATA_DIR, 'datos_municipios.csv')

    ruta_cand = os.path.join(DATA_DIR, 'candidatos.csv')

    df_muni = cargar_csv_robusto(ruta_muni)
    df_cand = cargar_csv_robusto(ruta_cand)

    if df_muni.empty:
        print("  Error: No se pudo cargar el archivo de municipios.")
        return

    # 3. Normalizar columnas
    df_muni.columns = df_muni.columns.str.strip().str.lower()
    if not df_cand.empty:
        df_cand.columns = df_cand.columns.str.strip().str.lower()

    # --- DETECCIÓN DE COLUMNAS ---
    m_lat = 'latitud' if 'latitud' in df_muni.columns else 'lat'
    m_lon = 'longitud' if 'longitud' in df_muni.columns else 'lon'
    col_pob = 'poblacion' if 'poblacion' in df_muni.columns else 'habitantes'

    c_lat = 'latitud' if 'latitud' in df_cand.columns else 'lat'
    c_lon = 'longitud' if 'longitud' in df_cand.columns else 'lon'

    if m_lat not in df_muni.columns:
        print("Error: Falta latitud en municipios.")
        return
    mapa_1 = folium.Map(location=[41.6, -4.7], zoom_start=7, tiles='CartoDB positron')

    if not df_cand.empty:
        for _, row in df_cand.iterrows():
            folium.Marker(
                location=[row[c_lat], row[c_lon]],
                popup=f"Candidato: {row.get('nombre', 'Base')}",
                icon=folium.Icon(color='red', icon='helicopter', prefix='fa')
            ).add_to(mapa_1)

    mapa_1.save(os.path.join(MAPS_DIR, 'mapa_inicial_cyl.html'))

    print(" Mapa generado correctamente.")

if __name__ == "__main__":
    generar_analisis_previo()