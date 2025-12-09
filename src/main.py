import pandas as pd
import os
import sys

# Importamos todos tus módulos
try:
    import datos
    import modelo
    # IMPORTANTE: Importamos el generador para ejecutarlo aquí
    import generar_candidatos_masivos 
except ImportError as e:
    sys.exit(f"❌ Error crítico de importación: {e}. Asegúrate de estar en la raíz del proyecto.")

def main():
    print("=========================================================")
    print("   🚁  PROYECTO HELICYL: EJECUCIÓN MAESTRA (AUTO)  🚁")
    print("=========================================================")

    # --- PASO 0: GENERACIÓN AUTOMÁTICA DE CANDIDATOS ---
    # Esto asegura que el profesor tenga los ~80 candidatos creados al momento
    print("\n>>> [PASO 0] Generando candidatos estratégicos...")
    try:
        # Llamamos a la función que creaste en el otro script
        generar_candidatos_masivos.generar_masivos()
        print("   ✅ Candidatos generados correctamente.")
    except Exception as e:
        print(f"   ⚠️ Alerta: No se pudieron regenerar candidatos ({e}).")
        print("      Intentando usar el archivo 'candidatos.csv' existente...")

    # --- PASO 1: CARGA DE DATOS ---
    print("\n>>> [PASO 1] Cargando datos del sistema...")
    try:
        df_mun, df_cand = datos.cargar_datos()
    except Exception as e:
        print(f"❌ Error en datos: {e}")
        return

    # --- PASO 2: MATRIZ DE TIEMPOS ---
    print("\n>>> [PASO 2] Calculando matriz de tiempos de vuelo...")
    # Esto puede tardar un poco con 80 candidatos, es normal
    tiempos = datos.generar_matriz_tiempos(df_mun, df_cand)
    
    # --- PASO 3: EJECUCIÓN DE ESCENARIOS ---
    print("\n>>> [PASO 3] Optimizando escenarios...")
    
    escenarios = [
        {"nombre": "A_Eficiencia", "w_t": 1.0, "w_c": 0.0},
        {"nombre": "B_Equilibrado", "w_t": 0.5, "w_c": 0.5},
        {"nombre": "C_Equidad",     "w_t": 0.1, "w_c": 0.9}
    ]
    
    resumen_global = []
    # Usamos la ruta relativa para guardar datos
    ruta_data = os.path.dirname(df_cand.iloc[0].name) if hasattr(df_cand, 'name') else "data"
    # Fallback seguro para la ruta
    if not os.path.exists(ruta_data): ruta_data = "data"

    for esc in escenarios:
        print(f"   ⚙️  Procesando: {esc['nombre']}...")
        
        bases, df_res = modelo.resolver_modelo(
            df_mun, df_cand, tiempos, 
            peso_tiempo=esc['w_t'], 
            peso_cobertura=esc['w_c'],
            radio_ideal_km=30
        )
        
        if not bases:
            print(f"      ❌ Fallo en {esc['nombre']}")
            continue
            
        # Enriquecer y Guardar
        df_final = df_res.merge(df_mun[['id', 'municipio', 'poblacion']], left_on='municipio_id', right_on='id')
        df_final = df_final.merge(df_cand[['id', 'nombre', 'region']], left_on='base_asignada_id', right_on='id', suffixes=('_mun', '_base'))
        
        fichero = os.path.join("data", f"solucion_{esc['nombre']}.csv")
        df_final.to_csv(fichero, index=False, sep=';', encoding='utf-8')
        
        # Métricas
        t_medio = df_final['tiempo_minutos'].mean()
        # Cobertura <15 min
        pob_cubierta = df_final[df_final['tiempo_minutos'] <= 15]['poblacion'].sum()
        pct_cobertura = (pob_cubierta / df_final['poblacion'].sum()) * 100
        
        resumen_global.append({
            "Escenario": esc['nombre'],
            "Tiempo Medio (min)": round(t_medio, 2),
            "Cobertura <15min (%)": round(pct_cobertura, 2),
            "Bases Seleccionadas": len(bases)
        })

    # --- PASO 4: INFORME FINAL ---
    print("\n>>> [PASO 4] Generando informe comparativo...")
    if resumen_global:
        df_resumen = pd.DataFrame(resumen_global)
        ruta_resumen = os.path.join("data", "INFORME_COMPARATIVA.csv")
        df_resumen.to_csv(ruta_resumen, index=False, sep=';')
        
        print("\n" + "="*45)
        print("📊 RESUMEN DE RESULTADOS (Listo para entregar)")
        print("="*45)
        print(df_resumen[['Escenario', 'Tiempo Medio (min)', 'Cobertura <15min (%)']].to_string(index=False))
        print("\n✅ Ejecución completada con éxito.")
    else:
        print("❌ No se generaron resultados.")

if __name__ == "__main__":
    main()