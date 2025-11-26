import pandas as pd
import geopandas as gpd

from limpiar_municipios import limpiar_poblacion, limpiar_coord

def cargar_municipios_limpios():
    return pd.read_csv("../data/datos_municipios.csv")

def cargar_municipios_shp():
    return gpd.read_file("../data/municipios_cyl.shp")
