import pulp

def modelo_pmediana(df_mun, df_cand, t, P=10):
    # 1. Crear el Problema
    prob = pulp.LpProblem("pmediana_con_regiones", pulp.LpMinimize)

    # Listas de IDs para iterar
    I = df_mun['id'].tolist()       # Municipios (Demanda)
    J = df_cand['id'].tolist()      # Candidatos (Oferta)
    
    # Diccionarios para datos rápidos
    pob = dict(zip(df_mun['id'], df_mun['pob']))
    # IMPORTANTE: Necesitamos saber la provincia de cada candidato para la restricción
    provincia_cand = dict(zip(df_cand['id'], df_cand['provincia']))
    lista_provincias = list(set(df_cand['provincia'].unique()))

    # ---------------------------------------------------------
    # 2. VARIABLES DE DECISIÓN
    # ---------------------------------------------------------
    # x[j] = 1 si se abre el helipuerto j
    x = pulp.LpVariable.dicts("Base", J, cat='Binary')
    
    # y[i][j] = 1 si el municipio i va a la base j
    y = pulp.LpVariable.dicts("Asigna", (I, J), cat='Binary')

    # ---------------------------------------------------------
    # 3. FUNCIÓN OBJETIVO (Minimizar tiempo medio)
    # ---------------------------------------------------------
    # Suma de (Población * Tiempo * Variable_Asignación)
    prob += pulp.lpSum([pob[i] * t[(i,j)] * y[i][j] for i in I for j in J])

    # ---------------------------------------------------------
    # 4. RESTRICCIONES
    # ---------------------------------------------------------
    
    # A) Todo municipio debe tener asignada UNA base
    for i in I:
        prob += pulp.lpSum([y[i][j] for j in J]) == 1

    # B) Coherencia: Si asignas a j, j debe estar abierta
    for i in I:
        for j in J:
            prob += y[i][j] <= x[j]

    # C) REGLA DE ORO: 1 helicóptero por provincia + Bierzo
    # Esta es la que te da el aprobado. Sustituye a la simple "suma = 10"
    for prov in lista_provincias:
        candidatos_en_prov = [j for j in J if provincia_cand[j] == prov]
        prob += pulp.lpSum([x[j] for j in candidatos_en_prov]) == 1

    # ---------------------------------------------------------
    # 5. RESOLVER
    # ---------------------------------------------------------
    print("Resolviendo...")
    solver = pulp.PULP_CBC_CMD(msg=False) # msg=True para ver detalles
    prob.solve(solver)

    # 6. Procesar resultados
    centros = []
    asignaciones = {}
    
    if pulp.LpStatus[prob.status] == 'Optimal':
        # Guardar centros elegidos
        centros = [j for j in J if pulp.value(x[j]) > 0.5]
        
        # Guardar asignaciones
        for i in I:
            for j in J:
                if pulp.value(y[i][j]) > 0.5:
                    asignaciones[i] = j
    else:
        print("No se encontró solución óptima")

    return centros, asignaciones