import pandas as pd
import os
import sys

try:
    import datos
    import modelo
except ImportError:
    sys.exit("❌ Error: Ejecuta desde la carpeta raíz (python src/main.py)")

def main():
    print("===========================================")
    print("   🚁  HELICYL: GENERADOR DE ESCENARIOS  🚁")
    print("===========================================")
    
    # 1. Cargar Datos
    try:
        df_mun, df_cand = datos.cargar_datos()
    except Exception as e:
        print(f"❌ Error: {e}"); return

    # 2. Calcular Tiempos
    tiempos = datos.generar_matriz_tiempos(df_mun, df_cand)
    
    # --- DEFINICIÓN DE ESCENARIOS PARA EL INFORME ---
    escenarios = [
        # Escenario A: Solo importa la media (P-Mediana puro) -> Muy rápido, poco equitativo
        {"nombre": "A_Eficiencia", "w_t": 1.0, "w_c": 0.0},
        
        # Escenario B: Balanceado -> El recomendado
        {"nombre": "B_Equilibrado", "w_t": 0.5, "w_c": 0.5},
        
        # Escenario C: Equidad -> Prioriza que nadie quede lejos, aunque suba la media
        {"nombre": "C_Equidad",     "w_t": 0.1, "w_c": 0.9}
    ]
    
    resumen_global = []
    ruta_data = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

    for esc in escenarios:
        print(f"\n>>> Procesando Escenario: {esc['nombre']}...")
        
        bases, df_res = modelo.resolver_modelo(
            df_mun, df_cand, tiempos, 
            peso_tiempo=esc['w_t'], 
            peso_cobertura=esc['w_c'],
            radio_ideal_km=30
        )
        
        if not bases:
            print("   ❌ Falló el solver.")
            continue
            
        # Enriquecer datos con nombres
        df_final = df_res.merge(df_mun[['id', 'municipio', 'poblacion']], left_on='municipio_id', right_on='id')
        df_final = df_final.merge(df_cand[['id', 'nombre', 'region']], left_on='base_asignada_id', right_on='id', suffixes=('_mun', '_base'))
        
        # Guardar CSV individual
        fichero = os.path.join(ruta_data, f"solucion_{esc['nombre']}.csv")
        df_final.to_csv(fichero, index=False, sep=';', encoding='utf-8')
        print(f"   ✅ Guardado: {fichero}")
        
        # Calcular métricas para la tabla del informe
        t_medio = df_final['tiempo_minutos'].mean()
        t_max = df_final['tiempo_minutos'].max()
        # Cobertura: % de gente a menos de 30km (aprox 15 min)
        pob_cubierta = df_final[df_final['tiempo_minutos'] <= 15]['poblacion'].sum()
        pob_total = df_final['poblacion'].sum()
        pct_cobertura = (pob_cubierta / pob_total) * 100
        
        resumen_global.append({
            "Escenario": esc['nombre'],
            "Tiempo Medio (min)": round(t_medio, 2),
            "Tiempo Máximo (min)": round(t_max, 2),
            "Cobertura <15min (%)": round(pct_cobertura, 2),
            "Bases Seleccionadas": str(bases)
        })

    # Guardar Tabla Comparativa
    df_resumen = pd.DataFrame(resumen_global)
    ruta_resumen = os.path.join(ruta_data, "INFORME_COMPARATIVA.csv")
    df_resumen.to_csv(ruta_resumen, index=False, sep=';')
    
    print("\n" + "="*40)
    print("📊 TABLA DE RESULTADOS (Para copiar al informe):")
    print(df_resumen[['Escenario', 'Tiempo Medio (min)', 'Cobertura <15min (%)']].to_string(index=False))
    print(f"\nArchivo completo en: {ruta_resumen}")
    print("===========================================")

if __name__ == "__main__":
    main()