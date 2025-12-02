import pandas as pd
import numpy as np
import math
import os
import pulp

# --- CONFIGURACIÓN DE RUTAS ---
# Asumimos que este script corre en la carpeta 'src' y los datos están en 'data' (un nivel arriba)
DATA_DIR = os.path.join("..", "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "solucion_asignaciones.csv")

# Verificar si existe la carpeta data, si no, usar ruta local (por seguridad)
if not os.path.exists(DATA_DIR):
    DATA_DIR = "data"
    OUTPUT_FILE = os.path.join("data", "solucion_asignaciones.csv")
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

print(f"Leyendo datos desde: {DATA_DIR}")
print(f"El resultado se guardará en: {OUTPUT_FILE}")

# --- FUNCIONES AUXILIARES ---
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1 = math.radians(lat1); phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1); dl = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dl/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def find_column(cols, names):
    for name in names:
        for c in cols:
            if c == name:
                return c
    return None

# --- 1. CARGA Y LIMPIEZA DE DATOS ---
mun_path = os.path.join(DATA_DIR, "datos_municipios.csv")
cand_path = os.path.join(DATA_DIR, "candidatos.csv")

municipios = pd.read_csv(mun_path)
candidatos = pd.read_csv(cand_path)

# Normalizar columnas
mun_cols = municipios.columns.str.lower()
cand_cols = candidatos.columns.str.lower()

# Mapeo de columnas municipios
municipios = municipios.rename(columns={
    find_column(mun_cols, ['id']): 'id',
    find_column(mun_cols, ['nombre','municipio']): 'nombre',
    find_column(mun_cols, ['lat','latitude', 'latitud']): 'lat',
    find_column(mun_cols, ['lon','long', 'longitud']): 'lon',
    find_column(mun_cols, ['pob','poblacion']): 'pob'
})

# Mapeo de columnas candidatos
candidatos = candidatos.rename(columns={
    find_column(cand_cols, ['id', 'id_candidato']): 'id',
    find_column(cand_cols, ['nombre','municipio']): 'nombre',
    find_column(cand_cols, ['lat', 'latitud']): 'lat',
    find_column(cand_cols, ['lon', 'longitud']): 'lon'
})

# --- 2. CÁLCULO DE DISTANCIAS ---
VEL = 220.0  # km/h velocidad media helicóptero
I = municipios['id'].tolist()
J = candidatos['id'].tolist()

# Diccionarios para acceso rápido a coordenadas
coords_mun = municipios.set_index('id')[['lat', 'lon']].to_dict('index')
coords_cand = candidatos.set_index('id')[['lat', 'lon']].to_dict('index')

t = {}   # Tiempos
d = {}   # Distancias (necesarias para el mapa)

print("Calculando matriz de distancias...")
for _, mu in municipios.iterrows():
    for _, ca in candidatos.iterrows():
        dkm = haversine(mu['lat'], mu['lon'], ca['lat'], ca['lon'])
        tiempo_min = (dkm / VEL) * 60
        
        # Guardamos ambas métricas
        d[(mu['id'], ca['id'])] = dkm
        t[(mu['id'], ca['id'])] = tiempo_min

# --- 3. MODELO MATEMÁTICO (P-MEDIANA) ---
P = 10  # Número de helipuertos a instalar
print(f"Ejecutando modelo P-Mediana para P={P}...")

prob = pulp.LpProblem("p_mediana_cyl", pulp.LpMinimize)

# Variables
x = pulp.LpVariable.dicts("x", J, lowBound=0, upBound=1, cat="Binary") # 1 si se abre candidato j
y = pulp.LpVariable.dicts("y", (I, J), lowBound=0, upBound=1, cat="Binary") # 1 si municipio i va a j

# Objetivo: Minimizar coste social (Población * Tiempo)
# Nota: Se usa .values[0] para asegurar obtener el escalar si hay índices duplicados, o map directo
pob_dict = municipios.set_index('id')['pob'].to_dict()

prob += pulp.lpSum([
    pob_dict[i] * t[(i,j)] * y[i][j]
    for i in I for j in J
])

# Restricciones
# 1. Cada municipio asignado a exactamente 1 centro
for i in I:
    prob += pulp.lpSum(y[i][j] for j in J) == 1

# 2. Solo asignar si el centro está abierto
for i in I:
    for j in J:
        prob += y[i][j] <= x[j]

# 3. Abrir exactamente P centros
prob += pulp.lpSum(x[j] for j in J) == P

# Resolver
solver = pulp.PULP_CBC_CMD(msg=False) # msg=False para menos ruido en consola
prob.solve(solver)

status = pulp.LpStatus[prob.status]
print(f"Estado del modelo: {status}")

if status != 'Optimal':
    print("No se encontró solución óptima.")
else:
    # --- 4. GENERACIÓN DE RESULTADOS ---
    selected_centers = [j for j in J if pulp.value(x[j]) > 0.5]
    print(f"Centros seleccionados: {len(selected_centers)}")
    
    asignaciones = []
    
    # Mapeo de nombres para rapidez
    nom_mun_dict = municipios.set_index('id')['nombre'].to_dict()
    nom_cand_dict = candidatos.set_index('id')['nombre'].to_dict()

    for i in I:
        for j in J:
            if pulp.value(y[i][j]) > 0.5:
                # Recopilamos TODOS los datos necesarios para primermapa.ipynb
                asignaciones.append({
                    "municipio_id": i,
                    "municipio": nom_mun_dict[i],
                    "lat_muni": coords_mun[i]['lat'],
                    "lon_muni": coords_mun[i]['lon'],
                    
                    "centro_id": j,
                    "helipuerto_nombre": nom_cand_dict[j], # El mapa espera 'helipuerto_nombre'
                    "lat_heli": coords_cand[j]['lat'],
                    "lon_heli": coords_cand[j]['lon'],
                    
                    "tiempo_min": t[(i,j)],
                    "distancia_km": d[(i,j)] # El mapa usa esto para colorear líneas
                })

    # Crear DataFrame final
    df_solucion = pd.DataFrame(asignaciones)
    
    # Guardar en la carpeta DATA
    df_solucion.to_csv(OUTPUT_FILE, index=False)
    
    print(f"¡Éxito! Archivo guardado correctamente en: {OUTPUT_FILE}")
    print("Vista previa de las asignaciones:")
    print(df_solucion[['municipio', 'helipuerto_nombre', 'distancia_km']].head())