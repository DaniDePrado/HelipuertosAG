import pandas as pd
import numpy as np
import math
import os

# --- CONFIGURACIÓN DE ARCHIVOS ---
# Nombres exactos de los archivos que has subido
ARCHIVO_MUNICIPIOS = "municipios_cyl.csv"
ARCHIVO_CANDIDATOS = "candidatos.csv"
VELOCIDAD_HELICOPTERO = 220.0  # km/h

def haversine(lat1, lon1, lat2, lon2):
    """Calcula distancia en km entre dos coordenadas."""
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
        return 0.0 # En caso de error de datos (NaN), devuelve 0

def generar_matriz_tiempos(df_mun, df_cand):
    """Genera el diccionario {(id_mun, id_cand): minutos}."""
    print(f"Calculando matriz de tiempos para {len(df_mun)} municipios x {len(df_cand)} candidatos...")
    t = {}
    # Convertimos a diccionarios para velocidad
    muns = df_mun.to_dict('records')
    cands = df_cand.to_dict('records')
    
    for m in muns:
        for c in cands:
            dist_km = haversine(m['lat'], m['lon'], c['lat'], c['lon'])
            # Tiempo = (Distancia / Velocidad) * 60 min + 5 min de despegue
            tiempo = (dist_km / VELOCIDAD_HELICOPTERO) * 60 + 5
            t[(m['id'], c['id'])] = tiempo
    return t

def cargar_datos():
    """Carga y limpia tus archivos CSV específicos."""
    print("--- Cargando datos... ---")
    
    # 1. Cargar Municipios
    if os.path.exists(ARCHIVO_MUNICIPIOS):
        # El archivo 'municipios_cyl.csv' usa ';' como separador, según vi antes
        df_m = pd.read_csv(ARCHIVO_MUNICIPIOS, sep=';', encoding='utf-8')
        
        # Normalizar nombres de columnas (quita acentos y espacios)
        df_m.columns = df_m.columns.str.strip().str.lower().str.replace('ó','o').str.replace('á','a')
        
        # Renombrar a lo que necesita el modelo: id, poblacion, lat, lon
        # Ajustamos según los nombres probables en tu CSV:
        mapa_m = {
            'cod_ine': 'id', 'codigo_ine': 'id', 'ine': 'id', 
            'poblacion': 'poblacion', 'habitantes': 'poblacion',
            'latitud': 'lat', 'longitud': 'lon'
        }
        df_m.rename(columns=mapa_m, inplace=True)
        
        # Asegurar que tenemos lo necesario
        if 'id' not in df_m.columns or 'lat' not in df_m.columns:
             # Fallback si los nombres son muy distintos
             print(f"⚠️ Aviso: Columnas encontradas: {df_m.columns}. Intentando adivinar...")
             df_m.rename(columns={df_m.columns[0]: 'id', df_m.columns[1]: 'poblacion'}, inplace=True)

        print(f"Municipios cargados: {len(df_m)}")
    else:
        raise FileNotFoundError(f"¡Falta el archivo {ARCHIVO_MUNICIPIOS}!")

    # 2. Cargar Candidatos
    if os.path.exists(ARCHIVO_CANDIDATOS):
        # 'candidatos.csv' suele usar ',' pero por si acaso probamos ';'
        try:
            df_c = pd.read_csv(ARCHIVO_CANDIDATOS, sep=',')
            if len(df_c.columns) < 2: # Si falló el separador
                df_c = pd.read_csv(ARCHIVO_CANDIDATOS, sep=';')
        except:
            df_c = pd.read_csv(ARCHIVO_CANDIDATOS, sep=';')

        df_c.columns = df_c.columns.str.strip().str.lower()
        
        mapa_c = {
            'id_candidato': 'id', 'codigo': 'id',
            'latitud': 'lat', 'longitud': 'lon',
            'provincia': 'provincia'
        }
        df_c.rename(columns=mapa_c, inplace=True)
        
        # --- TRUCO PARA EL BIERZO ---
        # Crea la región 'El Bierzo' automáticamente para cumplir el requisito
        def asignar_region(row):
            texto = str(row).upper()
            if 'BIERZO' in texto or 'PONFERRADA' in texto:
                return 'El Bierzo'
            return row['provincia']
        
        df_c['region'] = df_c.apply(asignar_region, axis=1)
        
        print(f"Candidatos cargados: {len(df_c)}")
        print("Regiones detectadas para la restricción:", df_c['region'].unique())
    else:
        raise FileNotFoundError(f"¡Falta el archivo {ARCHIVO_CANDIDATOS}!")

    return df_m, df_c

if __name__ == "__main__":
    m, c = cargar_datos()
    print(m.head())
    print(c.head())
