import pandas as pd
import os

# -
# Como este archivo está en 'src/', tenemos que subir un nivel para llegar a la raíz
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SRC_DIR)
DATA_DIR = os.path.join(ROOT_DIR, "data")

MUNIC_CSV = os.path.join(DATA_DIR, "municipios_cyl.csv")
CAND_CSV = os.path.join(DATA_DIR, "candidatos.csv")

TOP_N = 8  # Con 8 por provincia tendremos ~80 candidatos

def generar_masivos():
    print(f" Generando Top {TOP_N} Candidatos por Provincia")
    
    # 1. Cargar Municipios (con el separador correcto)
    if not os.path.exists(MUNIC_CSV):
        print(f"Error: No encuentro el archivo en {MUNIC_CSV}")
        return

    try:
        df_m = pd.read_csv(MUNIC_CSV, sep=';', encoding='utf-8')
    except:
        df_m = pd.read_csv(MUNIC_CSV, sep=',', encoding='utf-8')
        
    # Limpieza rapida de columnas para que no falle
    df_m.columns = df_m.columns.str.strip().str.lower().str.replace('ó','o').str.replace('á','a')
    
    # Mapeo flexible
    mapa = {
        'cod_ine': 'id', 'ine': 'id', 
        'poblacion': 'poblacion', 'habitantes': 'poblacion',
        'latitud': 'lat', 'longitud': 'lon', 
        'provincia': 'provincia', 'municipio': 'nombre'
    }
    df_m.rename(columns=mapa, inplace=True)
    
    # Lógica del Bierzo 
    def get_region(row):
        nombre = str(row['nombre']).upper()
        # Lista rápida de municipios del Bierzo para separarlos
        bierzo_keys = ['PONFERRADA', 'BEMBIBRE', 'VILLAFRANCA DEL BIERZO', 'CACABELOS', 'FABERO']
        if any(k in nombre for k in bierzo_keys): 
            return 'El Bierzo'
        return row['provincia']
    
    df_m['region_temp'] = df_m.apply(get_region, axis=1)
    
    # Selección de Candidatoss
    nuevos_candidatos = []
    
    # Para cada región (Ávila, Burgos... El Bierzo), cogemos los N más grandes
    for reg in df_m['region_temp'].unique():
        # Ordenar por población y coger los TOP_N
        top_pueblos = df_m[df_m['region_temp'] == reg].nlargest(TOP_N, 'poblacion')
        
        for _, row in top_pueblos.iterrows():
            nuevos_candidatos.append({
                'id': row['id'],
                'nombre': f"Base {row['nombre']}", # Le ponemos "Base" para que quede pro
                'tipo': 'Aerodromo/Helipuerto',
                'municipio': row['nombre'],
                'provincia': row['provincia'], # Guardamos la provincia oficial
                'lat': row['lat'],
                'lon': row['lon'],
                'nota': f"Candidato Top {TOP_N} Poblacion"
            })
            
    df_final = pd.DataFrame(nuevos_candidatos)
    
    # 4. Guardar
    df_final.to_csv(CAND_CSV, index=False, sep=',')
    print(f"Archivo actualizado en: {CAND_CSV}")
    print(f"   -> Total candidatos: {len(df_final)}")

if __name__ == "__main__":
    generar_masivos()