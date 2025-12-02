# src/main.py
import sys
import os

# Importamos nuestros módulos
# Nota: p_mediana debe llamarse p_mediana.py (con guion bajo preferiblemente)
# si tu archivo se llama "p-mediana.py" (con guion medio), el import fallará.
# RENOMBRA "p-mediana.py" a "p_mediana.py" o usa importlib.
# Asumiremos que lo renombras a p_mediana.py por convención de Python.

try:
    from p_mediana import ejecutar_modelo
except ImportError:
    # Truco por si el archivo tiene guion medio y no quieres renombrarlo
    import importlib
    p_mediana = importlib.import_module("p-mediana")
    ejecutar_modelo = p_mediana.ejecutar_modelo

from visualizacion import generar_mapas_y_graficos

def main():
    print("==================================================")
    print("      SISTEMA DE OPTIMIZACIÓN DE HELIPUERTOS      ")
    print("==================================================")

    # 1. Ejecutar el modelo matemático
    # Esta función hace los cálculos y genera 'solucion_asignaciones.csv'
    ruta_csv = ejecutar_modelo()

    if ruta_csv:
        print("\n✅ Modelo matemático finalizado con éxito.")
        
        # 2. Ejecutar la visualización
        # Usa el CSV generado para pintar el mapa y los gráficos
        generar_mapas_y_graficos(ruta_csv)
        
        print("\n✅ Proceso completo.")
        print(f"Revisa la carpeta '../data' para ver los resultados.")
    else:
        print("\n❌ Hubo un error en la ejecución del modelo.")

if __name__ == "__main__":
    main()