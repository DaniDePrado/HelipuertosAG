import pulp

def modelo_pmediana(df_mun, df_cand, t, P=10):
    prob = pulp.LpProblem("pmediana", pulp.LpMinimize)

    # variables, restricciones, solver...
    # devuelve centros seleccionados y asignaciones

    return centros, asignaciones
