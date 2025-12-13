import pandas as pd
import os
import sys


try:
    import datos
    import modelo
    import generar_candidatos_masivos 
except ImportError as e:
    sys.exit(f"Error crítico de importación: {e}. Asegúrate de estar en la raíz del proyecto.")
# Mapa inical
try:
    from analisis_inicial import generar_analisis_previo
except ImportError:
    def generar_analisis_previo(): print("   (Saltando análisis inicial...)")

try:
    from visualizacion import generar_mapas_y_graficos
except ImportError:
    def generar_mapas_y_graficos(r): print(f"   (No se pueden generar mapas para {r})")

def main():
    print("=========================================================")
    print("     PROYECTO HELICYL: EJECUCIÓN                         ")
    print("=========================================================")

    # ANÁLISIS PREVIO 
    print("\nGenerando mapas de análisis inicial (ANTES)...")
    try:
        generar_analisis_previo()
    except Exception as e:
        print(f" Aviso: No se pudo generar el análisis previo ({e})")
        print("(Esto no afecta al cálculo del modelo, continuamos...)")

    # GENERACIÓN DE CANDIDATOS 
    print("\n Generando candidatos estratégicos...") 
    try:
        generar_candidatos_masivos.generar_masivos()
        print(" Candidatos generados correctamente.")
    except Exception as e:
        print(f"Alerta: No se pudieron regenerar candidatos ({e}).")

    # CARGA DE DATOS
    print("\nCargando datos del sistema...") 
    try:
        df_mun, df_cand = datos.cargar_datos()
    except Exception as e:
        print(f"Error fatal en datos: {e}")
        return

    # MATRIZ DE TIEMPOS 
    print("\n Calculando matriz de tiempos de vuelo...") 
    tiempos = datos.generar_matriz_tiempos(df_mun, df_cand)
    
    # OPTIMIZACIÓN DE ESCENARIOS 
    print("Optimizando escenarios (A, B, C)...") 
    
    escenarios = [
        {"nombre": "A_Eficiencia", "w_t": 1.0, "w_c": 0.0},
        {"nombre": "B_Equilibrado", "w_t": 0.5, "w_c": 0.5},
        {"nombre": "C_Equidad",     "w_t": 0.1, "w_c": 0.9}
    ]
    
    resumen_global = []
    if not os.path.exists("data"):
        os.makedirs("data")

    for esc in escenarios:
        print(f"\n   --- Procesando Escenario: {esc['nombre']} ---")
        
        # 1. Ejecutar el modelo matemático
        bases, df_res = modelo.resolver_modelo(
            df_mun, df_cand, tiempos, 
            peso_tiempo=esc['w_t'], 
            peso_cobertura=esc['w_c'],
            radio_ideal_km=30
        )
        
        if not bases:
            print(f"Fallo al resolver {esc['nombre']}")
            continue
            
        df_final = df_res.merge(
            df_mun[['id', 'municipio', 'poblacion', 'lat', 'lon']], 
            left_on='municipio_id', right_on='id'
        )
        df_final = df_final.merge(
            df_cand[['id', 'nombre', 'lat', 'lon']], #
            left_on='base_asignada_id', right_on='id', 
            suffixes=('_mun', '_base')
        )
        
        # 3. TRADUCIR COLUMNAS 
        df_final = df_final.rename(columns={
            'lat_mun': 'lat_muni',
            'lon_mun': 'lon_muni',
            'lat_base': 'lat_heli',
            'lon_base': 'lon_heli',
            'nombre': 'helipuerto_nombre'
        })

        # Calculamos distancia aprox si no existe
        if 'distancia_km' not in df_final.columns:
             df_final['distancia_km'] = (df_final['tiempo_minutos'] / 60) * 220

        # Guardar CSV
        fichero = os.path.join("data", f"solucion_{esc['nombre']}.csv")
        df_final.to_csv(fichero, index=False, sep=',', encoding='utf-8')
        print(f" Solución guardada en: {fichero}")
        
        # 4. VISUALIZACIÓN
        print(f"Generando mapas visuales...")
        try:
            generar_mapas_y_graficos(fichero)
        except Exception as e:
            print(f"Error visualización: {e}")

        # 5. Estadísticas
        t_medio = df_final['tiempo_minutos'].mean()
        pob_cubierta = df_final[df_final['tiempo_minutos'] <= 15]['poblacion'].sum()
        pct_cobertura = (pob_cubierta / df_final['poblacion'].sum()) * 100
        
        resumen_global.append({
            "Escenario": esc['nombre'],
            "Tiempo Medio (min)": round(t_medio, 2),
            "Cobertura <15min (%)": round(pct_cobertura, 2),
            "Bases Seleccionadas": len(bases)
        })

    # INFORME FINAL 
    print("\nGenerando informe comparativo...") 
    if resumen_global:
        df_resumen = pd.DataFrame(resumen_global)
        ruta_resumen = os.path.join("data", "INFORME_COMPARATIVA.csv")
        df_resumen.to_csv(ruta_resumen, index=False, sep=';')
        
        print("\n" + "="*45)
        print(" RESUMEN DE RESULTADOS")
        print("="*45)
        print(df_resumen[['Escenario', 'Tiempo Medio (min)', 'Cobertura <15min (%)']].to_string(index=False))
    else:
        print(" No se generaron resultados.")

if __name__ == "__main__":
    main()