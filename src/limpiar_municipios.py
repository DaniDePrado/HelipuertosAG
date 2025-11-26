import csv

INPUT_FILE = "../data/municipios_cyl.csv"
OUTPUT_FILE = "../data/datos_municipios.csv"



def limpiar_poblacion(valor):
    """Deja solo dígitos en la población (por si lleva puntos, espacios, etc.)."""
    if valor is None:
        return ""
    valor = str(valor)
    digitos = [ch for ch in valor if ch.isdigit()]
    if not digitos:
        return ""
    return "".join(digitos)


def limpiar_coord(valor):
    """Convierte '41,2345' en '41.2345' y quita espacios."""
    if valor is None:
        return ""
    valor = str(valor).strip().replace(",", ".")
    return valor


# Abrimos el fichero original y detectamos el separador (coma, punto y coma, etc.)
with open(INPUT_FILE, "r", encoding="utf-8-sig", newline="") as f_in:
    muestra = f_in.read(2048)
    f_in.seek(0)

    sniffer = csv.Sniffer()
    try:
        dialect = sniffer.sniff(muestra)
    except csv.Error:
        # Si no consigue detectar, por defecto usamos ';'
        dialect = csv.excel
        dialect.delimiter = ';'

    reader = csv.DictReader(f_in, dialect=dialect)

    # Creamos el fichero de salida
    with open(OUTPUT_FILE, "w", encoding="utf-8", newline="") as f_out:
        writer = csv.writer(f_out, delimiter=',')
        # Cabecera estándar
        writer.writerow(["cod_ine", "municipio", "provincia", "poblacion", "latitud", "longitud"])

        for fila in reader:
            cod_ine = fila.get("Cod_INE", "").strip()
            municipio = fila.get("Municipio", "").strip()
            provincia = fila.get("Provincia", "").strip()
            poblacion = limpiar_poblacion(fila.get("Población", ""))
            latitud = limpiar_coord(fila.get("Latitud", ""))
            longitud = limpiar_coord(fila.get("Longitud", ""))

            writer.writerow([cod_ine, municipio, provincia, poblacion, latitud, longitud])

print("✅ He creado el archivo", OUTPUT_FILE)
