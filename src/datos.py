import pandas as pd
import geopandas as gpd
import math

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    ...
    return dkm

def cargar_municipios(path="municipios_cyl.csv"):
    df = pd.read_csv(path)
    return df

def cargar_candidatos(path="candidatos.csv"):
    df = pd.read_csv(path)
    return df

def preparar_datos(df_mun, df_cand):
    # normaliza nombres de columnas, convierte tipos, etc.
    return df_mun, df_cand

def matriz_tiempos(df_mun, df_cand, velocidad=220):
    t = {}
    for _, mu in df_mun.iterrows():
        for _, ca in df_cand.iterrows():
            d = haversine(mu.lat, mu.lon, ca.lat, ca.lon)
            t[(mu.id, ca.id)] = (d / velocidad) * 60
    return t

