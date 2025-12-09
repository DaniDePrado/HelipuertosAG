import pulp
import pandas as pd

def resolver_modelo(df_mun, df_cand, matriz_tiempos, peso_tiempo=1.0, peso_cobertura=0.0, radio_ideal_km=30):
    """
    Solver P-Mediana Multiobjetivo.
    Versión optimizada: Acepta soluciones 'Feasible' (válidas) si se agota el tiempo.
    """
    print(f"\n[SOLVER] Optimizando... (W_Tiempo: {peso_tiempo}, W_Cobertura: {peso_cobertura})")
    
    # 1. Datos
    I = df_mun['id'].tolist()
    J = df_cand['id'].tolist()
    pob = dict(zip(df_mun['id'], df_mun['poblacion']))
    
    if 'region' not in df_cand.columns: df_cand['region'] = df_cand['provincia']
    region_cand = dict(zip(df_cand['id'], df_cand['region']))
    lista_regiones = list(set(df_cand['region'].unique()))

    # 2. Problema
    prob = pulp.LpProblem("HeliCyL_MultiObj", pulp.LpMinimize)
    
    # Variables
    y = pulp.LpVariable.dicts("Base", J, cat='Binary')
    x = pulp.LpVariable.dicts("Asigna", (I, J), cat='Binary')
    z = pulp.LpVariable.dicts("NoCubierto", I, cat='Binary')

    # 3. Función Objetivo
    coste_tiempo = pulp.lpSum([pob[i] * matriz_tiempos[(i,j)] * x[i][j] for i in I for j in J])
    penalizacion_cobertura = pulp.lpSum([pob[i] * z[i] for i in I]) * 50 
    prob += peso_tiempo * coste_tiempo + peso_cobertura * penalizacion_cobertura

    # 4. Restricciones
    # R1: Cobertura Total
    for i in I:
        prob += pulp.lpSum([x[i][j] for j in J]) == 1
        
    # R2: Coherencia
    for i in I:
        for j in J:
            prob += x[i][j] <= y[j]
            
    # R3: Regla de Oro (1 por región)
    for reg in lista_regiones:
        cands_region = [j for j in J if region_cand[j] == reg]
        if not cands_region:
            print(f"⚠️ ERROR: No hay candidatos en {reg}!")
        prob += pulp.lpSum([y[j] for j in cands_region]) == 1

    # R4: Cobertura (radio 30km aprox 13 min)
    limite_tiempo = (radio_ideal_km / 220.0) * 60 + 5 
    if peso_cobertura > 0:
        for i in I:
            bases_cercanas = [j for j in J if matriz_tiempos[(i,j)] <= limite_tiempo]
            prob += z[i] >= 1 - pulp.lpSum([x[i][j] for j in bases_cercanas])

    # 5. Resolución (AUMENTAMOS TIEMPO A 180s y ACEPTAMOS SOLUCIONES FACTIBLES)
    solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=180) # Más tiempo para pensar
    prob.solve(solver)
    
    status = pulp.LpStatus[prob.status]
    print(f"Estado del solver: {status}")
    
    # CAMBIO CLAVE: Aceptamos 'Optimal' O 'Feasible' (Factible pero cortado por tiempo)
    # Algunos solvers usan otros códigos, chequeamos que haya solución.
    if status == 'Infeasible' or status == 'Unbounded' or status == 'Not Solved':
         print("❌ ERROR: El solver falló.")
         return [], pd.DataFrame()

    # 6. Resultados
    bases = [j for j in J if pulp.value(y[j]) > 0.5]
    
    # Doble chequeo por seguridad
    if len(bases) != 10:
        print(f"⚠️ Aviso: Se seleccionaron {len(bases)} bases (se esperaban 10). Revisa resultados.")

    res = []
    for i in I:
        for j in J:
            if pulp.value(x[i][j]) > 0.5:
                res.append({
                    'municipio_id': i, 'base_asignada_id': j,
                    'tiempo_minutos': matriz_tiempos[(i,j)]
                })
    return bases, pd.DataFrame(res)