import pandas as pd
import numpy as np
import math
import os

# --- CONFIGURACIÓN ---
# Ajustamos para buscar en la carpeta 'data' que está un nivel arriba
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
ARCHIVO_MUNICIPIOS = os.path.join(BASE_DIR, "data", "municipios_cyl.csv")
ARCHIVO_CANDIDATOS = os.path.join(BASE_DIR, "data", "candidatos.csv")
VELOCIDAD_HELICOPTERO = 220.0  # km/h

def haversine(lat1, lon1, lat2, lon2):
    """Calcula distancia en km entre dos coordenadas (Fórmula Haversine)."""
    R = 6371.0
    try:
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = (math.sin(d_lat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(d_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c
    except Exception:
        return 0.0

def generar_matriz_tiempos(df_mun, df_cand):
    """Genera el diccionario {(id_mun, id_cand): minutos}."""
    print(f"[DATOS] Calculando matriz de tiempos ({len(df_mun)} x {len(df_cand)})...")
    t = {}
    muns = df_mun.to_dict('records')
    cands = df_cand.to_dict('records')
    
    for m in muns:
        for c in cands:
            dist_km = haversine(m['lat'], m['lon'], c['lat'], c['lon'])
            # Tiempo vuelo + 5 min despegue
            tiempo = (dist_km / VELOCIDAD_HELICOPTERO) * 60 + 5
            t[(m['id'], c['id'])] = tiempo
    return t

def cargar_datos():
    """Carga y limpia los CSVs."""
    print("--- Cargando datos... ---")
    
    if not os.path.exists(ARCHIVO_MUNICIPIOS):
        raise FileNotFoundError(f"¡Falta {ARCHIVO_MUNICIPIOS}!")
    
    # Cargar Municipios (con separador ;)
    df_m = pd.read_csv(ARCHIVO_MUNICIPIOS, sep=';', encoding='utf-8')
    # Limpieza de columnas
    df_m.columns = df_m.columns.str.strip().str.lower().str.replace('ó','o').str.replace('á','a')
    
    mapa_m = {
        'cod_ine': 'id', 'codigo_ine': 'id', 'ine': 'id', 
        'poblacion': 'poblacion', 'habitantes': 'poblacion',
        'latitud': 'lat', 'longitud': 'lon', 'municipio': 'municipio'
    }
    df_m.rename(columns=mapa_m, inplace=True)
    
    # Cargar Candidatos
    if not os.path.exists(ARCHIVO_CANDIDATOS):
        raise FileNotFoundError(f"¡Falta {ARCHIVO_CANDIDATOS}!")
        
    try:
        df_c = pd.read_csv(ARCHIVO_CANDIDATOS, sep=',') # Suele ser coma
        if len(df_c.columns) < 2: df_c = pd.read_csv(ARCHIVO_CANDIDATOS, sep=';')
    except:
        df_c = pd.read_csv(ARCHIVO_CANDIDATOS, sep=';')

    df_c.columns = df_c.columns.str.strip().str.lower()
    mapa_c = {'id_candidato': 'id', 'codigo': 'id', 'latitud': 'lat', 'longitud': 'lon', 'provincia': 'provincia', 'nombre': 'nombre'}
    df_c.rename(columns=mapa_c, inplace=True)
    
    # --- TRUCO DEL BIERZO (CRÍTICO) ---
    def asignar_region(row):
        texto = str(row).upper()
        if 'BIERZO' in texto or 'PONFERRADA' in texto: return 'El Bierzo'
        return row['provincia']
    
    df_c['region'] = df_c.apply(asignar_region, axis=1)
    
    print(f"✅ Datos listos: {len(df_m)} mun, {len(df_c)} cands. Regiones: {len(df_c['region'].unique())}")
    return df_m, df_c