import pandas as pd
import numpy as np
from io import StringIO
import pathlib
import re
import os


def crear_tabla_pattern(nombre_hoja):
    """Devuelve un patrón que permite extraer el nombre de la tabla a partir del nombre de la hoja.
    Si tiene más digitos el nombre de la hoja, el patrón tiene que tenerlo en cuenta."""
    # Define the regular expression pattern
    pattern = r"hoja-\d+\.[IVXLCDM]+\.((?:\d+\.)*\d+)"
    # Find the part of the string after the Roman numeral
    match = re.match(pattern, nombre_hoja)
    if match:
        # Extract the part of the string after the Roman numeral
        numbers_part = match.group(1)
        # Split the part by dots and count the numbers
        numbers = numbers_part.split(".")
        l_numeros = len(numbers)
    else:
        l_numeros = 0
    tabla_pattern = re.compile(
        "(?P<tabla>1\.[IV]+" + r"\.[0-9]+" * (l_numeros + 1) + ")"
    )
    return tabla_pattern


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


def extraer_tablas(hoja_path, definiciones_file, tabla_pattern):
    with open(hoja_path, "r") as hoja:
        lineas = [re.sub("\\n$", "", linea) for linea in hoja.readlines()]
        tablas = pd.DataFrame(
            columns=[
                "tabla",
                "inicio",
                "descripcion",
                "definicion",
            ]
        )
        # identifica las lineas que contienen el nombre de la tabla.
        # la linea siguiente contiene la definición
        # guardamos también el número de línea que empieza
        for nr, linea in enumerate(lineas):
            if match_object := tabla_pattern.match(linea):
                nombre_tabla = match_object.groupdict()["tabla"]
                tabla_desc = linea.split(" - ")[1].replace("|", "")
                definicion = lineas[nr + 1].replace("|", "")
                tablas.loc[len(tablas)] = [
                    nombre_tabla,
                    nr,
                    tabla_desc,
                    definicion,
                ]
                definiciones_file.write(
                    "|".join([nombre_tabla, tabla_desc, definicion]) + "\n"
                )

        # la linea de fin de la tabla, es cuando empieza la siguiente, menos cuando es la última.
        tablas["fin"] = (
            tablas["inicio"].shift(-1, fill_value=(len(lineas) + 1)).astype(int)
        )
        for i in range(len(tablas)):
            data_string = lineas[(tablas["inicio"][i] + 3) : tablas["fin"][i]]
            split_data = [row.split("|") for row in data_string]
            tabla_df = pd.DataFrame(split_data)
            tabla_df.replace("", np.nan, inplace=True)
            tabla_df.dropna(axis=0, how="all", inplace=True)
            ## Ponemos nombres para las columnas, que serán las de la columna con los años.
            s = tabla_df.iloc[:, 0]
            first_year_index = s[s == LISTA_ANYOS[0]].index[0]
            labels = [f"V{i+1}" for i in range(first_year_index)]
            # Replace elements up to and including "edicion" with the labels
            tabla_df.iloc[:first_year_index, 0] = labels
            tabla_df.set_index(0, inplace=True)
            print(tablas["tabla"][i])
            tabla_df = tabla_df.T
            tabla_df.dropna(axis=0, how="all", inplace=True)
            print(tabla_df)
            tabla_df.to_csv(
                TABLAS_DIRECTORY / f"tabla-{tablas['tabla'][i]}.csv", index=False
            )


if __name__ == "__main__":

    ## ----- aquí configurar para anio --------
    ANYO = "2023"
    # El encoding de los ficheros que pasa Mari Carmen
    ENCODING = "windows-1252"

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
            print(hoja_path.name)
            tabla_pattern = crear_tabla_pattern(hoja_retocada_path.name)
            extraer_tablas(hoja_retocada_path, definiciones_file, tabla_pattern)
