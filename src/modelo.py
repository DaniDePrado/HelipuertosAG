import pulp
import pandas as pd

def resolver_modelo(df_mun, df_cand, matriz_tiempos, peso_tiempo=1.0):
    """
    Resuelve el P-Mediana con la restricción OBLIGATORIA de 1 base por región.
    """
    print(f"\n>>> Lanzando Solver PuLP (Peso Tiempo: {peso_tiempo})")
    
    # Preparar datos
    I = df_mun['id'].tolist()
    J = df_cand['id'].tolist()
    pob = dict(zip(df_mun['id'], df_mun['poblacion']))
    region_cand = dict(zip(df_cand['id'], df_cand['region']))
    lista_regiones = list(set(df_cand['region'].unique())) # Las 10 regiones (9 prov + Bierzo)
    
    # 1. Problema
    prob = pulp.LpProblem("HeliCyL_Optimizacion", pulp.LpMinimize)
    
    # 2. Variables
    y = pulp.LpVariable.dicts("AbrirBase", J, cat='Binary')
    x = pulp.LpVariable.dicts("Asignar", (I, J), cat='Binary')
    
    # 3. Objetivo: Minimizar tiempo ponderado por gente afectada
    prob += pulp.lpSum([pob[i] * matriz_tiempos[(i,j)] * x[i][j] for i in I for j in J])
    
    # 4. Restricciones
    
    # R1: Todo pueblo debe tener un helicóptero
    for i in I:
        prob += pulp.lpSum([x[i][j] for j in J]) == 1
        
    # R2: Si asignas a J, J debe estar abierto
    for i in I:
        for j in J:
            prob += x[i][j] <= y[j]
            
    # R3: LA REGLA DE ORO (1 por provincia + Bierzo)
    for reg in lista_regiones:
        candidatos_en_region = [j for j in J if region_cand[j] == reg]
        prob += pulp.lpSum([y[j] for j in candidatos_en_region]) == 1

    # 5. Resolver
    # TimeLimit de 120s por si vuestro PC es lento con muchos datos
    solver = pulp.PULP_CBC_CMD(msg=True, timeLimit=120)
    prob.solve(solver)
    
    estado = pulp.LpStatus[prob.status]
    print(f"Estado Final del Solver: {estado}")
    
    if estado != 'Optimal':
        print("⚠️ Aviso: No se encontró solución óptima (quizás faltan candidatos en alguna provincia).")
        return [], pd.DataFrame()

    # 6. Guardar resultados
    bases_elegidas = [j for j in J if pulp.value(y[j]) > 0.5]
    
    asignaciones = []
    for i in I:
        for j in J:
            if pulp.value(x[i][j]) > 0.5:
                asignaciones.append({
                    'municipio_id': i,
                    'base_asignada': j,
                    'tiempo_min': matriz_tiempos[(i,j)]
                })
                
    return bases_elegidas, pd.DataFrame(asignaciones)