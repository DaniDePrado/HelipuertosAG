import sys
import os

# --- IMPORTACIÓN DE MÓDULOS ---

# 1. Importar el Análisis Inicial (Mapas del "Antes")
# Este es el archivo nuevo que creaste a partir del notebook
try:
    from analisis_inicial import generar_analisis_previo
except ImportError:
    print("AVISO: No se encontró 'analisis_inicial.py'.")
    # Creamos una función vacía para que no falle el programa si te falta el archivo
    def generar_analisis_previo(): 
        print("Saltando análisis inicial...")

# 2. Importar el Modelo Matemático (Cálculos)
try:
    from p_mediana import ejecutar_modelo
except ImportError:
    # Truco por si el archivo se llamaba 'p-mediana' con guion medio
    import importlib
    p_mediana = importlib.import_module("p-mediana")
    ejecutar_modelo = p_mediana.ejecutar_modelo

# 3. Importar la Visualización Final (Mapas del "Después" y Gráficos)
from visualizacion import generar_mapas_y_graficos

def main():
    print("==================================================")
    print("      SISTEMA DE OPTIMIZACIÓN DE HELIPUERTOS      ")
    print("==================================================")

    # --- PASO 1: ANÁLISIS PREVIO ---
    print("\nGenerando mapas de análisis inicial...")
    # Esto crea: 'mapa_inicial_cyl.html' y 'mapa_analisis_cobertura.html'
    generar_analisis_previo()

    # --- PASO 2: EJECUCIÓN DEL MODELO ---
    print("\nEjecutando modelo matemático de optimización...")
    # Esto genera el archivo 'solucion_asignaciones.csv'
    ruta_csv = ejecutar_modelo()

    if ruta_csv:
        print("Modelo matemático finalizado con éxito.")
        
        # --- PASO 3: VISUALIZACIÓN DE RESULTADOS ---
        print("\nGenerando mapas y gráficos finales...")
        # Esto crea: 'Mapa_Final_Asignaciones.html' y los gráficos PNG
        generar_mapas_y_graficos(ruta_csv)
        
        print("\n==================================================")
        print("       ✅ PROCESO COMPLETO EXITOSAMENTE           ")
        print("==================================================")
        print("📂 RESULTADOS DISPONIBLES EN:")
        print("   -> Mapas interactivos: carpeta '../maps'")
        print("   -> Gráficos estadísticos: carpeta '../maps'")
        print("==================================================")
    else:
        print("\n❌ ERROR: El modelo matemático no devolvió una solución válida.")

if __name__ == "__main__":
    main()