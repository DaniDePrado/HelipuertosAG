from datos import cargar_municipios, cargar_candidatos, preparar_datos, matriz_tiempos
from heuristicas import kmeans_poblacion   # opcional
from modelo import modelo_pmediana
from mapas import mapa_municipios, mapa_centros

def main():
    df_mun = cargar_municipios()
    df_cand = cargar_candidatos()

    df_mun, df_cand = preparar_datos(df_mun, df_cand)
    t = matriz_tiempos(df_mun, df_cand)

    # ejecutar modelo exacto
    centros, asign = modelo_pmediana(df_mun, df_cand, t, P=10)

    # generar mapas
    mapa_municipios(df_mun)
    mapa_centros(centros)

    print("Helipuertos óptimos:", centros)

if __name__ == "__main__":
    main()

