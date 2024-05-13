import pandas as pd
import pathlib
import re
import os


tabla_pattern = re.compile("(?P<tabla>1\.[IV]+\.[0-9]+\.[0-9]+)")


def unir_lineas(hoja_path):
    with open(hoja_path, "r", encoding=ENCODING) as hoja:
        lineas = hoja.readlines()

        separadores = pd.Series([linea.count("|") for linea in lineas])
        num_separadores = separadores.value_counts().idxmax()

        hoja_retocada_path = TMP_DIRECTORY / hoja_path.name

        with open(hoja_retocada_path, "w") as output_file:
            linea_file = ""
            separador_linea = 0

            for i, linea in enumerate(lineas):
                linea_file += linea.replace("\n", "")
                separador_linea += separadores[i]

                if separador_linea == num_separadores:
                    output_file.write(linea_file + "\n")

                    linea_file = ""
                    separador_linea = 0

                elif separador_linea > num_separadores:
                    raise Exception(
                        f"La suma de separadores es superior a {num_separadores}"
                    )

    return hoja_retocada_path


def extraer_tablas(hoja_path, definiciones_file):
    with open(hoja_path, "r") as hoja:
        nr_nivel = 1000000000
        tabla_in = False

        for nr, linea in enumerate(hoja):
            campos = re.sub("\\n$", "", linea).split("|")

            if match_object := tabla_pattern.match(linea):
                nombre_tabla = match_object.groupdict()["tabla"]
                tabla_desc = campos[0]

            if campos[0] == "Provisión:":
                definicion = campos[5]

                definiciones_file.write(
                    "|".join([nombre_tabla, tabla_desc, definicion]) + "\n"
                )

            if campos[0] == "Nivel:":
                nr_nivel = nr

            if nr == (nr_nivel + 4):
                tabla_in = True
                n_lineas = 0
                tabla_list = []

            if (nr >= (nr_nivel + 4)) & tabla_in:

                n_lineas += 1

                if re.match("20[1-2][0-9]", campos[0]) is None:
                    n_columnas = 1
                    if campos[0] == "":
                        campos[0] = f"Var{n_lineas}"

                    for j, campo in enumerate(campos[1:]):
                        if campo != "":
                            current = campo
                        else:
                            campos[j + 1] = current

                tabla_list.append(campos)

                ## si estamos en 2021, consideramos que hemos acabado la tabla
                ## eso hay que cambiarlo todos los años
                if campos[0] == ANYO:
                    tabla_in = False

                    transposed_tuples = list(zip(*tabla_list))
                    tlineas = [list(sublist) for sublist in transposed_tuples]

                    with open(
                        TABLAS_DIRECTORY / f"tabla-{nombre_tabla}.csv", "w"
                    ) as tabla_file:
                        for tlinea in tlineas:
                            tabla_file.write("|".join(tlinea) + "\n")

                    print(f"Tabla extraida: {nombre_tabla}")


def limpiar_tabla(tabla_path, years_list):
    """quita filas vacias para los años de years_list"""
    tabla = pd.read_csv(tabla_path, delimiter="|")
    tabla.dropna(subset=years_list, how="all", inplace=True)
    tabla.to_csv(TABLAS_DIRECTORY / tabla_path.name, index=False, sep="|")


if __name__ == "__main__":

    ## ----- aquí configurar para anio --------
    ANYO = "2023"
    # El encoding de los ficheros que pasa Mari Carmen
    ENCODING = "latin-1"

    # especificamos el triplete de años para limpiar filas vacias, que no
    # datos en ninguno de estos tres años.
    LISTA_ANYOS = [
        "2021",
        "2022",
        "2023",
    ]

    CSV_DIRECTORY = pathlib.Path("2022-23") / "hojascsv"
    ## ----- fin  configurar para anio --------

    TABLAS_DIRECTORY = CSV_DIRECTORY / "tablascsv"
    if not TABLAS_DIRECTORY.exists():
        os.mkdir(TABLAS_DIRECTORY)

    TMP_DIRECTORY = CSV_DIRECTORY / "tmp"
    if not TMP_DIRECTORY.exists():
        os.mkdir(TMP_DIRECTORY)

    with open(TABLAS_DIRECTORY / "definiciones-tablas.csv", "w") as definiciones_file:
        for hoja_path in CSV_DIRECTORY.glob("hoja*.csv"):
            print(f"hoja: {hoja_path}")

            hoja_retocada_path = unir_lineas(hoja_path)

            extraer_tablas(hoja_retocada_path, definiciones_file)

    for tabla_path in TABLAS_DIRECTORY.glob("tabla*.csv"):
        print(f"Limpiando tabla: {tabla_path}")
        limpiar_tabla(tabla_path, LISTA_ANYOS)
