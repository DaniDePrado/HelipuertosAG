# src/p_mediana.py
import pandas as pd
import numpy as np
import math
import os
import pulp

# --- FUNCIONES AUXILIARES (Las dejamos fuera o dentro, da igual) ---
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1 = math.radians(lat1); phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1); dl = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dl/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def ejecutar_modelo():
    """
    Ejecuta el modelo P-Mediana y genera el CSV de asignaciones.
    Retorna la ruta del archivo generado.
    """
    print("--- INICIANDO MODELO P-MEDIANA ---")
    
    # CONFIGURACIÓN DE RUTAS
    # Usamos rutas absolutas basadas en la ubicación de este script para evitar errores
    BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # Carpeta src
    DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data") # Carpeta data
    OUTPUT_FILE = os.path.join(DATA_DIR, "solucion_asignaciones.csv")

    if not os.path.exists(DATA_DIR):
        print(f"Error: No se encuentra la carpeta data en {DATA_DIR}")
        return None

    # 1. CARGA DE DATOS
    try:
        municipios = pd.read_csv(os.path.join(DATA_DIR, "datos_municipios.csv"))
        candidatos = pd.read_csv(os.path.join(DATA_DIR, "candidatos.csv"))
    except FileNotFoundError as e:
        print(f"Error cargando CSVs: {e}")
        return None

    # (Aquí va todo el código de limpieza y normalización que ya tenías...)
    # ... [CÓDIGO DE LIMPIEZA RESUMIDO PARA BREVEDAD, USA EL QUE YA TIENES] ...
    # Asegúrate de usar las columnas correctas como hicimos en la versión anterior
    
    # Normalización rápida para asegurar que funcione
    def clean_cols(df):
        df.columns = df.columns.str.lower()
        rename_map = {}
        for c in df.columns:
            if c in ['id', 'id_candidato', 'cod_ine']: rename_map[c] = 'id'
            elif c in ['nombre', 'municipio']: rename_map[c] = 'nombre'
            elif c in ['lat', 'latitud', 'latitude']: rename_map[c] = 'lat'
            elif c in ['lon', 'longitud', 'longitude']: rename_map[c] = 'lon'
            elif c in ['pob', 'poblacion']: rename_map[c] = 'pob'
        return df.rename(columns=rename_map)

    municipios = clean_cols(municipios)
    candidatos = clean_cols(candidatos)

    # 2. CÁLCULO DISTANCIAS
    VEL = 220.0
    I = municipios['id'].tolist()
    J = candidatos['id'].tolist()
    
    t = {}
    d = {}
    
    # Optimizamos diccionarios para acceso rápido
    mun_dict = municipios.set_index('id').to_dict('index')
    cand_dict = candidatos.set_index('id').to_dict('index')

    for i in I:
        for j in J:
            dist = haversine(mun_dict[i]['lat'], mun_dict[i]['lon'], 
                             cand_dict[j]['lat'], cand_dict[j]['lon'])
            d[(i,j)] = dist
            t[(i,j)] = (dist / VEL) * 60

    # 3. MODELO PULP
    P = 10
    prob = pulp.LpProblem("p_mediana", pulp.LpMinimize)
    x = pulp.LpVariable.dicts("x", J, cat="Binary")
    y = pulp.LpVariable.dicts("y", (I, J), cat="Binary")

    # Objetivo
    prob += pulp.lpSum([mun_dict[i]['pob'] * t[(i,j)] * y[i][j] for i in I for j in J])

    # Restricciones
    for i in I: prob += pulp.lpSum(y[i][j] for j in J) == 1
    for i in I:
        for j in J: prob += y[i][j] <= x[j]
    prob += pulp.lpSum(x[j] for j in J) == P

    solver = pulp.PULP_CBC_CMD(msg=False)
    prob.solve(solver)

    # 4. EXPORTAR
    if pulp.LpStatus[prob.status] == 'Optimal':
        asignaciones = []
        for i in I:
            for j in J:
                if pulp.value(y[i][j]) > 0.5:
                    asignaciones.append({
                        "municipio_id": i,
                        "municipio": mun_dict[i]['nombre'],
                        "poblacion": mun_dict[i]['pob'], # Importante para los gráficos
                        "lat_muni": mun_dict[i]['lat'],
                        "lon_muni": mun_dict[i]['lon'],
                        "centro_id": j,
                        "helipuerto_nombre": cand_dict[j]['nombre'],
                        "lat_heli": cand_dict[j]['lat'],
                        "lon_heli": cand_dict[j]['lon'],
                        "tiempo_min": t[(i,j)],
                        "distancia_km": d[(i,j)]
                    })
        
        df_out = pd.DataFrame(asignaciones)
        df_out.to_csv(OUTPUT_FILE, index=False)
        print(f"Modelo completado. Solución guardada en: {OUTPUT_FILE}")
        return OUTPUT_FILE
    else:
        print("El modelo no encontró solución óptima.")
        return None

if __name__ == "__main__":
    ejecutar_modelo()