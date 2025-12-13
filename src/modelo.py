import pulp
import pandas as pd

def resolver_modelo(df_mun, df_cand, matriz_tiempos, peso_tiempo=1.0, peso_cobertura=0.0, radio_ideal_km=30):
    """
    Solver P-Mediana Multiobjetivo.
    Versión optimizada: Acepta soluciones 'Feasible' (válidas) si se agota el tiempo.
    """
    #Aqui lo que conseguimos es imprimir los pesos utlizados en el escenario en el que estamos.
    print(f"\n[SOLVER] Optimizando... (W_Tiempo: {peso_tiempo}, W_Cobertura: {peso_cobertura})")
    
    I = df_mun['id'].tolist()  #Recogemos la lista de IDs de los municipios
    J = df_cand['id'].tolist() #Recogemos la lista de IDs de los candidatos a base
    pob = dict(zip(df_mun['id'], df_mun['poblacion'])) #Esto nos sirve para saber la poblacion que hay por municipio
    
    if 'region' not in df_cand.columns: df_cand['region'] = df_cand['provincia']
    region_cand = dict(zip(df_cand['id'], df_cand['region']))
    lista_regiones = list(set(df_cand['region'].unique()))

    #Aqui simplemente damos nombre al proble de optimazación
    prob = pulp.LpProblem("HeliCyL_MultiObj", pulp.LpMinimize)
    
    # Las variables a usar
    y = pulp.LpVariable.dicts("Base", J, cat='Binary')
    x = pulp.LpVariable.dicts("Asigna", (I, J), cat='Binary')
    z = pulp.LpVariable.dicts("NoCubierto", I, cat='Binary')

    #Intentamos minimizar el tiempo de respuesta ponderado por poblacion
    coste_tiempo = pulp.lpSum([pob[i] * matriz_tiempos[(i,j)] * x[i][j] for i in I for j in J])
    penalizacion_cobertura = pulp.lpSum([pob[i] * z[i] for i in I]) * 50 #Esta parte la usamos para intentar minimizar lo maximo posible la poblacion no cubierta dentro del radio
    prob += peso_tiempo * coste_tiempo + peso_cobertura * penalizacion_cobertura

   #Declaramos las restricciones
    for i in I:
        prob += pulp.lpSum([x[i][j] for j in J]) == 1
        
    # R2: Coherencia, es decir un municipio i solo puede asignarse a una base j si la base j está activa
    for i in I:
        for j in J:
            prob += x[i][j] <= y[j]
            
    # Forzamos a que solo haya un helipuerto por region
    for reg in lista_regiones:
        cands_region = [j for j in J if region_cand[j] == reg]
        if not cands_region:
            print(f" ERROR: No hay candidatos en {reg}!")
        prob += pulp.lpSum([y[j] for j in cands_region]) == 1

    # R4: Cobertura  en un radio de  30km cuya duracion aproximadamente sería de 13 min
    limite_tiempo = (radio_ideal_km / 220.0) * 60 + 5 
    if peso_cobertura > 0:
        for i in I:
            bases_cercanas = [j for j in J if matriz_tiempos[(i,j)] <= limite_tiempo]
            prob += z[i] >= 1 - pulp.lpSum([x[i][j] for j in bases_cercanas])

    # 5.Resolvemos el problema, inicializando el solver
    solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=180) # Más tiempo para pensar
    prob.solve(solver)
    
    status = pulp.LpStatus[prob.status] #Obtenemos el estado final de la resolucion
    print(f"Estado del solver: {status}")
    
    # Nos aseguramos de que haya solución.
    if status == 'Infeasible' or status == 'Unbounded' or status == 'Not Solved':
         print(" ERROR: El solver falló.")
         return [], pd.DataFrame()

    # Mostramos los resultados y guarda los IDs de las bases que fueron seleccionadas
    bases = [j for j in J if pulp.value(y[j]) > 0.5]
    
    if len(bases) != 10:
        print(f" Aviso: Se seleccionaron {len(bases)} bases (se esperaban 10). Revisa resultados.")

    res = []
    for i in I:
        for j in J:
            if pulp.value(x[i][j]) > 0.5:
                res.append({
                    'municipio_id': i, 'base_asignada_id': j,
                    'tiempo_minutos': matriz_tiempos[(i,j)]
                })
    return bases, pd.DataFrame(res)