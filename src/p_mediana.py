# src/p_mediana.py
import pandas as pd
import numpy as np
import math
import os
import pulp

#Calculamos la distancia del radio maximo, entre dos puntos dados. Gracias a sus coordenadas de latitud y longitud
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
    
    # Usamos rutas absolutas basadas en la ubicación de este script para evitar errores
    BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # Carpeta src
    DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data") # Carpeta data
    OUTPUT_FILE = os.path.join(DATA_DIR, "solucion_asignaciones.csv")

    if not os.path.exists(DATA_DIR): #Comprobamos que la carpeta data exista
        print(f"Error: No se encuentra la carpeta data en {DATA_DIR}")
        return None

    # Cargamos los datos
    try:
        municipios = pd.read_csv(os.path.join(DATA_DIR, "datos_municipios.csv")) #Listado de municipios
        candidatos = pd.read_csv(os.path.join(DATA_DIR, "candidatos.csv")) #Listado de candidatos a donde poner los helipuertos
    except FileNotFoundError as e:
        print(f"Error cargando CSVs: {e}")
        return None
 
    # Nos aseguramos de su funcion
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

    # Calculamos las distancias
    VEL = 220.0
    I = municipios['id'].tolist()
    J = candidatos['id'].tolist()
    
    t = {}
    d = {}
    
    mun_dict = municipios.set_index('id').to_dict('index')
    cand_dict = candidatos.set_index('id').to_dict('index')

    # Bucle para calcular la matriz de distancias y tiempos entre todos los municipios  y todos los candidatos a base
    for i in I:
        for j in J:
            dist = haversine(mun_dict[i]['lat'], mun_dict[i]['lon'], 
                             cand_dict[j]['lat'], cand_dict[j]['lon'])
            d[(i,j)] = dist
            t[(i,j)] = (dist / VEL) * 60

    #El modelo PuLP
    P = 10 #Numero de bases
    prob = pulp.LpProblem("p_mediana", pulp.LpMinimize) 

    #Variables de decision
    x = pulp.LpVariable.dicts("x", J, cat="Binary")
    y = pulp.LpVariable.dicts("y", (I, J), cat="Binary")

    #Nuestra funcion objetivo
    prob += pulp.lpSum([mun_dict[i]['pob'] * t[(i,j)] * y[i][j] for i in I for j in J])

    # Restricciones, la cual es cada municipio debe asignarse a exactamente una base
    for i in I: prob += pulp.lpSum(y[i][j] for j in J) == 1
    for i in I:
        for j in J: prob += y[i][j] <= x[j]
    prob += pulp.lpSum(x[j] for j in J) == P

    solver = pulp.PULP_CBC_CMD(msg=False) #Resolucion
    prob.solve(solver)

    # Comprobamos que el estado del solver sea el optimo
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
        
        df_out = pd.DataFrame(asignaciones) #Creamos un DataFrama y guardamos en el archivo CSV de salida
        df_out.to_csv(OUTPUT_FILE, index=False)
        print(f"Modelo completado. Solución guardada en: {OUTPUT_FILE}")
        return OUTPUT_FILE
    else:
        print("El modelo no encontró solución óptima.")
        return None

if __name__ == "__main__":
    ejecutar_modelo()