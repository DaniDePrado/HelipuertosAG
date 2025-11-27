#!/usr/bin/env python3
# resolver_pmediana_cyl.py
# Requisitos: pip install pandas numpy pulp folium matplotlib
# Ubica los CSV en /mnt/data o en la misma carpeta y edita las rutas si hace falta.

import os, math
import pandas as pd
import numpy as np

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1 = math.radians(lat1); phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1); dl = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dl/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# --- Ajusta estas rutas si necesitas ---
mun_path = "/mnt/data/municipios_cyl.csv"
cand_path = "/mnt/data/candidatos.csv"
out_dir = "/mnt/data"
# -------------------------------------

if not os.path.exists(mun_path) or not os.path.exists(cand_path):
    raise FileNotFoundError("Asegúrate de que municipios_cyl.csv y candidatos.csv existan en /mnt/data")

municipios = pd.read_csv(mun_path)
candidatos = pd.read_csv(cand_path)

# Detectar columnas comunes (heurística)
mun_cols = municipios.columns.str.lower()
cand_cols = candidatos.columns.str.lower()

def find_column(cols, targets):
    for t in targets:
        for c in cols:
            if t == c:
                return c
    return None

# Heurística: id, nombre, lat, lon, poblacion
mun_id = find_column(mun_cols, ['id','codigo','cod','mun_id']) or municipios.columns[0]
mun_name = find_column(mun_cols, ['nombre','municipio','name']) or municipios.columns[1] if municipios.shape[1]>1 else municipios.columns[0]
mun_lat = find_column(mun_cols, ['lat','latitude','y']) 
mun_lon = find_column(mun_cols, ['lon','long','longitude','x'])
mun_pop = find_column(mun_cols, ['pob','poblacion','population','pop'])

# fallback si no detecta lat/lon/pob
numeric_mun = municipios.select_dtypes(include=[float,int]).columns.tolist()
if mun_lat is None or mun_lon is None:
    if len(numeric_mun) >= 2:
        mun_lat, mun_lon = numeric_mun[0], numeric_mun[1]
if mun_pop is None:
    for c in reversed(numeric_mun):
        if c not in (mun_lat, mun_lon):
            mun_pop = c; break

cand_id = find_column(cand_cols, ['id','codigo','cod']) or candidatos.columns[0]
cand_name = find_column(cand_cols, ['nombre','name']) or candidatos.columns[1] if candidatos.shape[1]>1 else candidatos.columns[0]
cand_lat = find_column(cand_cols, ['lat','latitude','y'])
cand_lon = find_column(cand_cols, ['lon','long','longitude','x'])

numeric_cand = candidatos.select_dtypes(include=[float,int]).columns.tolist()
if cand_lat is None or cand_lon is None:
    if len(numeric_cand) >= 2:
        cand_lat, cand_lon = numeric_cand[0], numeric_cand[1]

# Normalizar nombres a columnas esperadas
municipios = municipios.rename(columns={
    mun_id: 'id', mun_name: 'nombre', mun_lat: 'lat', mun_lon: 'lon', mun_pop: 'pob'
})
candidatos = candidatos.rename(columns={
    cand_id: 'id', cand_name: 'nombre', cand_lat: 'lat', cand_lon: 'lon'
})

# Asegurar que existan columnas requeridas
for c in ['id','nombre','lat','lon','pob']:
    if c not in municipios.columns:
        raise ValueError(f"Columna {c} no encontrada en municipios (detectada: {municipios.columns.tolist()})")
for c in ['id','nombre','lat','lon']:
    if c not in candidatos.columns:
        raise ValueError(f"Columna {c} no encontrada en candidatos (detectada: {candidatos.columns.tolist()})")

# Tipos apropiados
municipios['id'] = municipios['id'].astype(int)
municipios['pob'] = municipios['pob'].astype(float)
# candidatos['id'] can be string or int; keep as is

# Parámetros del modelo
P = 10      # número de helipuertos a instalar
VEL = 220.0 # km/h

I = municipios['id'].tolist()
J = candidatos['id'].tolist()

# Calcular t_ij (minutos)
t = {}
for _, mu in municipios.iterrows():
    for _, ca in candidatos.iterrows():
        d_km = haversine(mu['lat'], mu['lon'], ca['lat'], ca['lon'])
        t[(int(mu['id']), ca['id'])] = (d_km / VEL) * 60.0

# Intentar resolver con PuLP
use_pulp = True
try:
    import pulp
except Exception as e:
    print("PuLP no disponible:", e)
    use_pulp = False

results = {}
if use_pulp:
    prob = pulp.LpProblem('p_mediana_cyl', pulp.LpMinimize)
    x = pulp.LpVariable.dicts('x', J, lowBound=0, upBound=1, cat='Binary')
    y = pulp.LpVariable.dicts('y', [(i,j) for i in I for j in J], lowBound=0, upBound=1, cat='Binary')
    # Objetivo
    prob += pulp.lpSum([municipios.loc[municipios['id']==i,'pob'].values[0] * t[(i,j)] * y[(i,j)] for i in I for j in J])
    # Restricciones
    for i in I:
        prob += pulp.lpSum([y[(i,j)] for j in J]) == 1
    for i in I:
        for j in J:
            prob += y[(i,j)] <= x[j]
    prob += pulp.lpSum([x[j] for j in J]) == P
    # Resolver (ajusta timeLimit si quieres)
    solver = pulp.PULP_CBC_CMD(msg=True, timeLimit=300)
    prob.solve(solver)
    status = pulp.LpStatus[prob.status]
    print("Solver status:", status)
    if status.lower() in ('optimal','optimal solution found'):
        seleccionados = [j for j in J if pulp.value(x[j]) > 0.5]
        asignaciones = {}
        for i in I:
            for j in J:
                if pulp.value(y[(i,j)]) > 0.5:
                    asignaciones[i] = j
        results['method'] = 'PuLP_MILP'
        results['selected'] = seleccionados
        results['assignments'] = asignaciones
    else:
        print("Solver no encontró solución óptima. Cambiando a heurística.")
        use_pulp = False

# Fallback heurístico greedy si no hay PuLP o solver falló
if not use_pulp:
    pop = municipios.set_index('id')['pob'].to_dict()
    selected = []
    remaining = set(J)
    def total_cost(selected_centers):
        total = 0.0
        for _, mu in municipios.iterrows():
            i = int(mu['id'])
            best = min([t[(i,j)] for j in selected_centers]) if selected_centers else float('inf')
            total += mu['pob'] * best
        return total
    for k in range(P):
        best_c = None
        best_cost = float('inf')
        for cand in remaining:
            trial = selected + [cand]
            cost = total_cost(trial)
            if cost < best_cost:
                best_cost = cost; best_c = cand
        selected.append(best_c)
        remaining.remove(best_c)
        print(f"Seleccionado {k+1}/{P}: {best_c} (coste {best_cost:.2f})")
    assignments = {}
    for _, mu in municipios.iterrows():
        i = int(mu['id'])
        best = min(selected, key=lambda j: t[(i,j)])
        assignments[i] = best
    results['method'] = 'Greedy'
    results['selected'] = selected
    results['assignments'] = assignments

# Construir DataFrames de salida y guardarlos
sel_df = pd.DataFrame(results['selected'], columns=['center_id'])
sel_df = sel_df.merge(candidatos, left_on='center_id', right_on='id', how='left').drop(columns=['id']).rename(columns={'nombre':'center_name'})

assign_rows = []
for _, mu in municipios.iterrows():
    i = int(mu['id'])
    center = results['assignments'][i]
    assign_rows.append({
        'id': i,
        'municipio': mu['nombre'],
        'lat': mu['lat'],
        'lon': mu['lon'],
        'pob': mu['pob'],
        'assigned_center_id': center,
        'assigned_center_name': candidatos.loc[candidatos['id']==center,'nombre'].values[0],
        'time_min': t[(i,center)]
    })
assign_df = pd.DataFrame(assign_rows)
metrics = assign_df.groupby('assigned_center_name').agg(
    total_pob=('pob','sum'),
    mean_time=('time_min','mean'),
    n_municipios=('id','count')
).reset_index().sort_values('total_pob', ascending=False)

assign_file = os.path.join(out_dir, "assignments_cyl.csv")
sel_file = os.path.join(out_dir, "selected_centers_cyl.csv")
metrics_file = os.path.join(out_dir, "metrics_centers_cyl.csv")
assign_df.to_csv(assign_file, index=False)
sel_df.to_csv(sel_file, index=False)
metrics.to_csv(metrics_file, index=False)

print("Generados:\n -", assign_file, "\n -", sel_file, "\n -", metrics_file)

# Opcional: mapa HTML y gráfico PNG (intenta crearlos si folium/matplotlib están instalados)
try:
    import folium
    center_lat = municipios['lat'].mean(); center_lon = municipios['lon'].mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=7)
    for _, row in candidatos.iterrows():
        if row['id'] in results['selected']:
            folium.Marker([row['lat'], row['lon']], popup=str(row['nombre']), icon=folium.Icon(color='red')).add_to(m)
        else:
            folium.CircleMarker([row['lat'], row['lon']], radius=3).add_to(m)
    for _, r in assign_df.iterrows():
        cent_row = candidatos[candidatos['nombre']==r['assigned_center_name']].iloc[0]
        folium.PolyLine([[r['lat'], r['lon']], [cent_row['lat'], cent_row['lon']]], weight=1).add_to(m)
    map_file = os.path.join(out_dir, "mapa_asignaciones_cyl.html")
    m.save(map_file)
    print("Mapa guardado en:", map_file)
except Exception as e:
    print("No se generó mapa (folium ausente o error):", e)

try:
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(10,4))
    ax.bar(metrics['assigned_center_name'], metrics['total_pob'])
    ax.set_xticklabels(metrics['assigned_center_name'], rotation=45, ha='right')
    plt.tight_layout()
    plot_file = os.path.join(out_dir, "poblacion_por_centro_cyl.png")
    fig.savefig(plot_file)
    print("Gráfico guardado en:", plot_file)
except Exception as e:
    print("No se generó gráfico (matplotlib ausente o error):", e)

print("Resumen: método ->", results['method'])
print("Centros seleccionados:", results['selected'])
